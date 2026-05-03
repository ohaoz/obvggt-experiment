# Infra Runtime Acceleration Notes - 2026-05-03

## Scope

This note tracks non-OBCache-algorithm acceleration experiments on branch `exp/2026-0503-infra-runtime-accel`.
The intent is to keep cache policy and budget fixed unless explicitly marked as a full-cache control.

## Stable Findings

| Area | Run / Evidence | Result | Decision |
|---|---:|---:|---|
| Default backend probe | `20260503_123103_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth` | Bonn 40-frame `5.9065 FPS`, `8813.6 MB`, RoPE=`pytorch_python`, SDPA request=`pytorch_default_dispatch` | Baseline for infra comparisons |
| Forced SDPA Flash | `20260503_125412_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth` | Bonn 40-frame `5.8144 FPS`, same memory/cache as default | Not a candidate; about `-1.56%` vs default |
| Depth-only heads, OBCache | `20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth` | Bonn 40-frame `6.6313 FPS`, `8560.3 MB`, same quality as full-head | Candidate as video_depth task-runtime optimization |
| Depth-only heads, full matrix | ctrl `20260504_014720_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth` vs depth-only `20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth` | Sintel `+10.3%`, Bonn `+13.1%`, KITTI `+18.9%` FPS; AbsRel/RMSE/delta unchanged; cache hit and evict calls unchanged | Accepted as same-cache-budget video_depth runtime optimization, not an OBCache policy win |
| Depth-only heads, full-cache | `20260503_131047_full_cache_depth_only_video_depth` | Bonn 40-frame `7.0471 FPS`, `13563.5 MB` | Full-cache is faster at 40 frames, but uses much more memory |
| CUDA RoPE2D microbench | isolated inline CUDA event bench | contiguous `0.083 ms` vs PyTorch `0.498 ms`; qkv-view `0.044 ms` vs `0.504 ms` | Kernel promising, but not safe end-to-end |
| CUDA RoPE2D full-model smoke | `20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth` | inference writes `system_metrics.json`, then process exits with `free(): invalid pointer` / SIGABRT | Rejected; config marked non-runnable |
| Phase profiler | `20260504_012022_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth` | Profile-only Bonn 40-frame run, `formal_fps_valid=false`; model `40.68s`, aggregator `33.55s`, RoPE2D `10.57s`, OBCache scoring `8.89s`, heads `6.00s`, save-depth-maps `31.60s` | Profiler works; do not use FPS as formal speed; next infra target should be RoPE or OBCache bookkeeping/allocation |
| PyTorch RoPE2D fallback component cache | server-side CUDA microbench, `4999abd` vs `87e056a` | median `0.4869 -> 0.3794 ms/call` for `[1,16,1004,64]`, about `1.28x` faster; server unittest `test_rope/test_runtime_diagnostics/test_phase_profile` all pass | Safe microbench candidate; requires Bonn smoke/full rerun before any end-to-end FPS claim |

## Interpretation

Depth-only head gating is the first clean runtime win for `video_depth`: it skips camera/point/track heads that `prepare_output()` does not consume, without changing cache policy or depth outputs. It should not be reported as an OBCache algorithm improvement. If used in paper tables or main reports, every `video_depth` baseline must be rerun with the same `head_mode=depth_only` task contract.

The 2026-05-04 full-matrix rerun confirms the Bonn-only signal across `sintel/bonn/kitti`: `depth_only` keeps AbsRel/RMSE/delta, cache hit rate, and evict calls identical to ctrl while improving FPS by `+10.3% / +13.1% / +18.9%` and lowering peak allocated memory by `284 / 744 / 298 MB`. Detailed values are in `analysis/tables/depth_only_full_matrix_20260504.csv`.

Forced SDPA backend routing is useful as instrumentation but not as an optimization on this environment. PyTorch default dispatch is already at least as good as forced Flash for the tested 40-frame Bonn setup.

The compiled croco cuRoPE2D kernel is fast in isolation but unsafe in full-model execution in this branch and environment. Keep it behind `OBVGGT_ALLOW_UNSAFE_CUROPE=1` for isolated microbenchmarks only.

The safe PyTorch RoPE2D fallback optimization caches position-dependent cosine/sine embeddings for repeated calls with the same position grid. On `amd_server` with Torch `2.3.1+cu121`, the isolated CUDA event bench improved the fallback path from median `0.4869 ms/call` at `4999abd` to `0.3794 ms/call` at `87e056a`. This is only a kernel-path signal; it must be followed by paired Bonn smoke/full runs before being treated as an end-to-end FPS result.

The phase profiler confirms that the largest model-side time is still inside the aggregator stack. Within that stack, PyTorch RoPE2D fallback and OBCache scoring/bookkeeping are large enough to justify further infra work. The save-depth-maps phase is also large, but it is evaluation IO/output overhead and should be separated from model FPS claims.

## Current Recommendation

1. Treat `depth_only` as an accepted `video_depth` task-runtime candidate under the same OBCache cache budget.
2. Keep SDPA backend logging in all future runs, but do not force Flash by default.
3. Do not use `obcache_p1_no_recent_ctrl_cuda_rope` in quick_run; it is intentionally `runnable=false`.
4. Treat PyTorch RoPE2D fallback component caching as a safe microbench candidate, then gate it with paired Bonn smoke/full reruns before full matrix.
5. If continuing infra work, prioritize safe RoPE2D replacement or OBCache bookkeeping/allocation optimization over more SDPA backend forcing.
