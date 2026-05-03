"""Lightweight runtime diagnostics for inference backend preflight.

The helpers in this module intentionally avoid CUDA synchronization and heavy
profiling. They only capture first-call metadata needed to explain which
runtime path a run used.
"""

from __future__ import annotations

import os
import platform
import sys
from contextlib import nullcontext
from typing import Any, Dict, Optional

_STATE: Dict[str, Any] = {
    "environment": None,
    "rope2d": None,
    "sdpa": None,
    "counters": {"rope2d_calls": 0, "sdpa_calls": 0},
}

_SDPA_BACKEND_ENV = "OBVGGT_SDPA_BACKEND"
_SDPA_BACKENDS = {"default", "flash", "efficient", "math", "cudnn"}


def _shape(value: Any) -> Optional[list[int]]:
    if value is None or not hasattr(value, "shape"):
        return None
    return [int(dim) for dim in value.shape]


def _stride(value: Any) -> Optional[list[int]]:
    if value is None or not hasattr(value, "stride"):
        return None
    try:
        return [int(dim) for dim in value.stride()]
    except TypeError:
        return None


def _dtype(value: Any) -> str:
    return str(getattr(value, "dtype", "unknown"))


def _device(value: Any) -> str:
    return str(getattr(value, "device", "unknown"))


def _safe_call(obj: Any, name: str) -> Optional[Any]:
    fn = getattr(obj, name, None)
    if fn is None:
        return None


def get_sdpa_backend_request() -> str:
    raw = os.environ.get(_SDPA_BACKEND_ENV, "default")
    value = str(raw).strip().lower() or "default"
    if value not in _SDPA_BACKENDS:
        raise ValueError(
            f"Invalid {_SDPA_BACKEND_ENV}={raw!r}; expected one of {sorted(_SDPA_BACKENDS)}"
        )
    return value


def sdpa_kernel_context(backend_request: str):
    backend = str(backend_request or "default").strip().lower()
    if backend == "default":
        return nullcontext()
    if backend not in _SDPA_BACKENDS:
        raise ValueError(f"Invalid SDPA backend request: {backend_request!r}")

    try:
        import torch

        return torch.backends.cuda.sdp_kernel(
            enable_flash=backend == "flash",
            enable_mem_efficient=backend == "efficient",
            enable_math=backend == "math",
            enable_cudnn=backend == "cudnn",
        )
    except Exception as exc:
        raise RuntimeError(f"Unable to configure SDPA backend {backend!r}: {exc}") from exc
    try:
        return fn()
    except Exception:
        return None


def _torch_environment() -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
    }
    try:
        import torch

        payload.update(
            {
                "torch_version": str(torch.__version__),
                "torch_cuda_version": str(torch.version.cuda),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
        )
        if torch.cuda.is_available():
            current = torch.cuda.current_device()
            payload.update(
                {
                    "cuda_current_device": int(current),
                    "cuda_device_name": str(torch.cuda.get_device_name(current)),
                    "cuda_capability": list(torch.cuda.get_device_capability(current)),
                }
            )
    except Exception as exc:
        payload["torch_error"] = f"{type(exc).__name__}: {exc}"
    return payload


def record_environment_once() -> None:
    if _STATE["environment"] is None:
        _STATE["environment"] = _torch_environment()


def record_rope2d_call(tokens: Any, positions: Any, *, backend: str, module: str) -> None:
    _STATE["counters"]["rope2d_calls"] += 1
    record_environment_once()
    if _STATE["rope2d"] is not None:
        return
    _STATE["rope2d"] = {
        "backend": backend,
        "module": module,
        "tokens_shape": _shape(tokens),
        "tokens_stride": _stride(tokens),
        "tokens_dtype": _dtype(tokens),
        "tokens_device": _device(tokens),
        "positions_shape": _shape(positions),
        "positions_stride": _stride(positions),
        "positions_dtype": _dtype(positions),
        "positions_device": _device(positions),
    }


def record_sdpa_call(
    q: Any,
    k: Any,
    v: Any,
    *,
    attn_mask: Any,
    dropout_p: float,
    backend_request: str = "default",
    is_causal: bool = False,
) -> None:
    _STATE["counters"]["sdpa_calls"] += 1
    record_environment_once()
    if _STATE["sdpa"] is not None:
        return

    payload: Dict[str, Any] = {
        "api": "torch.nn.functional.scaled_dot_product_attention",
        "backend_request": backend_request or "default",
        "q_shape": _shape(q),
        "k_shape": _shape(k),
        "v_shape": _shape(v),
        "q_stride": _stride(q),
        "k_stride": _stride(k),
        "v_stride": _stride(v),
        "q_dtype": _dtype(q),
        "k_dtype": _dtype(k),
        "v_dtype": _dtype(v),
        "q_device": _device(q),
        "k_device": _device(k),
        "v_device": _device(v),
        "attn_mask_present": attn_mask is not None,
        "attn_mask_shape": _shape(attn_mask),
        "attn_mask_dtype": _dtype(attn_mask) if attn_mask is not None else "",
        "dropout_p": float(dropout_p),
        "is_causal": bool(is_causal),
    }

    try:
        import torch

        cuda_backend = getattr(torch.backends, "cuda", None)
        payload.update(
            {
                "flash_sdp_enabled": _safe_call(cuda_backend, "flash_sdp_enabled"),
                "mem_efficient_sdp_enabled": _safe_call(cuda_backend, "mem_efficient_sdp_enabled"),
                "math_sdp_enabled": _safe_call(cuda_backend, "math_sdp_enabled"),
                "cudnn_sdp_enabled": _safe_call(cuda_backend, "cudnn_sdp_enabled"),
            }
        )
        payload["likely_fused_candidate"] = bool(
            getattr(q, "is_cuda", False)
            and getattr(k, "is_cuda", False)
            and getattr(v, "is_cuda", False)
            and getattr(q, "dtype", None) in {torch.float16, torch.bfloat16}
            and attn_mask is None
        )
    except Exception as exc:
        payload["backend_probe_error"] = f"{type(exc).__name__}: {exc}"

    _STATE["sdpa"] = payload


def snapshot_runtime_diagnostics(*, reset: bool = False) -> Dict[str, Any]:
    record_environment_once()
    payload = {
        "environment": dict(_STATE["environment"] or {}),
        "rope2d": dict(_STATE["rope2d"] or {}),
        "sdpa": dict(_STATE["sdpa"] or {}),
        "counters": dict(_STATE["counters"]),
    }
    if reset:
        _STATE["rope2d"] = None
        _STATE["sdpa"] = None
        _STATE["counters"] = {"rope2d_calls": 0, "sdpa_calls": 0}
    return payload
