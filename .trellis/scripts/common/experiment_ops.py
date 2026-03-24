#!/usr/bin/env python3
"""
Experiment operations context helpers for Trellis.
"""

from __future__ import annotations

from pathlib import Path

from .config import get_experiment_ops_config


def _boolish(value: object, default: bool = False) -> bool:
    """Interpret config values that may arrive as strings."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _as_string_list(value: object) -> list[str]:
    """Normalize config values to a flat string list."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_server(slot: str, value: object) -> dict | None:
    """Normalize a server config block."""
    if not isinstance(value, dict):
        return None
    server = {
        "slot": slot,
        "name": str(value.get("name", slot)).strip(),
        "host": str(value.get("host", "")).strip(),
        "port": str(value.get("port", "")).strip(),
        "purpose": str(value.get("purpose", "")).strip(),
        "remoteRoot": str(value.get("remote_root", "")).strip(),
        "codeRoot": str(value.get("code_root", "")).strip(),
        "dataRoot": str(value.get("data_root", "")).strip(),
        "runsRoot": str(value.get("runs_root", "")).strip(),
    }
    return server


def get_experiment_preflight(repo_root: Path | None = None) -> dict | None:
    """Return normalized experiment preflight config, or None if disabled."""
    raw = get_experiment_ops_config(repo_root)
    if not raw or not _boolish(raw.get("enabled", True), default=True):
        return None

    raw_servers = raw.get("servers")
    servers: list[dict] = []
    default_server: dict | None = None
    if isinstance(raw_servers, dict):
        for slot, value in raw_servers.items():
            server = _normalize_server(str(slot), value)
            if server is None:
                continue
            if slot == "default":
                default_server = server
            else:
                servers.append(server)

    return {
        "enabled": True,
        "defaultServer": default_server,
        "otherServers": servers,
        "requiredBeforeRun": _as_string_list(raw.get("required_before_run")),
        "forbidden": _as_string_list(raw.get("forbidden")),
        "docsToSync": _as_string_list(raw.get("docs_to_sync")),
        "benchmarkStance": _as_string_list(raw.get("benchmark_stance")),
    }


def get_experiment_preflight_lines(repo_root: Path | None = None) -> list[str]:
    """Format experiment preflight as session-context lines."""
    cfg = get_experiment_preflight(repo_root)
    if not cfg:
        return []

    lines: list[str] = []
    lines.append("## EXPERIMENT PREFLIGHT")

    default_server = cfg.get("defaultServer")
    if isinstance(default_server, dict):
        header = default_server.get("name", "unknown")
        host = default_server.get("host", "")
        port = default_server.get("port", "")
        purpose = default_server.get("purpose", "")
        endpoint = host
        if host and port:
            endpoint = f"{host}:{port}"
        if endpoint:
            lines.append(f"Default server: {header} ({endpoint})")
        else:
            lines.append(f"Default server: {header}")
        if purpose:
            lines.append(f"Purpose: {purpose}")

        preferred_roots = []
        if default_server.get("remoteRoot"):
            preferred_roots.append(f"remote={default_server['remoteRoot']}")
        if default_server.get("codeRoot"):
            preferred_roots.append(f"code={default_server['codeRoot']}")
        if default_server.get("dataRoot"):
            preferred_roots.append(f"data={default_server['dataRoot']}")
        if default_server.get("runsRoot"):
            preferred_roots.append(f"runs={default_server['runsRoot']}")
        if preferred_roots:
            lines.append("Preferred roots: " + ", ".join(preferred_roots))

    other_servers = cfg.get("otherServers", [])
    if isinstance(other_servers, list) and other_servers:
        lines.append("Other server notes:")
        for server in other_servers:
            if not isinstance(server, dict):
                continue
            endpoint = server.get("host", "")
            if server.get("host") and server.get("port"):
                endpoint = f"{server['host']}:{server['port']}"
            summary = server.get("name", server.get("slot", "server"))
            if endpoint:
                summary += f" ({endpoint})"
            if server.get("purpose"):
                summary += f" - {server['purpose']}"
            lines.append(f"- {summary}")

    required_before_run = cfg.get("requiredBeforeRun", [])
    if isinstance(required_before_run, list) and required_before_run:
        lines.append("Before heavy runs:")
        for item in required_before_run:
            lines.append(f"- {item}")

    forbidden = cfg.get("forbidden", [])
    if isinstance(forbidden, list) and forbidden:
        lines.append("Forbidden:")
        for item in forbidden:
            lines.append(f"- {item}")

    docs_to_sync = cfg.get("docsToSync", [])
    if isinstance(docs_to_sync, list) and docs_to_sync:
        lines.append("Docs to sync after run:")
        for item in docs_to_sync:
            lines.append(f"- {item}")

    benchmark_stance = cfg.get("benchmarkStance", [])
    if isinstance(benchmark_stance, list) and benchmark_stance:
        lines.append("Benchmark stance:")
        for item in benchmark_stance:
            lines.append(f"- {item}")

    return lines


def get_experiment_preflight_banner(repo_root: Path | None = None) -> str:
    """Format a compact banner for task start output."""
    cfg = get_experiment_preflight(repo_root)
    if not cfg:
        return ""

    lines = ["========================================", "EXPERIMENT PREFLIGHT", "========================================"]

    default_server = cfg.get("defaultServer")
    if isinstance(default_server, dict):
        endpoint = default_server.get("host", "")
        if default_server.get("host") and default_server.get("port"):
            endpoint = f"{default_server['host']}:{default_server['port']}"
        label = default_server.get("name", "unknown")
        if endpoint:
            label += f" ({endpoint})"
        if default_server.get("remoteRoot"):
            label += f" -> {default_server['remoteRoot']}"
        lines.append(label)

    required_before_run = cfg.get("requiredBeforeRun", [])
    if isinstance(required_before_run, list) and required_before_run:
        lines.append("Before run:")
        for item in required_before_run[:4]:
            lines.append(f"- {item}")

    forbidden = cfg.get("forbidden", [])
    if isinstance(forbidden, list) and forbidden:
        lines.append("Forbidden:")
        for item in forbidden[:4]:
            lines.append(f"- {item}")

    return "\n".join(lines)
