# OBVGGT 实验追踪表

## 实验概览

说明：
- `Run ID` 对应 `experiments/runs/<run_id>/`
- 单次运行的权威记录以 `experiments/runs/<run_id>/record.md` 为准
- `报告路径` 可保留为外部总结或历史报告位置，但不替代 run 记录
- 统一中台当前可分发到：`StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`
- 历史 `Variant=baseline` 表示 `StreamVGGT`；历史 `Variant=obcache` 表示 `OBVGGT`
- 当前工作区内可运行 repo 是 `StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT`
- `IncVGGT` 当前为 literature-only，不列为 runnable variant
- `monodepth` 是 regression-only，不作为 KV 主 benchmark 结论来源

| Run ID | Variant | Task | Date | Status | 报告路径 | 关键指标 |
|--------|---------|------|------|--------|----------|----------|
| 20260304_obcache_monodepth | obcache | monodepth | 2026-03-04 | ✅ DONE | reports/monodepth_20260304_msi3/ | 5个数据集完成 |
| 20260304_baseline_video_depth_sintel | baseline | video_depth | 2026-03-04 | ✅ DONE | reports/video_depth_sys_benchmark_20260304/ | FPS: 6.79 |
| 20260304_obcache_video_depth_sintel | obcache | video_depth | 2026-03-04 | ✅ DONE | reports/video_depth_sys_benchmark_20260304/ | FPS: 5.69, Mem: -58% |
| 20260304_baseline_video_depth_bonn | baseline | video_depth | 2026-03-04 | ❌ FAILED | reports/video_depth_sys_benchmark_20260304/ | 全部 OOM (0/5) |
| 20260304_obcache_video_depth_bonn | obcache | video_depth | 2026-03-04 | ✅ DONE | reports/video_depth_sys_benchmark_20260304/ | 全部成功 (5/5) |
| 20260304_baseline_video_depth_kitti | baseline | video_depth | 2026-03-04 | ✅ DONE | reports/video_depth_sys_benchmark_20260304/ | FPS: 6.70 |
| 20260304_obcache_video_depth_kitti | obcache | video_depth | 2026-03-04 | ✅ DONE | reports/video_depth_sys_benchmark_20260304/ | FPS: 6.14, Mem: -56% |
| 20260304_obcache_mv_recon | obcache | mv_recon | 2026-03-04 | ✅ DONE | reports/video_depth_sys_benchmark_20260304/ | 7scenes + NRGBD |
| 20260304_obcache_pose_co3d | obcache | pose_evaluation | 2026-03-04 | ⚠️ PARTIAL_DONE | reports/video_depth_sys_benchmark_20260304/ | 注释缺失，未生成 pose_summary.json |

## 待补充实验

### 高优先级
- [ ] **streamvggt_monodepth_regression** - 补充 `StreamVGGT` 线的 monodepth regression（历史脚本标签：`baseline_monodepth_full`）
- [ ] **streamvggt_mv_recon_baseline** - 补充 `StreamVGGT` 线的 mv_recon baseline

### 中优先级（消融实验）
- [ ] **obcache_v_only_monodepth** - V-score only 配置
- [ ] **obcache_k_only_monodepth** - K-score only 配置
- [ ] **obcache_large_budget_video_depth** - 更大的 token budget
- [ ] **xstreamvggt_manual_smoke** - 为 `XStreamVGGT` 补一条可复核的手动运行记录
- [ ] **infinitevggt_manual_smoke** - 为 `InfiniteVGGT` 补一条可复核的手动运行记录

### 低优先级
- [ ] **baseline_pose_co3d** - CO3D pose 评测（需要数据集）
- [ ] **incvggt_placeholder_cleanup** - 继续清理文档里把 `IncVGGT` 写成可运行变体的残留说法

## 实验配置说明

### baseline（历史标签）
- 配置文件: `experiments/configs/baseline.json`
- 对应 repo: `StreamVGGT`
- KV cache: 关闭
- 用途: 作为对照组

### obcache（历史标签）
- 配置文件: `experiments/configs/obcache.json`
- 对应 repo: `OBVGGT`
- KV cache: 开启
- 方法: obcvk（当前实现 canonical 为 `joint`，即 V+K joint scoring）
- Budget: sink=1, recent=2, heavy=4 frames

### XStreamVGGT / InfiniteVGGT
- 当前状态: 本地 repo 可运行，但未接入本目录 quick-run
- 记录要求: 若手动运行，仍需把结果登记回本表与对应 run record

### IncVGGT
- 当前状态: literature-only / no public code
- 记录要求: 不作为 runnable 配置，不写成“待补 checkpoint 即可跑”

## 评测口径说明

- `monodepth`：仅用于精度 regression，不作为 KV eviction 主 benchmark。
- `video_depth`：当前主时序 KV benchmark。
- `mv_recon`：当前主多视角 KV benchmark。
- `pose_co3d`：可选补充 benchmark，前提是注释与 kv wiring 都完整。

## 关键发现汇总

### video_depth (已完成 baseline vs obcache 对比)
- **显存收益**: sintel/kitti 峰值显存下降 56-59%
- **可运行性**: bonn 从完全 OOM 到全部成功
- **性能代价**: FPS 下降 8-16%
- **精度影响**: kitti 略优，sintel 略降

### monodepth (仅 obcache，缺 baseline)
- 5个数据集完成: sintel, bonn, kitti, nyu, scannet
- **定位**: regression-only，不用来判断 KV 显存/FPS 主结论
- **需要补充**: `StreamVGGT` 对照组以验证精度影响

### mv_recon (仅 obcache，缺 baseline)
- 7scenes + NRGBD 完成
- **需要补充**: baseline 对照组和系统指标

### pose_co3d
- 已执行但未完成（`*_test.jgz` 注释缺失）
- **需要补充**: CO3D annotation 后重跑

## 下一步行动

1. **立即**: 补跑 `StreamVGGT` 线的 monodepth regression
2. **短期**: 补跑 `StreamVGGT` 线的 mv_recon baseline
3. **短期**: 为 `XStreamVGGT` / `InfiniteVGGT` 补可复核的手动 run 入口记录
4. **短期**: 补齐 CO3D 注释并重跑 `pose_co3d`
5. **中期**: 消融实验（不同 KV 配置）
