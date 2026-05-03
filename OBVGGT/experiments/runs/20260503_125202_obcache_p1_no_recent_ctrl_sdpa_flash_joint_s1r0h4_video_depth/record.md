# Run Record: 20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth

## 0. Status
- Status: FAILED
- Start: 2026-05-03T12:52:03+08:00
- End: 2026-05-03T12:53:46+08:00
- Exit code: 1

## 1. Experiment
- Variant: obcache_p1_no_recent_ctrl_sdpa_flash
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash`
- Repo path: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT`
- Log file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data5/OBVGGT/code/branches/2026-0503-infra-runtime-accel/OBVGGT/experiments/runs/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/config_snapshot.json`

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
- `system_metrics.json`: `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash/sintel_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4/system_metrics.json`
- 缺失必需产物:
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash/sintel_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4/result_scale.json`
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash/bonn_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4/result_scale.json`
  - `/mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl_sdpa_flash/kitti_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4/result_scale.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
- 当前状态已按必需产物 contract 自动降级；请优先检查缺失产物对应的数据集或汇总步骤。
- 失败原因：命令参数误用。`quick_run.sh` 的 `video_depth` 配置默认展开 sintel/bonn/kitti 三条命令，本次追加了 `--eval_dataset bonn --max_frames 40`，导致第一条命令输出目录仍是 `sintel_*`，但实际数据集被后追加参数覆盖为 bonn；后续 `eval_depth.py --eval_dataset sintel` 在 bonn 输出目录上评测，触发 `list index out of range`。
- 正确做法：单数据集运行必须使用 adapter 层 `--dataset-filter bonn`，不要追加底层 `--eval_dataset`。
- 本地同步状态：已同步 `manifest.json`、`artifacts.json`、`record.md`，并额外同步误生成的 `remote_artifacts/sintel_system_metrics.json` 作为失败证据；该 run 不进入吞吐对比。
