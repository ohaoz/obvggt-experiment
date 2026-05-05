# Findings: Further OBVGGT Optimization

## Current Bottlenecks

Existing phase profiling already narrowed the model-side bottleneck:

- Aggregator stack dominates model time.
- RoPE2D fallback is large enough that component caching produced a real end-to-end win.
- OBCache scoring/bookkeeping is still non-trivial.
- Heads and save-depth-map IO are separate; depth-only solves only `video_depth` runtime.

The code confirms the next hot path:

- `OBVGGT/src/streamvggt/layers/attention.py` computes dense SDPA over the retained cache.
- OBCache scoring uses `q_probe.float() @ K.float()`, `softmax`, and `A @ V` over retained tokens.
- Probe selection is evenly spaced and cached.
- Cache budget is uniform across layers.

## Scope Correction: Keep OBCache Algorithm Fixed

The current optimization pass must not change the core OBCache/OBVGGT algorithm.
OBVGGT is based on OBCache, so the following are out of scope for this branch:

- New eviction policies, new scoring formulas, or different token-retention semantics.
- Layer-adaptive cache budgets, even if the total token count stays fixed.
- Query-aware probe/page selection that changes which retained tokens are scored or attended.
- Visual token pruning/merging.
- Runtime KV quantization of the cache.
- `score_interval=2` as a strict same-budget speed claim.

Allowed work is limited to existing config validation, backend/kernel/runtime
infrastructure, measurement, profiling, and evaluation wall-clock improvements
that do not alter cache decisions.

## Ranked Hypotheses

### P0: best_infra + probe6

Why: `probe4` was a small same-budget win; `probe6` is already configured and
may be a better quality/speed compromise. This is the fastest useful experiment
because it needs no code changes.

Expected: `+1-4%` over ctrl or current best infra, with no budget drift. If it
is below noise, stop.

Validation:

- Paired Bonn smoke with current best infra as ctrl.
- Bonn full only if smoke exceeds `+3%`.
- Full `sintel/bonn/kitti` only if Bonn full passes.
- Reject if `cache_max`, `seq_max`, or metrics drift beyond ctrl noise.

### P0: depth_only fairness expansion

Why: `depth_only` is a strong runtime win, but current cross-baseline table is
full-head. If the paper/report uses `depth_only`, every baseline must be rerun
with that same task contract.

Expected: Higher FPS for all video_depth baselines, unchanged depth metrics.
XStreamVGGT may still be fastest but lower quality.

Validation:

- Expose equivalent head gating in StreamVGGT, XStreamVGGT, InfiniteVGGT only if
  it does not change model internals.
- Run same-window full `sintel/bonn/kitti`.
- Label it as `video_depth` task-runtime, not OBVGGT algorithm speedup.

### P1: eval IO wall-clock split and optional fast mode

Why: `video_depth` formal FPS is model-only, but `save_depth_maps` still writes
colorized PNG, colorbar images, and `.npy` files. After model-side speedups, IO
can dominate server wall-clock and CI turnaround.

Design:

- Keep formal FPS timing unchanged.
- Add or document a report-only wall-clock metric for postprocess/save time.
- If implemented, any fast mode must be explicitly labeled as eval-output mode,
  not model FPS.

Risk: This improves experiment turnaround, not strict inference FPS.

### P1: CUDA graph or regional compile feasibility probe

Why: The model has repeated attention/head calls, and PyTorch has inference
features for static-shape graph capture and regional compilation. However,
dynamic cache length and Python control flow may block real gains.

Design:

- Start with microbench or opt-in wrapper only.
- Measure compile/capture overhead separately from steady-state runtime.
- Do not make it default unless paired Bonn smoke beats the current best branch.

Risk: Compile cold start may hide the gain; graph capture can fail on dynamic
allocation or unsupported ops.

### P1: scoring implementation microbench

Why: OBCache scoring uses float32 dense matmul + softmax + value matmul. This
is measurable overhead.

Design:

- First isolate scoring-only microbench with current q/k/v shapes.
- Test layout/contiguity/synchronization effects before changing arithmetic.
- Treat lower precision scoring (`bf16` or `fp16`) as diagnostic only unless
  retained-index decisions match the current float32 path.
- Test whether any implementation variant preserves keep-index overlap.

Risk: Small numerical changes can alter eviction and quality. If keep indices
change, this is an algorithm change and is out of current scope.

### P2: backend preflight logging expansion

Why: Prior forced SDPA Flash was negative, but backend dispatch can silently
change across machines, PyTorch versions, and tensor shapes. The same applies
to TF32/autocast/cuDNN attention settings.

Design:

- Log PyTorch/CUDA version, GPU name, TF32 settings, SDPA backend availability,
  and selected backend hints once per run.
- Keep this outside formal timing or before timed loops.
- Do not force a backend by default without paired evidence.

Risk: Logging is low risk, but forced backend changes are not.

## Out-of-Scope Algorithm Background

These remain useful literature directions, but not for this non-algorithm pass:

- Layer-adaptive budgets inspired by PyramidKV.
- Query-aware selection inspired by Quest/SnapKV.
- Visual token pruning/merging inspired by ToMe/FastV.
- Runtime KV quantization inspired by KIVI/PolarQuant/TurboQuant.

These would be separate algorithmic research branches and should require
explicit approval before implementation.

## Rejected Or Low-Value Repeats

- Current `prealloc_kv`: already slower and higher memory.
- Forced SDPA Flash on current environment: already negative.
- `score_interval=2` as strict conclusion: invalid because it changes effective cache/sequence behavior.
- More Bonn-only claims without full-matrix gate.
