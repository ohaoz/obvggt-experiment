# Run Record: 20260504_011534_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth

## 0. Status
- Status: FAILED
- Start: 2026-05-04T01:15:36+08:00
- End: 2026-05-04T01:15:41+08:00
- Exit code: 1

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_phase_profile
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_011534_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_011534_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_phase_profile`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_011534_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_011534_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel-clean/OBVGGT/experiments/runs/20260504_011534_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel-clean
- Git commit: bdb186202c9845d46f876c9d24dee58f2bd2d260
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
- 暂无已发现产物
- 缺失必需产物:
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_011534_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_phase_profile/bonn_obcache_p1_no_recent_ctrl_phase_profile_joint_s1r0h4/result_scale.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。
- Failure cause: `--dry-run` was passed through `quick_run.sh` to `launch.py`; `quick_run.sh` only uses adapter dry-run internally and does not expose a top-level dry-run flag.
- Local docs synced after run: `EXPERIMENTS.md` / `analysis/SUMMARY.md` / `analysis/ALL_RESULTS.md` rebuilt. `AGENTS.md`, `PROJECT_BRIEF.md`, and `experiments/README.md` checked; no update needed because this was a failed launch attempt and did not change project status.
