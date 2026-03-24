# Error Handling

> How controller scripts fail, downgrade, and preserve diagnostics.

---

## Overview

This workspace uses CLI tooling, not HTTP APIs. Error handling should optimize for:

- fast failure on bad configuration
- preservation of logs and run metadata
- accurate final status (`FAILED` vs `PARTIAL_DONE`)
- actionable diagnostics for the next operator

---

## Error Types

### 1. Preflight / Configuration Errors

Examples:

- missing required env vars
- missing config file
- unsupported task / variant combination
- missing required task arguments such as CO3D paths

Handling rule:

- fail **before** starting the heavy run
- print a short, human-readable message
- exit nonzero

### 2. Execution Errors

Examples:

- subprocess returns nonzero
- Python evaluation script raises
- OOM or missing dependency inside repo-local code

Handling rule:

- keep `stdout.log`
- preserve `command.sh` and environment snapshot
- finalize run state as `FAILED`

### 3. Contract / Coverage Errors

Examples:

- command exits 0 but required artifacts are missing
- docs claim 5 datasets, adapters only produced 4
- analysis expects an artifact filename that the run never wrote

Handling rule:

- do **not** silently call this `DONE`
- downgrade to `PARTIAL_DONE` when execution succeeded but required outputs are incomplete
- list missing outputs explicitly in the run record

---

## Error Handling Patterns

### Validate Early

Use explicit checks at the boundary:

- shell entrypoint validates env and config presence
- adapters validate task support and required args
- aggregators skip malformed optional files but should not redefine the run as successful

### Keep Messages Short And Specific

Good:

- "Task `pose_co3d` requires --pose-co3d-dir and --pose-co3d-anno-dir."
- "Variant `incvggt` is literature-only / not runnable in this workspace."

### Record Before Recovering

If a run fails or partially succeeds, preserve:

- exit code
- start / end timestamps
- output root
- missing artifact list
- next-action note in `record.md`

### Run Status Contract

For the controller path under `OBVGGT/experiments/`, status is resolved from both
the subprocess exit code and the artifact contract:

- adapter dry-run payload must expose `expected_artifacts`
- `quick_run.sh` must persist that list into `manifest.json`
- `run_record.py finalize` must compare discovered artifacts against that list

Status resolution rule:

- `DONE`: exit code is zero and all expected artifacts exist
- `PARTIAL_DONE`: at least one expected artifact is missing, but some expected
  outputs exist or the subprocess itself exited zero
- `FAILED`: subprocess exited nonzero and no expected outputs were produced

Batch watcher rule:

- helper scripts may continue to the next run after one child fails
- but the batch script itself must exit nonzero if any child returned nonzero

---

## CLI Error Surface

The standard error surface here is:

1. concise stderr/stdout explanation
2. nonzero exit code for hard failure
3. updated run record for post-mortem

Prefer stable wording so logs remain grep-friendly.

---

## Common Mistakes

- Swallowing adapter validation errors and continuing anyway
- Marking a run `DONE` from exit code alone
- Catching `Exception` broadly and returning success
- Losing the original error because finalize/cleanup raised afterwards
- Writing only prose to Markdown without preserving machine-readable state in JSON
