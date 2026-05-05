# Goal Completion Audit Against `0503-1.md`

## Scope Update

The original `0503-1.md` plan targeted infra/runtime/kernel acceleration under
the rule "do not modify OBCache algorithm strategy." The user later reaffirmed
a stricter interpretation: OBVGGT is based on OBCache, so do not touch the core
algorithm.

This audit evaluates completion under that stricter scope.

## Completed Or Closed

Branch/worktree:

- Completed. Current branch is `exp/2026-0506-obvggt-research-opt`.
- Work was isolated from the dirty main worktree.
- Latest pushed commit at audit time: `e93c4ea`.

Backend and instrumentation:

- Completed enough for current scope.
- `runtime_diagnostics.py` instrumentation bug fixed and tested.
- Backend/preflight logging remains instrumentation-only, not a claimed speedup.

RoPE2D:

- Already accepted from the prior infra branch as the main same-budget infra
  win: PyTorch RoPE2D fallback component caching improves full
  `sintel/bonn/kitti` video_depth FPS with unchanged cache budget and metrics.
- No new CUDA RoPE2D compile work was promoted in this branch.

SDPA backend:

- Existing evidence says forced SDPA Flash is not a current win in this
  environment.
- This branch keeps backend selection as diagnostics/preflight rather than a
  default forced backend.

OBCache runtime allocation:

- Current `prealloc_kv` path is closed as a negative result from prior smoke:
  slower and higher memory.
- This branch does not continue that implementation.

Probe-count candidates:

- Closed as negative under clean 2026-05-06 Bonn `balloon2` 40-frame smoke.
- `probe6`: `5.0544 -> 4.3749 FPS` (`-13.44%`) with unchanged cache/seq budget.
- `probe4`: `5.0544 -> 4.9659 FPS` (`-1.75%`) with unchanged cache/seq budget.
- Decision: do not promote current `probe4/probe6` to Bonn full.

`score_interval`:

- Closed for strict same-budget claims.
- It remains invalid as a same-budget acceleration conclusion because observed
  cache/sequence budget drift changes the comparison.

Depth-only:

- OBVGGT depth-only was already accepted as a `video_depth` task-runtime mode.
- This branch prepared equivalent opt-in `depth_only` plumbing for
  StreamVGGT, XStreamVGGT, and InfiniteVGGT.
- Server-side dry-runs passed for all three sibling baselines.
- Server runtime smoke passed at 2-frame Bonn scale for all three sibling
  baselines after prefix-eval support was added to XStreamVGGT/InfiniteVGGT.
- Still not a full cross-baseline conclusion until planned full smoke/full
  reruns pass.

Eval IO:

- Audited. `eval_depth.py` consumes `.npy`; PNG/colorbar output is visualization
  and can be separated later as wall-clock/output-mode work.
- No formal FPS claim is attached to IO fast-mode notes.

Scoring microbench:

- Planned only. Exact `keep_topk_idx` equality is documented as the required
  promotion gate.
- No scoring implementation change was made.

## Not Completed As Final Claims

The following are intentionally not final conclusions:

- Cross-baseline `depth_only` full table.
- `mv_recon` rerun for accepted infra candidates.
- New CUDA RoPE2D compilation.
- New accepted OBCache runtime allocation optimization.
- Any algorithmic OBCache variant such as layer-adaptive budgets, query-aware
  probe/page selection, token pruning/merging, or KV quantization.

## Current Next Step

The next legitimate experiment is not another probe-count rerun. It is:

1. Server Bonn 40-frame paired smoke for `depth_only` across StreamVGGT,
   XStreamVGGT, InfiniteVGGT, and OBVGGT under the same task contract.
2. Promote to Bonn full only if metrics match.
3. Promote to full `sintel/bonn/kitti` only after Bonn full passes.

All results must stay labeled as `video_depth` task-runtime, not OBCache
algorithm improvement.

