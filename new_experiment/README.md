# 补充实验结果（2026-05-11）

针对毕设论文弱点3/4/5的补充实验，在 amd_server 上完成。

## P0: 推荐配置评分对比 + 交叉消融（弱点4+5）

### A. 评分方法对比（固定 p=1, S/R/H=1/0/4）

验证联合评分在推荐配置下确实最优。

### B. 2×2 交互表（p × recent）

量化 p=1 和去除 recent 的独立贡献及交互效应。

## P2: 预算-精度曲线（弱点3）

在等预算条件下公平对比 OBVGGT 和 XStreamVGGT。

## 文件说明

- `p0_scoring_comparison.csv` — P0-A 评分方法对比结果
- `p0_interaction_table.csv` — P0-B 2×2 交互表
- `p2_budget_curve.csv` — P2 预算曲线完整数据
- `summary.md` — 结果分析与论文写作建议
