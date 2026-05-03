# Run Record: 20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-03T12:45:16+08:00
- End: 2026-05-03T12:45:54+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_sdpa_math
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_math`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth/config_snapshot.json`

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
- `result_scale.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_math/bonn_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_math/bonn_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 强制 SDPA math smoke 成功完成；`runtime_diagnostics_sample.sdpa.backend_request=math`，`backend_effective=math`。
- Bonn 2-frame smoke 指标：`overall_fps=3.8853920837681093`，`max_peak_allocated_mb=7517.04736328125`，`kv_cache_tokens_max=1004`，`kv_max_seq_len_seen=2008`。该 run 只作为非 fused 下界和诊断对照，不作为候选优化。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`、`remote_artifacts/result_scale.json`、`remote_artifacts/system_metrics.json`。
