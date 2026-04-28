"""
Model loading and inference wrapper.
Supports baseline (full-cache) and OBVGGT (compressed-cache) modes.
"""

import os
import sys
import gc
import glob

import torch
import numpy as np

# Add OBVGGT/src to path so we can import the model
_SRC = os.path.join(os.path.dirname(__file__), "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from streamvggt.models.streamvggt import StreamVGGT
from streamvggt.utils.load_fn import load_and_preprocess_images
from streamvggt.utils.pose_enc import pose_encoding_to_extri_intri
from visual_util import predictions_to_glb

from monitor import GPUMonitor, RunMetrics

# ── KV cache configs ────────────────────────────────────────────────

OBVGGT_CONFIGS = {
    "p1_no_recent_ctrl": {
        "enable": True,
        "method": "joint",
        "p": 1,
        "use_vnorm": True,
        "num_sink_frames": 1,
        "num_recent_frames": 0,
        "num_heavy_frames": 4,
        "probe_mode": True,
        "num_patch_probes": 8,
    },
    "default": {
        "enable": True,
        "method": "joint",
        "p": 2,
        "use_vnorm": True,
        "num_sink_frames": 1,
        "num_recent_frames": 2,
        "num_heavy_frames": 4,
        "probe_mode": True,
        "num_patch_probes": 8,
    },
}

# ── Model loading ───────────────────────────────────────────────────

_model_cache: StreamVGGT | None = None


def load_model() -> StreamVGGT:
    """Load StreamVGGT model (cached after first call)."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    local_paths = [
        os.path.join(os.path.dirname(__file__), "..", "ckpt", "checkpoints.pth"),
        "ckpt/checkpoints.pth",
    ]

    ckpt_path = None
    for p in local_paths:
        if os.path.isfile(p):
            ckpt_path = p
            break

    model = StreamVGGT()

    if ckpt_path:
        print(f"Loading checkpoint from {ckpt_path}")
        ckpt = torch.load(ckpt_path, map_location="cpu")
    else:
        print("Downloading checkpoint from HuggingFace...")
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id="lch01/StreamVGGT",
            filename="checkpoints.pth",
            revision="main",
        )
        ckpt = torch.load(path, map_location="cpu")

    model.load_state_dict(ckpt, strict=True)
    model.eval()
    del ckpt

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    _model_cache = model
    return model


# ── Image loading helpers ───────────────────────────────────────────

def load_images_from_dir(image_dir: str) -> torch.Tensor:
    """Load and preprocess images from a directory. Returns (S, 3, H, W)."""
    names = sorted(glob.glob(os.path.join(image_dir, "*")))
    names = [n for n in names if n.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]
    if not names:
        raise ValueError(f"No images found in {image_dir}")
    return load_and_preprocess_images(names)


def load_images_from_paths(paths: list[str]) -> torch.Tensor:
    """Load and preprocess images from a list of file paths."""
    if not paths:
        raise ValueError("Empty image list")
    return load_and_preprocess_images(sorted(paths))


def video_to_frames(video_path: str, target_fps: int = 1) -> list[np.ndarray]:
    """Extract frames from a video file at target_fps."""
    import cv2
    cap = cv2.VideoCapture(video_path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    interval = max(1, int(src_fps / target_fps))

    frames = []
    idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % interval == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += 1
    cap.release()
    return frames


# ── Core inference ──────────────────────────────────────────────────

def run_inference(
    images: torch.Tensor,
    kv_cache_cfg: dict | None = None,
) -> tuple[dict, RunMetrics]:
    """
    Run streaming inference on images.

    Args:
        images: (S, 3, H, W) preprocessed image tensor
        kv_cache_cfg: None for baseline, dict for OBVGGT

    Returns:
        predictions dict, RunMetrics
    """
    model = load_model()
    device = next(model.parameters()).device
    images = images.to(device)

    frames = [{"img": images[i].unsqueeze(0)} for i in range(images.shape[0])]

    dtype = (
        torch.bfloat16
        if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8
        else torch.float16
    )

    monitor = GPUMonitor()
    monitor.reset()
    metrics = RunMetrics()

    try:
        with torch.no_grad(), torch.cuda.amp.autocast(dtype=dtype):
            # StreamVGGT.inference processes frames one-at-a-time internally
            monitor.frame_start()
            output = model.inference(frames, kv_cache_cfg=kv_cache_cfg)

            # Record a single summary metric for the whole run
            fm = monitor.frame_end(len(frames) - 1)
            metrics.frames.append(fm)
            metrics.total_elapsed_sec = fm.elapsed_sec

    except torch.cuda.OutOfMemoryError:
        metrics.oom = True
        metrics.oom_at_frame = len(metrics.frames)
        torch.cuda.empty_cache()
        return {}, metrics

    # Collect per-frame outputs
    all_pts3d, all_conf, all_depth, all_depth_conf, all_pose = [], [], [], [], []
    for res in output.ress:
        all_pts3d.append(res["pts3d_in_other_view"].squeeze(0))
        all_conf.append(res["conf"].squeeze(0))
        all_depth.append(res["depth"].squeeze(0))
        all_depth_conf.append(res["depth_conf"].squeeze(0))
        all_pose.append(res["camera_pose"].squeeze(0))

    predictions = {
        "images": images,
        "world_points": torch.stack(all_pts3d, dim=0),
        "world_points_conf": torch.stack(all_conf, dim=0),
        "depth": torch.stack(all_depth, dim=0),
        "depth_conf": torch.stack(all_depth_conf, dim=0),
        "pose_enc": torch.stack(all_pose, dim=0),
    }

    # Pose → extrinsic/intrinsic
    pose = predictions["pose_enc"]
    if pose.ndim == 2:
        pose = pose.unsqueeze(0)
    extrinsic, intrinsic = pose_encoding_to_extri_intri(pose, images.shape[-2:])
    predictions["extrinsic"] = extrinsic.squeeze(0)
    predictions["intrinsic"] = intrinsic.squeeze(0) if intrinsic is not None else None
    predictions["world_points_from_depth"] = predictions["world_points"]

    # To numpy
    preds_np = {}
    for k, v in predictions.items():
        preds_np[k] = v.cpu().numpy() if isinstance(v, torch.Tensor) else v

    torch.cuda.empty_cache()
    return preds_np, metrics


# ── Per-frame streaming inference (for live depth demo) ─────────────

def run_streaming_inference(
    images: torch.Tensor,
    kv_cache_cfg: dict | None = None,
):
    """
    Generator that yields (frame_idx, depth_map_np, frame_metrics) per frame.
    Suitable for live visualization in Tab 2.
    """
    model = load_model()
    device = next(model.parameters()).device
    images = images.to(device)

    dtype = (
        torch.bfloat16
        if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8
        else torch.float16
    )

    monitor = GPUMonitor()
    monitor.reset()

    past_key_values = None

    for i in range(images.shape[0]):
        frame = [{"img": images[i].unsqueeze(0)}]

        monitor.frame_start()
        try:
            with torch.no_grad(), torch.cuda.amp.autocast(dtype=dtype):
                output = model.inference(frame, kv_cache_cfg=kv_cache_cfg)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            yield i, None, None, True
            return

        fm = monitor.frame_end(i)

        depth = output.ress[-1]["depth"].squeeze(0)  # (H, W, 1)
        depth_np = depth[..., -1].cpu().numpy()  # (H, W)

        yield i, depth_np, fm, False


# ── GLB generation ──────────────────────────────────────────────────

def make_glb(predictions: dict, conf_thresh: float = 50.0) -> str:
    """Build a GLB file from predictions and return the path."""
    import tempfile
    glb_path = os.path.join(tempfile.mkdtemp(), "scene.glb")

    scene = predictions_to_glb(
        predictions,
        conf_thres=conf_thresh / 100.0,
        filter_by_frames="all",
        target_dir=None,
    )
    scene.export(glb_path)
    return glb_path
