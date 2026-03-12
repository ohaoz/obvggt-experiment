# Database Guidelines

> File-backed state rules for this workspace.

---

## Overview

There is **no relational database** in this workspace today. Persistent state lives in:

- JSON config files
- JSON run manifests / artifact indexes
- Markdown status documents
- CSV analysis tables

Treat these files as a lightweight schema, not as disposable scratch output.

---

## Query Patterns

Use the narrowest source of truth for the question you need to answer:

- Variant defaults -> `OBVGGT/experiments/configs/*.json`
- Single-run machine state -> `runs/<run_id>/manifest.json`, `artifacts.json`
- Single-run human summary -> `runs/<run_id>/record.md`
- Cross-run derived metrics -> `analysis/tables/*.csv`, `analysis/figures/*.csv`
- Human ledger / narrative -> `EXPERIMENTS.md`, `README.md`, `analysis/SUMMARY.md`

Prefer this debug order:

1. `manifest.json`
2. `artifacts.json`
3. `stdout.log`
4. eval artifact JSON files
5. human-written Markdown summaries

---

## Migrations

In this repo, "migration" means changing a JSON / CSV / Markdown contract.

When you change a file contract:

1. Update both writer and reader in the same patch.
2. Update any downstream aggregator that consumes the file.
3. Update the human docs if the interpretation changes.
4. Prefer additive schema changes over destructive renames.

Examples of coupled readers/writers:

- `run_record.py` <-> `compare_variants.py`
- `configs/*.json` <-> `quick_run.sh`
- adapter artifact expectations <-> SOP coverage rules

---

## Naming Conventions

- JSON keys: `snake_case`
- Status values: uppercase fixed vocabulary (`RUNNING`, `DONE`, `PARTIAL_DONE`, `FAILED`)
- Timestamps: ISO 8601 with timezone offset
- CSV columns: stable machine-readable headers

---

## Common Mistakes

- Treating a derived CSV as the authoritative store
- Editing `manifest.json` by hand instead of fixing the writer
- Introducing a new artifact filename without updating the discovery list
- Storing secrets, tokens, or passwords in JSON / Markdown records
- Adding a database for a problem that only needs deterministic files
