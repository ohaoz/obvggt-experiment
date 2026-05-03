# Run Record: 20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-03T13:04:33+08:00
- End: 2026-05-03T13:05:10+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_depth_only
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: bb7307d4f3a138746d8424ad80e64329911a4347
- Adapter: run_obvggt.py
- Expected env: obvggt

## 4. KV Cache
- Enabled: True
- Config:
```json
{
  "enable": true,
  "method": "obcvk",
  "p": 1,
  "use_vnorm": true,
  "num_sink_frames": 1,
  "num_recent_frames": 0,
  "num_heavy_frames": 4,
  "probe_mode": true,
  "num_patch_probes": 8
}
```

## 5. Artifacts
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/bonn_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/bonn_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Depth-only head gating 2-frame smoke 成功完成；`head_mode=depth_only` 已写入 `system_metrics.json` 的 per-sequence 记录。
- Bonn 2-frame smoke 指标：`overall_fps=4.68861023587925`，`max_peak_allocated_mb=7496.3876953125`，`kv_evict_calls_total=0`，`kv_cache_hit_rate=0.3333333333333333`。
- 质量指标：`Abs Rel=0.03588450426784576`，`RMSE=0.18818932593307167`，`δ < 1.25=0.9864885144679889`。该短序列 run 只用于可用性验证，不作为最终吞吐结论。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`、`remote_artifacts/result_scale.json`、`remote_artifacts/system_metrics.json`。
