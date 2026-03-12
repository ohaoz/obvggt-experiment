# Logging Guidelines

> Run-time logging and machine-readable diagnostics for this workspace.

---

## Overview

Logging in this repo is split across:

- `stdout.log` for the command stream
- `env_snapshot.txt` / `command.sh` for reproducibility
- `manifest.json` / `artifacts.json` for machine-readable state
- `record.md` for operator-facing summary

Use plain, grep-friendly text for the live log stream and JSON for structured state.

---

## Log Levels

- `INFO`: run banner, resolved paths, selected variant/task, command list
- `WARN`: env mismatch, fallback behavior, missing optional outputs, partial coverage
- `ERROR`: invalid config, subprocess failure, missing required artifacts

Most controller scripts currently log with `print()` rather than a Python logging framework. That is acceptable as long as the output remains short, stable, and structured by section.

---

## Structured Logging

The minimum structured context for every run is:

- `run_id`
- `variant`
- `task`
- `model_name`
- `repo_path`
- `output_root`
- `git branch/commit`
- current vs expected env
- KV cache summary / config when relevant

Store those fields in files, not just in banner text.

---

## What To Log

Always log:

- resolved repo root
- chosen adapter
- exact command(s)
- output root
- checkpoint path
- final status and exit code

When relevant, also log:

- KV configuration and policy summary
- dataset coverage
- missing artifact names
- warnings about regression-only benchmarks such as `monodepth`

For aggregators, use a stable prefix such as `[compare_variants]`.

---

## What NOT To Log

- `SWANLAB_API_KEY`
- `WANDB_API_KEY`
- server passwords
- secrets copied from shell env

Do not paste credentials from `agents.md` into logs, records, or generated scripts.

---

## Common Mistakes

- Printing high-value context only to stdout and not preserving it in files
- Emitting noisy per-frame debug logs by default
- Logging a warning but still presenting the run as unqualified success
- Changing artifact filenames without changing log/record discovery
