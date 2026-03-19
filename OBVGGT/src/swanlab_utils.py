import datetime
import os
import socket
import subprocess
from typing import Any, Dict, Iterable, List, Optional


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_config_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    try:
        from omegaconf import OmegaConf

        if OmegaConf.is_config(obj):
            return OmegaConf.to_container(obj, resolve=True) or {}
    except Exception:
        pass
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return {}


def _parse_tags(raw_tags: Any) -> List[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        tags = [t.strip() for t in raw_tags.split(",")]
        return [t for t in tags if t]
    if isinstance(raw_tags, Iterable):
        tags = [str(t).strip() for t in raw_tags]
        return [t for t in tags if t]
    return []


def _safe_git_commit() -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return commit or "unknown"
    except Exception:
        return "unknown"


def _safe_hostname() -> str:
    return (
        os.environ.get("HOSTNAME")
        or os.environ.get("COMPUTERNAME")
        or socket.gethostname()
        or "unknown"
    )


def resolve_mode(mode: str, api_key_env: str) -> str:
    normalized = str(mode or "auto").strip().lower()
    if normalized in {"cloud", "local", "offline", "disabled"}:
        return normalized
    if normalized != "auto":
        return "offline"
    return "cloud" if os.environ.get(api_key_env, "").strip() else "offline"


def init_swanlab_run(
    config: Any,
    job_type: str,
    default_dataset: str,
    output_dir: str,
    config_for_log: Optional[Dict[str, Any]] = None,
):
    if not _to_bool(_safe_get(config, "swanlab_enable", True), default=True):
        return None

    try:
        import swanlab
    except Exception as exc:
        print(f"[swanlab] import failed, disable logging: {exc}")
        return None

    api_key_env = str(_safe_get(config, "swanlab_api_key_env", "SWANLAB_API_KEY"))
    mode = resolve_mode(_safe_get(config, "swanlab_mode", "auto"), api_key_env)
    if mode == "disabled":
        return None

    logdir = str(_safe_get(config, "swanlab_logdir", "") or "").strip()
    if not logdir:
        logdir = os.environ.get("SWANLAB_LOG_DIR", "").strip()
    if not logdir:
        logdir = os.path.join(output_dir or ".", "swanlab")
    os.makedirs(logdir, exist_ok=True)

    project = str(_safe_get(config, "swanlab_project", "StreamVGGT"))
    workspace = str(_safe_get(config, "swanlab_workspace", "") or "").strip()
    description = str(_safe_get(config, "swanlab_description", "") or "").strip()

    experiment_name = str(_safe_get(config, "swanlab_experiment_name", "") or "").strip()
    if not experiment_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"{job_type}_{default_dataset}_{timestamp}"

    tags = _parse_tags(_safe_get(config, "swanlab_tags", ""))
    commit = _safe_git_commit()
    host = _safe_hostname()
    auto_tags = [
        f"job:{job_type}",
        f"dataset:{default_dataset}",
        f"server:{host}",
        f"commit:{commit}",
    ]
    seen = set()
    merged_tags = []
    for tag in tags + auto_tags:
        if tag in seen:
            continue
        merged_tags.append(tag)
        seen.add(tag)

    payload = config_for_log if config_for_log is not None else _to_config_dict(config)

    try:
        init_kwargs = {
            "project": project,
            "workspace": workspace or None,
            "experiment_name": experiment_name,
            "description": description or None,
            "config": payload,
            "mode": mode,
            "logdir": logdir,
            "tags": merged_tags,
            "sync_tensorboard": True,
        }
        run = swanlab.init(**init_kwargs)
        print(
            f"[swanlab] initialized: project={project}, mode={mode}, "
            f"experiment={experiment_name}"
        )
        return {"module": swanlab, "run": run}
    except Exception as exc:
        print(f"[swanlab] init failed, disable logging: {exc}")
        return None


def log_swanlab(state: Any, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
    if not state or not metrics:
        return
    safe_metrics: Dict[str, Any] = {}
    for key, value in metrics.items():
        if value is None:
            continue
        if isinstance(value, (int, float, bool, str)):
            safe_metrics[key] = value
            continue
        try:
            safe_metrics[key] = float(value)
        except Exception:
            continue
    if not safe_metrics:
        return
    try:
        if step is None:
            state["module"].log(safe_metrics)
        else:
            state["module"].log(safe_metrics, step=step)
    except Exception as exc:
        print(f"[swanlab] log failed: {exc}")


def finish_swanlab(state: Any) -> None:
    if not state:
        return
    try:
        if state.get("run") is not None and hasattr(state["run"], "finish"):
            state["run"].finish()
        else:
            state["module"].finish()
    except Exception as exc:
        print(f"[swanlab] finish failed: {exc}")
