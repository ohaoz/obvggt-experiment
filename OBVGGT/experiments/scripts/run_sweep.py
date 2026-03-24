import argparse
import json
import subprocess
from pathlib import Path
from typing import List


DEFAULT_VARIANTS = ["baseline", "obcache", "xstreamvggt", "infinitevggt"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["short_sequence", "memory_fixed", "quality_fixed", "long_stream"], default="short_sequence")
    parser.add_argument("--variants", nargs="+", default=DEFAULT_VARIANTS)
    parser.add_argument("--tasks", nargs="+", default=None)
    parser.add_argument("--sequence-lengths", nargs="+", type=int, default=[])
    parser.add_argument("--budget-json", default="")
    parser.add_argument("--quality-target", default="")
    parser.add_argument("--pose-co3d-dir", default="")
    parser.add_argument("--pose-co3d-anno-dir", default="")
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--frame-cache-dir", default="")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def default_tasks_for_mode(mode: str) -> List[str]:
    if mode == "short_sequence":
        return ["video_depth", "mv_recon", "monodepth"]
    if mode == "memory_fixed":
        return ["video_depth", "mv_recon"]
    if mode == "quality_fixed":
        return ["video_depth", "mv_recon"]
    if mode == "long_stream":
        return ["long_stream"]
    raise ValueError(mode)


def build_commands(args: argparse.Namespace, quick_run: Path) -> List[List[str]]:
    tasks = args.tasks or default_tasks_for_mode(args.mode)
    commands: List[List[str]] = []
    configs_dir = quick_run.parent / "configs"
    for variant in args.variants:
        config_path = configs_dir / f"{variant}.json"
        if not config_path.exists():
            continue
        with config_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg.get("runnable", False):
            continue
        supported = set(cfg.get("supported_tasks", []))
        for task in tasks:
            if task not in supported:
                continue
            base_cmd = ["bash", str(quick_run), variant, task]
            if args.budget_json:
                base_cmd.extend(["--budget-json", args.budget_json])
            if args.quality_target:
                base_cmd.extend(["--quality-target", args.quality_target])
            if args.pose_co3d_dir:
                base_cmd.extend(["--pose-co3d-dir", args.pose_co3d_dir])
            if args.pose_co3d_anno_dir:
                base_cmd.extend(["--pose-co3d-anno-dir", args.pose_co3d_anno_dir])
            if args.input_dir:
                base_cmd.extend(["--input-dir", args.input_dir])
            if args.frame_cache_dir:
                base_cmd.extend(["--frame-cache-dir", args.frame_cache_dir])
            if args.sequence_lengths:
                for seq_len in args.sequence_lengths:
                    commands.append(base_cmd + ["--sequence-length", str(seq_len)])
            else:
                commands.append(base_cmd)
    return commands


def main() -> None:
    args = parse_args()
    experiments_root = Path(__file__).resolve().parents[1]
    quick_run = experiments_root / "quick_run.sh"
    commands = build_commands(args, quick_run)

    for command in commands:
        print("COMMAND:", " ".join(command))
        if args.execute:
            completed = subprocess.run(command, cwd=str(experiments_root))
            if completed.returncode != 0:
                raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
