# Directory Structure

> Where controller code, runnable repos, artifacts, and docs live in this workspace.

---

## Overview

This workspace is a **multi-repo evaluation harness**. Keep controller logic, repo-local model code, run artifacts, and human-readable docs in clearly separated locations.

---

## Directory Layout

```text
vggt/
├── PROJECT_BRIEF.md
├── agents.md
├── .trellis/
├── StreamVGGT/
├── OBVGGT/
│   ├── src/
│   └── experiments/
│       ├── configs/
│       ├── scripts/
│       ├── runs/
│       ├── analysis/
│       ├── README.md
│       ├── EXPERIMENTS.md
│       └── VARIANTS.md
├── XStreamVGGT/
└── InfiniteVGGT/
```

---

## Module Organization

### Controller Layer

Put orchestration logic in `OBVGGT/experiments/scripts/`:

- `run_<variant>.py` for repo-specific dispatch
- `adapter_utils.py` for shared constants / helpers
- `run_record.py` for manifest + artifact indexing
- `compare_variants.py` for derived analysis

### Variant Metadata

Put static defaults in `OBVGGT/experiments/configs/*.json`.

Variant config is the source of truth for:

- repo path
- adapter script
- environment name
- supported tasks
- default KV policy summary

### Repo-Local Model / Eval Code

Keep model implementation and repo-specific eval scripts in each repo's own `src/` tree.

If a change only affects one repo's internal evaluation logic, make it there. Do not copy that logic into `OBVGGT/experiments/scripts/` unless it becomes shared controller behavior.

### Run Outputs

Separate controller records from heavy eval outputs:

- controller-owned run metadata: `OBVGGT/experiments/runs/<run_id>/`
- eval artifacts: `$STREAMVGGT_RUNS/eval_results/by_run/<run_id>/<task>/<variant>/`

### Human Docs

Use these docs for different purposes:

- `PROJECT_BRIEF.md`: top-level orientation
- `agents.md`: production SOP and hard constraints
- `OBVGGT/experiments/README.md`: current harness usage
- `OBVGGT/experiments/EXPERIMENTS.md`: run ledger
- `OBVGGT/experiments/analysis/SUMMARY.md`: distilled conclusions

---

## Naming Conventions

- Python controller files: `snake_case.py`
- Variant adapters: `run_<variant>.py`
- Variant IDs in config and CLI: lowercase (`baseline`, `obcache`, `xstreamvggt`, `infinitevggt`)
- Use repo names in new prose when possible; keep `baseline` / `obcache` only for historical IDs and legacy labels

---

## Common Mistakes

- Mixing controller glue into repo-local `src/` when it belongs in `experiments/scripts/`
- Adding a new variant without a `configs/*.json` entry
- Treating `analysis/*.csv` or `SUMMARY.md` as the source of truth instead of regenerable outputs
- Writing eval outputs under the repo root when they should land under `$STREAMVGGT_RUNS`
