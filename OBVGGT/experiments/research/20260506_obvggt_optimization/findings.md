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
- Probe selection is evenly spaced and cached, but it is not query-aware or layer-aware.
- Cache budget is uniform across layers.

## Ranked Hypotheses

### P0: best_infra + probe6

Why: `probe4` was a small same-budget win; `probe6` is already configured and may be a better quality/speed compromise. This is the fastest useful experiment because it needs no code changes.

Expected: `+1-4%` over ctrl or current best infra, with no budget drift. If it is below noise, stop.

Validation:

- Paired Bonn smoke with current best infra as ctrl.
- Bonn full only if smoke exceeds `+3%`.
- Full `sintel/bonn/kitti` only if Bonn full passes.

### P0: depth_only fairness expansion

Why: `depth_only` is a strong runtime win, but current cross-baseline table is full-head. If the paper/report uses `depth_only`, every baseline must be rerun with that same task contract.

Expected: Higher FPS for all video_depth baselines, unchanged depth metrics. XStreamVGGT may still be fastest but lower quality.

Validation:

- Implement or expose equivalent head gating in StreamVGGT, XStreamVGGT, InfiniteVGGT adapters.
- Run same-window full `sintel/bonn/kitti`.

### P1: layer-adaptive budget

Why: PyramidKV suggests uniform layer budgets are suboptimal. Visual geometry may need more cache in early/mid layers and less in later layers.

Design:

- Add `layer_budget_schedule` to `kv_cache_cfg`, e.g. `flat`, `front_heavy`, `mid_heavy`, `pyramid`.
- Keep total token budget equal to ctrl for strict comparison.
- Record per-layer cache sizes in diagnostics.

Risk: This changes OBCache policy and must be reported as algorithmic, not infra.

### P1: query-aware frame/page selection

Why: Quest/SnapKV suggest query-aware page selection can avoid loading/scoring irrelevant KV. OBVGGT tokens have natural pages: frame, special tokens, and spatial patch groups.

Design:

- Maintain per-frame/per-head summary statistics: min/max K, mean K, V norm, or centroid.
- Use current-frame q probes to shortlist frame pages before full token scoring.
- Keep exact OBCache budget after selection to avoid relaxed-budget claims.

Risk: More complex than probe count changes; must prove no quality drop on KITTI.

### P1: scoring kernel refactor

Why: OBCache scoring uses float32 dense matmul + softmax + value matmul. This is measurable overhead.

Design:

- First isolate scoring-only microbench with current q/k/v shapes.
- Test lower precision scoring (`bf16` or `fp16`) against score-ranking stability.
- Test whether approximate top-k decisions match float32 decisions.

Risk: Small numerical changes can alter eviction and quality; must compare keep-index overlap before end-to-end runs.

### P2: visual token merging/pruning

Why: ToMe/FastV-like methods can accelerate visual transformers, but geometry tasks are sensitive to spatial detail.

Design:

- Only late-layer or non-depth-head tokens first.
- Never merge special/register tokens.
- Start with diagnostic-only token-importance maps before pruning.

Risk: High quality risk, especially KITTI geometry.

### P2: low-bit KV quantization

Why: PolarQuant/TurboQuant/KIVI-style methods target exactly the KV memory bottleneck.

Design:

- Capture q/k/v tensors from a Bonn sequence.
- Offline test attention logit distortion and top-k/softmax-output error under int8/4bit/PolarQuant-like transforms.
- Only implement runtime quantized cache if offline error is low.

Risk: Speed requires custom kernels or efficient dequantization; naive PyTorch quantization may reduce memory but slow runtime.

## Rejected Or Low-Value Repeats

- Current `prealloc_kv`: already slower and higher memory.
- Forced SDPA Flash on current environment: already negative.
- `score_interval=2` as strict conclusion: invalid because it changes effective cache/sequence behavior.
- More Bonn-only claims without full-matrix gate.
