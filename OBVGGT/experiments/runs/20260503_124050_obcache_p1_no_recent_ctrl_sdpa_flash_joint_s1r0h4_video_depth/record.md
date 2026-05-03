# Run Record: 20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth

## 0. Status
- Status: FAILED
- Start: 2026-05-03T12:40:51+08:00
- End: 2026-05-03T12:41:20+08:00
- Exit code: 1

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_sdpa_flash
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: f625fd26eea18818db06313c65dad3971483ec7b
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
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash/bonn_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4/result_scale.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。
- 失败原因：首次强制 `sdpa_backend=flash` 时没有按 call eligibility 过滤，camera head 的 float32 SDPA 也被强制走 Flash，触发 PyTorch `No available kernel. Aborting execution.`
- 处理结果：随后已加入 dtype/device/mask eligibility guard；CUDA half/bfloat16 且无 mask 的 attention 才强制 fused backend，其他调用回退默认 dispatch。修复后的远端代码提交为 `5a9681af05e6805ced9cf296b4db898aa3f30762`。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`；该失败 run 无有效 `remote_artifacts`。
