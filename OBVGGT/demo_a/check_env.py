"""
Environment check — run before starting the demo.
Usage: python demo_a/check_env.py
"""

import shutil
import importlib
import os
import sys

REQUIRED_PACKAGES = [
    "torch", "gradio", "trimesh", "cv2", "numpy", "matplotlib",
    "plotly", "PIL", "scipy",
]

CHECKPOINT_PATHS = [
    os.path.join("ckpt", "checkpoints.pth"),
    os.path.join("OBVGGT", "ckpt", "checkpoints.pth"),
]


def check_env() -> dict:
    """Return a status dict with environment info and pass/fail flags."""
    status = {
        "cuda_available": False,
        "gpu_name": "N/A",
        "gpu_memory_gb": 0.0,
        "checkpoint_found": False,
        "checkpoint_path": None,
        "missing_packages": [],
        "disk_free_gb": 0.0,
        "errors": [],
        "ok": True,
    }

    # ---- CUDA / GPU ----
    try:
        import torch
        status["cuda_available"] = torch.cuda.is_available()
        if status["cuda_available"]:
            status["gpu_name"] = torch.cuda.get_device_name(0)
            status["gpu_memory_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1024**3, 1
            )
        else:
            status["errors"].append("CUDA not available — demo requires a GPU")
    except ImportError:
        status["errors"].append("PyTorch is not installed")

    # ---- Model checkpoint ----
    for p in CHECKPOINT_PATHS:
        if os.path.isfile(p):
            status["checkpoint_found"] = True
            status["checkpoint_path"] = os.path.abspath(p)
            break
    if not status["checkpoint_found"]:
        status["errors"].append(
            "Model checkpoint not found. Download with:\n"
            "  pip install huggingface_hub\n"
            "  python -c \"from huggingface_hub import hf_hub_download; "
            "hf_hub_download('lch01/StreamVGGT', 'checkpoints.pth', "
            "local_dir='ckpt')\""
        )

    # ---- Python packages ----
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            status["missing_packages"].append(pkg)
    if status["missing_packages"]:
        status["errors"].append(
            f"Missing packages: {', '.join(status['missing_packages'])}"
        )

    # ---- Disk space ----
    usage = shutil.disk_usage(os.getcwd())
    status["disk_free_gb"] = round(usage.free / 1024**3, 1)
    if status["disk_free_gb"] < 5:
        status["errors"].append(
            f"Low disk space: {status['disk_free_gb']} GB free"
        )

    status["ok"] = len(status["errors"]) == 0
    return status


def format_status(status: dict) -> str:
    """Human-readable status summary."""
    lines = []
    if status["cuda_available"]:
        lines.append(f"GPU: {status['gpu_name']} ({status['gpu_memory_gb']} GB)")
    else:
        lines.append("GPU: not available")

    if status["checkpoint_found"]:
        lines.append(f"Checkpoint: {status['checkpoint_path']}")
    else:
        lines.append("Checkpoint: NOT FOUND")

    lines.append(f"Disk free: {status['disk_free_gb']} GB")

    if status["missing_packages"]:
        lines.append(f"Missing packages: {', '.join(status['missing_packages'])}")

    if status["ok"]:
        lines.append("Status: READY")
    else:
        lines.append("Status: NOT READY")
        for err in status["errors"]:
            lines.append(f"  - {err}")

    return "\n".join(lines)


if __name__ == "__main__":
    s = check_env()
    print(format_status(s))
    sys.exit(0 if s["ok"] else 1)
