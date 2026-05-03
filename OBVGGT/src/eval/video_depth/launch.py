import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import math
import cv2
import numpy as np
import torch
import argparse
import json
import random

from copy import deepcopy
from eval.video_depth.metadata import dataset_metadata
from eval.video_depth.utils import save_depth_maps
from accelerate import PartialState
from add_ckpt_path import add_path_to_dust3r
from streamvggt.utils.phase_profile import (
    phase_profile_end,
    phase_profile_start,
    reset_phase_profile,
    snapshot_phase_profile,
)
import time
from tqdm import tqdm


def _str2bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _set_random_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def get_args_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--weights",
        type=str,
        help="path to the model weights",
        default="",
    )

    parser.add_argument("--device", type=str, default="cuda", help="pytorch device")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="",
        help="value for outdir",
    )
    parser.add_argument(
        "--no_crop", type=bool, default=True, help="whether to crop input data"
    )

    parser.add_argument(
        "--eval_dataset",
        type=str,
        default="sintel",
        choices=list(dataset_metadata.keys()),
    )
    parser.add_argument("--size", type=int, default="224")

    parser.add_argument(
        "--pose_eval_stride", default=1, type=int, help="stride for pose evaluation"
    )
    parser.add_argument(
        "--full_seq",
        action="store_true",
        default=False,
        help="use full sequence for pose evaluation",
    )
    parser.add_argument(
        "--seq_list",
        nargs="+",
        default=None,
        help="list of sequences for pose evaluation",
    )
    parser.add_argument(
        "--max_frames",
        type=int,
        default=0,
        help="If > 0, evaluate only the first N frames from each selected sequence.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducible prefix-eval and random-eviction runs.",
    )
    parser.add_argument("--kv_cache_enable", type=_str2bool, default=False)
    parser.add_argument("--kv_cache_cfg_json", type=str, default="")
    parser.add_argument(
        "--sdpa_backend",
        type=str,
        default=os.environ.get("OBVGGT_SDPA_BACKEND", "default"),
        choices=["default", "flash", "efficient", "math", "cudnn"],
        help="Force a PyTorch SDPA backend for backend-routing experiments. Default keeps PyTorch dispatch unchanged.",
    )
    parser.add_argument(
        "--rope2d_backend",
        type=str,
        default=os.environ.get("OBVGGT_ROPE2D_BACKEND", "pytorch"),
        choices=["pytorch", "auto", "cuda"],
        help="Select StreamVGGT RoPE2D backend. Default keeps the PyTorch implementation; cuda requires compiled cuRoPE2D.",
    )
    parser.add_argument(
        "--head_mode",
        type=str,
        default="full",
        choices=["full", "depth_only"],
        help="When set to depth_only, StreamVGGT inference skips camera/point/track heads for video_depth.",
    )
    parser.add_argument(
        "--phase_profile",
        type=_str2bool,
        default=False,
        help="Enable phase-level timing for profile-only runs. These runs should not be treated as formal FPS.",
    )
    return parser


def build_kv_cache_cfg(args):
    cfg = {}
    if args.kv_cache_cfg_json:
        parsed = json.loads(args.kv_cache_cfg_json)
        if not isinstance(parsed, dict):
            raise ValueError("--kv_cache_cfg_json must be a JSON object")
        cfg.update(parsed)
    enabled = bool(args.kv_cache_enable) or bool(cfg.get("enable", False))
    if not enabled:
        return None
    cfg["enable"] = True
    return cfg


def _aggregate_phase_profiles(records):
    totals = {}
    profiled = 0
    for record in records:
        phase_profile = record.get("phase_profile")
        if not isinstance(phase_profile, dict):
            continue
        phases = phase_profile.get("phases", {})
        if not isinstance(phases, dict) or not phases:
            continue
        profiled += 1
        for name, stats in phases.items():
            if not isinstance(stats, dict):
                continue
            slot = totals.setdefault(str(name), {"total_ms": 0.0, "calls": 0.0})
            slot["total_ms"] += float(stats.get("total_ms", 0.0))
            slot["calls"] += float(stats.get("calls", 0.0))

    if profiled <= 0:
        return None

    means = {
        name: {
            "mean_ms_per_profiled_sequence": float(stats["total_ms"] / profiled),
            "calls_total": float(stats["calls"]),
        }
        for name, stats in totals.items()
    }
    return {
        "profile_run": True,
        "not_for_formal_fps": True,
        "profiled_sequences": int(profiled),
        "phase_totals_ms": {name: float(stats["total_ms"]) for name, stats in totals.items()},
        "phase_means": means,
    }


def eval_pose_estimation(args, model, save_dir=None, kv_cache_cfg=None):
    metadata = dataset_metadata.get(args.eval_dataset)
    img_path = metadata["img_path"]
    mask_path = metadata["mask_path"]

    ate_mean, rpe_trans_mean, rpe_rot_mean = eval_pose_estimation_dist(
        args, model, save_dir=save_dir, img_path=img_path, mask_path=mask_path, kv_cache_cfg=kv_cache_cfg
    )
    return ate_mean, rpe_trans_mean, rpe_rot_mean


def eval_pose_estimation_dist(args, model, img_path, save_dir=None, mask_path=None, kv_cache_cfg=None):
    from dust3r.inference import loss_of_one_batch

    metadata = dataset_metadata.get(args.eval_dataset)
    anno_path = metadata.get("anno_path", None)

    seq_list = args.seq_list
    if seq_list is None:
        if metadata.get("full_seq", False):
            args.full_seq = True
        else:
            seq_list = metadata.get("seq_list", [])
        if args.full_seq:
            seq_list = os.listdir(img_path)
            seq_list = [
                seq for seq in seq_list if os.path.isdir(os.path.join(img_path, seq))
            ]
        seq_list = sorted(seq_list)

    if save_dir is None:
        save_dir = args.output_dir
    os.makedirs(save_dir, exist_ok=True)

    distributed_state = PartialState()
    _set_random_seeds(int(args.seed))
    model.to(distributed_state.device)
    device = distributed_state.device
    system_log_path = f"{save_dir}/_system_metrics_{distributed_state.process_index}.jsonl"
    if os.path.exists(system_log_path):
        os.remove(system_log_path)

    with distributed_state.split_between_processes(seq_list) as seqs:
        load_img_size = args.size
        assert load_img_size == 518
        error_log_path = f"{save_dir}/_error_log_{distributed_state.process_index}.txt"  # Unique log file per process
        for seq in tqdm(seqs):
            try:
                dir_path = metadata["dir_path_func"](img_path, seq)

                # Handle skip_condition
                skip_condition = metadata.get("skip_condition", None)
                if skip_condition is not None and skip_condition(save_dir, seq):
                    continue

                mask_path_seq_func = metadata.get(
                    "mask_path_seq_func", lambda mask_path, seq: None
                )
                mask_path_seq = mask_path_seq_func(mask_path, seq)

                filelist = [
                    os.path.join(dir_path, name) for name in os.listdir(dir_path)
                ]
                filelist.sort()
                filelist = filelist[:: args.pose_eval_stride]
                if args.max_frames and args.max_frames > 0:
                    filelist = filelist[: args.max_frames]
                num_frames = len(filelist)
                if num_frames == 0:
                    continue

                views = prepare_input(
                    filelist,
                    [True for _ in filelist],
                    size=load_img_size,
                    crop=not args.no_crop,
                )
                for view in views:
                    view["img"] = (view["img"] + 1.0) / 2.0

                if args.phase_profile:
                    reset_phase_profile()
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                    torch.cuda.reset_peak_memory_stats(device)

                inference_output_keys = ["depth"] if args.head_mode == "depth_only" else None
                model_phase = phase_profile_start("launch_model_total")
                start = time.perf_counter()
                outputs = loss_of_one_batch(
                    views,
                    model,
                    None,
                    None,
                    inference=True,
                    kv_cache_cfg=kv_cache_cfg,
                    inference_output_keys=inference_output_keys,
                )
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                end = time.perf_counter()
                phase_profile_end(model_phase)

                elapsed_sec = max(end - start, 1e-8)
                fps = float(num_frames / elapsed_sec)
                latency_ms_per_frame = float(1000.0 * elapsed_sec / num_frames)
                if device.type == "cuda":
                    peak_allocated_mb = float(torch.cuda.max_memory_allocated(device) / (1024**2))
                    peak_reserved_mb = float(torch.cuda.max_memory_reserved(device) / (1024**2))
                else:
                    peak_allocated_mb = 0.0
                    peak_reserved_mb = 0.0

                seq_stats = {
                    "sequence": seq,
                    "status": "ok",
                    "head_mode": args.head_mode,
                    "num_frames": int(num_frames),
                    "elapsed_sec": float(elapsed_sec),
                    "fps": float(fps),
                    "latency_ms_per_frame": float(latency_ms_per_frame),
                    "peak_allocated_mb": float(peak_allocated_mb),
                    "peak_reserved_mb": float(peak_reserved_mb),
                }
                kv_stats = outputs.get("kv_cache_stats", {}) if isinstance(outputs, dict) else {}
                if isinstance(kv_stats, dict):
                    for key, value in kv_stats.items():
                        try:
                            seq_stats[f"kv_{key}"] = float(value)
                        except (TypeError, ValueError):
                            continue
                runtime_diagnostics = outputs.get("runtime_diagnostics", {}) if isinstance(outputs, dict) else {}
                if isinstance(runtime_diagnostics, dict) and runtime_diagnostics:
                    seq_stats["runtime_diagnostics"] = runtime_diagnostics
                    rope2d = runtime_diagnostics.get("rope2d", {})
                    sdpa = runtime_diagnostics.get("sdpa", {})
                    if isinstance(rope2d, dict):
                        seq_stats["runtime_rope2d_backend"] = str(rope2d.get("backend", ""))
                    if isinstance(sdpa, dict):
                        seq_stats["runtime_sdpa_backend_request"] = str(sdpa.get("backend_request", ""))
                        seq_stats["runtime_sdpa_backend_effective"] = str(sdpa.get("backend_effective", ""))
                        seq_stats["runtime_sdpa_likely_fused_candidate"] = bool(
                            sdpa.get("likely_fused_candidate", False)
                        )
                with torch.cuda.amp.autocast(dtype=torch.float32):
                    prepare_phase = phase_profile_start("launch_prepare_output")
                    (
                        pts3ds_self,
                        conf_self,
                    ) = prepare_output(outputs)
                    phase_profile_end(prepare_phase)

                    os.makedirs(f"{save_dir}/{seq}", exist_ok=True)
                    save_phase = phase_profile_start("launch_save_depth_maps")
                    save_depth_maps(pts3ds_self, f"{save_dir}/{seq}", conf_self=conf_self)
                    phase_profile_end(save_phase)

                if args.phase_profile:
                    seq_stats["profile_run"] = True
                    seq_stats["phase_profile"] = snapshot_phase_profile(reset=True)

                with open(system_log_path, "a", encoding="utf-8") as f_sys:
                    f_sys.write(json.dumps(seq_stats, ensure_ascii=False) + "\n")

            except Exception as e:
                if "out of memory" in str(e):
                    # Handle OOM
                    torch.cuda.empty_cache()  # Clear the CUDA memory
                    with open(error_log_path, "a") as f:
                        f.write(
                            f"OOM error in sequence {seq}, skipping this sequence.\n"
                        )
                    with open(system_log_path, "a", encoding="utf-8") as f_sys:
                        f_sys.write(json.dumps({"sequence": seq, "status": "oom_skip"}, ensure_ascii=False) + "\n")
                    print(f"OOM error in sequence {seq}, skipping...")
                elif "Degenerate covariance rank" in str(
                    e
                ) or "Eigenvalues did not converge" in str(e):
                    # Handle Degenerate covariance rank exception and Eigenvalues did not converge exception
                    with open(error_log_path, "a") as f:
                        f.write(f"Exception in sequence {seq}: {str(e)}\n")
                    with open(system_log_path, "a", encoding="utf-8") as f_sys:
                        f_sys.write(
                            json.dumps(
                                {"sequence": seq, "status": "traj_eval_skip", "error": str(e)},
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                    print(f"Traj evaluation error in sequence {seq}, skipping.")
                else:
                    raise e  # Rethrow if it's not an expected exception

    distributed_state.wait_for_everyone()
    if distributed_state.is_main_process:
        merged_records = []
        for proc_idx in range(distributed_state.num_processes):
            proc_path = f"{save_dir}/_system_metrics_{proc_idx}.jsonl"
            if not os.path.exists(proc_path):
                continue
            with open(proc_path, "r", encoding="utf-8") as f_proc:
                for line in f_proc:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        merged_records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        valid_records = [
            r
            for r in merged_records
            if r.get("status") == "ok" and ("elapsed_sec" in r) and ("num_frames" in r)
        ]
        summary = {
            "num_sequences_total": int(len(merged_records)),
            "num_sequences_ok": int(len(valid_records)),
            "num_sequences_oom_skip": int(sum(1 for r in merged_records if r.get("status") == "oom_skip")),
            "num_sequences_other_skip": int(
                sum(1 for r in merged_records if r.get("status") not in {"ok", "oom_skip"})
            ),
        }

        if valid_records:
            total_frames = int(sum(int(r.get("num_frames", 0)) for r in valid_records))
            total_elapsed = float(sum(float(r.get("elapsed_sec", 0.0)) for r in valid_records))
            summary.update(
                {
                    "total_frames": total_frames,
                    "total_elapsed_sec": total_elapsed,
                    "overall_fps": float(total_frames / total_elapsed) if total_elapsed > 0 else 0.0,
                    "avg_latency_ms_per_frame": float(1000.0 * total_elapsed / total_frames)
                    if total_frames > 0
                    else 0.0,
                    "max_peak_allocated_mb": float(
                        max(float(r.get("peak_allocated_mb", 0.0)) for r in valid_records)
                    ),
                    "max_peak_reserved_mb": float(
                        max(float(r.get("peak_reserved_mb", 0.0)) for r in valid_records)
                    ),
                    "profile_run": bool(args.phase_profile),
                    "formal_fps_valid": not bool(args.phase_profile),
                }
            )

            kv_evicted_total = float(sum(float(r.get("kv_evicted_tokens_total", 0.0)) for r in valid_records))
            kv_evict_calls_total = float(sum(float(r.get("kv_evict_calls", 0.0)) for r in valid_records))
            kv_appended_total = float(sum(float(r.get("kv_appended_tokens_total", 0.0)) for r in valid_records))
            kv_reused_total = float(sum(float(r.get("kv_reused_tokens_total", 0.0)) for r in valid_records))
            kv_denom = kv_appended_total + kv_reused_total
            summary.update(
                {
                    "kv_evicted_tokens_total": kv_evicted_total,
                    "kv_evict_calls_total": kv_evict_calls_total,
                    "kv_appended_tokens_total": kv_appended_total,
                    "kv_reused_tokens_total": kv_reused_total,
                    "kv_cache_hit_rate": float(kv_reused_total / kv_denom) if kv_denom > 0 else 0.0,
                }
            )
            runtime_samples = [
                r.get("runtime_diagnostics")
                for r in valid_records
                if isinstance(r.get("runtime_diagnostics"), dict) and r.get("runtime_diagnostics")
            ]
            if runtime_samples:
                summary["runtime_diagnostics_sample"] = runtime_samples[0]

            profile_summary = _aggregate_phase_profiles(valid_records)
            if profile_summary is not None:
                summary["phase_profile_enabled"] = True
                summary["phase_profile_sample"] = next(
                    r.get("phase_profile") for r in valid_records if isinstance(r.get("phase_profile"), dict)
                )
                profile_summary_path = os.path.join(save_dir, "profile_summary.json")
                with open(profile_summary_path, "w", encoding="utf-8") as f_profile:
                    json.dump(profile_summary, f_profile, ensure_ascii=False, indent=2)
                print(f"[profile_summary] saved: {profile_summary_path}")

        system_metrics_path = os.path.join(save_dir, "system_metrics.json")
        with open(system_metrics_path, "w", encoding="utf-8") as f_out:
            json.dump({"summary": summary, "per_sequence": merged_records}, f_out, ensure_ascii=False, indent=2)
        print(f"[system_metrics] saved: {system_metrics_path}")
    return None, None, None


if __name__ == "__main__":
    args = get_args_parser()
    args = args.parse_args()
    os.environ["OBVGGT_SDPA_BACKEND"] = args.sdpa_backend
    os.environ["OBVGGT_ROPE2D_BACKEND"] = args.rope2d_backend
    os.environ["OBVGGT_PHASE_PROFILE"] = "1" if args.phase_profile else "0"
    add_path_to_dust3r(args.weights)
    from dust3r.utils.image import load_images_for_eval as load_images
    from dust3r.post_process import estimate_focal_knowing_depth
    from dust3r.model import ARCroco3DStereo
    from dust3r.utils.camera import pose_encoding_to_camera

    from streamvggt.models.streamvggt import StreamVGGT
    from streamvggt.utils.pose_enc import pose_encoding_to_extri_intri
    from streamvggt.utils.geometry import unproject_depth_map_to_point_map
    from eval.mv_recon.criterion import Regr3D_t_ScaleShiftInv, L21
    from dust3r.utils.geometry import geotrf
    from copy import deepcopy

    if args.eval_dataset == "sintel":
        args.full_seq = True
    else:
        args.full_seq = False
    args.no_crop = True

    def prepare_input(
        img_paths,
        img_mask,
        size,
        raymaps=None,
        raymap_mask=None,
        revisit=1,
        update=True,
        crop=True,
    ):
        images = load_images(img_paths, size=size, crop=crop)
        views = []
        if raymaps is None and raymap_mask is None:
            num_views = len(images)

            for i in range(num_views):
                view = {
                    "img": images[i]["img"].to(device='cuda'),
                    "ray_map": torch.full(
                        (
                            images[i]["img"].shape[0],
                            6,
                            images[i]["img"].shape[-2],
                            images[i]["img"].shape[-1],
                        ),
                        torch.nan,
                    ).to(device='cuda'),
                    "true_shape": torch.from_numpy(images[i]["true_shape"]).to(device='cuda'),
                    "idx": i,
                    "instance": str(i),
                    "camera_pose": torch.from_numpy(
                        np.eye(4).astype(np.float32)
                    ).unsqueeze(0).to(device='cuda'),
                    "img_mask": torch.tensor(True).unsqueeze(0).to(device='cuda'),
                    "ray_mask": torch.tensor(False).unsqueeze(0).to(device='cuda'),
                    "update": torch.tensor(True).unsqueeze(0).to(device='cuda'),
                    "reset": torch.tensor(False).unsqueeze(0).to(device='cuda'),
                }
                views.append(view)
        else:

            num_views = len(images) + len(raymaps)
            assert len(img_mask) == len(raymap_mask) == num_views
            assert sum(img_mask) == len(images) and sum(raymap_mask) == len(raymaps)

            j = 0
            k = 0
            for i in range(num_views):
                view = {
                    "img": (
                        images[j]["img"].to(device='cuda')
                        if img_mask[i]
                        else torch.full_like(images[0]["img"], torch.nan).to(device='cuda')
                    ),
                    "ray_map": (
                        raymaps[k].to(device='cuda')
                        if raymap_mask[i]
                        else torch.full_like(raymaps[0], torch.nan).to(device='cuda')
                    ),
                    "true_shape": (
                        torch.from_numpy(images[j]["true_shape"]).to(device='cuda')
                        if img_mask[i]
                        else torch.from_numpy(np.int32([raymaps[k].shape[1:-1][::-1]])).to(device='cuda')
                    ),
                    "idx": i,
                    "instance": str(i),
                    "camera_pose": torch.from_numpy(
                        np.eye(4).astype(np.float32)
                    ).unsqueeze(0).to(device='cuda'),
                    "img_mask": torch.tensor(img_mask[i]).unsqueeze(0).to(device='cuda'),
                    "ray_mask": torch.tensor(raymap_mask[i]).unsqueeze(0).to(device='cuda'),
                    "update": torch.tensor(img_mask[i]).unsqueeze(0).to(device='cuda'),
                    "reset": torch.tensor(False).unsqueeze(0).to(device='cuda'),
                }
                if img_mask[i]:
                    j += 1
                if raymap_mask[i]:
                    k += 1
                views.append(view)
            assert j == len(images) and k == len(raymaps)

        if revisit > 1:
            # repeat input for 'revisit' times
            new_views = []
            for r in range(revisit):
                for i in range(len(views)):
                    new_view = deepcopy(views[i])
                    new_view["idx"] = r * len(views) + i
                    new_view["instance"] = str(r * len(views) + i)
                    if r > 0:
                        if not update:
                            new_view["update"] = torch.tensor(False).unsqueeze(0)
                    new_views.append(new_view)
            return new_views
        return views

    def prepare_output(outputs, revisit=1):
        valid_length = len(outputs["pred"]) // revisit
        outputs["pred"] = outputs["pred"][-valid_length:]
        outputs["views"] = outputs["views"][-valid_length:]

        pts3ds_self = [output["depth"].cpu() for output in outputs["pred"]]
        conf_self = [output["depth_conf"].cpu() for output in outputs["pred"]]
        pts3ds_self = torch.cat(pts3ds_self, 0)
        return (
            pts3ds_self,
            conf_self,
        )

    model = StreamVGGT()
    # Load checkpoint weights on CPU first to avoid CUDA OOM during deserialization.
    ckpt = torch.load(args.weights, map_location=lambda storage, _loc: storage.cpu())
    model.load_state_dict(ckpt, strict=True)
    model.eval()
    model = model.to("cuda")
    del ckpt
    kv_cache_cfg = build_kv_cache_cfg(args)
    print(
        f"[kv_cache] {'enabled' if kv_cache_cfg is not None else 'disabled'}; "
        f"cfg={kv_cache_cfg if kv_cache_cfg is not None else '{}'}"
    )
    with torch.no_grad():
        eval_pose_estimation(args, model, save_dir=args.output_dir, kv_cache_cfg=kv_cache_cfg)
