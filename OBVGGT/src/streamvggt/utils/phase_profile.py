"""Optional phase-level timing for profile-only runs.

This module is intentionally separate from runtime_diagnostics.py:
runtime_diagnostics captures lightweight first-call metadata, while
phase_profile aggregates repeated timing events for dedicated profile runs.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional


_ENV = "OBVGGT_PHASE_PROFILE"
_STATE: Dict[str, Any] = {
    "phases": {},
    "pending_cuda": [],
}


def _enabled() -> bool:
    return os.environ.get(_ENV, "0").strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_name(name: Any) -> str:
    value = "".join(ch if str(ch).isalnum() else "_" for ch in str(name).strip().lower()).strip("_")
    return value or "unnamed"


def reset_phase_profile() -> None:
    _STATE["phases"] = {}
    _STATE["pending_cuda"] = []


def phase_profile_enabled() -> bool:
    return _enabled()


def _phase_slot(name: str) -> Dict[str, float]:
    phases = _STATE["phases"]
    slot = phases.get(name)
    if slot is None:
        slot = {"total_ms": 0.0, "calls": 0.0}
        phases[name] = slot
    return slot


def phase_profile_start(name: str, reference: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    if not _enabled():
        return None

    safe_name = _safe_name(name)
    if bool(getattr(reference, "is_cuda", False)):
        import torch

        start_event = torch.cuda.Event(enable_timing=True)
        start_event.record()
        return {"name": safe_name, "kind": "cuda", "start_event": start_event}

    return {"name": safe_name, "kind": "cpu", "start_time": time.perf_counter()}


def phase_profile_end(handle: Optional[Dict[str, Any]], reference: Optional[Any] = None) -> None:
    if handle is None:
        return

    name = str(handle["name"])
    if handle["kind"] == "cpu":
        elapsed_ms = (time.perf_counter() - float(handle["start_time"])) * 1000.0
        slot = _phase_slot(name)
        slot["total_ms"] += float(elapsed_ms)
        slot["calls"] += 1.0
        return

    import torch

    end_event = torch.cuda.Event(enable_timing=True)
    end_event.record()
    _STATE["pending_cuda"].append((name, handle["start_event"], end_event))


def snapshot_phase_profile(*, reset: bool = False) -> Dict[str, Any]:
    for name, start_event, end_event in list(_STATE["pending_cuda"]):
        elapsed_ms = float(start_event.elapsed_time(end_event))
        slot = _phase_slot(str(name))
        slot["total_ms"] += elapsed_ms
        slot["calls"] += 1.0
    _STATE["pending_cuda"] = []

    phases: Dict[str, Dict[str, float]] = {
        str(name): {"total_ms": float(values["total_ms"]), "calls": float(values["calls"])}
        for name, values in (_STATE["phases"] or {}).items()
    }

    payload = {
        "enabled": bool(_enabled()),
        "phases": phases,
        "pending_cuda_events": int(len(_STATE["pending_cuda"])),
    }
    if reset:
        reset_phase_profile()
    return payload
