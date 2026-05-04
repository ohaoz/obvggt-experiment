# Run Record: 20260504_060635_baseline_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-04T06:06:35+08:00
- End: 2026-05-04T06:25:02+08:00
- Exit code: 0

## 1. Experiment
- Variant: baseline
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: baseline

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060635_baseline_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060635_baseline_video_depth/video_depth/baseline`
- Repo path: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/StreamVGGT`
- Log file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060635_baseline_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060635_baseline_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_060635_baseline_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: 6fc9571f3371da224a98b538fccf5a61652f1164
- Adapter: run_streamvggt.py
- Expected env: streamvggt

## 4. KV Cache
- Enabled: False
- Config:
```json
{}
```

## 5. Artifacts
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060635_baseline_video_depth/video_depth/baseline/bonn_baseline/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060635_baseline_video_depth/video_depth/baseline/bonn_baseline/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060635_baseline_video_depth/video_depth/baseline/kitti_baseline/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060635_baseline_video_depth/video_depth/baseline/kitti_baseline/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060635_baseline_video_depth/video_depth/baseline/sintel_baseline/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060635_baseline_video_depth/video_depth/baseline/sintel_baseline/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Local sync completed on 2026-05-04: mirrored the full run directory (`manifest.json`, `artifacts.json`, `record.md`, `stdout.log`, `command.sh`, `config_snapshot.json`, `env_snapshot.txt`) from `amd_server`.
- Local artifacts synced to `OBVGGT/experiments/analysis/artifacts/20260504_cross_baseline_full_matrix/streamvggt_baseline/`.
- Local docs rebuilt after sync: `experiments/EXPERIMENTS.md`, `experiments/analysis/SUMMARY.md`, and `experiments/analysis/ALL_RESULTS.md`.
- Top-level docs updated for this same-window 48GB fairness snapshot: `PROJECT_BRIEF.md`, `OBVGGT/experiments/README.md`, and `experiments/analysis/infra_runtime_20260503.md`.
