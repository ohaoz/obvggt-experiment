# OBVGGT Further Optimization Roadmap

## Bottom Line

Current scope: OBVGGT is an OBCache-based method, and this branch must not
change the core cache algorithm. The next credible work should focus on:

1. Existing same-algorithm config validation (`probe6` / repeated `probe4`).
2. Fair `video_depth` task-runtime comparison using `depth_only` across all baselines.
3. Infra and measurement improvements that do not alter cache decisions.

Do not spend more time rerunning the current `prealloc_kv` implementation. It
is a confirmed negative. Do not treat `score_interval=2` as a same-budget
speedup because it changes effective cache/sequence behavior.

## Immediate Experiment Queue

| Priority | Candidate | Why now | Pass gate |
|---|---|---|---|
| P0 | `best_infra + probe6` | Existing config; no new OBCache policy | Bonn smoke `>+3%`, no cache/seq/quality drift |
| P0 | `best_infra + probe4` confirm | Prior small same-budget signal | Full matrix only if repeated Bonn full survives |
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
2. Create or verify configs only for already-supported probe counts:
   - `obcache_p1_no_recent_ctrl_best_infra_probe6`
   - `obcache_p1_no_recent_ctrl_best_infra_probe4`
3. Run paired Bonn 40-frame smoke:
   - ctrl: current `obcache_p1_no_recent_ctrl` on the same infra branch
   - candidates: probe6/probe4 under the same branch
4. Promote a candidate only if FPS improves by `>3%` and `cache_max`, `seq_max`, and depth metrics match ctrl.
5. If a candidate passes, run Bonn full, then full `sintel/bonn/kitti`.
6. Separately prepare a `depth_only` fairness run plan for StreamVGGT, XStreamVGGT, InfiniteVGGT, and OBVGGT.
7. Keep IO/compile/scoring work in opt-in diagnostics until a paired smoke justifies promotion.

## Report Impact If Successful

- `best_infra + probe6/probe4`: strengthens OBVGGT FPS without changing the method.
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
