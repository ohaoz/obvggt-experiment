# Literature Survey: OBVGGT Optimization Directions

This survey maps recent attention/KV-cache research to concrete OBVGGT opportunities. It is intentionally decision-oriented: each paper is classified by how directly it can change the current codebase.

## Current Scope

After the user scope correction, this survey is background only for ideas that
would change OBCache semantics. The current branch must not implement:

- Layer-adaptive cache budgets.
- Query-aware probe/page selection.
- New eviction or scoring formulas.
- Visual token pruning/merging.
- Runtime KV-cache quantization.

The allowed near-term work is same-algorithm existing config validation,
inference infrastructure, backend logging, profiling, task-runtime fairness, and
evaluation wall-clock cleanup.

## Local Baseline Before New Research

The current best branch-local results are already strong:

- PyTorch RoPE2D fallback component caching improves `video_depth` FPS by `+14.04% / +8.21% / +5.56%` on `sintel/bonn/kitti`, with unchanged cache budget and depth metrics.
- `depth_only` improves `video_depth` FPS by `+10.27% / +13.14% / +18.94%`, again with unchanged quality/cache behavior, but only under the video_depth task contract.
- Current `prealloc_kv` is rejected: Bonn smoke `5.9636 -> 5.4050 FPS`, peak memory `8819 -> 9845 MB`.

## Sources And Relevance

### FlashAttention-3

Source: https://arxiv.org/abs/2407.08608

FlashAttention-3 targets Hopper GPUs with asynchrony, TMA, warp specialization, and FP8 support. The paper reports `1.5-2.0x` speedup on H100 and high FP16/FP8 throughput. For OBVGGT, this is not an immediate fix because the current server uses RTX 4090D, and forced SDPA Flash already underperformed PyTorch default dispatch in the existing Bonn smoke. Keep this as an environment/hardware upgrade path, not a near-term algorithm direction.

### PyTorch FlexAttention / FlexDecoding

Sources:

- https://docs.pytorch.org/docs/stable/nn.attention.flex_attention.html
- https://pytorch.org/blog/flexattention-for-inference/

FlexAttention is relevant because it supports custom `score_mod`/`mask_mod`, BlockMask, and inference-oriented FlexDecoding. The official PyTorch blog highlights preallocated KV caches and in-place updates as a key inference pattern, but OBVGGT's direct prealloc attempt was slower because it duplicated buffers and added copy overhead. The actionable insight is not "preallocate again"; it is to investigate block-sparse masks and page-level selection if the server PyTorch version can be upgraded safely.

### H2O and StreamingLLM

Sources:

- H2O: https://papers.nips.cc/paper_files/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract-Conference.html
- StreamingLLM: https://proceedings.iclr.cc/paper_files/paper/2024/hash/5e5fd18f863cbe6d8ae392a93fd271c9-Abstract-Conference.html

These are the conceptual ancestors of OBVGGT's sink/recent/heavy split. H2O motivates recent + heavy-hitter retention; StreamingLLM motivates keeping initial sink tokens. OBVGGT already implements this family. New work in the current branch should not alter this policy; any deeper H2O/StreamingLLM-style change belongs in a separate algorithm branch.

### SnapKV

Source: https://arxiv.org/abs/2404.14469

SnapKV observes attention-head-specific prompt attention features from an observation window and selects clustered important KV positions per head. OBVGGT currently uses evenly spaced probes plus joint V/K scoring. This is relevant background, but implementing SnapKV-like selection would change OBCache retention decisions and is out of the current non-algorithm scope.

### PyramidKV

Source: https://arxiv.org/abs/2406.02069

PyramidKV argues that information flow is broader in lower layers and concentrates in higher layers, so KV cache budget should vary by layer. OBVGGT currently uses the same frame budget for every layer. This is a plausible future algorithm direction, but it is not allowed in the current branch because it changes cache allocation semantics.

### Quest

Source: https://arxiv.org/abs/2406.10774

Quest is query-aware: it tracks min/max key ranges in cache pages and loads only Top-K critical pages for attention. OBVGGT's attention still attends to retained cache tokens densely, and OBCache scoring computes dense probe attention over the retained cache. A visual analogue could group KV by frame/page and use current-frame queries to shortlist pages before scoring or attention, but that changes the algorithm and is deferred.

### MInference

Source: https://arxiv.org/abs/2407.02490

MInference identifies per-head sparse attention patterns and builds sparse indices during inference. In OBVGGT, attention patterns may be strongly structured by frame and spatial locality. For this branch, the only allowed derivative is diagnostic profiling of attention patterns. Building sparse masks for scoring or attention is algorithmic and deferred.

### ToMe / Visual Token Reduction

Sources:

- ToMe: https://openreview.net/forum?id=JroZRaRw7Eu
- FastV: https://arxiv.org/abs/2403.06764

ToMe merges tokens to speed ViTs; FastV prunes visual tokens in later layers of LVLMs. These are tempting because OBVGGT has many image tokens per frame, but they are high risk for geometry: depth and pose are sensitive to spatial detail. They are out of scope for this branch.

### KV Quantization: KIVI, PolarQuant, TurboQuant

Sources:

- PolarQuant: https://arxiv.org/abs/2502.02617
- Google TurboQuant blog: https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/

Low-bit KV quantization is a major frontier. PolarQuant reports over `4.2x` KV compression in long-context evaluation; Google describes TurboQuant as targeting KV bottlenecks with 3-bit cache compression and faster attention logits. For OBVGGT, this is high engineering and algorithm/runtime intrusive. It is not part of the current non-algorithm plan.

## Decision Summary

Immediate practical work:

1. Cross-baseline `depth_only` fairness table.
2. Eval IO wall-clock split and optional fast-output mode.
3. CUDA graph/regional compile feasibility only as opt-in infra microbench.
4. Scoring implementation diagnostics with keep-index overlap as the guard.
5. Backend preflight logging expansion for reproducibility.

Defer:

- FlashAttention-3 unless H100/Hopper or compatible kernels are available.
- Current `probe4/probe6` configs; the 2026-05-06 smoke rejected both.
- TurboQuant/PolarQuant until offline fidelity and compressed-kernel path exist.
- ToMe/FastV until a geometry-safe token-reduction protocol is defined.
- Layer-adaptive and query-aware OBCache variants until an explicit algorithm branch is approved.
