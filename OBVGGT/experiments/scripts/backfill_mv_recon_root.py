import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


PATTERN = re.compile(
    r"""
    Idx:\s*(?P<scene_id>[^,]+),\s*
    Acc:\s*(?P<acc>[^,]+),\s*
    Comp:\s*(?P<comp>[^,]+),\s*
    NC1:\s*(?P<nc1>[^,]+),\s*
    NC2:\s*(?P<nc2>[^,]+)\s*-\s*
    Acc_med:\s*(?P<acc_med>[^,]+),\s*
    Compc_med:\s*(?P<comp_med>[^,]+),\s*
    NC1c_med:\s*(?P<nc1_med>[^,]+),\s*
    NC2c_med:\s*(?P<nc2_med>[^,]+)
    """,
    re.VERBOSE,
)


def parse_logs_all(log_path: Path, dataset: str) -> list[dict]:
    records = []
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        match = PATTERN.match(line.strip())
        if not match:
            continue
        data = match.groupdict()
        record = {"dataset": dataset, "scene_id": data["scene_id"]}
        for key, value in data.items():
            if key == "scene_id":
                continue
            record[key] = float(value)
        record["nc"] = (record["nc1"] + record["nc2"]) / 2.0
        record["nc_med"] = (record["nc1_med"] + record["nc2_med"]) / 2.0
        records.append(record)
    return records


def load_dataset_summaries(root: Path) -> list[dict]:
    rows = []
    for summary_path in sorted(root.glob("*/summary_metrics.json")):
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        rows.append({"dataset": summary_path.parent.name, **payload})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="mv_recon result root (the directory containing dataset subdirectories)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"missing root: {root}")

    all_scene_records = []
    for log_path in sorted(root.glob("*/logs_all.txt")):
        all_scene_records.extend(parse_logs_all(log_path, dataset=log_path.parent.name))

    if not all_scene_records:
        raise SystemExit(f"no scene records found under {root}")

    aggregate_metrics = defaultdict(list)
    for scene_record in all_scene_records:
        for key, value in scene_record.items():
            if key in {"dataset", "scene_id"}:
                continue
            aggregate_metrics[key].append(float(value))

    root_summary = {
        key: sum(values) / len(values)
        for key, values in aggregate_metrics.items()
        if values
    }
    dataset_summaries = load_dataset_summaries(root)

    (root / "summary_metrics.json").write_text(
        json.dumps(root_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "system_metrics.json").write_text(
        json.dumps(
            {
                "summary": {
                    "num_datasets_total": int(len(dataset_summaries)),
                    "num_datasets_ok": int(len(dataset_summaries)),
                    "num_scenes_total": int(len(all_scene_records)),
                    "num_scenes_ok": int(len(all_scene_records)),
                },
                "per_dataset": dataset_summaries,
                "per_scene": all_scene_records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[backfill-root] wrote {root / 'summary_metrics.json'}")
    print(f"[backfill-root] wrote {root / 'system_metrics.json'}")


if __name__ == "__main__":
    main()
