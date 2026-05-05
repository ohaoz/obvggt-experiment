# Non-Algorithm Optimization Validation Protocol

## Purpose

This note converts the current research pass into executable gates. It keeps
the OBVGGT/OBCache algorithm fixed and only permits changes that preserve cache
policy, cache budget, and token-retention decisions.

## Code Evidence

### Formal FPS is model-only

`OBVGGT/src/eval/video_depth/launch.py` synchronizes and times only
`loss_of_one_batch()`:

- Lines `264-282`: reset CUDA peak stats, synchronize, run model, synchronize.
- Lines `285-304`: compute FPS, latency, peak memory from that model-only window.
- Lines `326-337`: `prepare_output()` and `save_depth_maps()` happen after the
  FPS window and are phase-profiled separately.
- Lines `423-424`: phase-profile runs are explicitly marked
  `formal_fps_valid=false`.

Consequence: IO/colorization changes can reduce wall-clock experiment time, but
must not be reported as strict model FPS improvements.

### Depth-map saving is heavy but outside formal FPS

`OBVGGT/src/eval/video_depth/utils.py` lines `53-86` show the save path:

- Stack all depth maps.
- Colorize depth with colorbar.
- Optionally colorize confidence with colorbar.
- Write PNG for every frame.
- Re-open every PNG with `PIL.Image.open`.
- Write `.npy` for every frame.

Consequence: a fast-output mode is valid only as an eval-output/wall-clock
optimization. It must keep metric inputs intact or be isolated from metric runs.

`OBVGGT/src/eval/video_depth/eval_depth.py` uses `frame*.npy` predictions for
Sintel, Bonn, and KITTI metrics:

- Sintel: lines `110-112` glob `frame_*.npy`; lines `164-172` load with `np.load`.
- Bonn: lines `256-258` glob `frame*.npy`; lines `276-284` load with `np.load`.
- KITTI: lines `359-360` glob `frame_*.npy`; lines `377-384` load with `np.load`.

Consequence: metric-preserving IO optimization may skip or defer PNG/colorbar
visualization only if it still writes identical `.npy` depth arrays.

### OBCache scoring is measurable but semantically sensitive

`OBVGGT/src/streamvggt/layers/attention.py` lines `200-235` show the scoring
path:

- Select cached probe indices.
- Compute `q_probe.float() @ state.k.float().T`.
- Apply float32 softmax.
- Compute `A_probe @ state.v.float()`.
- Update the existing tracker and evict.

Consequence: precision/layout changes are not automatically safe. A scoring
implementation experiment must first prove retained-index equivalence or it
becomes an algorithm change.

### Backend diagnostics had a local instrumentation bug

`runtime_diagnostics._safe_call()` was intended to query PyTorch SDPA backend
flags. Before this pass it returned `None` for all existing methods because the
call/exception block was unreachable. This has been fixed and covered by
`test_runtime_diagnostics`.

Consequence: prior forced-backend FPS evidence remains valid, but future backend
preflight logs will be more informative.

## Allowed Candidate Gates

### Gate A: Existing probe configs

Allowed variants:

- `obcache_p1_no_recent_probe6`
- `obcache_p1_no_recent_probe4`
- ctrl: `obcache_p1_no_recent_ctrl_backend_probe` or matching
  `obcache_p1_no_recent_ctrl`

Why allowed: these configs already exist and keep `p=1`, `method=obcvk`,
`use_vnorm=true`, `sink=1`, `recent=0`, `heavy=4`. They only vary the number of
patch probes used by the existing OBCache scoring path.

Promotion gate:

- Paired Bonn 40-frame smoke first.
- FPS improvement must be `>3%` against the same-branch ctrl.
- `cache_max` and `seq_max` must match ctrl.
- `kv_evict_calls_total`, hit rate, and appended/reused token totals must not
  show budget drift.
- AbsRel/RMSE/delta must remain within run noise.
- Only after passing smoke: Bonn full, then full `sintel/bonn/kitti`.

Reject immediately if the gain is below noise or cache/sequence budget drifts.

Server command template:

```bash
cd $STREAMVGGT_CODE/experiments
bash quick_run.sh obcache_p1_no_recent_ctrl_backend_probe video_depth --dataset-filter bonn --seq_list balloon2 --max_frames 40
bash quick_run.sh obcache_p1_no_recent_probe6 video_depth --dataset-filter bonn --seq_list balloon2 --max_frames 40
bash quick_run.sh obcache_p1_no_recent_probe4 video_depth --dataset-filter bonn --seq_list balloon2 --max_frames 40
```

`quick_run.sh` writes `env_snapshot.txt`, `command.sh`, `manifest.json`, and
`record.md`; `run_obvggt.py` expands `video_depth` into `launch.py` plus
`eval_depth.py`, so the smoke gate covers both runtime and depth metrics.
Local dry-run validation confirmed this command shape expands to
`launch.py --eval_dataset bonn --seq_list balloon2 --max_frames 40` followed by
`eval_depth.py --eval_dataset bonn --align scale`.

### Gate B: Depth-only fairness table

Allowed because `head_mode=depth_only` changes the `video_depth` output contract,
not OBCache retention.

Promotion gate:

- Apply the same depth-only contract to every compared `video_depth` baseline.
- Report it separately from full-head FPS.
- Require identical depth metrics and unchanged cache stats for OBVGGT.
- Do not use it for `monodepth` / `mv_recon` claims.

Server command shape for OBVGGT:

```bash
cd $STREAMVGGT_CODE/experiments
bash quick_run.sh obcache_p1_no_recent_ctrl_backend_probe video_depth --head_mode depth_only
```

Other baselines need equivalent task-output gating before they can enter the
same table. If an adapter cannot express depth-only without changing model
internals, exclude it from the depth-only fairness table rather than mixing
contracts.

Adapter audit:

- `run_obvggt.py` and `run_streamvggt.py` both use `resolve_dataset_filter()`
  for `video_depth`, so smoke/full subset selection is supported.
- `run_xstreamvggt.py` and `run_infinitevggt.py` currently iterate their full
  `VIDEO_DEPTH_DATASETS` list and do not consume `args.dataset_filter` for
  `video_depth`.
- All adapters forward unknown extra args into their target `launch.py`, but
  `--head_mode depth_only` is only proven for this OBVGGT branch's
  `eval/video_depth/launch.py`.

Consequence: before a cross-baseline depth-only table, first dry-run and, if
needed, patch the XStreamVGGT/InfiniteVGGT adapters or target repos so they
support the same dataset filter and the same output contract. Otherwise use the
existing full-head cross-baseline table instead.

### Gate C: Eval IO wall-clock fast mode

Allowed only if labeled as experiment-throughput or output-mode work.

Promotion gate:

- Preserve metric-producing `.npy` outputs for metric runs.
- Treat PNG/colorbar/confidence visualization as optional wall-clock output.
- Keep formal model FPS unchanged and clearly separated.
- Add wall-clock fields or phase summaries rather than replacing FPS.
- Verify that `eval_depth.py` still consumes the expected files for the selected mode.

### Gate D: CUDA graph / regional compile feasibility

Allowed only as opt-in infra research.

Promotion gate:

- Microbench first, no default behavior change.
- Record compile/capture cold start separately from steady-state runtime.
- Disable if graph breaks, shape recompilations, or dynamic cache updates erase
  the gain.
- Promote only after paired Bonn smoke with unchanged metrics and cache stats.

Official PyTorch constraints that matter:

- `torch.compile` can graph-break on hard-to-trace Python and may recompile on
  guard failures.
- Regional compilation is useful for repeated regions and PyTorch 2.5+; it is
  not automatically faster than eager for every model.
- AOT compile features are experimental and should not be a default path here.

### Gate E: Scoring implementation microbench

Allowed only as diagnostics unless decisions match.

Promotion gate:

- Capture q/k/v shape distributions from an existing profile run or synthetic
  tensors matching `[B,H,Q,D]` and `[B,H,L,D]`.
- Compare wall time for layout/contiguity variants first.
- If testing lower precision, compare retained-index overlap and score order.
- Any variant that changes retained indices is out of current scope unless the
  user explicitly approves an algorithm branch.

## Current Ranking

1. P0: paired `probe6` smoke under best infra. It is the smallest same-algorithm
   experiment that can plausibly add FPS.
2. P0: depth-only cross-baseline fairness plan. It converts an accepted
   task-runtime win into a fair table.
3. P1: IO wall-clock split. It reduces server time but is not model FPS.
4. P1: compile/CUDA graph feasibility. High uncertainty due dynamic cache and
   Python control flow.
5. P1: scoring microbench. Useful for diagnosis, but promotion is hard because
   keep decisions must remain unchanged.
6. P2: backend logging. Low-risk support work; not an optimization by itself.

## Existing Evidence Check

Local `OBVGGT/experiments/analysis/tables/` currently contains full evidence
for RoPE fallback, depth-only, cross-baseline full-head, and prealloc-KV
rejection. It does not contain a dedicated probe summary CSV for `probe4` or
`probe6`, so those remain unverified next experiments in this branch rather
than accepted conclusions.

Relevant synchronized tables:

- `rope_fallback_full_matrix_20260504.csv`: accepted same-cache-budget infra
  improvement.
- `depth_only_full_matrix_20260504.csv`: accepted `video_depth` task-runtime
  result, not a general OBCache algorithm improvement.
- `cross_baseline_video_depth_48gb_20260504.csv`: full-head fairness snapshot
  against StreamVGGT/XStreamVGGT/InfiniteVGGT.
- `prealloc_kv_bonn_smoke_20260504.csv`: rejected current preallocation attempt.

## Explicit Non-Goals

- No layer-adaptive budget.
- No query-aware page/probe selection.
- No new OBCache scoring or eviction policy.
- No token pruning/merging.
- No runtime KV quantization.
- No `score_interval=2` same-budget claim.

## Source Notes

- PyTorch SDPA backend selection is controlled through `sdpa_kernel` and
  `SDPBackend`: https://docs.pytorch.org/docs/2.12/generated/torch.nn.attention.sdpa_kernel.html
- PyTorch SDPA tutorial discusses backend forcing and benchmarking:
  https://docs.pytorch.org/tutorials/intermediate/scaled_dot_product_attention_tutorial.html
- PyTorch regional compilation targets repeated regions and PyTorch 2.5+:
  https://docs.pytorch.org/tutorials/recipes/regional_compilation.html
- PyTorch `torch.compile` docs note graph breaks and guard-failure recompiles:
  https://docs.pytorch.org/docs/stable/generated/torch.compile.html
