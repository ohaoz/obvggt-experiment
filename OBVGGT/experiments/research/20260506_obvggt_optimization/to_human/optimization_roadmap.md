# OBVGGT Further Optimization Roadmap

## Bottom Line

Current scope: OBVGGT is an OBCache-based method, and this branch must not
change the core cache algorithm. The next credible work should focus on:

1. Fair `video_depth` task-runtime comparison using `depth_only` across all baselines.
2. Infra and measurement improvements that do not alter cache decisions.
3. Eval/runtime diagnostics that make future FPS claims harder to misread.

Do not spend more time rerunning the current `prealloc_kv` implementation or
the current `probe4/probe6` variants. They are confirmed negative under smoke
gates. Do not treat `score_interval=2` as a same-budget speedup because it
changes effective cache/sequence behavior.

## Immediate Experiment Queue

| Priority | Candidate | Why now | Pass gate |
|---|---|---|---|
| P0 | `depth_only` for all baselines | Fair task-runtime table for `video_depth` | All baselines rerun with same `head_mode=depth_only` |
| P1 | Eval IO wall-clock split | Faster experiment turnaround, formal FPS kept separate | Metrics unchanged; formal FPS label unchanged |
| P1 | CUDA graph / regional compile feasibility | Possible infra gain without algorithm changes | Opt-in microbench first; compile overhead reported |
| P1 | Scoring implementation microbench | Locate overhead without changing policy | Keep-index overlap first; otherwise reject |
| P2 | Backend preflight logging expansion | Prevent false SDPA/TF32/CUDA conclusions | One-time logs, outside formal timing |

## Out Of Current Scope

These are not allowed in the current non-algorithm optimization branch because
they change OBCache semantics or token-retention decisions:

- Layer-adaptive cache budgets.
- Query-aware probe/page selection.
- New scoring formulas or eviction policies.
- Visual token pruning or merging.
- Runtime KV-cache quantization.

They can be kept as background literature only. If pursued later, they should
be explicit algorithm branches, not infra cleanups.

## Suggested First 24h Plan

1. Keep the current branch as a research/planning branch; do not alter core OBCache files for algorithmic behavior.
2. Treat the 2026-05-06 `probe4/probe6` smoke as closed unless a new non-algorithm implementation is proposed.
3. Prepare a `depth_only` fairness run plan for StreamVGGT, XStreamVGGT, InfiniteVGGT, and OBVGGT.
4. Keep IO/compile/scoring work in opt-in diagnostics until a paired smoke justifies promotion.

## Report Impact If Successful

- `depth_only` cross-baseline: strengthens deployment/runtime story for `video_depth` only.
- IO/compile/scoring diagnostics: improves reproducibility and may identify a later safe infra patch.

## Sources Used

- FlashAttention-3: https://arxiv.org/abs/2407.08608
- PyTorch CUDA Graphs: https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html
- PyTorch regional compilation: https://docs.pytorch.org/tutorials/recipes/regional_compilation.html
- PyTorch SDPA tutorial: https://docs.pytorch.org/tutorials/intermediate/scaled_dot_product_attention_tutorial.html
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
