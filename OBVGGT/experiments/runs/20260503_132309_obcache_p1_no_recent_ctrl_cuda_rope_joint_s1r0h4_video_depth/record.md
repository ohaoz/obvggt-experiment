# Run Record: 20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth

## 0. Status
- Status: FAILED
- Start: 2026-05-03T13:23:10+08:00
- End: 2026-05-03T13:23:47+08:00
- Exit code: 1

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_cuda_rope
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_cuda_rope`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0503-infra-runtime-accel
- Git commit: c6c7821588fa51d7733447687c52624240eb4c56
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
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_cuda_rope/bonn_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4/system_metrics.json`
- 缺失必需产物:
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_132309_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_cuda_rope/bonn_obcache_p1_no_recent_ctrl_cuda_rope_joint_s1r0h4/result_scale.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。
- 失败原因：修复 contiguous 输入后，inference 阶段可以完成并写出 `system_metrics.json`，但 Python 进程退出时触发 `free(): invalid pointer` / `SIGABRT`。这表明 croco cuRoPE2D extension 在完整 StreamVGGT 进程中存在内存破坏风险。
- microbench 观察：孤立 RoPE microbench 中 cuRoPE 可记录为 `cuda_curope`，contiguous 输入约 `0.083 ms` vs PyTorch `0.498 ms`，qkv-view 输入约 `0.044 ms` vs PyTorch `0.504 ms`；但该 kernel-level 收益不能转化为可接受的端到端候选，因为完整进程会崩溃。
- 决策：`obcache_p1_no_recent_ctrl_cuda_rope` 不作为候选；后续已给 cuRoPE 路径加 `OBVGGT_ALLOW_UNSAFE_CUROPE=1` 安全阀，并把该 quick_run config 标为 non-runnable，避免误触发。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`，并同步失败前生成的 `remote_artifacts/system_metrics.json` 作为证据；无有效 `result_scale.json`。
