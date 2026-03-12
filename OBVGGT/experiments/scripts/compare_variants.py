import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


RUN_ARTIFACT_FILENAMES = {
    "metric.json",
    "result_scale.json",
    "result_scale&shift.json",
    "result_metric.json",
    "summary_metrics.json",
    "pose_summary.json",
    "system_metrics.json",
}


def read_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def numeric_items(payload: Dict, prefix: str = "") -> Iterable[Tuple[str, float]]:
    for key, value in payload.items():
        name = f"{prefix}{key}" if prefix else key
        if isinstance(value, dict):
            yield from numeric_items(value, prefix=f"{name}.")
        elif isinstance(value, (int, float)):
            yield name, float(value)


def dataset_from_artifact(path: Path, task: str) -> str:
    if task in {"monodepth", "video_depth"}:
        return path.parent.name
    if task in {"mv_recon", "pose_co3d"}:
        return path.parent.name
    return "unknown"


def gather_runs(experiments_root: Path) -> List[Dict]:
    runs_dir = experiments_root / "runs"
    manifests = []
    if not runs_dir.exists():
        return manifests
    for manifest_path in sorted(runs_dir.glob("*/manifest.json")):
        manifest = read_json(manifest_path)
        manifest["_run_dir"] = str(manifest_path.parent)
        manifests.append(manifest)
    return manifests


def write_csv(path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def main() -> None:
    experiments_root = Path(__file__).resolve().parents[1]
    analysis_root = experiments_root / "analysis"
    tables_dir = analysis_root / "tables"
    figures_dir = analysis_root / "figures"

    short_rows: List[Dict] = []
    efficiency_rows: List[Dict] = []
    long_rows: List[Dict] = []
    memory_curve_rows: List[Dict] = []
    quality_curve_rows: List[Dict] = []

    for manifest in gather_runs(experiments_root):
        task = manifest.get("task", "")
        run_id = manifest.get("run_id", "")
        variant = manifest.get("variant", "")
        benchmark_role = manifest.get("benchmark_role", "")
        output_root = Path(manifest.get("output_root", ""))
        if not output_root.exists():
            continue

        for artifact_path in sorted(output_root.rglob("*")):
            if not artifact_path.is_file() or artifact_path.name not in RUN_ARTIFACT_FILENAMES:
                continue
            try:
                payload = read_json(artifact_path)
            except Exception:
                continue

            if artifact_path.name in {"metric.json", "result_scale.json", "result_scale&shift.json", "result_metric.json", "summary_metrics.json", "pose_summary.json"}:
                row = {
                    "run_id": run_id,
                    "variant": variant,
                    "task": task,
                    "benchmark_role": benchmark_role,
                    "dataset": dataset_from_artifact(artifact_path, task),
                    "artifact": artifact_path.name,
                    "path": str(artifact_path),
                }
                for key, value in numeric_items(payload):
                    row[key] = value
                short_rows.append(row)

            if artifact_path.name == "system_metrics.json":
                summary = payload.get("summary", payload)
                row = {
                    "run_id": run_id,
                    "variant": variant,
                    "task": task,
                    "benchmark_role": benchmark_role,
                    "dataset": dataset_from_artifact(artifact_path, task),
                    "artifact": artifact_path.name,
                    "path": str(artifact_path),
                }
                for key, value in numeric_items(summary):
                    row[key] = value
                efficiency_rows.append(row)

                seq_len = manifest.get("sequence_length") or summary.get("sequence_length") or ""
                memory_curve_rows.append(
                    {
                        "run_id": run_id,
                        "variant": variant,
                        "task": task,
                        "sequence_length": seq_len,
                        "peak_mem_mb": row.get("max_peak_allocated_mb", row.get("peak_allocated_mb", "")),
                        "kv_cache_mem_mb": row.get("kv_cache_mem_mb", ""),
                    }
                )
                quality_curve_rows.append(
                    {
                        "run_id": run_id,
                        "variant": variant,
                        "task": task,
                        "sequence_length": seq_len,
                        "fps": row.get("overall_fps", row.get("fps", "")),
                        "latency_ms_per_frame": row.get("avg_latency_ms_per_frame", row.get("latency_ms_per_frame", "")),
                    }
                )
                if task == "long_stream":
                    long_rows.append(row)

    short_fields = sorted({key for row in short_rows for key in row.keys()}) or [
        "run_id",
        "variant",
        "task",
        "benchmark_role",
        "dataset",
        "artifact",
        "path",
    ]
    efficiency_fields = sorted({key for row in efficiency_rows for key in row.keys()}) or [
        "run_id",
        "variant",
        "task",
        "benchmark_role",
        "dataset",
        "artifact",
        "path",
    ]
    long_fields = sorted({key for row in long_rows for key in row.keys()}) or efficiency_fields
    memory_fields = ["run_id", "variant", "task", "sequence_length", "peak_mem_mb", "kv_cache_mem_mb"]
    quality_fields = ["run_id", "variant", "task", "sequence_length", "fps", "latency_ms_per_frame"]

    write_csv(tables_dir / "short_sequence_metrics.csv", short_rows, short_fields)
    write_csv(tables_dir / "efficiency_metrics.csv", efficiency_rows, efficiency_fields)
    write_csv(tables_dir / "long_horizon_metrics.csv", long_rows, long_fields)
    write_csv(figures_dir / "memory_vs_length.csv", memory_curve_rows, memory_fields)
    write_csv(figures_dir / "quality_vs_length.csv", quality_curve_rows, quality_fields)

    print(f"[compare_variants] wrote {tables_dir / 'short_sequence_metrics.csv'}")
    print(f"[compare_variants] wrote {tables_dir / 'efficiency_metrics.csv'}")
    print(f"[compare_variants] wrote {tables_dir / 'long_horizon_metrics.csv'}")
    print(f"[compare_variants] wrote {figures_dir / 'memory_vs_length.csv'}")
    print(f"[compare_variants] wrote {figures_dir / 'quality_vs_length.csv'}")


if __name__ == "__main__":
    main()
