# Code Reuse Thinking Guide

> Reuse the existing contract machinery before adding new glue.

---

## Why Reuse Matters Here

In this workspace, duplication usually shows up as:

- the same dataset list copied into multiple files
- the same artifact filename list maintained in two readers
- the same variant metadata written once in config and once again in shell
- near-identical adapter logic forked per variant

That kind of duplication causes silent drift in experiment results and docs.

---

## Search First

Before adding a new constant, filename, or helper, search these hotspots:

- `OBVGGT/experiments/scripts/adapter_utils.py`
- `OBVGGT/experiments/scripts/run_*.py`
- `OBVGGT/experiments/scripts/run_record.py`
- `OBVGGT/experiments/scripts/compare_variants.py`
- `OBVGGT/experiments/configs/*.json`
- `PROJECT_BRIEF.md`, `agents.md`, `README.md`, `EXPERIMENTS.md`

---

## Checklist Before Finishing

- [ ] searched for every consumer of the changed value
- [ ] reused shared constants/helpers where possible
- [ ] updated both machine readers and human docs
- [ ] avoided introducing a second source of truth
