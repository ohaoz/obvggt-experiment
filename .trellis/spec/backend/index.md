# Experiment Harness Guidelines

> Conventions for the controller and tooling layer in this workspace.

---

## Scope

This workspace is **not** a web backend. In this repo, "backend" means:

- the controller layer under `OBVGGT/experiments/`
- adapter scripts that dispatch into runnable sibling repos
- run manifests / artifacts / analysis generation
- production-safe server operations and document sync

Read these docs after:

1. `PROJECT_BRIEF.md`
2. `agents.md`
3. `OBVGGT/experiments/README.md`

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Where controller code, configs, artifacts, and docs live | Filled |
| [Database Guidelines](./database-guidelines.md) | File-backed state rules for manifests / CSV / Markdown | Filled |
| [Error Handling](./error-handling.md) | How controller scripts fail, downgrade, and preserve diagnostics | Filled |
| [Experiment Operations](./experiment-operations.md) | Server targets, preflight checks, forbidden operations, and doc-sync obligations | Filled |
| [Logging Guidelines](./logging-guidelines.md) | What run context must be logged and what must never be logged | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Reproducibility, artifact contract, and review expectations | Filled |

---

## Mental Model

The main production path in this workspace is:

`config JSON -> quick_run.sh -> adapter dry-run payload -> repo-local command(s) -> eval artifacts -> run record -> generated docs -> human review`

If you change any node in that chain, you are changing a **contract**, not just a file.

---

## Examples To Study First

- `OBVGGT/experiments/quick_run.sh`
- `OBVGGT/experiments/scripts/run_record.py`
- `OBVGGT/experiments/scripts/render_experiment_docs.py`
- `OBVGGT/experiments/scripts/adapter_utils.py`
- `OBVGGT/experiments/scripts/run_streamvggt.py`
- `OBVGGT/experiments/scripts/compare_variants.py`

---

**Language**: Keep Trellis docs in **English** so they work across tools and teammates.
