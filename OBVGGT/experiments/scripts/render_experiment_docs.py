import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


VARIANT_DISPLAY = {
    "baseline": "StreamVGGT",
    "obcache": "OBVGGT",
    "xstreamvggt": "XStreamVGGT",
    "infinitevggt": "InfiniteVGGT",
}

TASK_EXPECTED_DATASETS = {
    "monodepth": ["sintel", "bonn", "kitti", "nyu", "scannet"],
    "video_depth": ["sintel", "bonn", "kitti"],
    "mv_recon": ["7scenes", "NRGBD"],
}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_iso(ts: str | None) -> datetime:
    if not ts:
        return datetime.min
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.min


def discover_runs(experiments_root: Path) -> list[dict]:
    runs = []
    runs_dir = experiments_root / "runs"
    if not runs_dir.exists():
        return runs

    for manifest_path in sorted(runs_dir.glob("*/manifest.json")):
        run_dir = manifest_path.parent
        manifest = read_json(manifest_path)
        artifacts_path = run_dir / "artifacts.json"
        artifacts = read_json(artifacts_path) if artifacts_path.exists() else {}
        runs.append(
            {
                "run_dir": run_dir,
                "manifest": manifest,
                "artifacts": artifacts,
            }
        )
    runs.sort(key=lambda item: parse_iso(item["manifest"].get("timestamps", {}).get("end")), reverse=True)
    return runs


def artifact_paths(run: dict, name: str) -> list[Path]:
    items = run.get("artifacts", {}).get("artifacts", [])
    return [Path(item["path"]) for item in items if item.get("name") == name]


def dataset_name_from_path(task: str, path: Path) -> str:
    if task in {"monodepth", "video_depth"}:
        return path.parent.name
    if task == "mv_recon":
        return path.parent.name
    if task == "pose_co3d":
        return path.parent.name
    return path.parent.name


def summarize_run(run: dict) -> str:
    manifest = run["manifest"]
    task = manifest.get("task", "")

    if task == "monodepth":
        datasets = sorted({dataset_name_from_path(task, p).split("_")[0] for p in artifact_paths(run, "metric.json")})
        return f"datasets={len(datasets)}/{len(TASK_EXPECTED_DATASETS['monodepth'])}: {', '.join(datasets)}"

    if task == "video_depth":
        result_datasets = sorted({dataset_name_from_path(task, p).split("_")[0] for p in artifact_paths(run, 'result_scale.json')})
        system_datasets = sorted({dataset_name_from_path(task, p).split("_")[0] for p in artifact_paths(run, 'system_metrics.json') if p.parent.name != manifest.get('result_tag', '')})
        return f"result={len(result_datasets)}/3, system={len(system_datasets)}/3"

    if task == "mv_recon":
        dataset_summaries = sorted({dataset_name_from_path(task, p) for p in artifact_paths(run, "summary_metrics.json") if dataset_name_from_path(task, p) in TASK_EXPECTED_DATASETS["mv_recon"]})
        has_root_summary = any(p.parent.name == manifest.get("result_tag", "") for p in artifact_paths(run, "summary_metrics.json"))
        has_root_system = any(p.parent.name == manifest.get("result_tag", "") for p in artifact_paths(run, "system_metrics.json"))
        return f"datasets={len(dataset_summaries)}/2, root_summary={'yes' if has_root_summary else 'no'}, root_system={'yes' if has_root_system else 'no'}"

    if task == "pose_co3d":
        pose_summary = next(iter(artifact_paths(run, "pose_summary.json")), None)
        if pose_summary and pose_summary.exists():
            try:
                payload = read_json(pose_summary)
                mean_auc30 = payload.get("mean", {}).get("Auc_30")
                if mean_auc30 is not None:
                    return f"AUC30={mean_auc30:.4f}"
            except Exception:
                pass
        return "pose summary pending"

    return "n/a"


def metric_rows_for_run(run: dict) -> list[dict]:
    manifest = run["manifest"]
    task = manifest.get("task", "")
    rows = []

    if task == "monodepth":
        for path in artifact_paths(run, "metric.json"):
            payload = read_json(path)
            rows.append(
                {
                    "dataset": dataset_name_from_path(task, path),
                    "metrics": {
                        "Abs Rel": payload.get("Abs Rel"),
                        "RMSE": payload.get("RMSE"),
                        "δ<1.25": payload.get("δ < 1.25"),
                    },
                }
            )
        return sorted(rows, key=lambda row: row["dataset"])

    if task == "video_depth":
        for path in artifact_paths(run, "result_scale.json"):
            payload = read_json(path)
            rows.append(
                {
                    "dataset": dataset_name_from_path(task, path),
                    "metrics": {
                        "Abs Rel": payload.get("Abs Rel"),
                        "RMSE": payload.get("RMSE"),
                        "δ<1.25": payload.get("δ < 1.25"),
                    },
                }
            )
        return sorted(rows, key=lambda row: row["dataset"])

    if task == "mv_recon":
        for path in artifact_paths(run, "summary_metrics.json"):
            dataset = dataset_name_from_path(task, path)
            if dataset not in TASK_EXPECTED_DATASETS["mv_recon"]:
                continue
            payload = read_json(path)
            rows.append(
                {
                    "dataset": dataset,
                    "metrics": {
                        "acc": payload.get("acc"),
                        "comp": payload.get("comp"),
                        "nc": payload.get("nc"),
                    },
                }
            )
        return sorted(rows, key=lambda row: row["dataset"])

    if task == "pose_co3d":
        pose_summary = next(iter(artifact_paths(run, "pose_summary.json")), None)
        if pose_summary and pose_summary.exists():
            payload = read_json(pose_summary)
            per_category = payload.get("per_category", {})
            for dataset, values in sorted(per_category.items()):
                rows.append(
                    {
                        "dataset": dataset,
                        "metrics": {
                            "AUC30": values.get("Auc_30"),
                            "AUC15": values.get("Auc_15"),
                            "AUC5": values.get("Auc_5"),
                        },
                    }
                )
        return rows

    return rows


def render_experiments_md(experiments_root: Path, runs: list[dict]) -> str:
    lines = [
        "# OBVGGT 实验追踪表",
        "",
        "> 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。",
        "> 单次运行的权威来源是 `experiments/runs/<run_id>/manifest.json`、`artifacts.json` 与 `record.md`。",
        "",
        "## 实验概览",
        "",
        "说明：",
        "- 优先用 repo 名称表达变体：`StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`。",
        "- 历史脚本参数仍可能出现 `baseline / obcache`；其中 `obcache = OBVGGT`。",
        "- `monodepth` 是 regression-only，不作为 KV 主 benchmark 结论来源。",
        "",
        "| Run ID | Variant | Task | Date | Status | Run Record | 关键指标 |",
        "|--------|---------|------|------|--------|------------|----------|",
    ]

    if not runs:
        lines.append("| _(当前本地 experiments/runs 无记录；可运行 refresh 脚本从服务器同步)_ | | | | | | |")
    else:
        for run in runs:
            manifest = run["manifest"]
            run_id = manifest.get("run_id", run["run_dir"].name)
            variant = VARIANT_DISPLAY.get(manifest.get("variant", ""), manifest.get("variant", "unknown"))
            task = manifest.get("task", "unknown")
            status = manifest.get("status", "UNKNOWN")
            end_ts = manifest.get("timestamps", {}).get("end") or manifest.get("timestamps", {}).get("start") or ""
            date_str = end_ts[:10] if end_ts else ""
            record_rel = f"experiments/runs/{run_id}/record.md"
            lines.append(
                f"| `{run_id}` | `{variant}` | `{task}` | `{date_str}` | `{status}` | `{record_rel}` | {summarize_run(run)} |"
            )

    lines.extend(
        [
            "",
            "## 评测口径说明",
            "",
            "- `monodepth`：仅用于精度 regression，不作为 KV eviction 主 benchmark。",
            "- `video_depth`：当前主时序 KV benchmark。",
            "- `mv_recon`：当前主多视角 KV benchmark。",
            "- `pose_co3d`：当前补充 benchmark；需要 CO3D 原始数据和 annotations 同时到位。",
            "",
            "## 维护规范",
            "",
            "1. `experiments/runs/<run_id>/manifest.json` 和 `artifacts.json` 是唯一机器可读真相。",
            "2. `EXPERIMENTS.md` 与 `analysis/SUMMARY.md` 一律由生成器重建，不手工编辑。",
            "3. 每次 run 结束后，应重新执行生成器；若在服务器上运行，优先更新服务器上的 docs。",
            "4. 本地 docs 需要时通过 refresh 脚本从默认服务器重新拉取。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_summary_md(runs: list[dict]) -> str:
    lines = [
        "# 已完成实验报告汇总",
        "",
        "> 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。",
        "",
    ]

    if not runs:
        lines.append("> 当前没有本地 run 记录可汇总。")
        return "\n".join(lines) + "\n"

    index = 1
    for run in runs:
        manifest = run["manifest"]
        run_id = manifest.get("run_id", run["run_dir"].name)
        variant = VARIANT_DISPLAY.get(manifest.get("variant", ""), manifest.get("variant", "unknown"))
        task = manifest.get("task", "unknown")
        status = manifest.get("status", "UNKNOWN")
        date_str = (manifest.get("timestamps", {}).get("end") or manifest.get("timestamps", {}).get("start") or "")[:10]

        lines.extend(
            [
                f"## {index}. {task} ({variant}) - {date_str}",
                "",
                f"**Run ID**: `{run_id}`",
                f"**状态**: `{status}`",
                f"**结果摘要**: {summarize_run(run)}",
                "",
            ]
        )

        rows = metric_rows_for_run(run)
        if rows:
            headers = sorted({key for row in rows for key in row["metrics"].keys() if row["metrics"].get(key) is not None})
            lines.append("| 数据集 | " + " | ".join(headers) + " |")
            lines.append("|--------|" + "|".join(["---"] * len(headers)) + "|")
            for row in rows:
                values = []
                for header in headers:
                    value = row["metrics"].get(header)
                    if isinstance(value, float):
                        values.append(f"{value:.4f}")
                    elif value is None:
                        values.append("")
                    else:
                        values.append(str(value))
                lines.append("| " + row["dataset"] + " | " + " | ".join(values) + " |")
            lines.append("")

        lines.append(f"**Run record**: `experiments/runs/{run_id}/record.md`")
        lines.append("")
        index += 1

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiments-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    experiments_root = Path(args.experiments_root).resolve()
    runs = discover_runs(experiments_root)

    experiments_md = render_experiments_md(experiments_root, runs)
    summary_md = render_summary_md(runs)

    (experiments_root / "EXPERIMENTS.md").write_text(experiments_md, encoding="utf-8")
    analysis_dir = experiments_root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "SUMMARY.md").write_text(summary_md, encoding="utf-8")

    print(f"[render-experiment-docs] wrote {experiments_root / 'EXPERIMENTS.md'}")
    print(f"[render-experiment-docs] wrote {analysis_dir / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
