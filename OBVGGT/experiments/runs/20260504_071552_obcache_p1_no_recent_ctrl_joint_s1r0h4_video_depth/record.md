# Run Record: 20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-04T07:15:52+08:00
- End: 2026-05-04T07:32:20+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl`
- Repo path: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT`
- Log file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/OBVGGT/experiments/runs/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: 6fc9571f3371da224a98b538fccf5a61652f1164
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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/kitti_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/kitti_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/sintel_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_071552_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/sintel_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Local sync completed on 2026-05-04: mirrored the full run directory (`manifest.json`, `artifacts.json`, `record.md`, `stdout.log`, `command.sh`, `config_snapshot.json`, `env_snapshot.txt`) from `amd_server`.
- Local artifacts synced to `OBVGGT/experiments/analysis/artifacts/20260504_cross_baseline_full_matrix/obvggt_best_6fc9571/`.
- Local docs rebuilt after sync: `experiments/EXPERIMENTS.md`, `experiments/analysis/SUMMARY.md`, and `experiments/analysis/ALL_RESULTS.md`.
- Top-level docs updated for this same-window 48GB fairness snapshot: `PROJECT_BRIEF.md`, `OBVGGT/experiments/README.md`, and `experiments/analysis/infra_runtime_20260503.md`.
