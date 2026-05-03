# Run Record: 20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-03T13:05:29+08:00
- End: 2026-05-03T13:07:08+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_depth_only
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/config_snapshot.json`

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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/bonn_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/bonn_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Depth-only head gating Bonn 40-frame 对照成功完成；`head_mode=depth_only` 已写入 `system_metrics.json` 的 per-sequence 记录。
- 系统指标：`overall_fps=6.63134924614148`，`max_peak_allocated_mb=8560.2978515625`，`max_peak_reserved_mb=9370.0`，`kv_evict_calls_total=4200`，`kv_cache_hit_rate=0.8222222222222222`。
- 质量指标：`Abs Rel=0.05892063733017017`，`RMSE=0.2529923753237279`，`δ < 1.25=0.969246337180353`，与 full-head/forced-Flash 40-frame Bonn 对照一致。
- 对比结论：相对 full-head default 40-frame run `20260503_123103...` 的 `overall_fps=5.90648576397909`，depth-only 为约 `+12.27%`；峰值 allocated 显存从 `8813.56494140625 MB` 降至 `8560.2978515625 MB`。cache 行为一致，因此收益来自跳过 video_depth 未消费的 camera/point/track heads。
- 口径限制：这是 video_depth task-specific runtime gating。若用于论文或主报告，必须对所有 video_depth baseline 使用相同 depth-only head 口径公平重跑，不能作为 OBCache 算法加速单独声称。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`、`remote_artifacts/result_scale.json`、`remote_artifacts/system_metrics.json`。
