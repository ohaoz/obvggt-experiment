#!/usr/bin/env python3
"""Backfill inline_metrics into artifacts.json from existing CSV tables.

This makes the local experiment mirror self-contained: render_experiment_docs.py
can produce full result tables without needing access to remote artifact files.

Usage:
    python3 backfill_inline_metrics.py [--experiments-root EXPERIMENTS_ROOT] [--dry-run]
"""

import argparse
import csv
import json
from pathlib import Path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_video_depth_lookup(csv_path: Path) -> dict[str, dict[str, dict]]:
    """Build lookup: config_tag -> dataset -> metrics."""
    if not csv_path.exists():
        return {}
    lookup: dict[str, dict[str, dict]] = {}
    for row in read_csv_rows(csv_path):
        tag = row.get("config_tag", "")
        for dataset in ["sintel", "bonn", "kitti"]:
            absrel = row.get(f"{dataset}_absrel")
            rmse = row.get(f"{dataset}_rmse")
            d125 = row.get(f"{dataset}_d125")
            if absrel and rmse and d125:
                lookup.setdefault(tag, {})[dataset] = {
                    "Abs Rel": float(absrel),
                    "RMSE": float(rmse),
                    "δ < 1.25": float(d125),
                }
    return lookup


def build_mv_recon_lookup(csv_path: Path) -> dict[str, dict[str, dict]]:
    """Build lookup: config_tag -> dataset -> metrics."""
    if not csv_path.exists():
        return {}
    lookup: dict[str, dict[str, dict]] = {}
    for row in read_csv_rows(csv_path):
        tag = row.get("config_tag", "")
        for dataset_key, dataset_name in [("7scenes", "7scenes"), ("nrgbd", "NRGBD")]:
            acc = row.get(f"{dataset_key}_acc")
            comp = row.get(f"{dataset_key}_comp")
            nc = row.get(f"{dataset_key}_nc")
            if acc and comp and nc:
                lookup.setdefault(tag, {})[dataset_name] = {
                    "acc": float(acc),
                    "comp": float(comp),
                    "nc": float(nc),
                }
    return lookup


def dataset_from_artifact_path(artifact_path: str) -> str:
    """Extract dataset name from artifact path like .../bonn_obcache/result_scale.json."""
    parent = Path(artifact_path).parent.name
    for ds in ["sintel", "bonn", "kitti", "7scenes", "7Scenes", "NRGBD", "nrgbd", "nyu", "scannet"]:
        if ds.lower() in parent.lower():
            return ds.lower()
    return parent


def normalize_dataset(ds: str) -> str:
    mapping = {"7scenes": "7scenes", "nrgbd": "NRGBD"}
    return mapping.get(ds, ds)


def build_monodepth_lookup(csv_path: Path) -> dict[str, dict[str, dict]]:
    """Build lookup for monodepth from main_comparison CSV: config_tag -> dataset -> metrics."""
    if not csv_path.exists():
        return {}
    lookup: dict[str, dict[str, dict]] = {}
    for row in read_csv_rows(csv_path):
        tag = row.get("config_tag", "")
        task = row.get("task", "")
        dataset = row.get("dataset", "")
        if task != "monodepth":
            continue
        absrel = row.get("absrel")
        rmse = row.get("rmse")
        d125 = row.get("d125")
        if absrel and rmse and d125:
            lookup.setdefault(tag, {})[dataset] = {
                "Abs Rel": float(absrel),
                "RMSE": float(rmse),
                "δ < 1.25": float(d125),
            }
    return lookup


def build_main_comparison_lookup(csv_path: Path) -> dict[str, dict[str, dict]]:
    """Build lookup from main_comparison_4variants.csv: config_tag -> dataset -> metrics."""
    if not csv_path.exists():
        return {}
    lookup: dict[str, dict[str, dict]] = {}
    for row in read_csv_rows(csv_path):
        tag = row.get("config_tag", "")
        task = row.get("task", "")
        dataset = row.get("dataset", "")

        if task == "video_depth":
            absrel = row.get("absrel")
            rmse = row.get("rmse")
            d125 = row.get("d125")
            if absrel and rmse and d125:
                lookup.setdefault(tag, {})[dataset] = {
                    "Abs Rel": float(absrel),
                    "RMSE": float(rmse),
                    "δ < 1.25": float(d125),
                }
        elif task == "mv_recon":
            acc = row.get("acc")
            comp = row.get("comp")
            nc = row.get("nc")
            if acc and comp and nc:
                lookup.setdefault(tag, {})[dataset] = {
                    "acc": float(acc),
                    "comp": float(comp),
                    "nc": float(nc),
                }
    return lookup


def main():
    parser = argparse.ArgumentParser(description="Backfill inline_metrics into artifacts.json")
    parser.add_argument("--experiments-root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    experiments_root = args.experiments_root
    tables_dir = experiments_root / "analysis" / "tables"

    vd_lookup = build_video_depth_lookup(tables_dir / "ablation_video_depth_20260324.csv")
    mr_lookup = build_mv_recon_lookup(tables_dir / "ablation_mv_recon_20260326.csv")
    main_lookup = build_main_comparison_lookup(tables_dir / "main_comparison_4variants.csv")
    mono_lookup = build_monodepth_lookup(tables_dir / "main_comparison_4variants.csv")

    # Merge main_lookup into vd/mr lookups (main_lookup takes precedence for new keys)
    for tag, datasets in main_lookup.items():
        for ds, metrics in datasets.items():
            if "Abs Rel" in metrics:
                vd_lookup.setdefault(tag, {})[ds] = metrics
            elif "acc" in metrics:
                mr_lookup.setdefault(tag, {})[ds] = metrics

    runs_dir = experiments_root / "runs"
    if not runs_dir.exists():
        print("No runs/ directory found.")
        return

    updated_count = 0
    for manifest_path in sorted(runs_dir.glob("*/manifest.json")):
        run_dir = manifest_path.parent
        artifacts_path = run_dir / "artifacts.json"
        if not artifacts_path.exists():
            continue

        with artifacts_path.open("r", encoding="utf-8") as f:
            artifacts = json.load(f)

        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        task = manifest.get("task", "")
        config_tag = manifest.get("config_tag", "") or manifest.get("result_tag", "")
        modified = False

        for item in artifacts.get("artifacts", []):
            if "inline_metrics" in item:
                continue

            artifact_name = item.get("name", "")
            artifact_path = item.get("path", "")
            ds = dataset_from_artifact_path(artifact_path)

            if task == "video_depth" and artifact_name == "result_scale.json":
                metrics = vd_lookup.get(config_tag, {}).get(ds)
                if metrics:
                    item["inline_metrics"] = metrics
                    modified = True

            elif task == "mv_recon" and artifact_name == "summary_metrics.json":
                ds_norm = normalize_dataset(ds)
                metrics = mr_lookup.get(config_tag, {}).get(ds_norm)
                if metrics:
                    item["inline_metrics"] = metrics
                    modified = True

            elif task == "monodepth" and artifact_name == "metric.json":
                metrics = mono_lookup.get(config_tag, {}).get(ds)
                if metrics:
                    item["inline_metrics"] = metrics
                    modified = True

        if modified:
            updated_count += 1
            if args.dry_run:
                print(f"[DRY RUN] Would update: {artifacts_path.name} in {run_dir.name}")
            else:
                with artifacts_path.open("w", encoding="utf-8") as f:
                    json.dump(artifacts, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                print(f"Updated: {run_dir.name}")

    print(f"\nTotal: {updated_count} artifacts.json files {'would be ' if args.dry_run else ''}updated.")


if __name__ == "__main__":
    main()
