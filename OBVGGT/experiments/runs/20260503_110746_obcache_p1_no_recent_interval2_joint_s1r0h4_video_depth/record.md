# Run Record: 20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-03T11:07:46+08:00
- End: 2026-05-03T11:11:17+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_interval2
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_interval2_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/fps_verify_20260503/eval_results/by_run/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_interval2`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify/experiments/runs/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-fps-verify
- Git commit: ae61fade8d7398f946e6b2d4ce1e11385d07cdcd
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
  "num_patch_probes": 8,
  "score_interval": 2
}
```

## 5. Artifacts
- `result_scale.json`: `/mnt/data3/OBVGGT/fps_verify_20260503/eval_results/by_run/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_interval2/bonn_obcache_p1_no_recent_interval2_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/fps_verify_20260503/eval_results/by_run/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_interval2/bonn_obcache_p1_no_recent_interval2_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Post-run sync completed on 2026-05-03: remote `manifest.json` / `artifacts.json` / `record.md` plus `result_scale.json` / `system_metrics.json` were mirrored locally, `EXPERIMENTS.md` / `analysis/SUMMARY.md` / `analysis/ALL_RESULTS.md` were rebuilt, and `experiments/README.md` / `AGENTS.md` were checked with no top-level status update required because this was a branch-local Bonn-only speed verification, not a finalized full benchmark.
