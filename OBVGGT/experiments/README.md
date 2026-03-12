# OBVGGT 实验管理系统

> 新对话先看根目录 `PROJECT_BRIEF.md`；这里是 OBVGGT 实验中台和历史 run 管理入口。

## 0. 当前默认服务器（2026-03-04起）
- 默认执行服务器：**2号机 `amd_server`**（`192.168.166.137`）。
- 推荐根路径：`/mnt/data5/OBVGGT`。
- 3号机（`192.168.166.9`）作为历史结果与迁移来源，不再作为默认入口。

## 1. 文档目的
- 为新工程师提供单一入口：当前做到哪里、下一步跑什么、在哪里看证据。
- 与根目录 `agents.md` / `PROJECT_BRIEF.md` 联动维护：每次实验结束后同步更新状态。
- 说明当前“可运行 repo”与“历史 experiment label”的映射，避免把旧标签误当成当前唯一口径。

## 2. 目录结构

```text
experiments/
├── configs/              # 统一实验配置（baseline / obcache / xstreamvggt / infinitevggt）
├── runs/
│   └── <run_id>/         # 每次运行的单独记录目录（manifest / record / log / artifacts）
├── scripts/
│   └── run_record.py     # 生成和更新 run 记录
├── results/              # 预留/历史目录；不再作为单次 run 的主入口
├── analysis/
│   └── SUMMARY.md        # 已完成实验摘要
├── EXPERIMENTS.md        # 实验追踪主表（优先看）
├── VARIANTS.md           # 变体说明
└── quick_run.sh          # 快速运行脚本（自动创建 runs/<run_id>/）
```

同时，评测产物默认落盘到：

```text
$STREAMVGGT_RUNS/eval_results/
└── by_run/
    └── <run_id>/
        └── <task>/
            └── <variant>/
```

如果未设置 `STREAMVGGT_RUNS`，则回退到 `<repo>/eval_results/by_run/...`。

建议记忆方式：
- `experiments/runs/<run_id>/`：看“这次到底跑了什么”
- `eval_results/by_run/<run_id>/...`：看“这次产出了什么文件”
- `experiments/analysis/SUMMARY.md`：看“已经整理过的结论”

## 3. 当前状态（2026-03-12）
- ✅ `video_depth`：baseline vs obcache 对比已完成（含系统指标）。
- ✅ `monodepth`：obcache 已完成 5 个数据集（缺 baseline 对照；仅作为 regression check）。
- ✅ `mv_recon`：obcache 已完成 7scenes + NRGBD（缺 baseline 对照；应作为主 KV benchmark 之一）。
- ⚠️ `pose_co3d`：已执行但注释缺失，未生成 `pose_summary.json`。
- 当前工作区内可运行的 baseline repo 是：`StreamVGGT`、`OBVGGT`、`XStreamVGGT`、`InfiniteVGGT`。
- `IncVGGT` 当前只保留论文参考位，不应在本工作区文档里写成“可直接运行”。

## 4. 变体 / repo 命名约定（2026-03-12 起）
- 历史标签 `baseline` = `StreamVGGT`。
- 历史标签 `obcache` = `OBVGGT`。
- `XStreamVGGT` 与 `InfiniteVGGT` 有本地 repo，且已接入统一 `quick_run.sh` 调度器。
- `IncVGGT` = literature-only / no public code；不要把它列为待下载后即可跑的 baseline。

## 5. 快速开始

```bash
cd $STREAMVGGT_CODE/experiments
bash quick_run.sh baseline monodepth
bash quick_run.sh baseline mv_recon
bash quick_run.sh xstreamvggt video_depth
bash quick_run.sh infinitevggt mv_recon
```

说明：
- `baseline` 调用的是 `StreamVGGT` 基线线。
- `obcache` 调用的是当前 `OBVGGT` 线。
- `xstreamvggt` / `infinitevggt` 现在也通过本目录的统一入口调度，但底层仍执行各自 repo 的原生命令。

状态优先查看：
- `experiments/EXPERIMENTS.md`
- `experiments/analysis/SUMMARY.md`
- `experiments/runs/<run_id>/record.md`（单次运行记录）
- `experiments/runs/<run_id>/artifacts.json`（单次运行产物索引）

## 6. 评测口径（第一次上手必看）
1. `monodepth` 仅用于精度 regression，不作为主 KV benchmark。
2. `video_depth` 与 `mv_recon` 是当前主 KV benchmark；二者都会落盘 `kv_eval_config.json` 与 `system_metrics.json`。
3. `obcache.json` 中的 `method=obcvk` 在当前实现里会归一到 `joint`；日志会同时保留原始方法名与 canonical 名。
4. `quick_run.sh` 现在统一支持 `baseline / obcache / xstreamvggt / infinitevggt`。
5. 当前工作区可运行 repo 是 `StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`。
6. `IncVGGT` 目前没有公共代码入口，不进入 runnable baseline 列表，也不进入 quick-run 规划。
7. 单次 run 的权威记录在 `experiments/runs/<run_id>/`；`experiments/results/` 当前不作为主入口。

## 7. 跑后文档同步（强制）
每次 run（成功/失败/部分完成）后必须检查并更新：
1. `experiments/EXPERIMENTS.md`：状态、覆盖、缺失项、报告路径。
2. `experiments/analysis/SUMMARY.md`：关键指标与结论。
3. 根目录 `agents.md` 顶部“项目当前状态”与 `PROJECT_BRIEF.md`。
4. 本 README 的“当前状态 / 已知限制 / 下一步”。
5. `experiments/runs/<run_id>/record.md`：补充人工总结、失败原因、后续动作。

若确认无需更新，也要在 run record 中写明“已检查无需更新 + 理由”。

## 8. 下一步优先级
1. 补跑 `StreamVGGT` 线的 `monodepth` regression（历史标签：`baseline_monodepth_full`）。
2. 补跑 `StreamVGGT` 线的 `mv_recon` baseline。
3. 用新中台验证 `XStreamVGGT` / `InfiniteVGGT` 的 smoke 入口和结果 contract。
4. 用统一口径补齐 `video_depth + mv_recon` 的系统指标对比。
5. 补齐 CO3D 注释后重跑 `pose_co3d`。
