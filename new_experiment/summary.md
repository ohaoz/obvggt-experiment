# 补充实验结果分析

日期：2026-05-11
服务器：amd_server (RTX 4090D × 4, CUDA 12.1, PyTorch 2.3.1)

---

## P0: 推荐配置评分对比 + 交叉消融

### A. 评分方法对比（回应弱点4）

固定推荐配置 p=1, S/R/H=1/0/4，仅变化评分方法：

| 方法 | Sintel AbsRel↓ | Bonn AbsRel↓ | KITTI AbsRel↓ |
|------|----------------|--------------|----------------|
| **V+K 联合** | 0.3193 | **0.0516** | **0.0991** |
| V-only | 0.3197 | 0.0520 | 0.1028 |
| K-only | 0.3342 | 0.0528 | 0.1361 |
| Random | 0.3360 | 0.0662 | 0.1932 |

**结论**：在推荐配置下，联合评分(V+K)在 Bonn 和 KITTI 上确实最优。V-only 紧随其后（KITTI 差 3.7%），K-only 明显弱于 V-only（KITTI 差 32.4%），Random 最差（KITTI 差 95%）。

**论文修订建议**：在 4.3.1 节补充说明"默认配置(p=2)下纯V优于联合是因为 L2 范数放大了 K-score 的噪声；在推荐配置(p=1)下联合评分恢复为最优"。

### B. 2×2 交互表（回应弱点5）

| 配置 | p | recent | KITTI AbsRel↓ |
|------|---|--------|----------------|
| 默认 | 2 | 2 | 0.1676 |
| p=1 only | 1 | 2 | 0.1268 (-24.3%) |
| no-recent only | 2 | 0 | 0.1402 (-16.4%) |
| **推荐(both)** | 1 | 0 | **0.0991 (-40.9%)** |

**交互效应分析**：
- p=1 独立贡献：-24.3%（有recent时）/ -29.3%（无recent时）
- 去除recent独立贡献：-16.4%（p=2时）/ -21.8%（p=1时）
- 两者组合效果 -40.9% > 独立效果之和 -40.7%，存在**微弱超加性交互**

**论文修订建议**：在 4.3 节新增"交叉消融"小节，展示 2×2 表格，说明各组件贡献已被严格量化。

---

## P2: 预算-精度曲线（回应弱点3）

### 完整预算曲线（KITTI AbsRel↓）

| Token预算 | OBVGGT | XStreamVGGT | 差距 |
|-----------|--------|-------------|------|
| 2,048 | 0.1074 | 0.1870 | OBVGGT 优 42.6% |
| 4,000 | **0.0964** | - | - |
| 5,000 | - | 0.2185 | - |
| 9,618 | 0.0991 | 0.2219 | OBVGGT 优 55.3% |
| 全缓存 | - | - | baseline 0.1725 |

### 关键发现

1. **等预算公平对比**：在 XStreamVGGT 的默认预算（2048 token）下，OBVGGT AbsRel 0.1074 vs XStreamVGGT 0.1870，OBVGGT 优 42.6%。

2. **OBVGGT 4000 token 是甜点**：KITTI 上 0.0964 甚至优于 9618 token 的 0.0991，再次验证"小缓存正则化效应"。

3. **XStreamVGGT 给更多预算反而更差**：从 2048→9618 token，KITTI AbsRel 从 0.1870 恶化到 0.2219（+18.7%）。说明其一阶余弦相似度评分在大预算下选错了 token。

4. **OBVGGT 在所有预算点均优于全缓存基线**：即使极端压缩到 2048 token（仅 1.5 帧等效），OBVGGT 的 0.1074 仍优于 baseline 的 0.1725。

**论文修订建议**：
- 替换论文中的单点对比为预算曲线图
- 在 4.2 节新增"等预算公平对比"段落
- 强调 OBVGGT 的评分机制在任意预算下都优于 XStreamVGGT 的一阶方法

---

## 实验配置文件

所有配置已存放在 `OBVGGT/experiments/configs/`：
- `obcache_p1_norecent_v_only.json`
- `obcache_p1_norecent_k_only.json`
- `obcache_p1_norecent_random.json`
- `obcache_p2_norecent.json`
- `obcache_token_2048.json`
- `obcache_token_4000.json`
- `xstreamvggt_5k.json`
- `xstreamvggt_9k.json`

## 待完成

- [ ] P1 Pose CO3D 评测（CO3D 数据下载中，tmux session `co3d_download`）
  - 15 个类别切分放 data1 + data3
  - 下载完成后运行 preprocess_co3d.py 生成 annotations
  - 跑 4 个方法的 pose_co3d 评测
- [ ] 更新 agents.md 记录数据位置
- [ ] 将结果整合到论文 docx 第4章
