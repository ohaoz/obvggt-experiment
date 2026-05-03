# Run Record: 20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-04T04:50:03+08:00
- End: 2026-05-04T04:53:40+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-bundle-v2/OBVGGT/experiments/runs/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl`
- Repo path: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-bundle-v2/OBVGGT`
- Log file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-bundle-v2/OBVGGT/experiments/runs/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-bundle-v2/OBVGGT/experiments/runs/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-bundle-v2/OBVGGT/experiments/runs/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: HEAD
- Git commit: 87e056a926815d67210d09c9d8d213cc89088d1a
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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Local sync completed: `manifest.json`, `artifacts.json`, and `record.md` copied to local mirror under `OBVGGT/experiments/runs/20260504_045003_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/`.
- Local artifacts synced: `system_metrics.json` and `result_scale.json` copied to `OBVGGT/experiments/analysis/artifacts/20260504_rope_fallback_bonn_full/after/`.
- Documentation sync: rebuilt generated experiment docs locally after syncing this run.
- Top-level docs checked: no root `AGENTS.md`/`agents.md` file exists in this worktree, so the session-provided SOP was used as the operative AGENTS instruction; `PROJECT_BRIEF.md` and `OBVGGT/experiments/README.md` need no update because this is a Bonn-only candidate gate, not a project-wide default or paper-result status change.
