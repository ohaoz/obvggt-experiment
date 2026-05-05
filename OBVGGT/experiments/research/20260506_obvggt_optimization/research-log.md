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
3. Keep infra/microbench work limited to paths that do not change OBCache retention decisions.

## Scope Correction After User Constraint

User clarified: OBVGGT is based on OBCache and the core algorithm must not be
changed. The research state and human roadmap were updated accordingly:

- Layer-adaptive budgets moved out of the current execution queue.
- Query-aware selection moved out of the current execution queue.
- Token pruning/merging and runtime KV quantization moved out of scope.
- Current work is limited to existing configs, backend/runtime infra, profiling,
  eval wall-clock separation, and diagnostics that preserve keep decisions.

## Guardrails

- Do not report `score_interval=2` as strict same-budget speedup.
- Do not rerun `prealloc_kv` as-is; it is already a negative result.
- Do not claim `depth_only` as a general OBVGGT algorithm improvement; it is a `video_depth` task contract.
- Do not adopt low-bit KV quantization until an offline attention-logit fidelity harness exists.
- Do not implement algorithmic variants without explicit approval.

## Second Pass: Non-Algorithm Protocol

- Added `non_algorithm_validation_protocol.md` to map each allowed direction to
  concrete code evidence, promotion gates, and rejection criteria.
- Confirmed `video_depth` formal FPS is model-only; depth-map saving is outside
  the timed model window and must be reported as wall-clock/output-mode work.
- Confirmed OBCache scoring is a measurable hot path, but implementation changes
  must preserve retained-index decisions before any end-to-end promotion.
- Found and fixed a runtime diagnostics instrumentation bug: `_safe_call()`
  returned `None` for all backend flag methods because its call block was
  unreachable. Added unit-test coverage.

## Server Preflight Attempt

- `ssh amd_server` and SSH-config direct commands routed to a timed-out
  `100.125.15.86:22`; bypassed local SSH config with
  `ssh -F NUL -o ProxyCommand=none -p 2222 szw@192.168.166.137`.
- `amd_server` was reachable through direct port `2222`.
- Preflight did not satisfy run conditions:
  - GPU 1 and GPU 3 were busy; GPU 0 and GPU 2 were idle.
  - `/mnt/data5` was at `97%` usage with about `149G` available.
  - `/mnt/data5/OBVGGT/code/OBVGGT` was on branch `main` with many dirty and
    untracked files, not the clean research branch.
- Decision: do not start the probe smoke in that remote directory. Use the
  runbook only after preparing a clean branch/worktree on a safe disk or after
  confirming an existing clean server checkout.
