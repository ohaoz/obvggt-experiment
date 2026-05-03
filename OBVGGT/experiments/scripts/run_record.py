import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ARTIFACT_FILENAMES = {
    "metric.json",
    "result_scale.json",
    "result_scale&shift.json",
    "result_metric.json",
    "summary_metrics.json",
    "system_metrics.json",
    "profile_summary.json",
    "pose_summary.json",
    "kv_eval_config.json",
}


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def normalize_expected_artifacts(raw: Any) -> List[str]:
    if not raw:
        return []
    return [str(Path(item)) for item in raw if item]


def discover_artifacts(output_root: Path) -> List[Dict[str, Any]]:
    artifacts: List[Dict[str, Any]] = []
    if not output_root.exists():
        return artifacts

    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name not in ARTIFACT_FILENAMES:
            continue
        artifacts.append(
            {
                "path": str(path),
                "name": path.name,
                "size_bytes": path.stat().st_size,
            }
        )
    return artifacts


def summarize_contract(
    *,
    exit_code: int | None,
    requested_status: str,
    expected_artifacts: List[str],
    artifact_items: List[Dict[str, Any]],
) -> tuple[str, List[str]]:
    expected = normalize_expected_artifacts(expected_artifacts)
    if not expected:
        return requested_status, []

    discovered = {str(Path(item["path"])) for item in artifact_items}
    matched = [path for path in expected if path in discovered]
    missing = [path for path in expected if path not in discovered]

    if not missing:
        return ("DONE" if exit_code == 0 else "FAILED"), []

    if matched or exit_code == 0:
        return "PARTIAL_DONE", missing
    return "FAILED", missing


def render_record(manifest: Dict[str, Any], artifacts: Dict[str, Any]) -> str:
    kv_cfg = manifest.get("kv_cache", {}).get("config")
    kv_cfg_pretty = json.dumps(kv_cfg, ensure_ascii=False, indent=2) if kv_cfg else "{}"
    artifact_lines = artifacts.get("artifacts", [])
    missing_lines = artifacts.get("missing_artifacts", [])
    if artifact_lines:
        artifacts_md = "\n".join(f"- `{item['name']}`: `{item['path']}`" for item in artifact_lines)
    else:
        artifacts_md = "- 暂无已发现产物"
    if missing_lines:
        missing_md = "\n".join(f"  - `{path}`" for path in missing_lines)
        artifacts_md += f"\n- 缺失必需产物:\n{missing_md}"

    notes = [
        "- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。",
    ]
    if manifest.get("task") == "monodepth":
        notes.append("- `monodepth` 仅作为 depth regression check，不作为主 KV benchmark。")
    if missing_lines:
        notes.append("- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。")

    notes_md = "\n".join(notes)
    status = manifest.get("status", "RUNNING")
    timestamps = manifest.get("timestamps", {})
    git_info = manifest.get("git", {})

    return f"""# Run Record: {manifest.get('run_id', 'unknown')}

## 0. Status
- Status: {status}
- Start: {timestamps.get('start', 'unknown')}
- End: {timestamps.get('end', 'N/A')}
- Exit code: {manifest.get('exit_code', 'N/A')}

## 1. Experiment
- Variant: {manifest.get('variant', 'unknown')}
- Task: {manifest.get('task', 'unknown')}
- Benchmark role: {manifest.get('benchmark_role', 'unknown')}
- Model: {manifest.get('model_name', 'unknown')}
- Result tag: {manifest.get('result_tag', 'unknown')}

## 2. Paths
- Run dir: `{manifest.get('run_dir', '')}`
- Output root: `{manifest.get('output_root', '')}`
- Repo path: `{manifest.get('repo_path', '')}`
- Log file: `{manifest.get('log_file', '')}`
- Command file: `{manifest.get('command_file', '')}`
- Config snapshot: `{manifest.get('config_snapshot_file', '')}`

## 3. Code Version
- Git branch: {git_info.get('branch', 'unknown')}
- Git commit: {git_info.get('commit', 'unknown')}
- Adapter: {manifest.get('adapter', 'unknown')}
- Expected env: {manifest.get('env_name', '') or 'unspecified'}

## 4. KV Cache
- Enabled: {manifest.get('kv_cache', {}).get('enabled', False)}
- Config:
```json
{kv_cfg_pretty}
```

## 5. Artifacts
{artifacts_md}

## 6. Notes
{notes_md}
"""


def init_run(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    config_snapshot_path = run_dir / "config_snapshot.json"
    if args.config_file:
        shutil.copyfile(args.config_file, config_snapshot_path)
    else:
        config_snapshot_path.write_text("{}", encoding="utf-8")

    kv_cfg = json.loads(args.kv_cache_cfg_json) if args.kv_cache_cfg_json else {}
    manifest = {
        "run_id": args.run_id,
        "status": "RUNNING",
        "variant": args.variant,
        "task": args.task,
        "benchmark_role": args.benchmark_role,
        "model_name": args.model_name,
        "checkpoint": args.checkpoint,
  "result_tag": args.result_tag,
        "repo_path": args.repo_path,
        "env_name": args.env_name,
        "adapter": args.adapter,
        "run_dir": str(run_dir),
        "output_root": args.output_root,
        "log_file": str(run_dir / "stdout.log"),
        "command_file": str(run_dir / "command.sh"),
        "config_snapshot_file": str(config_snapshot_path),
        "git": {"branch": args.git_branch, "commit": args.git_commit},
        "kv_cache": {"enabled": args.kv_cache_enabled, "config": kv_cfg},
        "expected_artifacts": normalize_expected_artifacts(
            json.loads(args.expected_artifacts_json) if args.expected_artifacts_json else []
        ),
        "timestamps": {"start": iso_now(), "end": None},
        "exit_code": None,
    }
    artifacts = {
        "status": "RUNNING",
        "output_root": args.output_root,
        "expected_artifacts": manifest["expected_artifacts"],
        "missing_artifacts": [],
        "artifacts": [],
    }
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "artifacts.json", artifacts)
    (run_dir / "record.md").write_text(render_record(manifest, artifacts), encoding="utf-8")


def finalize_run(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    manifest_path = run_dir / "manifest.json"
    artifacts_path = run_dir / "artifacts.json"
    manifest = read_json(manifest_path)
    if not manifest:
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")

    output_root = Path(manifest.get("output_root", args.output_root or ""))
    artifact_items = discover_artifacts(output_root)
    expected_artifacts = normalize_expected_artifacts(manifest.get("expected_artifacts", []))
    final_status, missing_artifacts = summarize_contract(
        exit_code=args.exit_code,
        requested_status=args.status,
        expected_artifacts=expected_artifacts,
        artifact_items=artifact_items,
    )
    artifacts = {
        "status": final_status,
        "output_root": str(output_root),
        "expected_artifacts": expected_artifacts,
        "missing_artifacts": missing_artifacts,
        "artifacts": artifact_items,
        "updated_at": iso_now(),
    }

    manifest["status"] = final_status
    manifest["exit_code"] = args.exit_code
    manifest["timestamps"]["end"] = iso_now()

    write_json(manifest_path, manifest)
    write_json(artifacts_path, artifacts)
    (run_dir / "record.md").write_text(render_record(manifest, artifacts), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--run-dir", required=True)
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--variant", required=True)
    init_parser.add_argument("--task", required=True)
    init_parser.add_argument("--benchmark-role", required=True)
    init_parser.add_argument("--model-name", required=True)
    init_parser.add_argument("--checkpoint", required=True)
    init_parser.add_argument("--result-tag", required=True)
    init_parser.add_argument("--repo-path", required=True)
    init_parser.add_argument("--env-name", default="")
    init_parser.add_argument("--adapter", required=True)
    init_parser.add_argument("--output-root", required=True)
    init_parser.add_argument("--config-file", required=True)
    init_parser.add_argument("--git-branch", required=True)
    init_parser.add_argument("--git-commit", required=True)
    init_parser.add_argument("--kv-cache-enabled", action="store_true")
    init_parser.add_argument("--kv-cache-cfg-json", default="")
    init_parser.add_argument("--expected-artifacts-json", default="")

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--run-dir", required=True)
    finalize_parser.add_argument("--status", required=True)
    finalize_parser.add_argument("--exit-code", type=int, required=True)
    finalize_parser.add_argument("--output-root", default="")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        init_run(args)
    elif args.command == "finalize":
        finalize_run(args)
    else:
        raise ValueError(args.command)


if __name__ == "__main__":
    main()
