"""
Visualization utilities — depth colorization, memory curves, comparison images.
"""

import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from PIL import Image

from monitor import RunMetrics


# ── Depth colorization ──────────────────────────────────────────────

def colorize_depth(
    depth: np.ndarray,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap: str = "Spectral_r",
) -> np.ndarray:
    """
    Colorize a depth map (H, W) to an RGB uint8 image (H, W, 3).
    """
    if vmin is None:
        vmin = float(np.nanmin(depth))
    if vmax is None:
        vmax = float(np.nanmax(depth))

    if vmax - vmin < 1e-6:
        vmax = vmin + 1.0

    normed = np.clip((depth - vmin) / (vmax - vmin), 0, 1)
    colormap = cm.get_cmap(cmap)
    colored = colormap(normed)[:, :, :3]  # drop alpha
    return (colored * 255).astype(np.uint8)


# ── Memory curve ────────────────────────────────────────────────────

def plot_memory_curve(
    baseline_metrics: RunMetrics | None = None,
    obvggt_metrics: RunMetrics | None = None,
    gpu_total_gb: float = 24.0,
) -> Image.Image:
    """
    Plot memory usage over frames for baseline (red) and OBVGGT (blue).
    Returns a PIL Image.
    """
    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)

    if baseline_metrics and baseline_metrics.frames:
        xs, ys = baseline_metrics.memory_timeline
        ys_gb = [y / 1024 for y in ys]
        ax.plot(xs, ys_gb, "r-o", label="StreamVGGT (baseline)", markersize=3)
        if baseline_metrics.oom:
            ax.axvline(
                baseline_metrics.oom_at_frame,
                color="red", linestyle="--", alpha=0.7,
                label=f"OOM @ frame {baseline_metrics.oom_at_frame}",
            )

    if obvggt_metrics and obvggt_metrics.frames:
        xs, ys = obvggt_metrics.memory_timeline
        ys_gb = [y / 1024 for y in ys]
        ax.plot(xs, ys_gb, "b-s", label="OBVGGT", markersize=3)

    ax.axhline(gpu_total_gb, color="gray", linestyle=":", alpha=0.5, label=f"GPU limit ({gpu_total_gb} GB)")
    ax.set_xlabel("Frame")
    ax.set_ylabel("Peak GPU Memory (GB)")
    ax.set_title("Memory Usage Over Time")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


def plot_fps_comparison(
    baseline_metrics: RunMetrics | None = None,
    obvggt_metrics: RunMetrics | None = None,
) -> Image.Image:
    """Bar chart comparing average FPS."""
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)

    names, values, colors = [], [], []
    if baseline_metrics and baseline_metrics.frames:
        names.append("StreamVGGT")
        values.append(baseline_metrics.avg_fps)
        colors.append("#e74c3c")
    if obvggt_metrics and obvggt_metrics.frames:
        names.append("OBVGGT")
        values.append(obvggt_metrics.avg_fps)
        colors.append("#3498db")

    ax.bar(names, values, color=colors)
    ax.set_ylabel("FPS")
    ax.set_title("Throughput Comparison")
    for i, v in enumerate(values):
        ax.text(i, v + 0.1, f"{v:.2f}", ha="center", fontsize=10)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


# ── Side-by-side comparison image ───────────────────────────────────

def make_comparison_image(
    rgb: np.ndarray,
    depth_baseline: np.ndarray | None,
    depth_obvggt: np.ndarray | None,
    vmin: float | None = None,
    vmax: float | None = None,
) -> np.ndarray:
    """
    Create a horizontally-stacked comparison: RGB | Baseline Depth | OBVGGT Depth.
    All inputs/outputs are uint8 (H, W, 3).
    """
    h, w = rgb.shape[:2]

    parts = [rgb]

    if depth_baseline is not None:
        parts.append(colorize_depth(depth_baseline, vmin, vmax))
    else:
        # OOM placeholder
        oom_img = np.zeros((h, w, 3), dtype=np.uint8)
        oom_img[:, :] = [200, 50, 50]  # red background
        parts.append(oom_img)

    if depth_obvggt is not None:
        parts.append(colorize_depth(depth_obvggt, vmin, vmax))

    return np.concatenate(parts, axis=1)


# ── Ablation charts (from CSV) ──────────────────────────────────────

def plot_ablation_accuracy_vs_budget(csv_path: str):
    """Plotly figure: KITTI AbsRel vs cache budget size."""
    import plotly.graph_objects as go
    import csv

    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    budget_variants = [
        ("obcache_budget_tight", 4),
        ("obcache_budget_small", 5),
        ("obcache_default", 7),
        ("obcache_budget_medium", 10),
        ("obcache_budget_large", 13),
    ]

    xs, ys, labels = [], [], []
    for var_name, budget in budget_variants:
        for row in rows:
            if row["variant"] == var_name:
                xs.append(budget)
                ys.append(float(row["kitti_absrel"]))
                labels.append(var_name)
                break

    # Add baseline
    for row in rows:
        if row["variant"] == "baseline":
            xs.append(110)
            ys.append(float(row["kitti_absrel"]))
            labels.append("baseline (full cache)")
            break

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+lines", text=labels,
        marker=dict(size=10), name="KITTI Abs Rel",
    ))
    fig.update_layout(
        title="Cache Budget vs Accuracy (KITTI)",
        xaxis_title="Cache Budget (frames)",
        yaxis_title="Abs Rel ↓",
        template="plotly_white",
    )
    return fig


def plot_ablation_scoring_methods(csv_path: str):
    """Plotly figure: scoring method comparison."""
    import plotly.graph_objects as go
    import csv

    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    methods = {
        "obcache_default": "V+K Joint",
        "obcache_v_only_clean": "V Only",
        "obcache_k_only": "K Only",
        "obcache_random": "Random",
        "obcache_sliding_window": "Sliding Window",
        "baseline": "Full Cache",
    }

    names, kitti_vals, bonn_vals = [], [], []
    for var_key, label in methods.items():
        for row in rows:
            if row["variant"] == var_key:
                names.append(label)
                kitti_vals.append(float(row["kitti_absrel"]))
                bonn_vals.append(float(row["bonn_absrel"]))
                break

    fig = go.Figure()
    fig.add_trace(go.Bar(name="KITTI", x=names, y=kitti_vals, marker_color="#3498db"))
    fig.add_trace(go.Bar(name="Bonn", x=names, y=bonn_vals, marker_color="#e67e22"))
    fig.update_layout(
        title="Scoring Method Comparison (Abs Rel ↓)",
        barmode="group",
        template="plotly_white",
        yaxis_title="Abs Rel ↓",
    )
    return fig
