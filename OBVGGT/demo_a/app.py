"""
OBVGGT Demo — Gradio application for thesis defense.

Usage:
    cd OBVGGT
    python demo_a/app.py

Tabs:
    1. 3D Reconstruction Comparison (baseline vs OBVGGT)
    2. Video Depth Estimation (streaming depth with memory monitoring)
    3. Ablation Experiment Visualization (interactive charts from CSV)
"""

import os
import sys
import tempfile
import glob

import gradio as gr
import numpy as np
import torch

# Ensure OBVGGT/src is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_DEMO = os.path.dirname(os.path.abspath(__file__))
if _DEMO not in sys.path:
    sys.path.insert(0, _DEMO)

from check_env import check_env, format_status
from inference import (
    load_model,
    load_images_from_paths,
    video_to_frames,
    run_inference,
    run_streaming_inference,
    make_glb,
    OBVGGT_CONFIGS,
)
from monitor import RunMetrics
from viz import (
    colorize_depth,
    plot_memory_curve,
    plot_fps_comparison,
    make_comparison_image,
    plot_ablation_accuracy_vs_budget,
    plot_ablation_scoring_methods,
)

# ── Paths ───────────────────────────────────────────────────────────

EXAMPLE_DIR = os.path.join(_ROOT, "examples", "example_building")
ABLATION_CSV = os.path.join(
    _ROOT, "experiments", "analysis", "tables", "ablation_video_depth_20260324.csv"
)

# ── Environment check ───────────────────────────────────────────────

ENV_STATUS = check_env()


def env_banner() -> str:
    """Markdown banner showing environment status."""
    s = ENV_STATUS
    if s["ok"]:
        icon = "🟢"
        gpu_info = f"**{s['gpu_name']}** ({s['gpu_memory_gb']} GB)"
    else:
        icon = "🔴"
        gpu_info = "NOT AVAILABLE" if not s["cuda_available"] else s["gpu_name"]

    ckpt = "Found" if s["checkpoint_found"] else "**NOT FOUND**"

    lines = [
        f"## {icon} Environment Status",
        f"- GPU: {gpu_info}",
        f"- Checkpoint: {ckpt}",
        f"- Disk Free: {s['disk_free_gb']} GB",
    ]
    if s["missing_packages"]:
        lines.append(f"- Missing: {', '.join(s['missing_packages'])}")
    if not s["ok"]:
        lines.append("")
        lines.append("**Errors:**")
        for err in s["errors"]:
            lines.append(f"- {err}")
    return "\n".join(lines)


# =====================================================================
# Tab 1: 3D Reconstruction Comparison
# =====================================================================

def tab1_reconstruct(input_images, config_name, conf_thresh):
    """Run baseline and OBVGGT on uploaded images, return two GLBs + metrics."""
    if not input_images:
        return None, None, "No images uploaded.", None, None

    # Save uploaded images to temp dir
    paths = [img.name if hasattr(img, "name") else img for img in input_images]
    images = load_images_from_paths(paths)
    num_frames = images.shape[0]

    obvggt_cfg = OBVGGT_CONFIGS.get(config_name, OBVGGT_CONFIGS["p1_no_recent_ctrl"])

    # Run baseline
    preds_base, metrics_base = run_inference(images.clone(), kv_cache_cfg=None)

    # Clear cache between runs
    torch.cuda.empty_cache()

    # Run OBVGGT
    preds_obv, metrics_obv = run_inference(images.clone(), kv_cache_cfg=obvggt_cfg)

    # Build GLBs
    glb_base = make_glb(preds_base, conf_thresh) if preds_base else None
    glb_obv = make_glb(preds_obv, conf_thresh) if preds_obv else None

    # Metrics summary
    summary = f"**{num_frames} frames processed**\n\n"
    summary += "| | Baseline | OBVGGT |\n|---|---|---|\n"

    if metrics_base.frames:
        summary += f"| Peak Mem | {metrics_base.peak_memory_mb:.0f} MB | "
    else:
        summary += "| Peak Mem | OOM | "
    if metrics_obv.frames:
        summary += f"{metrics_obv.peak_memory_mb:.0f} MB |\n"
    else:
        summary += "OOM |\n"

    if metrics_base.frames:
        summary += f"| Time | {metrics_base.total_elapsed_sec:.1f}s | "
    else:
        summary += "| Time | — | "
    if metrics_obv.frames:
        summary += f"{metrics_obv.total_elapsed_sec:.1f}s |\n"
    else:
        summary += "— |\n"

    mem_plot = plot_memory_curve(
        metrics_base, metrics_obv,
        gpu_total_gb=ENV_STATUS.get("gpu_memory_gb", 24),
    )
    fps_plot = plot_fps_comparison(metrics_base, metrics_obv)

    return glb_base, glb_obv, summary, mem_plot, fps_plot


# =====================================================================
# Tab 2: Video Depth Estimation
# =====================================================================

def tab2_video_depth(input_video, max_frames):
    """
    Run streaming depth estimation on a video.
    Returns comparison image, memory curve, and a summary.
    """
    if input_video is None:
        return None, None, "No video uploaded."

    video_path = input_video.name if hasattr(input_video, "name") else input_video
    max_frames = int(max_frames)

    # Extract frames
    raw_frames = video_to_frames(video_path, target_fps=2)
    if len(raw_frames) > max_frames:
        raw_frames = raw_frames[:max_frames]

    if not raw_frames:
        return None, None, "Failed to extract frames from video."

    # Save frames to temp and load
    tmp = tempfile.mkdtemp()
    paths = []
    for i, f in enumerate(raw_frames):
        from PIL import Image
        p = os.path.join(tmp, f"{i:04d}.jpg")
        Image.fromarray(f).save(p)
        paths.append(p)

    images = load_images_from_paths(paths)
    num_frames = images.shape[0]

    obvggt_cfg = OBVGGT_CONFIGS["p1_no_recent_ctrl"]

    # Run both
    preds_base, metrics_base = run_inference(images.clone(), kv_cache_cfg=None)
    torch.cuda.empty_cache()
    preds_obv, metrics_obv = run_inference(images.clone(), kv_cache_cfg=obvggt_cfg)

    # Build comparison of the last frame
    last_idx = num_frames - 1
    rgb = raw_frames[last_idx]

    depth_b = preds_base["depth"][last_idx, ..., -1] if preds_base else None
    depth_o = preds_obv["depth"][last_idx, ..., -1] if preds_obv else None

    # Unify depth range for fair comparison
    all_depths = [d for d in [depth_b, depth_o] if d is not None]
    if all_depths:
        vmin = min(d.min() for d in all_depths)
        vmax = max(d.max() for d in all_depths)
    else:
        vmin, vmax = 0, 1

    # Resize rgb to match depth resolution
    from PIL import Image as PILImage
    if depth_b is not None:
        h, w = depth_b.shape
        rgb_resized = np.array(PILImage.fromarray(rgb).resize((w, h)))
    elif depth_o is not None:
        h, w = depth_o.shape
        rgb_resized = np.array(PILImage.fromarray(rgb).resize((w, h)))
    else:
        rgb_resized = rgb

    comp_img = make_comparison_image(rgb_resized, depth_b, depth_o, vmin, vmax)

    mem_plot = plot_memory_curve(
        metrics_base, metrics_obv,
        gpu_total_gb=ENV_STATUS.get("gpu_memory_gb", 24),
    )

    summary = f"**{num_frames} frames** | "
    if metrics_base.oom:
        summary += f"Baseline: OOM | "
    elif metrics_base.frames:
        summary += f"Baseline: {metrics_base.peak_memory_mb:.0f} MB, {metrics_base.avg_fps:.2f} FPS | "
    if metrics_obv.frames:
        summary += f"OBVGGT: {metrics_obv.peak_memory_mb:.0f} MB, {metrics_obv.avg_fps:.2f} FPS"

    return comp_img, mem_plot, summary


# =====================================================================
# Tab 3: Ablation Visualization
# =====================================================================

def tab3_budget_chart():
    if not os.path.isfile(ABLATION_CSV):
        return None
    return plot_ablation_accuracy_vs_budget(ABLATION_CSV)


def tab3_scoring_chart():
    if not os.path.isfile(ABLATION_CSV):
        return None
    return plot_ablation_scoring_methods(ABLATION_CSV)


# =====================================================================
# Gradio UI
# =====================================================================

def build_ui():
    with gr.Blocks(
        title="OBVGGT Demo",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown("# OBVGGT: Optimal Brain Visual Geometry Grounded Transformer")
        gr.Markdown("Training-free KV cache management for streaming 4D geometric reconstruction")
        gr.Markdown(env_banner())

        # ── Tab 1: 3D Reconstruction ──
        with gr.Tab("3D Reconstruction Comparison"):
            gr.Markdown(
                "Upload images to compare **baseline** (full cache) vs **OBVGGT** (compressed cache) "
                "3D point cloud reconstruction."
            )
            with gr.Row():
                input_images = gr.File(
                    label="Upload Images",
                    file_count="multiple",
                    file_types=["image"],
                )
                with gr.Column():
                    config_choice = gr.Dropdown(
                        choices=list(OBVGGT_CONFIGS.keys()),
                        value="p1_no_recent_ctrl",
                        label="OBVGGT Config",
                    )
                    conf_slider = gr.Slider(
                        minimum=10, maximum=99, value=50, step=5,
                        label="Confidence Threshold (%)",
                    )
                    run_btn = gr.Button("Run Reconstruction", variant="primary")

            with gr.Row():
                glb_baseline = gr.Model3D(label="StreamVGGT (Baseline)")
                glb_obvggt = gr.Model3D(label="OBVGGT")

            metrics_md = gr.Markdown()

            with gr.Row():
                mem_plot_1 = gr.Image(label="Memory Usage")
                fps_plot_1 = gr.Image(label="FPS Comparison")

            # Wire examples
            if os.path.isdir(EXAMPLE_DIR):
                example_imgs = sorted(glob.glob(os.path.join(EXAMPLE_DIR, "*.jpg")))
                if example_imgs:
                    gr.Examples(
                        examples=[example_imgs],
                        inputs=[input_images],
                        label="Example: Building",
                    )

            run_btn.click(
                fn=tab1_reconstruct,
                inputs=[input_images, config_choice, conf_slider],
                outputs=[glb_baseline, glb_obvggt, metrics_md, mem_plot_1, fps_plot_1],
            )

        # ── Tab 2: Video Depth ──
        with gr.Tab("Video Depth Estimation"):
            gr.Markdown(
                "Upload a video to compare streaming depth estimation. "
                "For long sequences, **baseline may OOM** while OBVGGT continues normally."
            )
            with gr.Row():
                input_video = gr.File(label="Upload Video", file_types=["video"])
                max_frames_slider = gr.Slider(
                    minimum=5, maximum=200, value=30, step=5,
                    label="Max Frames",
                )
            depth_btn = gr.Button("Run Depth Estimation", variant="primary")

            comp_image = gr.Image(label="RGB | Baseline Depth | OBVGGT Depth")
            with gr.Row():
                mem_plot_2 = gr.Image(label="Memory Curve")
            depth_summary = gr.Markdown()

            depth_btn.click(
                fn=tab2_video_depth,
                inputs=[input_video, max_frames_slider],
                outputs=[comp_image, mem_plot_2, depth_summary],
            )

        # ── Tab 3: Ablation ──
        with gr.Tab("Ablation Experiments"):
            gr.Markdown(
                "Interactive visualization of ablation results from "
                "`ablation_video_depth_20260324.csv`."
            )

            if os.path.isfile(ABLATION_CSV):
                with gr.Row():
                    budget_plot = gr.Plot(label="Cache Budget vs Accuracy")
                    scoring_plot = gr.Plot(label="Scoring Method Comparison")

                demo.load(fn=tab3_budget_chart, outputs=budget_plot)
                demo.load(fn=tab3_scoring_chart, outputs=scoring_plot)
            else:
                gr.Markdown(f"Ablation CSV not found at `{ABLATION_CSV}`")

    return demo


# =====================================================================
# Entry point
# =====================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OBVGGT Demo")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true", help="Create public Gradio link")
    args = parser.parse_args()

    print("=" * 60)
    print("OBVGGT Demo — Environment Check")
    print("=" * 60)
    print(format_status(ENV_STATUS))
    print("=" * 60)

    if not ENV_STATUS["ok"]:
        print("\nWARNING: Environment issues detected. Demo may not work correctly.\n")

    print(f"\nStarting on port {args.port}...")
    print(f"SSH tunnel access:  ssh -L {args.port}:localhost:{args.port} user@<tailscale-ip>")
    print(f"Then open:          http://localhost:{args.port}\n")

    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",  # localhost only; access via SSH tunnel
        server_port=args.port,
        share=args.share,
    )
