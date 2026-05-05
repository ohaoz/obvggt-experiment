# Literature Survey: OBVGGT Optimization Directions

This survey maps recent attention/KV-cache research to concrete OBVGGT opportunities. It is intentionally decision-oriented: each paper is classified by how directly it can change the current codebase.

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

These are the conceptual ancestors of OBVGGT's sink/recent/heavy split. H2O motivates recent + heavy-hitter retention; StreamingLLM motivates keeping initial sink tokens. OBVGGT already implements this family. New work should not simply rebrand H2O/StreamingLLM, but should test whether visual geometry needs layer-adaptive or query-aware variants.

### SnapKV

Source: https://arxiv.org/abs/2404.14469

SnapKV observes attention-head-specific prompt attention features from an observation window and selects clustered important KV positions per head. OBVGGT currently uses evenly spaced probes plus joint V/K scoring. The transferable idea is a per-head observation-window policy: use the last one or two incoming frames to estimate which historical frame/token clusters matter, then score fewer but more informative probes.

### PyramidKV

Source: https://arxiv.org/abs/2406.02069

PyramidKV argues that information flow is broader in lower layers and concentrates in higher layers, so KV cache budget should vary by layer. OBVGGT currently uses the same frame budget for every layer. This is one of the strongest P1 algorithm directions: keep total budget fixed but allocate more heavy tokens to lower or geometry-sensitive layers and less to redundant higher layers.

### Quest

Source: https://arxiv.org/abs/2406.10774

Quest is query-aware: it tracks min/max key ranges in cache pages and loads only Top-K critical pages for attention. OBVGGT's attention still attends to retained cache tokens densely, and OBCache scoring computes dense probe attention over the retained cache. A visual analogue could group KV by frame/page and use current-frame queries to shortlist pages before scoring or attention. This changes runtime path and must be guarded by strict quality gates.

### MInference

Source: https://arxiv.org/abs/2407.02490

MInference identifies per-head sparse attention patterns and builds sparse indices during inference. In OBVGGT, attention patterns may be strongly structured by frame and spatial locality. The practical derivative is not to import MInference directly, but to profile whether OBVGGT heads exhibit stable frame-local, vertical, or sink-like patterns. If yes, build head-specific block masks for scoring or attention.

### ToMe / Visual Token Reduction

Sources:

- ToMe: https://openreview.net/forum?id=JroZRaRw7Eu
- FastV: https://arxiv.org/abs/2403.06764

ToMe merges tokens to speed ViTs; FastV prunes visual tokens in later layers of LVLMs. These are tempting because OBVGGT has many image tokens per frame, but they are high risk for geometry: depth and pose are sensitive to spatial detail. If attempted, start with non-output heads, late layers, or low-gradient/low-score tokens, and gate on KITTI/Sintel before declaring success.

### KV Quantization: KIVI, PolarQuant, TurboQuant

Sources:

- PolarQuant: https://arxiv.org/abs/2502.02617
- Google TurboQuant blog: https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/

Low-bit KV quantization is a major frontier. PolarQuant reports over `4.2x` KV compression in long-context evaluation; Google describes TurboQuant as targeting KV bottlenecks with 3-bit cache compression and faster attention logits. For OBVGGT, this is high engineering: speed only materializes if attention/scoring kernels consume compressed KV directly. The first experiment should be offline logit/output fidelity on saved K/V/Q tensors, not an end-to-end implementation.

## Decision Summary

Immediate practical work:

1. `best_infra + probe6` paired gate.
2. Cross-baseline `depth_only` fairness table.
3. Layer-adaptive budgets inspired by PyramidKV.
4. Query-aware frame/page selection inspired by Quest/SnapKV.

Defer:

- FlashAttention-3 unless H100/Hopper or compatible kernels are available.
- TurboQuant/PolarQuant until offline fidelity and compressed-kernel path exist.
- ToMe/FastV until a geometry-safe token-reduction protocol is defined.
