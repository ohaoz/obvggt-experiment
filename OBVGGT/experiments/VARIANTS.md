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
| `OBVGGT` | Runnable baseline / 主实验 repo | 可运行 | `..` | 是，历史标签为 `obcache` | 当前实验中台和主要记录入口。 |
| `XStreamVGGT` | Runnable baseline | 可运行 | `../../XStreamVGGT` | 是 | 通过统一 adapter 分发到 repo-local 入口。 |
| `InfiniteVGGT` | Runnable baseline | 可运行 | `../../InfiniteVGGT` | 是 | 通过统一 adapter 分发到 repo-local 入口。 |
| `IncVGGT` | Literature-only | 不作为 runnable repo | N/A | 否 | 当前无公开代码口径，不纳入待下载后即可跑列表。 |

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
