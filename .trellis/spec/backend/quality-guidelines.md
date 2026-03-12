# Quality Guidelines

> Quality bar for experiment controller and tooling changes.

---

## Overview

Quality in this workspace means:

- reproducible runs
- correct artifact contracts
- safe production defaults
- synchronized human docs

Raw code style matters, but it is secondary to contract correctness and operational safety.

---

## Forbidden Patterns

- Hardcoding secrets, passwords, or API keys into tracked files
- Adding a runnable variant without `configs/*.json`, an adapter, and doc updates
- Marking a run `DONE` from subprocess exit code alone when required artifacts are missing
- Writing heavy outputs under the repo root when `$STREAMVGGT_RUNS` should be used
- Copy-pasting dataset lists or artifact filename lists without updating the shared source(s)
- Silently swallowing controller exceptions and pretending success
- Retroactively renaming historical run IDs in ledgers

---

## Required Patterns

- New controller behavior must preserve or explicitly update the contract between:
  - config JSON
  - `quick_run.sh`
  - adapter payload
  - artifact discovery
  - analysis generation
  - human docs
- Machine-readable state should live in JSON/CSV; Markdown is for summary and operator guidance
- Any status/coverage/conclusion change must be checked against:
  - `PROJECT_BRIEF.md`
  - `agents.md`
  - `OBVGGT/experiments/README.md`
  - `OBVGGT/experiments/EXPERIMENTS.md`
  - `OBVGGT/experiments/analysis/SUMMARY.md`
- Keep `monodepth` framed as regression-only unless the experimental stance is intentionally changed everywhere

---

## Testing Requirements

Before finishing a tooling change:

1. Activate `.venv` for local Python checks.
2. Run a syntax pass such as `python -m py_compile` or `python -m compileall` on edited Python files.
3. Run adapter `--dry-run` for the changed controller path when possible.
4. If you change artifact naming or status logic, verify a representative manifest / finalize flow locally.
5. If you only changed docs, re-read the linked source files to ensure the docs describe reality.

There is currently no full CI pipeline in this workspace, so controller changes require explicit local verification.

---

## Code Review Checklist

- Does the patch preserve production safety assumptions from `agents.md`?
- Are new constants or filenames updated in every coupled reader/writer?
- Does the final status reflect artifact completeness, not just command exit code?
- Are sibling repos still treated as repo-local sources of execution, with controller logic remaining in `OBVGGT/experiments/`?
- If docs were touched, do they match the current runnable variants and benchmark stance?
- If docs were not touched, is that omission clearly justified?
