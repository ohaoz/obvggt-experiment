# Run Record: 20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth

## 0. Status
- Status: FAILED
- Start: 2026-05-03T10:58:45+08:00
- End: 2026-05-03T10:59:15+08:00
- Exit code: 1

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/fps_verify_20260503/eval_results/by_run/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-fps-verify
- Git commit: 06cd388e7491240b67b32515ce808ba9597500dc
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
  - `/mnt/data3/OBVGGT/fps_verify_20260503/eval_results/by_run/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4/result_scale.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Post-run sync completed on 2026-05-03: remote `manifest.json` / `artifacts.json` / `record.md` were mirrored locally, `EXPERIMENTS.md` / `analysis/SUMMARY.md` / `analysis/ALL_RESULTS.md` were rebuilt, and `experiments/README.md` / `AGENTS.md` were checked with no branch-level status update required because this was a failed setup attempt before the Bonn verification runs.
- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。
