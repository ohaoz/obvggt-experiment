# 已完成实验报告汇总

## 1. Monodepth (OBCache) - 2026-03-04

**Run ID**: `20260304_obcache_monodepth`
**配置**: OBCache 开启
**状态**: ✅ DONE
**详细报告**: `reports/monodepth_20260304_msi3/REPORT_RERUN_KV_20260304.md`

### 结果摘要

| 数据集 | Abs Rel | RMSE | δ < 1.25 |
|--------|---------|------|----------|
| sintel | 0.2543 | 4.0014 | 0.6851 |
| bonn | 0.0515 | 0.2399 | 0.9711 |
| kitti | 0.0718 | 3.8340 | 0.9468 |
| nyu | 0.0550 | 0.2768 | 0.9585 |
| scannet | 0.0289 | 0.1190 | 0.9863 |

**关键发现**:
- 5个数据集全部完成
- ⚠️ `monodepth` 仅作为 depth regression check，不作为主 KV benchmark
- ⚠️ **缺少 baseline 对照组**，无法判断精度影响

---

## 2. Video Depth (Baseline vs OBCache) - 2026-03-04

**Run ID**: `20260304_video_depth_sys_benchmark`
**配置**: Baseline + OBCache 对比
**状态**: ✅ DONE
**详细报告**: `reports/video_depth_sys_benchmark_20260304/REPORT_COMPLETE_20260304.md`

### 系统指标对比

| 数据集 | 方案 | 成功率 | FPS | 峰值显存(MB) | 显存变化 | KV命中率 |
|--------|------|--------|-----|--------------|----------|----------|
| sintel | baseline | 23/23 | 6.79 | 23792 | - | - |
| sintel | obcache | 23/23 | 5.69 | 9874 | **-58.5%** | 86.5% |
| bonn | baseline | **0/5** | OOM | OOM | - | - |
| bonn | obcache | **5/5** | 4.00 | 11662 | - | 87.1% |
| kitti | baseline | 13/13 | 6.70 | 23868 | - | - |
| kitti | obcache | 13/13 | 6.14 | 10410 | **-56.4%** | 87.0% |

### 精度指标对比

| 数据集 | 方案 | Abs Rel | RMSE | δ < 1.25 |
|--------|------|---------|------|----------|
| sintel | baseline | 0.3267 | 3.8170 | 0.6508 |
| sintel | obcache | 0.3351 | 3.8421 | 0.6406 |
| kitti | baseline | 0.1728 | 4.9661 | 0.7219 |
| kitti | obcache | 0.1674 | 4.8969 | 0.7610 |
| bonn | baseline | N/A (OOM) | N/A | N/A |
| bonn | obcache | 0.0563 | 0.2584 | 0.9728 |

**关键发现**:
- ✅ **显存收益明确**: 56-59% 峰值显存下降
- ✅ **可运行性提升**: bonn 从完全不可用到全部成功
- ⚠️ **性能代价**: FPS 下降 8-16%
- ⚠️ **精度影响**: kitti 略优，sintel 略降（数据集相关）

---

## 3. Multi-view Reconstruction - 2026-03-04

**Run ID**: `20260304_obcache_mv_recon`
**配置**: OBCache 开启
**状态**: ✅ DONE
**详细报告**: `reports/video_depth_sys_benchmark_20260304/REPORT_8p5_8p6_8p7_20260304.md`

### 结果摘要
- ✅ 7scenes 完成
- ✅ Neural-RGBD 完成
- 结果路径: `eval_results/mv_recon/StreamVGGT_checkpoints/`

**关键发现**:
- 使用 `--model_name StreamVGGT` (不是 OBVGGT)
- ⚠️ **缺少 baseline 对照组**
- ⚠️ **缺少系统指标**（FPS、显存等）

---

## 4. Camera Pose (CO3D) - 2026-03-04

**Run ID**: `20260304_obcache_pose_co3d`
**配置**: OBCache 开启
**状态**: ⚠️ PARTIAL_DONE
**详细报告**: `reports/video_depth_sys_benchmark_20260304/REPORT_8p5_8p6_8p7_20260304.md`

### 结果摘要
- 已启动 `pose_evaluation/test_co3d.py` 并进入评测流程
- 触发阻塞：`co3d_v2_annotation/*_test.jgz` 缺失
- 未生成 `pose_summary.json`，当前结论仅为“流程已验证可启动”

**关键发现**:
- 评测脚本与依赖链可用（环境层面通过）
- ⚠️ **数据依赖不完整**：缺少 CO3D annotation 文件，无法形成可比指标

---

## 总结

### 已完成的对比实验
✅ **video_depth**: 完整的 baseline vs obcache 对比（精度 + 系统指标）

### 缺失的对比实验
❌ **monodepth**: 只有 obcache，缺 baseline
❌ **mv_recon**: 只有 obcache，缺 baseline
⚠️ **pose_co3d**: 流程可跑，但注释缺失，结果不完整

### 核心结论（基于 video_depth）
1. **主要价值**: 显存压降 + 可运行性提升
2. **代价**: 吞吐下降 8-16%
3. **精度**: 数据集相关，整体可接受

### 下一步优先级
1. 🔴 **高**: 补跑 monodepth baseline
2. 🔴 **高**: 补跑 mv_recon baseline + 系统指标
3. 🟡 **中**: 补齐 CO3D annotation 后重跑 pose_co3d
4. 🟢 **低**: 消融实验（不同 KV 配置）
