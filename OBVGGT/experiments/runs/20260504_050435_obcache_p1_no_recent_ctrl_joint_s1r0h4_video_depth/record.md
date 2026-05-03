# Run Record: 20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-04T05:04:35+08:00
- End: 2026-05-04T05:21:20+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl`
- Repo path: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT`
- Log file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/rope-fullmatrix-before-4999abd/rope-fullmatrix-before-4999abd.partial/OBVGGT/experiments/runs/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/config_snapshot.json`

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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/kitti_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/kitti_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/sintel_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/sintel_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Local sync completed: `manifest.json`, `artifacts.json`, and `record.md` copied to local mirror under `OBVGGT/experiments/runs/20260504_050435_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/`.
- Local artifacts synced: `system_metrics.json` and `result_scale.json` for `sintel`, `bonn`, and `kitti` copied to `OBVGGT/experiments/analysis/artifacts/20260504_rope_fallback_full_matrix/before/`.
- Documentation sync: rebuilt generated experiment docs locally after syncing this run.
- Top-level docs checked: no root `AGENTS.md`/`agents.md` file exists in this worktree, so the session-provided SOP was used as the operative AGENTS instruction; `PROJECT_BRIEF.md` and `OBVGGT/experiments/README.md` need no update because this is an infra-branch candidate result, with final conclusion tracked in `experiments/analysis/infra_runtime_20260503.md`.
