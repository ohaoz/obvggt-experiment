# Run Record: 20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-04T06:59:04+08:00
- End: 2026-05-04T07:15:36+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl`
- Repo path: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT`
- Log file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: HEAD
- Git commit: 4999abd24a5555c64f8690e307862117be2a8c1e
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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/kitti_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/kitti_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/sintel_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_065904_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/sintel_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Local sync completed on 2026-05-04: mirrored the full run directory (`manifest.json`, `artifacts.json`, `record.md`, `stdout.log`, `command.sh`, `config_snapshot.json`, `env_snapshot.txt`) from `amd_server`.
- Local artifacts synced to `OBVGGT/experiments/analysis/artifacts/20260504_cross_baseline_full_matrix/obvggt_ctrl_4999abd/`.
- Local docs rebuilt after sync: `experiments/EXPERIMENTS.md`, `experiments/analysis/SUMMARY.md`, and `experiments/analysis/ALL_RESULTS.md`.
- Top-level docs updated for this same-window 48GB fairness snapshot: `PROJECT_BRIEF.md`, `OBVGGT/experiments/README.md`, and `experiments/analysis/infra_runtime_20260503.md`.
