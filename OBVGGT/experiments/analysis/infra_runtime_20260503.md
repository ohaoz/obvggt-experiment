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
| PyTorch RoPE2D fallback component cache, Bonn smoke | `20260504_043337...` (`4999abd`) vs `20260504_043719...` (`87e056a`) | Bonn 40-frame `5.6036 -> 6.0259 FPS`, `+7.54%`; `cache_max=5020`, `seq_max=6024`, evict calls/hit rate/AbsRel/RMSE/delta unchanged | Passes same-budget smoke gate; next gate is paired Bonn full |
| PyTorch RoPE2D fallback component cache, Bonn full | `20260504_044550...` (`4999abd`) vs `20260504_045003...` (`87e056a`) | Bonn full `5.5147 -> 6.1978 FPS`, `+12.39%`; `cache_max=5020`, `seq_max=6024`, evict calls/hit rate/AbsRel/RMSE/delta unchanged | Passes same-budget Bonn full gate; promote to paired `sintel/bonn/kitti` full-matrix gate |
| PyTorch RoPE2D fallback component cache, full matrix | `20260504_050435...` (`4999abd`) vs `20260504_052145...` (`87e056a`) | FPS: Sintel `+14.04%`, Bonn `+8.21%`, KITTI `+5.56%`; all cache/seq/evict/hit-rate and AbsRel/RMSE/delta unchanged | Accepted as same-cache-budget infra runtime optimization |

## Interpretation

Depth-only head gating is the first clean runtime win for `video_depth`: it skips camera/point/track heads that `prepare_output()` does not consume, without changing cache policy or depth outputs. It should not be reported as an OBCache algorithm improvement. If used in paper tables or main reports, every `video_depth` baseline must be rerun with the same `head_mode=depth_only` task contract.

The 2026-05-04 full-matrix rerun confirms the Bonn-only signal across `sintel/bonn/kitti`: `depth_only` keeps AbsRel/RMSE/delta, cache hit rate, and evict calls identical to ctrl while improving FPS by `+10.3% / +13.1% / +18.9%` and lowering peak allocated memory by `284 / 744 / 298 MB`. Detailed values are in `analysis/tables/depth_only_full_matrix_20260504.csv`.

Forced SDPA backend routing is useful as instrumentation but not as an optimization on this environment. PyTorch default dispatch is already at least as good as forced Flash for the tested 40-frame Bonn setup.

The compiled croco cuRoPE2D kernel is fast in isolation but unsafe in full-model execution in this branch and environment. Keep it behind `OBVGGT_ALLOW_UNSAFE_CUROPE=1` for isolated microbenchmarks only.

The safe PyTorch RoPE2D fallback optimization caches position-dependent cosine/sine embeddings for repeated calls with the same position grid. On `amd_server` with Torch `2.3.1+cu121`, the isolated CUDA event bench improved the fallback path from median `0.4869 ms/call` at `4999abd` to `0.3794 ms/call` at `87e056a`. This is only a kernel-path signal; it must be followed by paired Bonn smoke/full runs before being treated as an end-to-end FPS result.

The first paired Bonn smoke rerun confirms the microbench signal at task level: `87e056a` improves Bonn 40-frame FPS by `+7.54%` over `4999abd` while keeping cache budget, sequence peak, evict calls, cache hit rate, and depth metrics unchanged. This is enough to justify paired Bonn full, but still not enough for a full `sintel/bonn/kitti` conclusion.

The paired Bonn full rerun confirms the same signal on the complete Bonn `video_depth` set: `87e056a` improves FPS by `+12.39%` over `4999abd` with identical `cache_max=5020`, `seq_max=6024`, `evict_calls_total=12600`, cache hit rate, and depth metrics. This is now strong enough to run the full `sintel/bonn/kitti` matrix, but it remains a Bonn-only result until that matrix is complete.

The paired full matrix completes that gate. Relative to `4999abd`, `87e056a` improves `video_depth` FPS by `+14.04%` on Sintel, `+8.21%` on Bonn, and `+5.56%` on KITTI. Cache budget, maximum sequence length, evict calls, cache hit rate, and all depth metrics remain unchanged per dataset. Detailed values are in `analysis/tables/rope_fallback_full_matrix_20260504.csv`.

The phase profiler confirms that the largest model-side time is still inside the aggregator stack. Within that stack, PyTorch RoPE2D fallback and OBCache scoring/bookkeeping are large enough to justify further infra work. The save-depth-maps phase is also large, but it is evaluation IO/output overhead and should be separated from model FPS claims.

## Current Recommendation

1. Treat `depth_only` as an accepted `video_depth` task-runtime candidate under the same OBCache cache budget.
2. Keep SDPA backend logging in all future runs, but do not force Flash by default.
3. Do not use `obcache_p1_no_recent_ctrl_cuda_rope` in quick_run; it is intentionally `runnable=false`.
4. Accept PyTorch RoPE2D fallback component caching as a same-cache-budget infra runtime optimization for `video_depth`.
5. If continuing infra work, prioritize safe RoPE2D replacement or OBCache bookkeeping/allocation optimization over more SDPA backend forcing.
