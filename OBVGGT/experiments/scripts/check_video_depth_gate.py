"""Check paired video_depth runtime gates from synced artifacts.

This script is intentionally read-only. It compares a control run and a
candidate run using their `system_metrics.json` and `result_scale.json` files,
then exits non-zero if the candidate does not satisfy the requested gate.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


LOWER_IS_BETTER = ("Abs Rel", "Sq Rel", "RMSE", "Log RMSE")
HIGHER_IS_BETTER = ("\u03b4 < 1.25", "\u03b4 < 1.25^2", "\u03b4 < 1.25^3")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return payload


def summary_value(system: Dict[str, Any], key: str, default: float = 0.0) -> float:
    summary = system.get("summary", {})
    if not isinstance(summary, dict):
        return default
    try:
        return float(summary.get(key, default))
    except (TypeError, ValueError):
        return default


def per_sequence_max(system: Dict[str, Any], key: str) -> float:
    records = system.get("per_sequence", [])
    if not isinstance(records, list):
        return 0.0
    values = []
    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            values.append(float(record.get(key, 0.0)))
        except (TypeError, ValueError):
            continue
    return max(values) if values else 0.0


def metric_delta(ctrl: Dict[str, Any], cand: Dict[str, Any], key: str) -> float:
    return float(cand.get(key, 0.0)) - float(ctrl.get(key, 0.0))


def close_enough(a: float, b: float, tolerance: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance)


def check_metric_drift(
    ctrl_metrics: Dict[str, Any],
    cand_metrics: Dict[str, Any],
    abs_tolerance: float,
) -> Tuple[bool, list[str]]:
    failures: list[str] = []
    for key in (*LOWER_IS_BETTER, *HIGHER_IS_BETTER):
        if key not in ctrl_metrics or key not in cand_metrics:
            continue
        delta = metric_delta(ctrl_metrics, cand_metrics, key)
        if abs(delta) > abs_tolerance:
            failures.append(f"{key} drift {delta:+.8g} exceeds {abs_tolerance}")
    return not failures, failures


def collect_gate_values(system: Dict[str, Any]) -> Dict[str, float]:
    return {
        "overall_fps": summary_value(system, "overall_fps"),
        "formal_fps_valid": float(bool(summary_value(system, "formal_fps_valid", 1.0))),
        "cache_max": per_sequence_max(system, "kv_cache_tokens_max"),
        "seq_max": per_sequence_max(system, "kv_max_seq_len_seen"),
        "evict_calls_total": summary_value(system, "kv_evict_calls_total"),
        "cache_hit_rate": summary_value(system, "kv_cache_hit_rate"),
    }


def print_values(title: str, values: Dict[str, float]) -> None:
    print(title)
    for key, value in values.items():
        print(f"  {key}: {value}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ctrl-system", type=Path, required=True)
    parser.add_argument("--cand-system", type=Path, required=True)
    parser.add_argument("--ctrl-result", type=Path, required=True)
    parser.add_argument("--cand-result", type=Path, required=True)
    parser.add_argument("--min-fps-gain-pct", type=float, default=3.0)
    parser.add_argument("--metric-abs-tol", type=float, default=1e-9)
    parser.add_argument("--cache-abs-tol", type=float, default=0.0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    ctrl_system = load_json(args.ctrl_system)
    cand_system = load_json(args.cand_system)
    ctrl_result = load_json(args.ctrl_result)
    cand_result = load_json(args.cand_result)

    ctrl = collect_gate_values(ctrl_system)
    cand = collect_gate_values(cand_system)
    fps_gain_pct = 100.0 * (cand["overall_fps"] - ctrl["overall_fps"]) / max(ctrl["overall_fps"], 1e-12)

    print_values("control", ctrl)
    print_values("candidate", cand)
    print(f"fps_gain_pct: {fps_gain_pct}")

    failures: list[str] = []
    if not bool(ctrl["formal_fps_valid"]) or not bool(cand["formal_fps_valid"]):
        failures.append("formal_fps_valid is false for ctrl or candidate")
    if fps_gain_pct < args.min_fps_gain_pct:
        failures.append(f"fps gain {fps_gain_pct:.4f}% below required {args.min_fps_gain_pct:.4f}%")

    for key in ("cache_max", "seq_max"):
        if not close_enough(ctrl[key], cand[key], args.cache_abs_tol):
            failures.append(f"{key} drift ctrl={ctrl[key]} cand={cand[key]}")

    for key in ("evict_calls_total", "cache_hit_rate"):
        if not close_enough(ctrl[key], cand[key], args.cache_abs_tol):
            failures.append(f"{key} drift ctrl={ctrl[key]} cand={cand[key]}")

    metrics_ok, metric_failures = check_metric_drift(ctrl_result, cand_result, args.metric_abs_tol)
    if not metrics_ok:
        failures.extend(metric_failures)

    if failures:
        print("GATE: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 2

    print("GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
