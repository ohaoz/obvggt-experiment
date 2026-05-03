# Run Record: 20260503_131047_full_cache_depth_only_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-03T13:10:48+08:00
- End: 2026-05-03T13:12:25+08:00
- Exit code: 0

## 1. Experiment
- Variant: full_cache_depth_only
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: full_cache_depth_only

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131047_full_cache_depth_only_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_131047_full_cache_depth_only_video_depth/video_depth/full_cache_depth_only`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131047_full_cache_depth_only_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131047_full_cache_depth_only_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131047_full_cache_depth_only_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: e4466545585ff63001e7637777699fc7fbf08488
- Adapter: run_obvggt.py
- Expected env: obvggt

## 4. KV Cache
- Enabled: False
- Config:
```json
{}
```

## 5. Artifacts
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_131047_full_cache_depth_only_video_depth/video_depth/full_cache_depth_only/bonn_full_cache_depth_only/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_131047_full_cache_depth_only_video_depth/video_depth/full_cache_depth_only/bonn_full_cache_depth_only/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Full-cache depth-only Bonn 40-frame 控制组成功完成；`head_mode=depth_only` 已写入 `system_metrics.json` 的 per-sequence 记录。
- 系统指标：`overall_fps=7.0471369138544`，`max_peak_allocated_mb=13563.53515625`，`max_peak_reserved_mb=23502.0`，`kv_evict_calls_total=0`，`kv_cache_hit_rate=0.0`。
- 质量指标：`Abs Rel=0.05913396617005341`，`RMSE=0.24564115372646242`，`δ < 1.25=0.9644934102980456`。
- 对比结论：相对 OBCache depth-only 40-frame run `20260503_130529...` 的 `overall_fps=6.63134924614148`，full-cache depth-only 速度约快 `6.27%`；但 peak allocated 显存从 `13563.53515625 MB` 降到 `8560.2978515625 MB`，OBCache depth-only 约省 `36.89%`。因此 depth-only 口径下，OBCache 的主价值是显存约束和长序列可运行性，不是 40-frame Bonn 的绝对 FPS。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`、`remote_artifacts/result_scale.json`、`remote_artifacts/system_metrics.json`。
