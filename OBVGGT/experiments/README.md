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
│   ├── run_record.py           # 生成和更新 run 记录
│   ├── render_experiment_docs.py # 从 runs/* 自动重建 EXPERIMENTS.md / analysis/SUMMARY.md
│   └── refresh_docs_from_amd_server.ps1 # 在本地一键拉取 amd_server 上的最新 docs
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
- `experiments/scripts/render_experiment_docs.py`：把 `runs/*` 的机器真相重建成文档

## 3. 当前状态（2026-03-24）
- ✅ `video_depth`：baseline vs obcache 对比已完成（含系统指标）。
- ✅ `monodepth`：obcache 已完成 5 个数据集（缺 baseline 对照；仅作为 regression check）。
- ✅ `mv_recon`：obcache 已完成 7scenes + NRGBD；`StreamVGGT / XStreamVGGT / InfiniteVGGT` 现已补齐统一中台 rerun。
- ✅ `XStreamVGGT`：`video_depth` 与 `mv_recon` 已补齐 `system_metrics.json`。
- ✅ `InfiniteVGGT`：`video_depth` 与 `mv_recon` 已补齐 `system_metrics.json`。
- ⚠️ `StreamVGGT video_depth`：2026-03-19 重跑已补到 `system=2/3`，但仍因原始 `eval_depth.py` 后处理报错处于 `PARTIAL_DONE`。
- ⚠️ `pose_co3d`：已执行但注释缺失，未生成 `pose_summary.json`。
- 🆕 **消融实验准备就绪**（2026-03-24）：15 个 `obcache_*` 消融配置已创建；代码已支持 `random` 驱逐和 `sliding_window` 模式。待跑 P0（7 runs）+ P1（8 runs）。
- 当前工作区内可运行的 baseline repo 是：`StreamVGGT`、`OBVGGT`、`XStreamVGGT`、`InfiniteVGGT`。
- `IncVGGT` 当前只保留论文参考位，不应在本工作区文档里写成”可直接运行”。

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
每次 run（成功/失败/部分完成）后按以下规范执行：
1. `experiments/runs/<run_id>/manifest.json` 与 `artifacts.json` 是唯一机器真相，不手工改。
2. `quick_run.sh` 结束后会自动重建服务器侧的 `EXPERIMENTS.md` 和 `analysis/SUMMARY.md`。
3. 本地需要刷新时，运行：

```powershell
pwsh -File OBVGGT/experiments/scripts/refresh_docs_from_amd_server.ps1
```

4. 仍然需要人工检查并按需更新：
   根目录 `agents.md` 顶部“项目当前状态”与 `PROJECT_BRIEF.md`，
   以及本 README 的“当前状态 / 已知限制 / 下一步”。
5. `experiments/runs/<run_id>/record.md` 继续保留人工结论、失败原因、后续动作。

换句话说：
- `EXPERIMENTS.md` / `analysis/SUMMARY.md` = 生成物
- `runs/<run_id>/manifest.json` / `artifacts.json` / `record.md` = 真相来源

## 8. 下一步优先级
1. 🔴 **跑消融实验 P0 批次**（评分方法 + 预算分配消融，7 runs via `quick_run.sh obcache_<ablation> video_depth`）。
2. 🔴 跑消融实验 P1 批次（组件 + Probe + 滑动窗口消融，8 runs）。
3. 跑完后执行 `python render_experiment_docs.py` 重建文档。
4. 修复并补齐 `StreamVGGT video_depth` 的最后一个缺口（当前 `result=1/3, system=2/3`）。
5. 补跑 `StreamVGGT` 线的 `monodepth` regression（历史标签：`baseline_monodepth_full`）。
6. 汇总 `StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT` 的统一效率对比表 + 消融结论，用于论文/报告。
