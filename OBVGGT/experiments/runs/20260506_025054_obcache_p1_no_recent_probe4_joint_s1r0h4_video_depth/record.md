# Run Record: 20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth

## 0. Status
- Status: DONE
- Start: 2026-05-06T02:50:55+08:00
- End: 2026-05-06T02:51:47+08:00
- Exit code: 0

## 1. Experiment
- Variant: obcache_p1_no_recent_probe4
- Task: video_depth
- Benchmark role: streaming_benchmark
- Model: StreamVGGT
- Result tag: obcache_p1_no_recent_probe4_joint_s1r0h4

## 2. Paths
- Run dir: `/mnt/data3/OBVGGT/research_20260506/code/OBVGGT/OBVGGT/experiments/runs/20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth`
- Output root: `/mnt/data3/OBVGGT/research_20260506/runs/eval_results/by_run/20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_probe4`
- Repo path: `/mnt/data3/OBVGGT/research_20260506/code/OBVGGT/OBVGGT`
- Log file: `/mnt/data3/OBVGGT/research_20260506/code/OBVGGT/OBVGGT/experiments/runs/20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth/stdout.log`
- Command file: `/mnt/data3/OBVGGT/research_20260506/code/OBVGGT/OBVGGT/experiments/runs/20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth/command.sh`
- Config snapshot: `/mnt/data3/OBVGGT/research_20260506/code/OBVGGT/OBVGGT/experiments/runs/20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth/config_snapshot.json`

## 3. Code Version
- Git branch: exp/2026-0506-obvggt-research-opt
- Git commit: 29c9ff13aa6c0b3334d1ae8638c812a64f96f80a
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
  "num_patch_probes": 4
}
```

## 5. Artifacts
- `result_scale.json`: `/mnt/data3/OBVGGT/research_20260506/runs/eval_results/by_run/20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_probe4/bonn_obcache_p1_no_recent_probe4_joint_s1r0h4/result_scale.json`
- `system_metrics.json`: `/mnt/data3/OBVGGT/research_20260506/runs/eval_results/by_run/20260506_025054_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_probe4/bonn_obcache_p1_no_recent_probe4_joint_s1r0h4/system_metrics.json`

## 6. Notes
- 结束后请同步检查 `experiments/EXPERIMENTS.md`、`experiments/analysis/SUMMARY.md`、`experiments/README.md` 与 `AGENTS.md`。
