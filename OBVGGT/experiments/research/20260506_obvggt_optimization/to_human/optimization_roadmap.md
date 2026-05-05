# OBVGGT Further Optimization Roadmap

## Bottom Line

The next credible OBVGGT gains should come from either:

1. Combining the accepted infra branch with already-defined same-budget probe variants.
2. Expanding `depth_only` fairly across baselines for a stronger `video_depth` table.
3. Moving beyond uniform OBCache budgets toward layer-adaptive or query-aware cache selection.

Do not spend more time rerunning the current `prealloc_kv` implementation. It is a confirmed negative.

## Immediate Experiment Queue

| Priority | Candidate | Why now | Pass gate |
|---|---|---|---|
| P0 | `best_infra + probe6` | Existing config; tests known probe/speed tradeoff | Bonn smoke `>+3%`, no cache/seq/quality drift |
| P0 | `best_infra + probe4` confirm | `probe4` had prior small same-budget signal | Full matrix only if repeated Bonn full survives |
| P0 | `depth_only` for all baselines | Turns accepted task-runtime win into fair cross-model table | All baselines rerun with same `head_mode=depth_only` |
| P1 | Layer-adaptive budget | PyramidKV-style insight; uniform layer budget likely suboptimal | Same total budget; full matrix quality guard |
| P1 | Query-aware page selection | Quest/SnapKV-style; reduce scoring/attention reads | Keep-index overlap + Bonn smoke before full run |
| P1 | Lower-precision scoring | Current scoring uses float32 matmul/softmax | Keep-index overlap first; then Bonn smoke |
| P2 | Token merge/prune | Large possible speedup but geometry risk | Offline token maps + strict KITTI/Sintel guard |
| P2 | KV quantization | Strong frontier direction but kernel-heavy | Offline q/k/v fidelity before runtime prototype |

## Suggested First 24h Plan

1. Create configs:
   - `obcache_p1_no_recent_ctrl_best_infra_probe6`
   - `obcache_p1_no_recent_ctrl_best_infra_probe4`
2. Run paired Bonn 40-frame smoke:
   - ctrl: current `obcache_p1_no_recent_ctrl`
   - candidates: probe6/probe4 under this branch
3. If one candidate beats ctrl by `>3%` with identical budget/metrics, run Bonn full.
4. If Bonn full passes, run full `sintel/bonn/kitti`.
5. In parallel, write a protocol for layer-adaptive budgets and implement only diagnostics first:
   - per-layer cache size
   - per-layer evict overlap
   - per-layer score entropy

## Paper/Report Impact If Successful

- `best_infra + probe6/probe4`: strengthens method FPS without changing task contract.
- `depth_only` cross-baseline: strengthens deployment/runtime story for video_depth only.
- Layer-adaptive/query-aware variants: could become a new algorithmic contribution beyond the current OBCache policy.

## Sources Used

- FlashAttention-3: https://arxiv.org/abs/2407.08608
- PyTorch FlexAttention inference: https://pytorch.org/blog/flexattention-for-inference/
- H2O: https://papers.nips.cc/paper_files/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract-Conference.html
- StreamingLLM: https://proceedings.iclr.cc/paper_files/paper/2024/hash/5e5fd18f863cbe6d8ae392a93fd271c9-Abstract-Conference.html
- SnapKV: https://arxiv.org/abs/2404.14469
- PyramidKV: https://arxiv.org/abs/2406.02069
- Quest: https://arxiv.org/abs/2406.10774
- MInference: https://arxiv.org/abs/2407.02490
- ToMe: https://openreview.net/forum?id=JroZRaRw7Eu
- FastV: https://arxiv.org/abs/2403.06764
- PolarQuant: https://arxiv.org/abs/2502.02617
- TurboQuant: https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
