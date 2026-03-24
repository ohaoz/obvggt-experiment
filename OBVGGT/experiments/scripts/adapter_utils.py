import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


MONODEPTH_DATASETS = ["sintel", "bonn", "kitti", "nyu", "scannet"]
VIDEO_DEPTH_DATASETS = ["sintel", "bonn", "kitti"]


def repo_root_from(path_str: str) -> Path:
    obvggt_root = Path(__file__).resolve().parents[2]
    repo_path = Path(path_str)
    if repo_path.is_absolute():
        return repo_path
    return (obvggt_root / repo_path).resolve()


def checkpoint_path(repo_root: Path, checkpoint: str) -> Path:
    ckpt = Path(checkpoint)
    if ckpt.is_absolute():
        return ckpt
    return (repo_root / ckpt).resolve()


def parse_json_arg(raw: str) -> Dict:
    if not raw:
        return {}
    return json.loads(raw)


def shell_join(parts: List[str]) -> str:
    if hasattr(shlex, "join"):
        return shlex.join(parts)
    return " ".join(shlex.quote(str(part)) for part in parts)


def accelerate_launch_parts(*args: str) -> List[str]:
    """Build an accelerate launch command via the current Python interpreter."""
    return ["python", "-m", "accelerate.commands.launch", *args]


def run_shell_commands(commands: List[str], cwd: Path, env: Optional[Dict[str, str]] = None) -> int:
    merged_env = os.environ.copy()
    if env:
        merged_env.update({k: str(v) for k, v in env.items() if v is not None})
    for command in commands:
        completed = subprocess.run(command, cwd=str(cwd), env=merged_env, shell=True)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def print_dry_run(payload: Dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def common_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--result-tag", required=True)
    parser.add_argument("--env-name", default="")
    parser.add_argument("--kv-cache-enable", default="false")
    parser.add_argument("--kv-cache-cfg-json", default="")
    parser.add_argument("--budget-json", default="")
    parser.add_argument("--quality-target", default="")
    parser.add_argument("--sequence-length", type=int, default=0)
    parser.add_argument("--pose-co3d-dir", default="")
    parser.add_argument("--pose-co3d-anno-dir", default="")
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--frame-cache-dir", default="")
    parser.add_argument("--extra-arg", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    return parser


def build_payload(
    *,
    adapter: str,
    repo_root: Path,
    env_name: str,
    supported_tasks: List[str],
    commands: List[str],
    env_overrides: Optional[Dict[str, str]] = None,
) -> Dict:
    return {
        "adapter": adapter,
        "repo_root": str(repo_root),
        "env_name": env_name,
        "supported_tasks": supported_tasks,
        "commands": commands,
        "env_overrides": env_overrides or {},
    }


def metric_path_for_task(task: str, output_root: Path, result_tag: str) -> List[Path]:
    if task == "monodepth":
        return [output_root / f"{dataset}_{result_tag}" / "metric.json" for dataset in MONODEPTH_DATASETS]
    if task == "video_depth":
        return [output_root / f"{dataset}_{result_tag}" / "result_scale.json" for dataset in VIDEO_DEPTH_DATASETS]
    if task == "mv_recon":
        return [output_root / result_tag / "summary_metrics.json", output_root / result_tag / "system_metrics.json"]
    if task == "pose_co3d":
        return [output_root / result_tag / "pose_summary.json", output_root / result_tag / "system_metrics.json"]
    if task == "long_stream":
        return [output_root / result_tag / "system_metrics.json"]
    return []


def ensure_task_supported(task: str, supported_tasks: List[str]) -> None:
    if task not in supported_tasks:
        raise ValueError(f"Task `{task}` is not supported by this adapter. Supported: {supported_tasks}")


def normalize_bool(raw: str) -> bool:
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}
