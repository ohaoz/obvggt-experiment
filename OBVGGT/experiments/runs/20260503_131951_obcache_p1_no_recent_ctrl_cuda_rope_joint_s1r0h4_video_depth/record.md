# Run Record: 20260503_131951_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth

## 0. Status
- Status: FAILED
- Start: 2026-05-03T13:19:52+08:00
- End: 2026-05-03T13:20:23+08:00
- Exit code: 1

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_cuda_rope
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131951_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_131951_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_cuda_rope`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131951_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131951_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_131951_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: 87d3349b422a0d5474e6d6387258ec2129ce1d49
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
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_131951_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_cuda_rope/bonn_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4/result_scale.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。
- 失败原因：第一版 `--rope2d_backend cuda` 只支持 qkv-view stride，实际完整模型中的 RoPE 输入是 contiguous `[B,H,N,D]`，触发 ineligible guard 并失败。
- 后续处理：已改为直接调用底层 `curope.rope_2d` kernel 以支持 contiguous 输入，但完整模型 smoke 仍在进程退出时触发 `free(): invalid pointer`，见后续 run `20260503_132309...`。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`；无有效 `result_scale.json`。
