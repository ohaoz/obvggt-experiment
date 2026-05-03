# OBVGGT 实验追踪表

> 本文件由 `experiments/scripts/render_experiment_docs.py` 自动生成。
> 单次运行的权威来源是 `experiments/runs/<run_id>/manifest.json`、`artifacts.json` 与 `record.md`。

## 实验概览

说明：
- 优先用 repo 名称表达变体：`StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`。
- 历史脚本参数仍可能出现 `baseline / obcache`；其中 `obcache = OBVGGT`。
- `monodepth` 是 regression-only，不作为 KV 主 benchmark 结论来源。

| Run ID | Variant | Task | Date | Status | Run Record | 关键指标 |
|--------|---------|------|------|--------|------------|----------|
| `20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_depth_only` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_130529_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_depth_only` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_130432_obcache_p1_no_recent_ctrl_depth_only_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_125412_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_sdpa_flash` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_125412_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_sdpa_flash` | `video_depth` | `2026-05-03` | `FAILED` | `experiments/runs/20260503_125202_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/record.md` | result=0/3, system=1/3 |
| `20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_sdpa_math` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_124515_obcache_p1_no_recent_ctrl_sdpa_math_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_124421_obcache_p1_no_recent_ctrl_sdpa_efficient_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_sdpa_efficient` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_124421_obcache_p1_no_recent_ctrl_sdpa_efficient_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_sdpa_flash` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_124328_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_sdpa_flash` | `video_depth` | `2026-05-03` | `FAILED` | `experiments/runs/20260503_124050_obcache_p1_no_recent_ctrl_sdpa_flash_joint_s1r0h4_video_depth/record.md` | result=0/3, system=0/3 |
| `20260503_123103_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_backend_probe` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_123103_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_122825_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_backend_probe` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_122825_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl_backend_probe` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_122116_obcache_p1_no_recent_ctrl_backend_probe_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_interval2` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_110746_obcache_p1_no_recent_interval2_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_110407_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_probe4` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_110407_obcache_p1_no_recent_probe4_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_110013_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl` | `video_depth` | `2026-05-03` | `DONE` | `experiments/runs/20260503_110013_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/record.md` | result=1/3, system=1/3 |
| `20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl` | `video_depth` | `2026-05-03` | `FAILED` | `experiments/runs/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/record.md` | result=0/3, system=0/3 |
| `20260503_105741_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl` | `video_depth` | `2026-05-03` | `FAILED` | `experiments/runs/20260503_105741_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/record.md` | result=0/3, system=0/3 |
| `20260503_105648_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth` | `obcache_p1_no_recent_ctrl` | `video_depth` | `2026-05-03` | `FAILED` | `experiments/runs/20260503_105648_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/record.md` | result=0/3, system=0/3 |
| `20260319_151439_infinitevggt_rolling_memory_budget1200000_video_depth` | `InfiniteVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_151439_infinitevggt_rolling_memory_budget1200000_video_depth/record.md` | result=3/3, system=3/3 |
| `20260319_145529_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_145529_baseline_video_depth/record.md` | result=3/3, system=3/3 |
| `20260319_145531_xstreamvggt_xstream_cache2048_video_depth` | `XStreamVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_145531_xstreamvggt_xstream_cache2048_video_depth/record.md` | result=3/3, system=3/3 |
| `20260319_150141_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-19` | `DONE` | `experiments/runs/20260319_150141_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=2/2, root_summary=yes, root_system=yes |
| `20260319_145533_xstreamvggt_xstream_cache2048_mv_recon` | `XStreamVGGT` | `mv_recon` | `2026-03-19` | `DONE` | `experiments/runs/20260319_145533_xstreamvggt_xstream_cache2048_mv_recon/record.md` | datasets=2/2, root_summary=yes, root_system=yes |
| `20260319_145527_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-19` | `DONE` | `experiments/runs/20260319_145527_baseline_mv_recon/record.md` | datasets=2/2, root_summary=yes, root_system=yes |
| `20260319_141428_infinitevggt_rolling_memory_budget1200000_video_depth` | `InfiniteVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_141428_infinitevggt_rolling_memory_budget1200000_video_depth/record.md` | result=3/3, system=3/3 |
| `20260319_141428_xstreamvggt_xstream_cache2048_video_depth` | `XStreamVGGT` | `video_depth` | `2026-03-19` | `DONE` | `experiments/runs/20260319_141428_xstreamvggt_xstream_cache2048_video_depth/record.md` | result=3/3, system=3/3 |
| `20260319_142406_xstreamvggt_xstream_cache2048_mv_recon` | `XStreamVGGT` | `mv_recon` | `2026-03-19` | `DONE` | `experiments/runs/20260319_142406_xstreamvggt_xstream_cache2048_mv_recon/record.md` | datasets=2/2, root_summary=yes, root_system=yes |
| `20260319_142405_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-19` | `DONE` | `experiments/runs/20260319_142405_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=2/2, root_summary=yes, root_system=yes |
| `20260319_141428_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-19` | `PARTIAL_DONE` | `experiments/runs/20260319_141428_baseline_video_depth/record.md` | result=1/3, system=2/3 |
| `20260319_142035_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-19` | `FAILED` | `experiments/runs/20260319_142035_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260319_142035_xstreamvggt_xstream_cache2048_mv_recon` | `XStreamVGGT` | `mv_recon` | `2026-03-19` | `FAILED` | `experiments/runs/20260319_142035_xstreamvggt_xstream_cache2048_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260319_141428_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-19` | `DONE` | `experiments/runs/20260319_141428_baseline_mv_recon/record.md` | datasets=2/2, root_summary=yes, root_system=yes |
| `20260319_141334_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-19` | `FAILED` | `experiments/runs/20260319_141334_baseline_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260319_141334_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-19` | `FAILED` | `experiments/runs/20260319_141334_baseline_video_depth/record.md` | result=0/3, system=0/3 |
| `20260319_141334_infinitevggt_rolling_memory_budget1200000_video_depth` | `InfiniteVGGT` | `video_depth` | `2026-03-19` | `FAILED` | `experiments/runs/20260319_141334_infinitevggt_rolling_memory_budget1200000_video_depth/record.md` | result=0/3, system=0/3 |
| `20260319_141334_xstreamvggt_xstream_cache2048_video_depth` | `XStreamVGGT` | `video_depth` | `2026-03-19` | `FAILED` | `experiments/runs/20260319_141334_xstreamvggt_xstream_cache2048_video_depth/record.md` | result=0/3, system=0/3 |
| `20260318_200314_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-19` | `DONE` | `experiments/runs/20260318_200314_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=2/2, root_summary=yes, root_system=yes |
| `20260318_202918_infinitevggt_rolling_memory_budget1200000_monodepth` | `InfiniteVGGT` | `monodepth` | `2026-03-18` | `DONE` | `experiments/runs/20260318_202918_infinitevggt_rolling_memory_budget1200000_monodepth/record.md` | datasets=5/5: bonn, kitti, nyu, scannet, sintel |
| `20260314_184640_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-18` | `DONE` | `experiments/runs/20260314_184640_baseline_mv_recon/record.md` | datasets=2/2, root_summary=no, root_system=no |
| `20260314_185714_xstreamvggt_xstream_cache2048_mv_recon` | `XStreamVGGT` | `mv_recon` | `2026-03-18` | `DONE` | `experiments/runs/20260314_185714_xstreamvggt_xstream_cache2048_mv_recon/record.md` | datasets=2/2, root_summary=no, root_system=no |
| `20260317_095707_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-18` | `PARTIAL_DONE` | `experiments/runs/20260317_095707_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=1/2, root_summary=no, root_system=no |
| `20260318_200214_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-18` | `FAILED` | `experiments/runs/20260318_200214_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260317_130019_xstreamvggt_xstream_cache2048_monodepth` | `XStreamVGGT` | `monodepth` | `2026-03-17` | `DONE` | `experiments/runs/20260317_130019_xstreamvggt_xstream_cache2048_monodepth/record.md` | datasets=5/5: bonn, kitti, nyu, scannet, sintel |
| `20260316_213618_baseline_monodepth` | `StreamVGGT` | `monodepth` | `2026-03-17` | `DONE` | `experiments/runs/20260316_213618_baseline_monodepth/record.md` | datasets=5/5: bonn, kitti, nyu, scannet, sintel |
| `20260317_093954_obcache_joint_s1r2h4_video_depth` | `OBVGGT` | `video_depth` | `2026-03-17` | `DONE` | `experiments/runs/20260317_093954_obcache_joint_s1r2h4_video_depth/record.md` | result=3/3, system=3/3 |
| `20260317_092152_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-17` | `DONE` | `experiments/runs/20260317_092152_baseline_video_depth/record.md` | result=3/3, system=0/3 |
| `20260315_182931_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-15` | `FAILED` | `experiments/runs/20260315_182931_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260315_180956_infinitevggt_rolling_memory_budget1200000_video_depth` | `InfiniteVGGT` | `video_depth` | `2026-03-15` | `DONE` | `experiments/runs/20260315_180956_infinitevggt_rolling_memory_budget1200000_video_depth/record.md` | result=3/3, system=0/3 |
| `20260314_191738_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-14` | `DONE` | `experiments/runs/20260314_191738_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=2/2, root_summary=no, root_system=no |
| `20260314_191733_obcache_joint_s1r2h4_video_depth` | `OBVGGT` | `video_depth` | `2026-03-14` | `FAILED` | `experiments/runs/20260314_191733_obcache_joint_s1r2h4_video_depth/record.md` | result=0/3, system=0/3 |
| `20260314_185310_obcache_joint_s1r2h4_monodepth` | `OBVGGT` | `monodepth` | `2026-03-14` | `DONE` | `experiments/runs/20260314_185310_obcache_joint_s1r2h4_monodepth/record.md` | datasets=5/5: bonn, kitti, nyu, scannet, sintel |
| `20260314_190418_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-14` | `FAILED` | `experiments/runs/20260314_190418_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260314_190346_infinitevggt_rolling_memory_budget1200000_video_depth` | `InfiniteVGGT` | `video_depth` | `2026-03-14` | `FAILED` | `experiments/runs/20260314_190346_infinitevggt_rolling_memory_budget1200000_video_depth/record.md` | result=0/3, system=0/3 |
| `20260314_183922_xstreamvggt_xstream_cache2048_video_depth` | `XStreamVGGT` | `video_depth` | `2026-03-14` | `DONE` | `experiments/runs/20260314_183922_xstreamvggt_xstream_cache2048_video_depth/record.md` | result=3/3, system=0/3 |
| `20260314_183922_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-14` | `FAILED` | `experiments/runs/20260314_183922_baseline_video_depth/record.md` | result=1/3, system=0/3 |
| `20260314_181115_baseline_monodepth` | `StreamVGGT` | `monodepth` | `2026-03-14` | `FAILED` | `experiments/runs/20260314_181115_baseline_monodepth/record.md` | datasets=4/5: bonn, kitti, nyu, sintel |
| `20260314_181115_xstreamvggt_xstream_cache2048_monodepth` | `XStreamVGGT` | `monodepth` | `2026-03-14` | `FAILED` | `experiments/runs/20260314_181115_xstreamvggt_xstream_cache2048_monodepth/record.md` | datasets=4/5: bonn, kitti, nyu, sintel |
| `20260313_125316_xstreamvggt_xstream_cache2048_monodepth` | `XStreamVGGT` | `monodepth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_125316_xstreamvggt_xstream_cache2048_monodepth/record.md` | datasets=4/5: bonn, kitti, nyu, sintel |
| `20260313_122743_xstreamvggt_xstream_cache2048_mv_recon` | `XStreamVGGT` | `mv_recon` | `2026-03-13` | `DONE` | `experiments/runs/20260313_122743_xstreamvggt_xstream_cache2048_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_120427_xstreamvggt_xstream_cache2048_monodepth` | `XStreamVGGT` | `monodepth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_120427_xstreamvggt_xstream_cache2048_monodepth/record.md` | datasets=4/5: bonn, kitti, nyu, sintel |
| `20260313_114628_xstreamvggt_xstream_cache2048_video_depth` | `XStreamVGGT` | `video_depth` | `2026-03-13` | `DONE` | `experiments/runs/20260313_114628_xstreamvggt_xstream_cache2048_video_depth/record.md` | result=3/3, system=0/3 |
| `20260313_115336_infinitevggt_rolling_memory_budget1200000_mv_recon` | `InfiniteVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_115336_infinitevggt_rolling_memory_budget1200000_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_115304_infinitevggt_rolling_memory_budget1200000_video_depth` | `InfiniteVGGT` | `video_depth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_115304_infinitevggt_rolling_memory_budget1200000_video_depth/record.md` | result=0/3, system=0/3 |
| `20260313_111924_obcache_joint_s1r2h4_monodepth` | `OBVGGT` | `monodepth` | `2026-03-13` | `DONE` | `experiments/runs/20260313_111924_obcache_joint_s1r2h4_monodepth/record.md` | datasets=5/5: bonn, kitti, nyu, scannet, sintel |
| `20260313_105533_baseline_monodepth` | `StreamVGGT` | `monodepth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_105533_baseline_monodepth/record.md` | datasets=4/5: bonn, kitti, nyu, sintel |
| `20260313_104733_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_104733_baseline_video_depth/record.md` | result=1/3, system=0/3 |
| `20260313_104733_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-13` | `DONE` | `experiments/runs/20260313_104733_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=2/2, root_summary=no, root_system=no |
| `20260313_102849_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_102849_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_102234_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-13` | `DONE` | `experiments/runs/20260313_102234_baseline_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_102302_obcache_joint_s1r2h4_monodepth` | `OBVGGT` | `monodepth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_102302_obcache_joint_s1r2h4_monodepth/record.md` | datasets=0/5:  |
| `20260313_095910_baseline_monodepth` | `StreamVGGT` | `monodepth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_095910_baseline_monodepth/record.md` | datasets=4/5: bonn, kitti, nyu, sintel |
| `20260313_102049_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_102049_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_102041_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_102041_baseline_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_101834_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_101834_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_101826_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_101826_baseline_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_093759_obcache_joint_s1r2h4_video_depth` | `OBVGGT` | `video_depth` | `2026-03-13` | `DONE` | `experiments/runs/20260313_093759_obcache_joint_s1r2h4_video_depth/record.md` | result=3/3, system=3/3 |
| `20260313_093841_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_093841_baseline_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_093841_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_093841_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_092944_baseline_video_depth` | `StreamVGGT` | `video_depth` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_092944_baseline_video_depth/record.md` | result=1/3, system=0/3 |
| `20260313_093702_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_093702_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_093658_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_093658_baseline_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_093028_obcache_joint_s1r2h4_mv_recon` | `OBVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_093028_obcache_joint_s1r2h4_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |
| `20260313_093024_baseline_mv_recon` | `StreamVGGT` | `mv_recon` | `2026-03-13` | `FAILED` | `experiments/runs/20260313_093024_baseline_mv_recon/record.md` | datasets=0/2, root_summary=no, root_system=no |

## 评测口径说明

- `monodepth`：仅用于精度 regression，不作为 KV eviction 主 benchmark。
- `video_depth`：当前主时序 KV benchmark。
- `mv_recon`：当前主多视角 KV benchmark。
- `pose_co3d`：当前补充 benchmark；需要 CO3D 原始数据和 annotations 同时到位。

## 维护规范

1. `experiments/runs/<run_id>/manifest.json` 和 `artifacts.json` 是唯一机器可读真相。
2. `EXPERIMENTS.md`、`analysis/SUMMARY.md` 与 `analysis/ALL_RESULTS.md` 一律由生成器重建，不手工编辑。
3. 每次 run 结束后，应重新执行生成器；若在服务器上运行，优先更新服务器上的 docs。
4. 本地 docs 如需对照服务器状态，请通过跳板机人工核对远端文档；不要依赖自动 refresh 脚本。
