# Run Record: 20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-03T12:43:29+08:00
- End: 2026-05-03T12:44:06+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_sdpa_flash
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: 5a9681af05e6805ced9cf296b4db898aa3f30762
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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash/bonn_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash/bonn_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 强制 SDPA Flash smoke 在 eligibility guard 后成功完成；`runtime_diagnostics_sample.sdpa.backend_request=flash`，`backend_effective=flash`。
- Bonn 2-frame smoke 指标：`overall_fps=4.303139374215527`，`max_peak_allocated_mb=7507.9482421875`，`kv_cache_tokens_max=1004`，`kv_max_seq_len_seen=2008`。这是短序列可用性检查，不作为最终吞吐结论。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`、`remote_artifacts/result_scale.json`、`remote_artifacts/system_metrics.json`。
