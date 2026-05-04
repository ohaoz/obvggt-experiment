# Run Record: 20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth

## 0. Status
- Status: FAILED
- Start: 2026-05-04T06:06:05+08:00
- End: 2026-05-04T06:06:10+08:00
- Exit code: 1

## 1. Experiment
- Variant: infinitevggt
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: infinitevggt_rolling_memory_budget1200000

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth/video_depth/infinitevggt`
- Repo path: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/InfiniteVGGT`
- Log file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: 6fc9571f3371da224a98b538fccf5a61652f1164
- Adapter: run_infinitevggt.py
- Expected env: infinitevggt

## 4. KV Cache
- Enabled: True
- Config:
```json
{
  "method": "rolling_memory",
  "total_budget": 1200000,
  "max_frames": 300
}
```

## 5. Artifacts
- 暂无已发现产物
- 缺失必需产物:
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth/video_depth/infinitevggt/sintel_infinitevggt_rolling_memory_budget1200000/result_scale.json`
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth/video_depth/infinitevggt/bonn_infinitevggt_rolling_memory_budget1200000/result_scale.json`
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060605_infinitevggt_rolling_memory_budget1200000_video_depth/video_depth/infinitevggt/kitti_infinitevggt_rolling_memory_budget1200000/result_scale.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。
- Local sync completed on 2026-05-04: mirrored the full run directory (`manifest.json`, `artifacts.json`, `record.md`, `stdout.log`, `command.sh`, `config_snapshot.json`, `env_snapshot.txt`) from `amd_server`.
- No local metric artifacts were synced because the run failed before writing valid `result_scale.json` / `system_metrics.json`.
- Failure cause confirmed from `stdout.log`: the native `InfiniteVGGT` `launch.py` rejects `--max_frames 2` (`error: unrecognized arguments: --max_frames 2`).
- This preflight is superseded by the successful full rerun `20260504_064047_infinitevggt_rolling_memory_budget1200000_video_depth`.
- Local docs rebuilt after sync, and the top-level branch docs were updated to record this as a failed preflight rather than throughput evidence.
