# PROJECT_BRIEF

Last updated: 2026-05-06

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
- As of May 4, 2026, a same-machine same-window `video_depth` rerun on the 48GB RTX 4090D exists for `StreamVGGT`, `XStreamVGGT`, `InfiniteVGGT`, `OBVGGT_ctrl` (`4999abd`), and `OBVGGT_best_infra` (`6fc9571`).
- Accepted branch-local infra result: PyTorch RoPE2D fallback component caching is a same-cache-budget `OBVGGT video_depth` optimization. The tight paired gate remains `4999abd -> 87e056a`, with FPS gains of `+14.04%` on Sintel, `+8.21%` on Bonn, and `+5.56%` on KITTI at unchanged cache budget and depth metrics.
- Accepted branch-local task-runtime result: `depth_only` is a same-budget `video_depth` optimization for `OBVGGT`, but it remains task-specific and is not yet a cross-model fairness setting.
- Prepared branch-local fairness support: `exp/2026-0506-obvggt-research-opt` adds opt-in `video_depth --head_mode depth_only` plumbing for `StreamVGGT`, `XStreamVGGT`, and `InfiniteVGGT`, plus Bonn dry-run-safe dataset filtering. This is only run preparation until server metrics pass.
- Rejected branch-local runtime-equivalent candidate: `obcache_p1_no_recent_ctrl_prealloc_kv` failed the paired Bonn smoke gate, dropping FPS from `5.9636` to `5.4050` and raising peak allocated memory from `8819 MB` to `9845 MB` at unchanged depth metrics.
- Rejected branch-local same-algorithm config candidates: the clean 2026-05-06 Bonn `balloon2` 40-frame smoke rejected `obcache_p1_no_recent_probe6` and `obcache_p1_no_recent_probe4`; both kept `cache_max=5020` and `seq_max=6024`, but FPS changed `5.0544 -> 4.3749` (`-13.44%`) and `5.0544 -> 4.9659` (`-1.75%`), respectively.
- The broader fairness window `4999abd -> 6fc9571` only showed `+3.19% / +3.18% / +0.08%` FPS. Use it as a cross-baseline comparison window, not as the primary effect-size estimate for the infra claim.
- In that 48GB full-head window, `OBVGGT_best_infra` is much better than `StreamVGGT` on Bonn (`6.02 vs 3.17 FPS`, `-51.6%` peak memory, better AbsRel), slightly faster and much more accurate on KITTI (`6.11 vs 5.85 FPS`, AbsRel `0.0991 vs 0.1725`), and roughly equal-FPS but lower-memory on Sintel.
- `XStreamVGGT` is the fastest full-head baseline in that window, but it is clearly worse than `OBVGGT_best_infra` on Bonn/KITTI accuracy; `InfiniteVGGT` is slower and less accurate than `OBVGGT_best_infra` on Bonn/KITTI.
- Any cross-model use of `depth_only` still requires rerunning every compared baseline with the same task contract.

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
