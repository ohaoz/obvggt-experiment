# 变体 / 代码库口径说明

## 1. 当前统一口径
- 当前工作区内可运行的 baseline repo 是：`StreamVGGT`、`OBVGGT`、`XStreamVGGT`、`InfiniteVGGT`。
- `IncVGGT` 当前只作为论文对照，不应写成“待下载后即可跑”的公开代码变体。
- `OBVGGT/experiments/quick_run.sh` 目前只稳定承接两条历史标签：
  - `baseline` = `StreamVGGT`
  - `obcache` = `OBVGGT`
- 历史 run ID 和历史报告可以保留旧标签，不要强行回改；在新文档里补映射说明即可。

## 2. 工作区代码库状态

| Repo / Label | 类型 | 当前状态 | 工作区路径 | 是否已接入 `OBVGGT/experiments/quick_run.sh` | 备注 |
|---|---|---|---|---|---|
| `StreamVGGT` | Runnable baseline | 可运行 | `../../StreamVGGT` | 是，历史标签为 `baseline` | 当前 canonical baseline。 |
| `OBVGGT` | Runnable method / 主实验 repo | 可运行 | `..` | 是，历史标签为 `obcache` | 用户改进方法，当前实验中台和主要记录入口。 |
| `XStreamVGGT` | Runnable baseline | 可运行 | `../../XStreamVGGT` | 是 | 通过统一 adapter 分发到 repo-local 入口。 |
| `InfiniteVGGT` | Runnable baseline | 可运行 | `../../InfiniteVGGT` | 是 | 通过统一 adapter 分发到 repo-local 入口。 |
| `IncVGGT` | Literature-only | 不作为 runnable repo | N/A | 否 | 当前无公开代码口径，不纳入待下载后即可跑列表。 |

### 消融变体（2026-03-24 新增）

15 个消融配置均基于 `obcache.json` 修改，仅改变单一维度，通过 `bash quick_run.sh obcache_<ablation> video_depth` 运行。

| Group | Config 标签 | 消融维度 | 关键参数差异 |
|---|---|---|---|
| A: 评分方法 | `obcache_v_only` | scoring | method=obcv |
| A | `obcache_k_only` | scoring | method=obck |
| A | `obcache_random` | scoring | method=random（RandomEvictionTracker） |
| B: 预算分配 | `obcache_budget_tight` | budget | sink=1/recent=1/heavy=2 |
| B | `obcache_budget_small` | budget | sink=1/recent=1/heavy=3 |
| B | `obcache_budget_medium` | budget | sink=1/recent=3/heavy=6 |
| B | `obcache_budget_large` | budget | sink=1/recent=4/heavy=8 |
| C: 组件 | `obcache_no_sink` | component | num_sink_frames=0, heavy=5 |
| C | `obcache_no_recent` | component | num_recent_frames=0, heavy=6 |
| C | `obcache_no_vnorm` | component | use_vnorm=false |
| C | `obcache_p1` | component | p=1 |
| D: Probe | `obcache_probe2` | probe | num_patch_probes=2 |
| D | `obcache_probe32` | probe | num_patch_probes=32 |
| D | `obcache_probe_full` | probe | probe_mode=false（全量） |
| E: 滑动窗口 | `obcache_sliding_window` | baseline | method=sliding_window, recent=7, heavy=0, sink=0 |

### FPS 调试候选（未验证，Bonn 优先）

以下配置用于 `video_depth` Bonn 上定位/提升 OBVGGT 绝对 FPS。它们不替代论文主线 `obcache_p1_no_recent_ctrl`，也不应在完成同口径质量/FPS 验证前写入结论表。

| Config 标签 | 用途 | 关键参数差异 |
|---|---|---|
| `obcache_p1_no_recent_ctrl_profile` | profiling only | 与 `obcache_p1_no_recent_ctrl` 同策略，但 `kv_cache_cfg.profile=true`，会引入同步计时开销 |
| `obcache_p1_no_recent_probe4` | Rejected smoke candidate | p=1, sink=1/recent=0/heavy=4, `num_patch_probes=4`; 2026-05-06 Bonn 40-frame smoke `-1.75%` FPS vs ctrl |
| `obcache_p1_no_recent_probe6` | Rejected smoke candidate | p=1, sink=1/recent=0/heavy=4, `num_patch_probes=6`; 2026-05-06 Bonn 40-frame smoke `-13.44%` FPS vs ctrl |
| `obcache_p1_no_recent_v_only_probe4` | Unpromoted config | method=obcv, p=1, sink=1/recent=0/heavy=4, `num_patch_probes=4`; scoring-method variant, not part of current non-algorithm plan |
| `obcache_p1_no_recent_interval2` | Invalid same-budget speed claim | p=1, sink=1/recent=0/heavy=4, `score_interval=2`; observed cache/sequence budget drift, do not use as strict FPS conclusion |
| `obcache_p1_no_recent_interval3` | Unpromoted / high-risk config | p=1, sink=1/recent=0/heavy=4, `score_interval=3`; likely same semantic risk as interval2 until budget gate proves otherwise |
| `obcache_p1_no_recent_v_only_interval2` | Invalid same-budget speed claim | method=obcv, p=1, sink=1/recent=0/heavy=4, `score_interval=2`; combines scoring-method and interval changes, not current non-algorithm plan |

### Infra / runtime variants（`exp/2026-0503-infra-runtime-accel`）

以下变体用于 runtime / backend / kernel 层验证，不应自动解释成 OBCache 算法改进。

| Config 标签 | 用途 | 当前状态 |
|---|---|---|
| `obcache_p1_no_recent_ctrl_backend_probe` | 记录 RoPE2D / SDPA backend、shape、dtype、GPU、torch/cuda version | Accepted instrumentation |
| `obcache_p1_no_recent_ctrl_profile` | phase profile，区分 aggregator / RoPE / SDPA / OBCache / heads / IO | Profile-only，formal FPS 无效 |
| `obcache_p1_no_recent_ctrl_sdpa_flash` | 强制 SDPA Flash backend | Rejected candidate；本环境不如 default dispatch |
| `obcache_p1_no_recent_ctrl_sdpa_efficient` | 强制 SDPA efficient backend | Instrumentation-only；未进入 accepted candidate |
| `obcache_p1_no_recent_ctrl_sdpa_math` | 强制 SDPA math backend | Instrumentation-only；未进入 accepted candidate |
| `obcache_p1_no_recent_ctrl_depth_only` | `video_depth` 仅保留 depth 所需 heads | Accepted `video_depth` task-runtime candidate |
| `full_cache_depth_only` | full-cache 下验证 depth-only contract | Control-only；显存更高，不作为主候选 |
| `obcache_p1_no_recent_ctrl_prealloc_kv` | 预分配 OBCache KV buffer，避免 append/evict 分配 | Rejected candidate；paired Bonn smoke 更慢且更占显存 |

## 3. 如何解释历史标签
- `baseline`：历史上在本目录中表示 `StreamVGGT` 基线线。
- `obcache`：历史上在本目录中表示当前 `OBVGGT` 线，而不是“继续新增一个独立 OBCache baseline”。
- 新的总结、brief、表格里优先写 repo 名称；只有在引用旧 run ID 或旧脚本参数时才继续写 `baseline/obcache`。

## 4. 运行建议
- 如果目标是复现当前 `OBVGGT` 中台下的统一对比，使用：

```bash
cd OBVGGT/experiments
bash quick_run.sh baseline monodepth
bash quick_run.sh obcache video_depth
bash quick_run.sh xstreamvggt video_depth
bash quick_run.sh infinitevggt mv_recon
```

- 如果目标是调试某个 repo 的原生命令，仍可以进入各自 repo 手动运行；统一中台并不替代 repo-local 调试。
- 不要为 `IncVGGT` 编写“可运行占位说明”，除非后续明确获得公开代码与可复现实验入口。

## 5. 评测使用建议
- `monodepth`：仅做 regression check。
- `video_depth`：主时序 KV benchmark。
- `mv_recon`：主多视角 KV benchmark。
- `pose_co3d`：补充 benchmark，前提是注释和结果汇总脚本齐全。

## 6. 文档维护规则
1. 新增 runnable repo 时，先更新本文件，再更新 `README.md` 与 `EXPERIMENTS.md`。
2. 旧 run ID 不重命名，只在文档中补映射。
3. 如果某 repo 只有论文没有公共代码，不写成“待补 checkpoint 即可运行”。
