# OBVGGT Experiment Results Summary

Last updated: 2026-03-19

## Scope

This note merges:

- stable generated results from `OBVGGT/experiments/EXPERIMENTS.md`
- stable generated summaries from `OBVGGT/experiments/analysis/SUMMARY.md`
- the latest system-metrics backfill runs on `amd_server`
- the in-progress KV-hit-rate backfill status

Unless otherwise stated:

- `monodepth` is regression-only
- primary KV-sensitive benchmarks are `video_depth` and `mv_recon`
- `baseline = StreamVGGT`
- `obcache = OBVGGT`

## Key Takeaways

1. `OBVGGT` still has the most complete and stable quality + efficiency + KV-hit results.
2. `XStreamVGGT` and `InfiniteVGGT` now both have unified-harness `system_metrics.json` for `video_depth` and `mv_recon`.
3. `StreamVGGT mv_recon` now also has unified-harness `system_metrics.json`.
4. `StreamVGGT video_depth` KV-hit rerun has now been promoted to `DONE`.
5. KV-hit backfill is now available for:
   - `StreamVGGT mv_recon`: complete
   - `StreamVGGT video_depth`: complete
   - `XStreamVGGT mv_recon`: complete
   - `XStreamVGGT video_depth`: complete
   - `InfiniteVGGT mv_recon`: complete
   - `InfiniteVGGT video_depth`: complete

## Stable Quality Results

### VideoDepth

Stable comparison set:

- `StreamVGGT`: `20260317_092152_baseline_video_depth` for full 3-dataset quality
- `OBVGGT`: `20260317_093954_obcache_joint_s1r2h4_video_depth`
- `XStreamVGGT`: `20260319_141428_xstreamvggt_xstream_cache2048_video_depth`
- `InfiniteVGGT`: `20260319_141428_infinitevggt_rolling_memory_budget1200000_video_depth`

| Variant | Bonn | KITTI | Sintel |
|---|---|---|---|
| StreamVGGT | `0.0585 / 0.2602 / 0.9721` | `0.1725 / 4.9677 / 0.7217` | `0.3242 / 3.8179 / 0.6528` |
| OBVGGT | `0.0561 / 0.2582 / 0.9728` | `0.1676 / 4.9045 / 0.7581` | `0.3391 / 3.8347 / 0.6384` |
| XStreamVGGT | `0.0637 / 0.2778 / 0.9717` | `0.1870 / 5.4604 / 0.7112` | `0.3406 / 3.9456 / 0.6211` |
| InfiniteVGGT | `0.0598 / 0.2641 / 0.9728` | `0.1723 / 4.9581 / 0.7241` | `0.3205 / 3.8116 / 0.6540` |

Format: `Abs Rel / RMSE / δ<1.25`

### MV-Recon

Stable comparison set:

- `StreamVGGT`: `20260319_141428_baseline_mv_recon`
- `OBVGGT`: `20260314_191738_obcache_joint_s1r2h4_mv_recon`
- `XStreamVGGT`: `20260319_142406_xstreamvggt_xstream_cache2048_mv_recon`
- `InfiniteVGGT`: `20260319_142405_infinitevggt_rolling_memory_budget1200000_mv_recon`

| Variant | 7scenes | NRGBD |
|---|---|---|
| StreamVGGT | `0.1288 / 0.1143 / 0.7509` | `0.0845 / 0.0789 / 0.8614` |
| OBVGGT | `0.1288 / 0.1143 / 0.7509` | `0.0845 / 0.0789 / 0.8614` |
| XStreamVGGT | `0.1642 / 0.1395 / 0.7386` | `0.0842 / 0.0763 / 0.8664` |
| InfiniteVGGT | `0.1364 / 0.1190 / 0.7481` | `0.0845 / 0.0789 / 0.8614` |

Format: `acc / comp / nc`

## System Metrics

### OBVGGT

#### VideoDepth

Run: `20260317_093954_obcache_joint_s1r2h4_video_depth`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| Bonn | `5.3772` | `185.97` | `10781.32` | `0.8709` |
| KITTI | `5.5535` | `180.07` | `8263.36` | `0.8704` |
| Sintel | `6.0376` | `165.63` | `8168.86` | `0.8648` |

#### MV-Recon

Run: `20260314_191738_obcache_joint_s1r2h4_mv_recon`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| 7scenes | `5.2262` | `191.34` | `8102.60` | `0.6587` |
| NRGBD | `5.2995` | `188.70` | `7934.20` | `0.5254` |

### StreamVGGT

#### MV-Recon

Run: `20260319_141428_baseline_mv_recon`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| 7scenes | `5.9354` | `168.48` | `7832.91` | `0.6587` |
| NRGBD | `5.9641` | `167.67` | `7721.14` | `0.5254` |

#### VideoDepth

Run: `20260319_145529_baseline_video_depth`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| Bonn | `3.0936` | `323.25` | `21643.22` | `0.9820` |
| KITTI | `5.2472` | `190.58` | `12725.68` | `0.9803` |
| Sintel | `6.4783` | `154.36` | `10553.96` | `0.9592` |

### XStreamVGGT

#### VideoDepth

Run: `20260319_141428_xstreamvggt_xstream_cache2048_video_depth`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| Bonn | `5.7335` | `174.41` | `10047.05` | `0.6679` |
| KITTI | `6.1350` | `163.00` | `8128.40` | `0.8281` |
| Sintel | `6.2646` | `159.63` | `7901.60` | `0.7763` |

#### MV-Recon

Run: `20260319_142406_xstreamvggt_xstream_cache2048_mv_recon`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| 7scenes | `6.0099` | `166.39` | `7639.18` | `0.5784` |
| NRGBD | `6.2057` | `161.14` | `7621.20` | `0.5088` |

### InfiniteVGGT

#### VideoDepth

Run: `20260319_151439_infinitevggt_rolling_memory_budget1200000_video_depth`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| Bonn | `3.7259` | `268.39` | `16069.77` | `0.9742` |
| KITTI | `5.9334` | `168.54` | `13810.16` | `0.9803` |
| Sintel | `6.0844` | `164.36` | `11152.77` | `0.9592` |

#### MV-Recon

Run: `20260319_142405_infinitevggt_rolling_memory_budget1200000_mv_recon`

| Dataset | FPS | Latency ms | Peak Mem MB | KV Hit Rate |
|---|---:|---:|---:|---:|
| 7scenes | `5.3913` | `185.48` | `7976.68` | `0.6587` |
| NRGBD | `5.5272` | `180.92` | `7819.87` | `0.5254` |

## KV Hit Rate Definition

For the new non-OBVGGT backfill, KV hit rate is defined as:

`reused_tokens_total / (reused_tokens_total + appended_tokens_total)`

This is now exposed from the model-side cache path and propagated into
`system_metrics.json` through the eval scripts.

Interpretation:

- larger value means more old KV tokens are being reused relative to newly appended tokens
- for pruning / rolling-memory methods, `evicted_tokens_total` helps explain why hit rate changes

## Current Gaps

1. `pose_co3d` remains incomplete because annotations / summary outputs are still missing.

## Suggested Meeting Wording

- Quality:
  `OBVGGT` still has the strongest complete quality + efficiency + KV-stat package; `StreamVGGT`、`XStreamVGGT` 和 `InfiniteVGGT` 现在都已经有可用的非-OBVGGT KV-hit rerun 结果。
- Efficiency:
  `XStreamVGGT` is currently the fastest on the finished `mv_recon` reruns, while `InfiniteVGGT` remains noticeably heavier on `video_depth`.
- KV cache behavior:
  non-OBVGGT KV-hit-rate logging is now available for `StreamVGGT/XStreamVGGT/InfiniteVGGT` on `mv_recon`，以及 `StreamVGGT/XStreamVGGT/InfiniteVGGT` on `video_depth`。
