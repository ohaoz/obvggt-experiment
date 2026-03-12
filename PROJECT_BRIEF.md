# PROJECT_BRIEF

Last updated: 2026-03-12

## What This Workspace Is
- Multi-repo workspace for VGGT long-sequence / KV-cache evaluation and reproduction.
- The codebases currently present here are `StreamVGGT`, `OBVGGT`, `XStreamVGGT`, `InfiniteVGGT`, plus historical/reference material such as `OBCache`.
- `IncVGGT` should currently be treated as literature-only: there is no public runnable code wired into this workspace.

## Read This First In New Conversations
- Single-file orientation: `PROJECT_BRIEF.md`
- Production/SOP rules: `agents.md`
- Experiment hub: `OBVGGT/experiments/README.md`
- Variant status: `OBVGGT/experiments/VARIANTS.md`
- Run ledger: `OBVGGT/experiments/EXPERIMENTS.md`

## Current Evaluation Stance
- Primary KV-sensitive benchmarks: `video_depth` and `mv_recon`.
- `monodepth` is regression-only. Use it to check accuracy drift, not to claim KV wins or losses.
- `pose_co3d` is supplementary and still incomplete because annotation / result cleanup is unfinished.

## Naming Map
- Historical `baseline` in `OBVGGT/experiments/*` means the `StreamVGGT` baseline line.
- Historical `obcache` in `OBVGGT/experiments/*` means the `OBVGGT` run/checkpoint line used by the current harness.
- `XStreamVGGT` and `InfiniteVGGT` are runnable sibling repos and are now addressable from `OBVGGT/experiments/quick_run.sh`.
- Do not retroactively rename historical run IDs; clarify the mapping in docs instead.

## Runnable Repos Today

| Repo | Status | Notes |
|---|---|---|
| `StreamVGGT` | Runnable | Canonical baseline repo; also appears as historical `baseline` in OBVGGT experiment docs. |
| `OBVGGT` | Runnable | Main modified repo and current experiment hub; also appears as historical `obcache` in older records. |
| `XStreamVGGT` | Runnable | Local repo exists and is now addressable from the unified `OBVGGT/experiments/quick_run.sh` harness. |
| `InfiniteVGGT` | Runnable | Local repo exists and is now addressable from the unified `OBVGGT/experiments/quick_run.sh` harness. |
| `IncVGGT` | Not runnable here | Literature-only for now; no public code path should be documented as runnable. |

## Unified Harness Status
- `OBVGGT/experiments/quick_run.sh` is the unified launcher for:
  - `baseline` → `StreamVGGT`
  - `obcache` → `OBVGGT`
  - `xstreamvggt` → `XStreamVGGT`
  - `infinitevggt` → `InfiniteVGGT`
- Primary short/medium benchmarks:
  - `video_depth`
  - `mv_recon`
  - `pose_co3d`
- `monodepth` stays available but is regression-only.
- `long_stream` is reserved for long-horizon / endless-stream evaluation, mainly for `InfiniteVGGT`.

## Default Operations Context
- Default server: `amd_server` (`192.168.166.137`, SSH port `2222`)
- Recommended root on server: `/mnt/data5/OBVGGT`
- Keep datasets, checkpoints, eval outputs, and SwanLab/W&B caches off the system disk.
- Unified harness output root:
  - preferred: `$STREAMVGGT_RUNS/eval_results/by_run/<run_id>/<task>/<variant>/`
  - fallback: `<repo>/eval_results/by_run/<run_id>/<task>/<variant>/`

## Documentation Rule Of Thumb
- If a run changes status, coverage, or conclusions, update `agents.md`, `OBVGGT/experiments/README.md`, and `OBVGGT/experiments/EXPERIMENTS.md`.
- If no doc changes are needed after a run, the run record still needs to say that the docs were checked and why no update was required.
