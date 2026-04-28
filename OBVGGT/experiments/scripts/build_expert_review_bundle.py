from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "OBVGGT" / "experiments" / "review_bundles"

DIRECT_FILES = [
    "PROJECT_BRIEF.md",
    "OBVGGT/README.md",
    "OBVGGT/experiments/README.md",
    "OBVGGT/experiments/EXPERIMENTS.md",
    "OBVGGT/experiments/VARIANTS.md",
    "OBVGGT/experiments/analysis/SUMMARY.md",
    "OBVGGT/experiments/analysis/ALL_RESULTS.md",
    "OBVGGT/experiments/analysis/ABLATION_ANALYSIS_20260324.md",
    "OBVGGT/experiments/analysis/PEAK_MEMORY_20260326.md",
    "OBVGGT/experiments/quick_run.sh",
    "OBVGGT/experiments/scripts/render_experiment_docs.py",
    "OBVGGT/src/eval/kv_cache_utils.py",
    "OBVGGT/src/eval/monodepth/launch.py",
    "OBVGGT/src/eval/monodepth/eval_metrics.py",
    "OBVGGT/src/eval/video_depth/launch.py",
    "OBVGGT/src/eval/mv_recon/launch.py",
    "OBVGGT/src/streamvggt/utils/obcache_kv.py",
    "OBVGGT/src/streamvggt/layers/attention.py",
    "OBVGGT/src/vggt/layers/attention.py",
    "StreamVGGT/README.md",
    "XStreamVGGT/README.md",
    "InfiniteVGGT/README.md",
]

GLOB_PATTERNS = [
    "OBVGGT/experiments/configs/obcache*.json",
    "OBVGGT/experiments/configs/baseline.json",
    "OBVGGT/experiments/configs/xstreamvggt.json",
    "OBVGGT/experiments/configs/infinitevggt.json",
    "OBVGGT/experiments/analysis/tables/ablation_*.csv",
]

SELECTED_RUN_IDS = [
    "20260326_001223_obcache_p1_small_joint_s1r1h3_video_depth",
    "20260327_214646_obcache_v_only_clean_v_s1r2h4_video_depth",
    "20260327_220720_obcache_no_recent_ctrl_joint_s1r0h4_video_depth",
    "20260327_222541_obcache_random_s2_random_s1r2h4_video_depth",
    "20260327_224254_obcache_random_s3_random_s1r2h4_video_depth",
    "20260326_001223_obcache_p1_joint_s1r2h4_mv_recon",
    "20260326_001835_obcache_random_random_s1r2h4_mv_recon",
    "20260326_002422_obcache_sliding_window_sliding_window_s0r7h0_mv_recon",
    "20260326_001223_baseline_video_depth",
]

RUN_METADATA_FILES = ["record.md", "manifest.json", "artifacts.json"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a lightweight code-and-results bundle for expert review."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory that will receive the bundle directory and zip archive.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=f"expert_review_bundle_{date.today().strftime('%Y%m%d')}",
        help="Bundle directory and zip basename.",
    )
    return parser.parse_args()


def copy_file(src: Path, dest_root: Path, copied: list[str]) -> None:
    if not src.exists():
        print(f"[WARN] missing file: {src}")
        return
    rel = src.relative_to(REPO_ROOT)
    dest = dest_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    copied.append(rel.as_posix())


def collect_direct_and_globbed_files() -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for rel_path in DIRECT_FILES:
        path = REPO_ROOT / rel_path
        if path not in seen:
            files.append(path)
            seen.add(path)

    for pattern in GLOB_PATTERNS:
        for path in sorted(REPO_ROOT.glob(pattern)):
            if path not in seen:
                files.append(path)
                seen.add(path)

    return files


def copy_selected_runs(dest_root: Path, copied: list[str]) -> list[str]:
    copied_run_ids: list[str] = []
    for run_id in SELECTED_RUN_IDS:
        run_dir = REPO_ROOT / "OBVGGT" / "experiments" / "runs" / run_id
        if not run_dir.exists():
            print(f"[WARN] missing run dir: {run_dir}")
            continue

        copied_any = False
        for filename in RUN_METADATA_FILES:
            copy_file(run_dir / filename, dest_root, copied)
            if (run_dir / filename).exists():
                copied_any = True

        if copied_any:
            copied_run_ids.append(run_id)

    return copied_run_ids


def write_guide(dest_root: Path, copied_run_ids: list[str]) -> None:
    guide = f"""# Expert Review Guide

This bundle is a lightweight subset of the workspace for asking an external expert to judge:

1. whether the current results look abnormal for streaming / KV-cache-compression papers,
2. whether the ablation design is reasonable and sufficiently convincing,
3. whether the current evidence really supports `obcache_p1_small` as the default setting.

## What Is Included

- experiment status and generated summaries:
  - `OBVGGT/experiments/EXPERIMENTS.md`
  - `OBVGGT/experiments/analysis/SUMMARY.md`
  - `OBVGGT/experiments/analysis/ALL_RESULTS.md`
  - `OBVGGT/experiments/analysis/ABLATION_ANALYSIS_20260324.md`
  - `OBVGGT/experiments/analysis/PEAK_MEMORY_20260326.md`
- raw ablation tables:
  - `OBVGGT/experiments/analysis/tables/ablation_video_depth_20260324.csv`
  - `OBVGGT/experiments/analysis/tables/ablation_mv_recon_20260326.csv`
- key launcher / artifact-generation code:
  - `OBVGGT/experiments/quick_run.sh`
  - `OBVGGT/experiments/scripts/render_experiment_docs.py`
- core KV-cache implementation and eval entrypoints:
  - `OBVGGT/src/streamvggt/utils/obcache_kv.py`
  - `OBVGGT/src/streamvggt/layers/attention.py`
  - `OBVGGT/src/vggt/layers/attention.py`
  - `OBVGGT/src/eval/kv_cache_utils.py`
  - `OBVGGT/src/eval/monodepth/launch.py`
  - `OBVGGT/src/eval/monodepth/eval_metrics.py`
  - `OBVGGT/src/eval/video_depth/launch.py`
  - `OBVGGT/src/eval/mv_recon/launch.py`
- configs:
  - baseline / OBVGGT / XStreamVGGT / InfiniteVGGT
  - all `obcache*.json` ablation configs
- selected run metadata only (no datasets / checkpoints / large logs):
{chr(10).join(f"  - `OBVGGT/experiments/runs/{run_id}/`" for run_id in copied_run_ids)}
- related-work repo READMEs:
  - `StreamVGGT/README.md`
  - `XStreamVGGT/README.md`
  - `InfiniteVGGT/README.md`

## What Is Intentionally Excluded

- datasets
- checkpoints
- rendered point clouds / images
- large runtime logs
- full repo history and unrelated tooling

## Suggested Reading Order

1. `OBVGGT/experiments/analysis/SUMMARY.md`
2. `OBVGGT/experiments/analysis/ABLATION_ANALYSIS_20260324.md`
3. `OBVGGT/experiments/analysis/ALL_RESULTS.md`
4. `OBVGGT/src/streamvggt/utils/obcache_kv.py`
5. `OBVGGT/src/streamvggt/layers/attention.py`
6. the selected run `record.md` / `manifest.json` / `artifacts.json`

## Main Questions For The Expert

1. For streaming 3D / long-context KV methods, do these result magnitudes look normal or suspiciously flat?
2. Is the current interpretation correct that `monodepth` and much of `mv_recon` are weakly KV-sensitive, while `video_depth` is the real evidence-bearing task?
3. Is the current ablation package enough for paper-level defense, or does it still need more stability runs / longer-sequence stress tests?
4. Does `obcache_p1_small` look like a justified default, given the newer controls `obcache_v_only_clean`, `obcache_no_recent_ctrl`, `obcache_random_s2`, and `obcache_random_s3`?

## Current Context

- This bundle was produced on {date.today().isoformat()} from the local mirrored workspace.
- Remote runs were synced back locally before regenerating the summary docs.
- `mv_recon` ablation runs are intentionally included even though they are `PARTIAL_DONE` at the artifact-contract level, because the per-dataset results exist and are relevant to expert judgment.

## Known Audit Gaps

- The main baseline numbers in generated summary tables trace back to an earlier `DONE` baseline run, while the locally mirrored `20260326_001223_baseline_video_depth` rerun is `FAILED`. This is enough for reading the current conclusion, but not enough for a perfectly clean audit trail.
- `obcache_random_s2` and `obcache_random_s3` are included as repeated random-baseline configs, but the current package still does not prove end-to-end seed plumbing unless the expert also checks the runtime command path.
- The four March 27 supplementary controls are mirrored as run metadata, but if their raw result payloads are not mirrored locally, generated tables may lag behind the latest control runs.
"""
    guide_path = dest_root / "EXPERT_REVIEW_GUIDE.md"
    guide_path.write_text(guide, encoding="utf-8")


def write_manifest(dest_root: Path, copied: list[str], copied_run_ids: list[str], zip_path: Path) -> None:
    manifest = {
        "bundle_name": dest_root.name,
        "created_on": date.today().isoformat(),
        "copied_files": copied,
        "selected_run_ids": copied_run_ids,
        "zip_path": str(zip_path),
    }
    (dest_root / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    output_root = args.output_root.resolve()
    bundle_dir = output_root / args.name
    zip_base = output_root / args.name

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for path in collect_direct_and_globbed_files():
        copy_file(path, bundle_dir, copied)

    copied_run_ids = copy_selected_runs(bundle_dir, copied)
    write_guide(bundle_dir, copied_run_ids)
    write_manifest(bundle_dir, copied, copied_run_ids, zip_base.with_suffix(".zip"))

    archive_path = Path(shutil.make_archive(str(zip_base), "zip", root_dir=bundle_dir))

    print(f"[OK] bundle dir: {bundle_dir}")
    print(f"[OK] zip archive: {archive_path}")
    print(f"[OK] copied files: {len(copied)}")
    print(f"[OK] selected runs: {len(copied_run_ids)}")


if __name__ == "__main__":
    main()
