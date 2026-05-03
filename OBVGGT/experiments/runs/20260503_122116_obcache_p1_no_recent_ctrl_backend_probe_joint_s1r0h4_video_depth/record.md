# Run Record: 20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-03T12:21:16+08:00
- End: 2026-05-03T12:21:51+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_backend_probe
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_backend_probe`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: b150c89487d93dd917c90e7d9247b59d4820e2a0
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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_backend_probe/bonn_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_backend_probe/bonn_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- Post-run sync completed on 2026-05-03: synced `manifest.json`, `artifacts.json`, `record.md`, `remote_artifacts/result_scale.json`, and `remote_artifacts/system_metrics.json` back to the local infra worktree.
- Local generated docs were rebuilt with `OBVGGT/experiments/scripts/render_experiment_docs.py --experiments-root OBVGGT/experiments`, updating `EXPERIMENTS.md`, `analysis/SUMMARY.md`, and `analysis/ALL_RESULTS.md`.
- `PROJECT_BRIEF.md`, `agents.md`, and `OBVGGT/experiments/README.md` were checked for required status changes. No top-level status update is needed yet because this was a 2-frame Bonn backend instrumentation smoke, not a new full benchmark conclusion.
- Runtime diagnostics confirmed `rope2d.backend=pytorch_python`; stdout also reported the slow PyTorch RoPE2D fallback warning. SDPA metadata recorded PyTorch default dispatch with fused-candidate dtype/shape.
