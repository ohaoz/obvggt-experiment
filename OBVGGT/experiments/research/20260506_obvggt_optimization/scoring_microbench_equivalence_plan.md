# Plan: OBCache Scoring Microbench With Equivalence Gate

## Scope

This is diagnostics-only unless it preserves eviction decisions exactly. Do not
change OBCache scoring formula, eviction policy, budgets, or probe selection in
the current branch.

## Current Hot Path

The scoring path spans:

- `OBVGGT/src/streamvggt/layers/attention.py`
  - `q_probe = q.index_select(...)`
  - `qk_probe = q_probe.float() @ state.k.transpose(-2, -1).float()`
  - `A_probe = torch.softmax(qk_probe, dim=-1, dtype=torch.float32)`
  - `O_probe = A_probe @ state.v.float()`
  - `state.tracker.update(...)`
- `OBVGGT/src/streamvggt/utils/obcache_kv.py`
  - `StreamOBCScoreTracker.update()`
  - `v_update()` / `k_update()`
  - `evict()`
  - `torch.topk(score_to_select, topk, dim=-1).sort().values`

The final semantic decision is `keep_topk_idx`. That tensor determines which
historical tokens survive and must be treated as the equivalence oracle.

## Safe Diagnostics

Allowed diagnostics:

- record q/k/v shapes and dtypes for real runs;
- benchmark contiguous vs non-contiguous inputs;
- benchmark isolated scoring kernels on synthetic tensors matching real shapes;
- measure `qk_probe`, softmax/value matmul, `v_update`, `k_update`, and `topk`
  separately;
- report time/memory only.

Not allowed as promotion without explicit algorithm approval:

- lower precision scoring if `keep_topk_idx` changes;
- approximate top-k;
- changed pooling/window/sink behavior;
- changed probe positions;
- layer-specific budget or score normalization changes.

## Equivalence Gate

Any implementation variant must pass this order:

1. Same input tensors, same config, same seed.
2. Compare `keep_topk_idx` after every evict call for every layer.
3. Require exact equality for non-algorithm promotion.
4. If exact equality fails, compute overlap only for diagnosis and stop.
5. Only after exact equality, run Bonn smoke and require unchanged cache stats
   and depth metrics.

## Suggested Harness Shape

Do not start with end-to-end code changes. First add an offline script that:

- creates or loads q/k/v tensors with shape samples from a profile run;
- runs the current scoring path as the reference;
- runs candidate implementation functions in isolation;
- records elapsed CUDA time with synchronization outside measured regions;
- writes JSON with timing and `keep_topk_idx_equal`.

The first useful output is a table of phase timings and equality status, not an
FPS claim.

