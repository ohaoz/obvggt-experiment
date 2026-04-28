import argparse
import csv
import json
import re
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_iso(ts: str | None) -> datetime:
    if not ts:
        return datetime.min
    try:
        dt = datetime.fromisoformat(ts)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
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
    runs.sort(key=lambda item: parse_iso(item["manifest"].get("timestamps", {}).get("end") or item["manifest"].get("timestamps", {}).get("start")), reverse=True)
    return runs


def artifact_items(run: dict, name: str) -> list[dict]:
    """Return full artifact entries (with path, name, and optional inline_metrics)."""
    items = run.get("artifacts", {}).get("artifacts", [])
    return [item for item in items if item.get("name") == name]


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
        pose_item = next(iter(artifact_items(run, "pose_summary.json")), None)
        if pose_item:
            payload = _load_artifact_payload(pose_item)
            if payload:
                mean_auc30 = payload.get("mean", {}).get("Auc_30")
                if mean_auc30 is not None:
                    return f"AUC30={mean_auc30:.4f}"
        return "pose summary pending"

    return "n/a"


def _load_artifact_payload(item: dict) -> dict | None:
    """Load metric payload from file path or inline_metrics fallback."""
    path = Path(item["path"])
    if path.exists():
        return read_json(path)
    if "inline_metrics" in item:
        return item["inline_metrics"]
    return None


def metric_rows_for_run(run: dict) -> list[dict]:
    manifest = run["manifest"]
    task = manifest.get("task", "")
    rows = []

    if task == "monodepth":
        for item in artifact_items(run, "metric.json"):
            payload = _load_artifact_payload(item)
            if payload is None:
                continue
            rows.append(
                {
                    "dataset": dataset_name_from_path(task, Path(item["path"])),
                    "metrics": {
                        "Abs Rel": payload.get("Abs Rel"),
                        "RMSE": payload.get("RMSE"),
                        "δ<1.25": payload.get("δ < 1.25"),
                    },
                }
            )
        return sorted(rows, key=lambda row: row["dataset"])

    if task == "video_depth":
        for item in artifact_items(run, "result_scale.json"):
            payload = _load_artifact_payload(item)
            if payload is None:
                continue
            rows.append(
                {
                    "dataset": dataset_name_from_path(task, Path(item["path"])),
                    "metrics": {
                        "Abs Rel": payload.get("Abs Rel"),
                        "RMSE": payload.get("RMSE"),
                        "δ<1.25": payload.get("δ < 1.25"),
                    },
                }
            )
        return sorted(rows, key=lambda row: row["dataset"])

    if task == "mv_recon":
        for item in artifact_items(run, "summary_metrics.json"):
            dataset = dataset_name_from_path(task, Path(item["path"]))
            if dataset not in TASK_EXPECTED_DATASETS["mv_recon"]:
                continue
            payload = _load_artifact_payload(item)
            if payload is None:
                continue
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
        pose_item = next(iter(artifact_items(run, "pose_summary.json")), None)
        if pose_item:
            payload = _load_artifact_payload(pose_item)
            if payload:
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


def parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def format_metric(value: float | None, digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def render_video_depth_ablation_section(experiments_root: Path) -> list[str]:
    path = experiments_root / "analysis" / "tables" / "ablation_video_depth_20260324.csv"
    if not path.exists():
        return []

    rows = read_csv_rows(path)
    rows.sort(key=lambda row: (parse_float(row.get("kitti_absrel")) is None, parse_float(row.get("kitti_absrel")) or float("inf")))

    lines = [
        "## 附加汇总：KV Cache 消融（video_depth）",
        "",
        f"**数据文件**: `analysis/tables/{path.name}`",
        "",
        "| Variant | Config | Bonn Abs Rel | Kitti Abs Rel | Kitti δ<1.25 | Kitti FPS |",
        "|--------|--------|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.get("variant", ""),
                    row.get("config_tag", ""),
                    format_metric(parse_float(row.get("bonn_absrel"))),
                    format_metric(parse_float(row.get("kitti_absrel"))),
                    format_metric(parse_float(row.get("kitti_d125"))),
                    format_metric(parse_float(row.get("kitti_fps")), digits=2),
                ]
            )
            + " |"
        )

    lines.append("")
    return lines


def render_mv_recon_ablation_section(experiments_root: Path) -> list[str]:
    path = experiments_root / "analysis" / "tables" / "ablation_mv_recon_20260326.csv"
    if not path.exists():
        return []

    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for row in read_csv_rows(path):
        grouped.setdefault(row.get("variant", ""), {})[row.get("dataset", "")] = row

    lines = [
        "## 附加汇总：KV Cache 消融（mv_recon）",
        "",
        f"**数据文件**: `analysis/tables/{path.name}`",
        "",
        "| Variant | 7Scenes Acc | 7Scenes Comp | NRGBD Acc | NRGBD Comp | Avg FPS |",
        "|--------|---|---|---|---|---|",
    ]

    for variant in sorted(grouped):
        seven_scenes = grouped[variant].get("7scenes", {})
        nrgbd = grouped[variant].get("NRGBD", {})
        fps_values = [parse_float(seven_scenes.get("fps")), parse_float(nrgbd.get("fps"))]
        fps_values = [value for value in fps_values if value is not None]
        avg_fps = sum(fps_values) / len(fps_values) if fps_values else None
        lines.append(
            "| "
            + " | ".join(
                [
                    variant,
                    format_metric(parse_float(seven_scenes.get("acc"))),
                    format_metric(parse_float(seven_scenes.get("comp"))),
                    format_metric(parse_float(nrgbd.get("acc"))),
                    format_metric(parse_float(nrgbd.get("comp"))),
                    format_metric(avg_fps, digits=2),
                ]
            )
            + " |"
        )

    lines.append("")
    return lines


def render_analysis_sections(experiments_root: Path) -> list[str]:
    lines: list[str] = []
    for section in (
        render_video_depth_ablation_section(experiments_root),
        render_mv_recon_ablation_section(experiments_root),
    ):
        if section:
            lines.extend(section)
    return lines


def load_existing_summary_body(experiments_root: Path) -> list[str]:
    summary_path = experiments_root / "analysis" / "SUMMARY.md"
    if not summary_path.exists():
        return []

    lines = summary_path.read_text(encoding="utf-8").splitlines()
    if lines[:1] == ["# 已完成实验报告汇总"]:
        lines = lines[1:]
        if lines[:1] == [""]:
            lines = lines[1:]
        if lines[:1] == ["> 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。"]:
            lines = lines[1:]
        if lines[:1] == [""]:
            lines = lines[1:]

    for idx, line in enumerate(lines):
        if line.startswith("## 附加汇总："):
            lines = lines[:idx]
            break

    while lines and lines[-1] == "":
        lines.pop()

    return lines


def load_existing_experiment_rows(experiments_root: Path) -> list[str]:
    experiments_md_path = experiments_root / "EXPERIMENTS.md"
    if not experiments_md_path.exists():
        return []

    lines = experiments_md_path.read_text(encoding="utf-8").splitlines()
    divider_index = next((idx for idx, line in enumerate(lines) if line.startswith("|--------|")), None)
    section_index = next((idx for idx, line in enumerate(lines) if line == "## 评测口径说明"), None)
    if divider_index is None or section_index is None or divider_index >= section_index:
        return []

    rows = [line for line in lines[divider_index + 1 : section_index] if line.startswith("| ")]
    if rows == ["| _(当前本地 experiments/runs 无记录；请通过跳板机人工核对远端文档，勿依赖自动 refresh 脚本)_ | | | | | | |"]:
        return []
    return rows


def run_id_from_experiment_row(row: str) -> str | None:
    match = re.match(r"\|\s+`([^`]+)`\s+\|", row)
    return match.group(1) if match else None


def strip_generated_doc_preamble(markdown: str, title: str) -> list[str]:
    lines = markdown.splitlines()
    if lines[:1] == [title]:
        lines = lines[1:]
    while lines and lines[0] == "":
        lines = lines[1:]
    while lines and lines[0].startswith("> "):
        lines = lines[1:]
    while lines and lines[0] == "":
        lines = lines[1:]
    return lines


def extract_section_body(lines: list[str], start_heading: str, end_heading: str | None = None) -> list[str]:
    start_idx = next((idx for idx, line in enumerate(lines) if line == start_heading), None)
    if start_idx is None:
        return []

    end_idx = len(lines)
    if end_heading is not None:
        found_end = next((idx for idx, line in enumerate(lines[start_idx + 1 :], start=start_idx + 1) if line == end_heading), None)
        if found_end is not None:
            end_idx = found_end

    section = lines[start_idx + 1 : end_idx]
    while section and section[0] == "":
        section = section[1:]
    while section and section[-1] == "":
        section = section[:-1]
    return section


def shift_heading_levels(lines: list[str], delta: int) -> list[str]:
    shifted: list[str] = []
    for line in lines:
        if not line.startswith("#"):
            shifted.append(line)
            continue
        hashes, sep, rest = line.partition(" ")
        if not sep:
            shifted.append(line)
            continue
        shifted.append("#" * (len(hashes) + delta) + " " + rest)
    return shifted


def load_existing_summary_sections(experiments_root: Path) -> list[list[str]]:
    body = load_existing_summary_body(experiments_root)
    sections: list[list[str]] = []
    current: list[str] = []
    for line in body:
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        sections.append(current)
    return sections


def run_id_from_summary_section(section: list[str]) -> str | None:
    for line in section:
        match = re.match(r"\*\*Run ID\*\*: `([^`]+)`", line)
        if match:
            return match.group(1)
    return None


def renumber_summary_sections(sections: list[list[str]]) -> list[str]:
    lines: list[str] = []
    for index, section in enumerate(sections, start=1):
        if not section:
            continue
        heading = re.sub(r"^##\s+(?:\d+\.\s+)*", f"## {index}. ", section[0])
        lines.append(heading)
        lines.extend(section[1:])
        if not lines or lines[-1] != "":
            lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def parse_markdown_cells(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")] if stripped else []


def normalize_dataset_key(task: str, dataset: str) -> str:
    if task in {"monodepth", "video_depth"}:
        return dataset.split("_")[0].lower()
    return dataset.lower()


def display_dataset_label(dataset: str) -> str:
    label_map = {
        "bonn": "Bonn",
        "kitti": "KITTI",
        "sintel": "Sintel",
        "nyu": "NYUv2",
        "scannet": "ScanNet",
        "7scenes": "7Scenes",
        "nrgbd": "NRGBD",
    }
    return label_map.get(dataset.lower(), dataset)


def display_variant_label(variant: str) -> str:
    if variant == "OBVGGT":
        return "OBVGGT (ours)"
    return variant


def parse_summary_sections_from_markdown(summary_md: str) -> list[dict]:
    lines = strip_generated_doc_preamble(summary_md, "# 已完成实验报告汇总")
    sections: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        sections.append(current)

    parsed_sections: list[dict] = []
    header_re = re.compile(r"^##\s+(?:\d+\.\s+)+([^(]+)\s+\(([^)]+)\)\s+-\s+(\d{4}-\d{2}-\d{2})$")
    status_re = re.compile(r"^\*\*状态\*\*: `([^`]+)`$")

    for section in sections:
        if not section:
            continue
        header_match = header_re.match(section[0])
        if not header_match:
            continue
        task = header_match.group(1).strip()
        variant = header_match.group(2).strip()
        date = header_match.group(3)
        status = ""
        metrics_rows: list[dict] = []

        for idx, line in enumerate(section):
            status_match = status_re.match(line)
            if status_match:
                status = status_match.group(1)

            if line.startswith("| 数据集 |") and idx + 2 < len(section):
                headers = parse_markdown_cells(line)
                row_idx = idx + 2
                while row_idx < len(section) and section[row_idx].startswith("| "):
                    values = parse_markdown_cells(section[row_idx])
                    if len(values) == len(headers):
                        row_payload = {headers[col]: values[col] for col in range(len(headers))}
                        metrics_rows.append(row_payload)
                    row_idx += 1

        parsed_sections.append(
            {
                "task": task,
                "variant": variant,
                "date": date,
                "status": status,
                "metrics_rows": metrics_rows,
            }
        )

    return parsed_sections


def latest_done_section(sections: list[dict], task: str, variant: str) -> dict | None:
    candidates = [section for section in sections if section["task"] == task and section["variant"] == variant and section["status"] == "DONE"]
    if not candidates:
        return None
    # Prefer the run with the most dataset coverage, then latest date as tiebreaker
    candidates.sort(key=lambda section: (len(section.get("metrics_rows", [])), section["date"]), reverse=True)
    return candidates[0]


def format_compound_metric(row: dict[str, str], columns: list[str]) -> str:
    values = [row.get(column, "") for column in columns]
    if any(value == "" for value in values):
        return ""
    return " / ".join(values)


def render_main_task_table(summary_sections: list[dict], task: str, dataset_order: list[str], metric_columns: list[str], metric_label: str) -> list[str]:
    core_variants = ["StreamVGGT", "OBVGGT", "XStreamVGGT", "InfiniteVGGT"]
    variant_sections = {variant: latest_done_section(summary_sections, task, variant) for variant in core_variants}
    if not any(variant_sections.values()):
        return []

    lines = [
        f"## 主结果：{task}",
        "",
        f"> 指标格式：`{metric_label}`",
        "",
        "| Variant | " + " | ".join(display_dataset_label(dataset) for dataset in dataset_order) + " |",
        "|--------|" + "|".join(["---"] * len(dataset_order)) + "|",
    ]

    for variant in core_variants:
        section = variant_sections[variant]
        dataset_map: dict[str, dict[str, str]] = {}
        if section is not None:
            for row in section["metrics_rows"]:
                dataset_map[normalize_dataset_key(task, row.get("数据集", ""))] = row
        rendered_cells = [format_compound_metric(dataset_map.get(dataset, {}), metric_columns) for dataset in dataset_order]
        lines.append("| " + " | ".join([display_variant_label(variant), *rendered_cells]) + " |")

    lines.append("")
    return lines


def render_peak_memory_tables(experiments_root: Path) -> list[str]:
    path = experiments_root / "analysis" / "tables" / "peak_memory_4variants.csv"
    if not path.exists():
        return []

    variant_display = {
        "baseline": "StreamVGGT",
        "obcache": "OBVGGT",
        "xstreamvggt": "XStreamVGGT",
        "infinitevggt": "InfiniteVGGT",
    }
    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for row in read_csv_rows(path):
        task = row.get("task", "")
        variant = variant_display.get(row.get("variant", ""), row.get("variant", ""))
        dataset = normalize_dataset_key(task, row.get("dataset", ""))
        grouped.setdefault(task, {}).setdefault(variant, {})[dataset] = row.get("max_peak_allocated_mb", "")

    sections: list[str] = []
    spec = [
        ("video_depth", ["sintel", "bonn", "kitti"]),
        ("mv_recon", ["7scenes", "nrgbd"]),
    ]
    for task, datasets in spec:
        if task not in grouped:
            continue
        sections.extend(
            [
                f"## 显存峰值：{task}",
                "",
                "| Variant | " + " | ".join(display_dataset_label(dataset) for dataset in datasets) + " |",
                "|--------|" + "|".join(["---"] * len(datasets)) + "|",
            ]
        )
        for variant in ["StreamVGGT", "OBVGGT", "XStreamVGGT", "InfiniteVGGT"]:
            dataset_map = grouped.get(task, {}).get(variant, {})
            values = [dataset_map.get(dataset, "") for dataset in datasets]
            sections.append("| " + " | ".join([display_variant_label(variant), *values]) + " |")
        sections.append("")

    return sections


def render_video_depth_ablation_paper_table(experiments_root: Path) -> list[str]:
    path = experiments_root / "analysis" / "tables" / "ablation_video_depth_20260324.csv"
    if not path.exists():
        return []

    rows = read_csv_rows(path)
    rows.sort(key=lambda row: (parse_float(row.get("kitti_absrel")) is None, parse_float(row.get("kitti_absrel")) or float("inf")))
    lines = [
        "## 消融：video_depth",
        "",
        "| Variant | Method | p | Sink | Recent | Heavy | Bonn AbsRel | Kitti AbsRel | Kitti δ<1.25 | Sintel AbsRel | Avg FPS |",
        "|--------|--------|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        fps_values = [parse_float(row.get("sintel_fps")), parse_float(row.get("bonn_fps")), parse_float(row.get("kitti_fps"))]
        fps_values = [value for value in fps_values if value is not None]
        avg_fps = sum(fps_values) / len(fps_values) if fps_values else None
        lines.append(
            "| "
            + " | ".join(
                [
                    row.get("variant", ""),
                    row.get("method", ""),
                    row.get("p", ""),
                    row.get("num_sink", ""),
                    row.get("num_recent", ""),
                    row.get("num_heavy", ""),
                    format_metric(parse_float(row.get("bonn_absrel"))),
                    format_metric(parse_float(row.get("kitti_absrel"))),
                    format_metric(parse_float(row.get("kitti_d125"))),
                    format_metric(parse_float(row.get("sintel_absrel"))),
                    format_metric(avg_fps, digits=2),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def render_mv_recon_ablation_paper_table(experiments_root: Path) -> list[str]:
    path = experiments_root / "analysis" / "tables" / "ablation_mv_recon_20260326.csv"
    if not path.exists():
        return []

    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for row in read_csv_rows(path):
        grouped.setdefault(row.get("variant", ""), {})[normalize_dataset_key("mv_recon", row.get("dataset", ""))] = row

    lines = [
        "## 消融：mv_recon",
        "",
        "| Variant | 7Scenes acc | 7Scenes comp | NRGBD acc | NRGBD comp | Avg FPS | Peak MB |",
        "|--------|---|---|---|---|---|---|",
    ]
    for variant in sorted(grouped):
        seven = grouped[variant].get("7scenes", {})
        nrgbd = grouped[variant].get("nrgbd", {})
        fps_values = [parse_float(seven.get("fps")), parse_float(nrgbd.get("fps"))]
        fps_values = [value for value in fps_values if value is not None]
        avg_fps = sum(fps_values) / len(fps_values) if fps_values else None
        peak_values = [parse_float(seven.get("peak_allocated_mb")), parse_float(nrgbd.get("peak_allocated_mb"))]
        peak_values = [value for value in peak_values if value is not None]
        peak_max = max(peak_values) if peak_values else None
        lines.append(
            "| "
            + " | ".join(
                [
                    variant,
                    format_metric(parse_float(seven.get("acc"))),
                    format_metric(parse_float(seven.get("comp"))),
                    format_metric(parse_float(nrgbd.get("acc"))),
                    format_metric(parse_float(nrgbd.get("comp"))),
                    format_metric(avg_fps, digits=2),
                    format_metric(peak_max, digits=2),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def render_experiments_md(experiments_root: Path, runs: list[dict]) -> str:
    existing_rows = load_existing_experiment_rows(experiments_root)
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
        if existing_rows:
            lines.extend(existing_rows)
        else:
            lines.append("| _(当前本地 experiments/runs 无记录；请通过跳板机人工核对远端文档，勿依赖自动 refresh 脚本)_ | | | | | | |")
    else:
        rendered_rows: list[str] = []
        for run in runs:
            manifest = run["manifest"]
            run_id = manifest.get("run_id", run["run_dir"].name)
            variant = VARIANT_DISPLAY.get(manifest.get("variant", ""), manifest.get("variant", "unknown"))
            task = manifest.get("task", "unknown")
            status = manifest.get("status", "UNKNOWN")
            end_ts = manifest.get("timestamps", {}).get("end") or manifest.get("timestamps", {}).get("start") or ""
            date_str = end_ts[:10] if end_ts else ""
            record_rel = f"experiments/runs/{run_id}/record.md"
            rendered_rows.append(
                f"| `{run_id}` | `{variant}` | `{task}` | `{date_str}` | `{status}` | `{record_rel}` | {summarize_run(run)} |"
            )
        seen_run_ids = {run_id_from_experiment_row(row) for row in rendered_rows}
        lines.extend(rendered_rows)
        lines.extend(row for row in existing_rows if run_id_from_experiment_row(row) not in seen_run_ids)

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
            "2. `EXPERIMENTS.md`、`analysis/SUMMARY.md` 与 `analysis/ALL_RESULTS.md` 一律由生成器重建，不手工编辑。",
            "3. 每次 run 结束后，应重新执行生成器；若在服务器上运行，优先更新服务器上的 docs。",
            "4. 本地 docs 如需对照服务器状态，请通过跳板机人工核对远端文档；不要依赖自动 refresh 脚本。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_summary_md(experiments_root: Path, runs: list[dict]) -> str:
    lines = [
        "# 已完成实验报告汇总",
        "",
        "> 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。",
        "",
    ]

    analysis_sections = render_analysis_sections(experiments_root)

    if not runs and not analysis_sections:
        lines.append("> 当前没有本地 run 记录可汇总。")
        return "\n".join(lines) + "\n"

    existing_summary_body = load_existing_summary_body(experiments_root) if not runs else []
    existing_summary_sections = load_existing_summary_sections(experiments_root) if runs else []

    if not runs:
        if existing_summary_body:
            lines.extend(existing_summary_body)
            lines.append("")
        elif analysis_sections:
            lines.extend(
                [
                    "> 当前本地 `experiments/runs/` 不完整，以下附加汇总来自 `analysis/tables/*.csv`。",
                    "",
                ]
            )

    rendered_sections: list[list[str]] = []
    for run in runs:
        manifest = run["manifest"]
        run_id = manifest.get("run_id", run["run_dir"].name)
        variant = VARIANT_DISPLAY.get(manifest.get("variant", ""), manifest.get("variant", "unknown"))
        task = manifest.get("task", "unknown")
        status = manifest.get("status", "UNKNOWN")
        date_str = (manifest.get("timestamps", {}).get("end") or manifest.get("timestamps", {}).get("start") or "")[:10]

        section_lines = [
            f"## 0. {task} ({variant}) - {date_str}",
            "",
            f"**Run ID**: `{run_id}`",
            f"**状态**: `{status}`",
            f"**结果摘要**: {summarize_run(run)}",
            "",
        ]

        rows = metric_rows_for_run(run)
        if rows:
            headers = sorted({key for row in rows for key in row["metrics"].keys() if row["metrics"].get(key) is not None})
            section_lines.append("| 数据集 | " + " | ".join(headers) + " |")
            section_lines.append("|--------|" + "|".join(["---"] * len(headers)) + "|")
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
                section_lines.append("| " + row["dataset"] + " | " + " | ".join(values) + " |")
            section_lines.append("")

        section_lines.append(f"**Run record**: `experiments/runs/{run_id}/record.md`")
        section_lines.append("")
        rendered_sections.append(section_lines)

    if rendered_sections:
        seen_run_ids = {run_id_from_summary_section(section) for section in rendered_sections}
        merged_sections = list(rendered_sections)
        merged_sections.extend(
            section
            for section in existing_summary_sections
            if run_id_from_summary_section(section) not in seen_run_ids
        )
        lines.extend(renumber_summary_sections(merged_sections))
        lines.append("")

    if analysis_sections:
        lines.extend(analysis_sections)

    return "\n".join(lines) + "\n"


def render_all_results_md(experiments_root: Path, experiments_md: str, summary_md: str) -> str:
    summary_sections = parse_summary_sections_from_markdown(summary_md)

    lines = [
        "# 论文式结果总表",
        "",
        "> 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。",
        "> 只保留论文/组会风格的结果表，不包含 run ledger、record 路径或过程性说明。",
        "",
    ]

    for section in (
        render_main_task_table(summary_sections, "video_depth", ["bonn", "kitti", "sintel"], ["Abs Rel", "RMSE", "δ<1.25"], "Abs Rel / RMSE / δ<1.25"),
        render_main_task_table(summary_sections, "mv_recon", ["7scenes", "nrgbd"], ["acc", "comp", "nc"], "acc / comp / nc"),
        render_main_task_table(summary_sections, "monodepth", ["bonn", "kitti", "nyu", "scannet", "sintel"], ["Abs Rel", "RMSE", "δ<1.25"], "Abs Rel / RMSE / δ<1.25"),
        render_peak_memory_tables(experiments_root),
        render_video_depth_ablation_paper_table(experiments_root),
        render_mv_recon_ablation_paper_table(experiments_root),
    ):
        if section:
            lines.extend(section)

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiments-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    experiments_root = Path(args.experiments_root).resolve()
    runs = discover_runs(experiments_root)

    experiments_md = render_experiments_md(experiments_root, runs)
    summary_md = render_summary_md(experiments_root, runs)
    all_results_md = render_all_results_md(experiments_root, experiments_md, summary_md)

    (experiments_root / "EXPERIMENTS.md").write_text(experiments_md, encoding="utf-8")
    analysis_dir = experiments_root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "SUMMARY.md").write_text(summary_md, encoding="utf-8")
    (analysis_dir / "ALL_RESULTS.md").write_text(all_results_md, encoding="utf-8")

    print(f"[render-experiment-docs] wrote {experiments_root / 'EXPERIMENTS.md'}")
    print(f"[render-experiment-docs] wrote {analysis_dir / 'SUMMARY.md'}")
    print(f"[render-experiment-docs] wrote {analysis_dir / 'ALL_RESULTS.md'}")


if __name__ == "__main__":
    main()
