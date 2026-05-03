# Run Record: 20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-04T01:30:36+08:00
- End: 2026-05-04T01:46:33+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_depth_only
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel-clean
- Git commit: 39de00fcad9791db44a2c816fede8317bfc20de4
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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/bonn_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/bonn_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/kitti_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/kitti_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/sintel_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_013035_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_depth_only/sintel_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Full `sintel/bonn/kitti` depth-only run for the same OBCache policy and cache budget as `obcache_p1_no_recent_ctrl`.
- Paired ctrl run: `20260504_014720_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth`.
- Local docs synced after run: `EXPERIMENTS.md` / `analysis/SUMMARY.md` / `analysis/ALL_RESULTS.md` rebuilt. `analysis/infra_runtime_20260503.md` and `analysis/tables/depth_only_full_matrix_20260504.csv` updated. `AGENTS.md`, `PROJECT_BRIEF.md`, and `experiments/README.md` checked; no update needed because this is an experimental branch result, not the project default state.
