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

## Probe Smoke Result

- Prepared a clean checkout on `/mnt/data3/OBVGGT/research_20260506` and used
  the clean branch `exp/2026-0506-obvggt-research-opt`.
- Ran Bonn `balloon2`, 40-frame smoke for:
  - ctrl: `20260506_024906_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth`
  - probe6: `20260506_025001_obcache_p1_no_recent_probe6_joint_s1r0h4_video_depth`
  - probe4: `20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth`
- Gate checker result:
  - probe6 failed: FPS `5.0544 -> 4.3749` (`-13.44%`), cache/seq unchanged,
    depth metrics worse.
  - probe4 failed: FPS `5.0544 -> 4.9659` (`-1.75%`), cache/seq unchanged,
    depth metrics roughly comparable but no speed gain.
- Decision: do not promote probe6/probe4 to Bonn full. This rejects the current
  probe-count follow-up under the clean 2026-05-06 smoke gate.

## Post-Rejection Non-Algorithm Audit

- User constraint reaffirmed: OBVGGT is OBCache-based; do not change the core
  OBCache algorithm.
- Updated project/research docs so current `probe4/probe6` and interval configs
  are not presented as active same-budget FPS candidates.
- Audited cross-baseline `depth_only` feasibility:
  - OBVGGT already supports `--head_mode depth_only` through
    `inference_output_keys=["depth"]`.
  - StreamVGGT/XStreamVGGT/InfiniteVGGT did not expose the same launch,
    inference, or model-output contract before this patch.
  - XStreamVGGT/InfiniteVGGT adapters also lacked normal `video_depth`
    `dataset_filter` support before this patch.
- Added `depth_only_cross_baseline_runbook.md` and
  `eval_io_wallclock_notes.md` as the next allowed work items.
- Audited OBCache scoring equivalence boundary:
  - scoring builds `qk_probe`, `A_probe`, and `O_probe` in `attention.py`;
  - `StreamOBCScoreTracker.evict()` selects retained tokens with
    `torch.topk(...).sort().values`;
  - any scoring implementation change must prove exact `keep_topk_idx`
    equality before it can be called non-algorithmic.
- Added `scoring_microbench_equivalence_plan.md`.

## Depth-Only Cross-Baseline Prep Patch

- Added opt-in `--head_mode full|depth_only` support to StreamVGGT,
  XStreamVGGT, and InfiniteVGGT `video_depth` launchers.
- Added optional `inference_output_keys` forwarding in the three sibling
  `dust3r/inference.py` files.
- Added optional `output_keys` head gating in the three sibling
  `streamvggt.models.streamvggt.StreamVGGT.inference()` methods.
- Default `output_keys=None` preserves full-head behavior.
- The aggregator, attention, cache, scoring, eviction, checkpoint loading,
  preprocessing, and metrics paths were not changed.
- Fixed XStreamVGGT/InfiniteVGGT `video_depth` adapters so `--dataset-filter`
  works for Bonn smoke runs and expected artifacts.
- Validation:
  - `python -m compileall -q` on all patched launch/inference/model/adapter
    files passed.
  - StreamVGGT/XStreamVGGT/InfiniteVGGT dry-runs with
    `--dataset-filter bonn --head_mode depth_only --max_frames 40 --seq_list balloon2`
    each expanded to exactly one Bonn launch plus one Bonn metric command.

## Server-Side Validation Of Depth-Only Prep

- Pushed local commit `84ba28c`, but amd_server GitHub fetch failed twice with
  transport errors:
  - `Encountered end of file`
  - `Empty reply from server`
- To avoid destructive git operations on the server checkout, copied only the
  patched source/adapter files into the clean
  `/mnt/data3/OBVGGT/research_20260506` checkout.
- Server validation under `conda run -n obvggt` passed:
  - `python -m compileall -q` on patched StreamVGGT/XStreamVGGT/InfiniteVGGT
    launch, inference, model files plus adapter scripts.
  - `run_streamvggt.py --dry-run` with Bonn depth-only smoke args.
  - `run_xstreamvggt.py --dry-run` with Bonn depth-only smoke args.
  - `run_infinitevggt.py --dry-run` with Bonn depth-only smoke args.
- Each server dry-run expanded to one Bonn launch command containing
  `--head_mode depth_only --max_frames 40 --seq_list balloon2` plus one Bonn
  `eval_depth.py` command.
