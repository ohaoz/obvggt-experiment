import argparse
import json
import re
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


def mean_metrics_from_log(log_path: Path) -> dict[str, float]:
    metrics: dict[str, list[float]] = {}
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        match = PATTERN.match(line.strip())
        if not match:
            continue
        data = match.groupdict()
        for key, value in data.items():
            if key == "scene_id":
                continue
            metrics.setdefault(key, []).append(float(value))
        metrics.setdefault("nc", []).append((float(data["nc1"]) + float(data["nc2"])) / 2.0)
        metrics.setdefault("nc_med", []).append((float(data["nc1_med"]) + float(data["nc2_med"])) / 2.0)

    if not metrics:
        raise ValueError(f"no mv_recon metrics found in {log_path}")

    return {key: sum(values) / len(values) for key, values in metrics.items()}


def backfill(root: Path) -> int:
    count = 0
    for log_path in sorted(root.rglob("logs_all.txt")):
        summary_path = log_path.with_name("summary_metrics.json")
        metrics = mean_metrics_from_log(log_path)
        summary_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[backfill] wrote {summary_path}")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="Run output root or any parent directory containing mv_recon logs_all.txt files.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"missing path: {root}")
    written = backfill(root)
    print(f"[backfill] total summaries written: {written}")


if __name__ == "__main__":
    main()
