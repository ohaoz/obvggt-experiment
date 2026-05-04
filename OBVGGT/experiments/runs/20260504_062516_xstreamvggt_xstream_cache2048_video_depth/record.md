# Run Record: 20260504_062516_xstreamvggt_xstream_cache2048_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-04T06:25:17+08:00
- End: 2026-05-04T06:40:33+08:00
- Exit code: 0

## 1. Experiment
- Variant: xstreamvggt
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: xstreamvggt_xstream_cache2048

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_062516_xstreamvggt_xstream_cache2048_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt`
- Repo path: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/XStreamVGGT`
- Log file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: 6fc9571f3371da224a98b538fccf5a61652f1164
- Adapter: run_xstreamvggt.py
- Expected env: streamvggt

## 4. KV Cache
- Enabled: True
- Config:
```json
{
  "method": "xstream",
  "kv_pool_size": 16,
  "kv_cache_size": 2048,
  "kv_quant_mode": ""
}
```

## 5. Artifacts
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/bonn_xstreamvggt_xstream_cache2048/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/bonn_xstreamvggt_xstream_cache2048/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/kitti_xstreamvggt_xstream_cache2048/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/kitti_xstreamvggt_xstream_cache2048/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/sintel_xstreamvggt_xstream_cache2048/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_062516_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/sintel_xstreamvggt_xstream_cache2048/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Local sync completed on 2026-05-04: mirrored the full run directory (`manifest.json`, `artifacts.json`, `record.md`, `stdout.log`, `command.sh`, `config_snapshot.json`, `env_snapshot.txt`) from `amd_server`.
- Local artifacts synced to `OBVGGT/experiments/analysis/artifacts/20260504_cross_baseline_full_matrix/xstreamvggt/`.
- Local docs rebuilt after sync: `experiments/EXPERIMENTS.md`, `experiments/analysis/SUMMARY.md`, and `experiments/analysis/ALL_RESULTS.md`.
- Top-level docs updated for this same-window 48GB fairness snapshot: `PROJECT_BRIEF.md`, `OBVGGT/experiments/README.md`, and `experiments/analysis/infra_runtime_20260503.md`.
