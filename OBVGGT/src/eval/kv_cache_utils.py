import argparse
import json
import os
from typing import Any, Dict, Optional


KV_METADATA_FILENAME = "kv_eval_config.json"


def str2bool(value):
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    if value in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def env_bool(name: str, default=None):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return str2bool(raw)


def env_int(name: str, default=None):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def add_kv_cache_args(parser: argparse.ArgumentParser, use_env_defaults: bool = True) -> argparse.ArgumentParser:
    getenv = os.getenv if use_env_defaults else (lambda _name, default=None: default)
    parser.add_argument(
        "--kv_cache_enable",
        type=str2bool,
        nargs="?",
        const=True,
        default=env_bool("OBVGGT_KV_CACHE_ENABLE", False) if use_env_defaults else False,
        help="Enable custom KV cache strategy during inference.",
    )
    parser.add_argument(
        "--kv_cache_cfg_json",
        type=str,
        default=getenv("OBVGGT_KV_CACHE_CFG", ""),
        help="KV cache config JSON string.",
    )
    parser.add_argument("--kv_cache_method", type=str, default=getenv("OBVGGT_KV_METHOD"))
    parser.add_argument("--kv_cache_p", type=int, default=env_int("OBVGGT_KV_P") if use_env_defaults else None)
    parser.add_argument(
        "--kv_cache_use_vnorm",
        type=str2bool,
        default=env_bool("OBVGGT_KV_USE_VNORM") if use_env_defaults else None,
    )
    parser.add_argument("--kv_cache_pool_fn", type=str, default=getenv("OBVGGT_KV_POOL_FN"))
    parser.add_argument(
        "--kv_cache_ptb_window",
        type=int,
        default=env_int("OBVGGT_KV_PTB_WINDOW") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_ptb_is_recent",
        type=str2bool,
        default=env_bool("OBVGGT_KV_PTB_IS_RECENT") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_probe_mode",
        type=str2bool,
        default=env_bool("OBVGGT_KV_PROBE_MODE") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_num_patch_probes",
        type=int,
        default=env_int("OBVGGT_KV_NUM_PATCH_PROBES") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_num_sink_frames",
        type=int,
        default=env_int("OBVGGT_KV_NUM_SINK_FRAMES") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_num_recent_frames",
        type=int,
        default=env_int("OBVGGT_KV_NUM_RECENT_FRAMES") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_num_heavy_frames",
        type=int,
        default=env_int("OBVGGT_KV_NUM_HEAVY_FRAMES") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_num_sink_tokens",
        type=int,
        default=env_int("OBVGGT_KV_NUM_SINK_TOKENS") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_num_recent_tokens",
        type=int,
        default=env_int("OBVGGT_KV_NUM_RECENT_TOKENS") if use_env_defaults else None,
    )
    parser.add_argument(
        "--kv_cache_num_heavy_tokens",
        type=int,
        default=env_int("OBVGGT_KV_NUM_HEAVY_TOKENS") if use_env_defaults else None,
    )
    return parser


def build_kv_cache_cfg(args) -> Optional[Dict[str, Any]]:
    cfg: Dict[str, Any] = {}
    if getattr(args, "kv_cache_cfg_json", ""):
        try:
            parsed = json.loads(args.kv_cache_cfg_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid --kv_cache_cfg_json: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("--kv_cache_cfg_json must be a JSON object")
        cfg.update(parsed)

    overrides = {
        "method": getattr(args, "kv_cache_method", None),
        "p": getattr(args, "kv_cache_p", None),
        "use_vnorm": getattr(args, "kv_cache_use_vnorm", None),
        "pool_fn": getattr(args, "kv_cache_pool_fn", None),
        "ptb_window": getattr(args, "kv_cache_ptb_window", None),
        "ptb_is_recent": getattr(args, "kv_cache_ptb_is_recent", None),
        "probe_mode": getattr(args, "kv_cache_probe_mode", None),
        "num_patch_probes": getattr(args, "kv_cache_num_patch_probes", None),
        "num_sink_frames": getattr(args, "kv_cache_num_sink_frames", None),
        "num_recent_frames": getattr(args, "kv_cache_num_recent_frames", None),
        "num_heavy_frames": getattr(args, "kv_cache_num_heavy_frames", None),
        "num_sink_tokens": getattr(args, "kv_cache_num_sink_tokens", None),
        "num_recent_tokens": getattr(args, "kv_cache_num_recent_tokens", None),
        "num_heavy_tokens": getattr(args, "kv_cache_num_heavy_tokens", None),
    }
    for key, value in overrides.items():
        if value is not None:
            cfg[key] = value

    enabled = bool(getattr(args, "kv_cache_enable", False)) or bool(cfg.get("enable", False))
    if not enabled:
        return None

    cfg["enable"] = True
    return cfg


def canonicalize_kv_method(method: Optional[str]) -> str:
    if not method:
        return "disabled"

    method_lower = str(method).strip().lower()
    alias_map = {
        "obcv": "v",
        "v": "v",
        "obck": "key",
        "k": "key",
        "key": "key",
        "obcvk": "joint",
        "vk": "joint",
        "joint": "joint",
    }
    return alias_map.get(method_lower, method_lower)


def kv_cache_metadata(kv_cache_cfg: Optional[Dict[str, Any]], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    enabled = bool(kv_cache_cfg and kv_cache_cfg.get("enable", False))
    cfg = dict(kv_cache_cfg or {})
    method = cfg.get("method")
    metadata: Dict[str, Any] = {
        "kv_enable": enabled,
        "kv_method": method if enabled and method is not None else ("disabled" if not enabled else "joint"),
        "kv_method_canonical": canonicalize_kv_method(method if enabled else None),
    }

    for key in (
        "p",
        "use_vnorm",
        "pool_fn",
        "ptb_window",
        "ptb_is_recent",
        "probe_mode",
        "num_patch_probes",
        "num_sink_frames",
        "num_recent_frames",
        "num_heavy_frames",
        "num_sink_tokens",
        "num_recent_tokens",
        "num_heavy_tokens",
    ):
        if key in cfg:
            metadata[f"kv_{key}"] = cfg[key]

    if enabled:
        metadata["kv_cfg"] = cfg

    if extra:
        metadata.update(extra)
    return metadata


def write_kv_metadata(
    output_dir: str,
    kv_cache_cfg: Optional[Dict[str, Any]],
    *,
    task: str,
    benchmark_role: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    payload = kv_cache_metadata(
        kv_cache_cfg,
        extra={
            "task": task,
            "benchmark_role": benchmark_role,
            **(extra or {}),
        },
    )
    path = os.path.join(output_dir, KV_METADATA_FILENAME)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def load_kv_metadata(output_dir: str) -> Dict[str, Any]:
    path = os.path.join(output_dir, KV_METADATA_FILENAME)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, dict) else {}


def with_meta(payload: Dict[str, Any], output_dir: str, extra_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    enriched = dict(payload)
    meta = load_kv_metadata(output_dir)
    if extra_meta:
        meta = {**meta, **extra_meta}
    if meta:
        enriched["_meta"] = meta
    return enriched


def format_kv_status(kv_cache_cfg: Optional[Dict[str, Any]]) -> str:
    return f"[kv_cache] {'enabled' if kv_cache_cfg is not None else 'disabled'}; cfg={kv_cache_cfg if kv_cache_cfg is not None else '{}'}"
