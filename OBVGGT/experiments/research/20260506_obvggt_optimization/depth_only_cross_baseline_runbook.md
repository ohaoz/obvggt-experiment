# Runbook: Cross-Baseline `depth_only` Fairness

## Scope

This runbook defines the next non-algorithm direction after the 2026-05-06
probe smoke rejection. It is allowed because it changes the `video_depth`
task-output contract, not OBCache scoring, eviction, cache budget, or retained
token decisions.

Do not use this as a general OBVGGT algorithm speed claim. Report it only as a
`video_depth` task-runtime comparison where every baseline uses the same
`depth_only` contract.

## Current Code Audit

OBVGGT already supports the contract:

- `OBVGGT/src/eval/video_depth/launch.py` exposes `--head_mode full|depth_only`.
- In `depth_only`, launch passes `inference_output_keys=["depth"]` to
  `loss_of_one_batch`.
- `OBVGGT/src/dust3r/inference.py` forwards `inference_output_keys` into
  `model.inference(..., output_keys=...)`.
- `OBVGGT/src/streamvggt/models/streamvggt.py` uses `output_keys` to run only
  requested heads. The aggregator and OBCache path still run unchanged.

This branch now prepares the same opt-in contract for sibling baseline repos:

- `StreamVGGT/src/eval/video_depth/launch.py` exposes `--head_mode`.
- `XStreamVGGT/src/eval/video_depth/launch.py` exposes `--head_mode` and
  `--max_frames`.
- `InfiniteVGGT/src/eval/video_depth/launch.py` exposes `--head_mode` and
  `--max_frames`.
- Their `src/dust3r/inference.py` files now accept
  `inference_output_keys=None` and forward it to `model.inference(...)`.
- Their `streamvggt.models.streamvggt.StreamVGGT.inference()` methods now
  accept `output_keys=None`; default `None` keeps full-head behavior, while
  `["depth"]` runs only the depth head after the unchanged aggregator/cache
  path.

## Required Adapter/Repo Work

Minimum same-contract patch for each sibling baseline was applied in this
branch:

1. Add `--head_mode full|depth_only` to `src/eval/video_depth/launch.py`.
2. Pass `inference_output_keys=["depth"]` only when `--head_mode depth_only`.
3. Add an optional `inference_output_keys=None` argument to
   `src/dust3r/inference.py`.
4. Add an optional `output_keys=None` argument to the repo-local
   `streamvggt.models.streamvggt.StreamVGGT.inference()`.
5. Gate only the head calls. Do not modify aggregator, cache, attention,
   temporal order, image preprocessing, checkpoint loading, or metrics.
6. Keep full mode behavior as close as possible to current code.

For XStreamVGGT and InfiniteVGGT adapters, dataset filtering was also fixed
before smoke gates:

- `run_xstreamvggt.py` now uses
  `resolve_dataset_filter(VIDEO_DEPTH_DATASETS, args.dataset_filter)`.
- `run_infinitevggt.py` now uses the same resolver for normal `video_depth`
  unless `sequence_length` intentionally selects a long dataset.
- Both adapters pass `dataset_filter` into expected-artifact generation.
- XStreamVGGT and InfiniteVGGT `eval_depth.py` now share the existing
  StreamVGGT prefix-eval alignment behavior, so `--max_frames` smoke outputs
  can be evaluated against longer ground-truth sequences.

## Validation Gates

Local checks before any server run:

```bash
python -m compileall -q \
  StreamVGGT/src/eval/video_depth/launch.py \
  StreamVGGT/src/dust3r/inference.py \
  StreamVGGT/src/streamvggt/models/streamvggt.py \
  XStreamVGGT/src/eval/video_depth/launch.py \
  XStreamVGGT/src/dust3r/inference.py \
  XStreamVGGT/src/streamvggt/models/streamvggt.py \
  InfiniteVGGT/src/eval/video_depth/launch.py \
  InfiniteVGGT/src/dust3r/inference.py \
  InfiniteVGGT/src/streamvggt/models/streamvggt.py
```

Dry-run checks:

```bash
cd OBVGGT/experiments

python scripts/run_streamvggt.py \
  --repo-path ../StreamVGGT \
  --checkpoint ckpt/checkpoints.pth \
  --task video_depth \
  --variant baseline_depth_only \
  --model-name StreamVGGT \
  --output-root /tmp/depth_only_dry \
  --result-tag StreamVGGT_depth_only \
  --dataset-filter bonn \
  --dry-run \
  --head_mode depth_only \
  --max_frames 40 \
  --seq_list balloon2

python scripts/run_xstreamvggt.py \
  --repo-path ../XStreamVGGT \
  --checkpoint ckpt/checkpoints.pth \
  --task video_depth \
  --variant xstream_depth_only \
  --model-name XStreamVGGT \
  --output-root /tmp/depth_only_dry \
  --result-tag XStreamVGGT_depth_only \
  --dataset-filter bonn \
  --dry-run \
  --head_mode depth_only \
  --max_frames 40 \
  --seq_list balloon2

python scripts/run_infinitevggt.py \
  --repo-path ../InfiniteVGGT \
  --checkpoint ckpt/checkpoints.pth \
  --task video_depth \
  --variant infinite_depth_only \
  --model-name InfiniteVGGT \
  --output-root /tmp/depth_only_dry \
  --result-tag InfiniteVGGT_depth_only \
  --dataset-filter bonn \
  --dry-run \
  --head_mode depth_only \
  --max_frames 40 \
  --seq_list balloon2
```

Reject the patch if dry-run output does not show only Bonn for the smoke.

Local validation already run:

- `python -m compileall -q` on all patched launch/inference/model/adapter files.
- Dry-run for StreamVGGT, XStreamVGGT, and InfiniteVGGT with
  `--dataset-filter bonn --head_mode depth_only --max_frames 40 --seq_list balloon2`.
- All three dry-runs expanded to exactly one Bonn launch command plus one
  Bonn `eval_depth.py` command.
- Server runtime smoke with `--max_frames 2 --seq_list balloon2` passed for
  StreamVGGT, XStreamVGGT, and InfiniteVGGT. These runs are code-path checks
  only, not FPS or accuracy conclusions.

Server smoke gate:

- Run ctrl full-head and depth-only on the same branch, same GPU, same Bonn
  sequence, same frame cap.
- Require identical depth metrics within file/float noise.
- For OBVGGT, require unchanged `cache_max`, `seq_max`, evict calls, and hit
  rate between full and depth-only.
- For sibling baselines, require output files and `result_scale.json` to match
  the full-head metric path.

Promotion order:

1. Bonn `balloon2` 40-frame smoke for all four baselines on server.
2. Bonn full only if smoke metrics match.
3. Full `sintel/bonn/kitti` only if Bonn full is clean.

## Reporting Rule

Use two separate tables:

- Full-head cross-baseline table: current canonical model/runtime comparison.
- `video_depth depth_only` table: deployment/task-runtime comparison.

Never mix full-head numbers from one baseline with depth-only numbers from
another baseline.
