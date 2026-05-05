# OBVGGT Optimization Research Log - 2026-05-06

## Bootstrap

- Created branch/worktree `exp/2026-0506-obvggt-research-opt` from `exp/2026-0503-infra-runtime-accel` at `b45bc4f`.
- Main worktree `G:\vggt` is dirty; all research artifacts are written only in the new worktree.
- Read `PROJECT_BRIEF.md` and `OBVGGT/experiments/analysis/infra_runtime_20260503.md`.
- Reused completed evidence:
  - RoPE fallback component cache accepted with full `sintel/bonn/kitti` paired matrix.
  - `video_depth` depth-only accepted as task-runtime optimization.
  - Current `prealloc_kv` implementation rejected by paired Bonn smoke.
- Web research used primary sources where possible:
  - PyTorch FlexAttention/FlexDecoding official blog and docs.
  - arXiv/OpenReview/NeurIPS/ICLR pages for FlashAttention-3, SnapKV, PyramidKV, Quest, MInference, ToMe, FastV, StreamingLLM, H2O, PolarQuant/TurboQuant.

## Initial Decision

The next best action is not another generic preallocation attempt. The highest-value near-term experiments are:

1. Pair `best_infra` with existing same-budget `probe6`, because `probe4` had a small positive signal and `probe6` may be a safer speed/quality compromise.
2. Apply `depth_only` fairly to all video_depth baselines if the goal is a stronger cross-baseline table.
3. Start a separate P1 protocol for layer-adaptive budgets and query-aware selection, because recent KV-cache literature points to per-layer/per-head/query-aware allocation rather than uniform token budgets.

## Guardrails

- Do not report `score_interval=2` as strict same-budget speedup.
- Do not rerun `prealloc_kv` as-is; it is already a negative result.
- Do not claim `depth_only` as a general OBVGGT algorithm improvement; it is a `video_depth` task contract.
- Do not adopt low-bit KV quantization until an offline attention-logit fidelity harness exists.
