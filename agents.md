# agents.md
注意先建立虚拟环境再跑
请先看.trellis
> **新对话快速入口**：先看根目录 `PROJECT_BRIEF.md`。它是单文件项目摘要；本文件保留生产环境 SOP、服务器约束和实验操作细则。
>
> **用途**：这是”上生产环境跑 OBVGGT 实验”的标准操作规程（SOP），给人或 AI agent 都能照着做。
>
> **硬约束**（务必遵守）：
> - **生产环境**：任何操作以”不会误删/误覆盖/误占满磁盘/误影响他人”为第一优先级。
> - **服务器一律使用 conda**；**禁止 sudo**（包含 `sudo yum/apt`、`sudo rm` 等）。
> - **必须使用 SwanLab（默认）进行可视化记录**（W&B 仅作为兼容备选）；**禁止把 SWANLAB_API_KEY/WANDB_API_KEY/服务器密码写进仓库**。
> - **每次实验（运行中/失败/成功）都必须写一份 Markdown 记录**（见本文模板）。
> - **每次实验跑完必须做文档同步检查**：检查并按需更新 `agents.md` / `PROJECT_BRIEF.md`（项目当前状态）、`OBVGGT/experiments/README.md`（上手说明）、`OBVGGT/experiments/EXPERIMENTS.md`（追踪表）；若确认“无需更新”，也要在 record 写明原因。
>
---

## 📍 项目当前状态（2026-03-04）

**研究目标**：围绕 `StreamVGGT / OBVGGT / XStreamVGGT / InfiniteVGGT` 做 KV cache / 长序列可运行性评测与复现；`IncVGGT` 当前只做文献参照。

**已完成实验**：
- ✅ video_depth: baseline vs obcache 完整对比（精度+系统指标）
- ✅ monodepth: obcache 已完成 5 个数据集（sintel/bonn/kitti/nyu/scannet）
- ✅ mv_recon: obcache 已完成 7scenes + NRGBD
- ⚠️ pose_co3d: 已执行但注释缺失，未产出 `pose_summary.json`

**当前缺口**：
- ⚠️ monodepth 缺 `StreamVGGT` 对照组（且仅作为 regression）
- ⚠️ mv_recon 缺 `StreamVGGT` 对照组

**核心发现**（基于 video_depth）：
- 显存峰值下降 56-59%
- bonn 数据集从完全 OOM 到全部成功
- FPS 下降 8-16%（可接受的代价）

**当前默认执行服务器**：
- ✅ 默认使用 **2号机 `amd_server`**（`192.168.166.137`）
- ✅ 推荐落盘：`/mnt/data5/OBVGGT`（代码/数据/runs）
- ℹ️ 3号机（`192.168.166.9`）保留为历史结果与迁移来源

**下一步优先级**：
1. 🔴 补跑 `StreamVGGT` 线的 monodepth regression（验证精度不掉点）
2. 🔴 补跑 `StreamVGGT` 线的 mv_recon baseline
3. 🟡 补齐 CO3D 注释后重跑 pose_evaluation
4. 🟡 用统一实验中台验证 `XStreamVGGT` / `InfiniteVGGT` 的 smoke 与结果 contract
5. 🟡 消融实验（不同 KV 配置）

**详细信息**：先看 `PROJECT_BRIEF.md`，再看 `OBVGGT/experiments/` 目录

---

## 🗂️ 实验管理系统

**新工程师必读**：本项目使用统一的实验管理系统，所有实验记录在 `OBVGGT/experiments/` 目录。

### 快速导航
- **实验追踪表**：`OBVGGT/experiments/EXPERIMENTS.md`（主文档，记录所有实验）
- **结果汇总**：`OBVGGT/experiments/analysis/SUMMARY.md`（已完成实验的详细指标）
- **配置文件**：`OBVGGT/experiments/configs/`（baseline / obcache / xstreamvggt / infinitevggt）
- **快速运行**：`OBVGGT/experiments/quick_run.sh`（一键运行脚本）

### 运行新实验
```bash
cd $STREAMVGGT_CODE/experiments
bash quick_run.sh <variant> <task>
# 例如: bash quick_run.sh baseline monodepth
```

### 实验命名规范
格式：`{date}_{variant}_{task}_{tag}`
- variant: baseline, obcache, incvggt, xstreamvggt
- task: monodepth, video_depth, mv_recon

**重要**：每次实验完成后，更新 `OBVGGT/experiments/EXPERIMENTS.md` 追踪表。

### 跑后文档同步（强制）

每次 run（成功/失败/部分完成）结束后，必须执行：
1. 更新 `OBVGGT/experiments/EXPERIMENTS.md`（状态、缺失数据集、报告路径）。
2. 更新 `OBVGGT/experiments/analysis/SUMMARY.md`（关键指标与对比结论）。
3. 检查 `AGENTS.md` 顶部“项目当前状态”是否需要更新。
4. 检查 `OBVGGT/experiments/README.md` 的“当前状态 / 已知限制 / 下一步”是否需要更新。
5. 在本次 record 的 `Notes / Failures` 中写明“文档已同步”或“已检查无需更新 + 理由”。

---

## 0. Quick Start（新对话秒启动推理）

> 目标：新开对话时，agent 可在 3-5 分钟内进入”可开推理/评测”状态。

### 方式 1：使用实验管理系统（推荐）

```bash
# 1) 连接目标服务器（默认：2号机 amd_server）
ssh -p 2222 szw@192.168.166.137

# 2) 激活环境 + 统一路径
conda activate obvggt
export STREAMVGGT_CODE=/mnt/data5/OBVGGT/code/OBVGGT
export STREAMVGGT_DATA=/mnt/data5/OBVGGT/data
export STREAMVGGT_RUNS=/mnt/data5/OBVGGT/runs
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache

# 3) 登录 SwanLab
export SWANLAB_API_KEY=<YOUR_SWANLAB_API_KEY>
swanlab login
export SWANLAB_PROJECT=OBVGGT

# 4) 开跑前检查
nvidia-smi
df -h | sed -n '1,120p'

# 5) 查看当前实验状态
cat $STREAMVGGT_CODE/experiments/EXPERIMENTS.md

# 6) 运行实验（使用快速脚本）
cd $STREAMVGGT_CODE/experiments
bash quick_run.sh baseline monodepth  # 补跑 baseline
# 或
bash quick_run.sh obcache video_depth  # 跑 obcache
```

### 方式 2：手动运行（传统方式）

```bash
# 前 1-4 步同上

# 5) 手动启动推理评测
export RUN_ID=$(date +%Y%m%d_%H%M%S)
export RUN_NAME=${RUN_ID}_<server>_<exp_tag>
export RUN_DIR=$STREAMVGGT_RUNS/runs/$RUN_NAME
mkdir -p $RUN_DIR
cd $STREAMVGGT_CODE/src
bash eval/monodepth/run.sh 2>&1 | tee $RUN_DIR/monodepth.log

# 6) 记得更新实验追踪表
# 编辑 $STREAMVGGT_CODE/experiments/EXPERIMENTS.md
```

> 如果要跑 `video_depth` 或 `mv_recon`，把最后一条命令替换成对应 `eval/*/run.sh` 或 `launch.py`。

## 1. 生产环境红线（Non‑negotiables）

1. **禁止 sudo**：任何依赖都用 `conda/pip` 安装到虚拟环境。
2. **禁止危险命令**：尤其是 `rm -rf /`、`rm -rf /mnt`、`mkfs`、`dd`、`chmod -R` 等。
3. **禁止把数据/日志写到系统盘**：
   - 所有数据集、训练 checkpoint、评测输出、实验追踪缓存（SwanLab/W&B）**必须落在大盘挂载点**。
   - `~`/系统盘只放轻量代码与少量配置。
4. **先检查再开跑**：每次开跑前必须做：
   - `nvidia-smi`（确认 GPU 空闲/不抢占）
   - `df -h`（确认目标盘剩余空间充足）
   - `du -sh <run_root>`（确认不会持续膨胀到爆盘）
5. **每次跑都要有实验记录**：
   - **开跑前创建 md**，填好“命令/路径/commit/配置/机器/磁盘”。
   - 失败要把 **错误栈、原因、下一步修复**写进去。

---

## 2. 服务器资源（2025/05/11 更新）
请走2222端口
1. (siton_server)3090×2: IP:192.168.166.123 almalinux系统，命令为yum而不是apt。包括/mnt/data 8T，/mnt/data3 10T，/mnt/data4 12T 账号:szw 密码:ANTxp2597 
2. (amd_server)(目前4090D 24g×2、4090D 48G×2，硬盘尺寸均为2.5寸，限制了硬盘容量。除系统盘外，包括1块2T固态，仅用于安装conda虚拟环境，不要放其他文件，以及其他5块5T机械硬盘： IP:192.168.166.137 centos系统，命令为yum而不是apt。 账号:szw 密码:BnSxq3608 
3. (msi_server)3090ti×1: IP:192.168.166.9 
4. (msi_server2)4090×1: IP:192.168.166.2 均为： 账号:szw 密码:BnSxq3608 
5. (x99_server)3090×2: IP:192.168.166.7 账号:szw 密码:AnTxp2597 almalinux系统，命令为yum而不是apt。 除已有的/mnt/data2 10T外，新增/mnt/data 10T（原siton_server: data2） 
6. (x99_server2)3090×2: IP:192.168.166.171 
7. (x99_server3)3090×2: IP:192.168.166.8 新增14T硬盘(/mnt/data3) 均为： 账号:boot 密码:AnTxp2597

### 2.1 机器选择建议

- **显存压力（长序列 / 大分辨率 / 大 batch / 多卡训练）**：优先 `amd_server` 的 4090D 48G。
- **常规评测（monodepth / video_depth / mv_recon）**：3090/3090Ti/4090 都可。
- **避免在小盘机器上下载/解压数据集**：优先在有 10T+ 挂载点机器上做数据准备。
- **本项目当前默认跑机**：`amd_server`（2号机，`192.168.166.137`）。

---

## 3. 目录与磁盘策略（必须按此执行）

### 3.1 统一使用环境变量（避免写死路径）

在每台服务器的 shell（或每次 tmux 会话）设置：

```bash
# 代码仓库目录（建议在 home 下）
export STREAMVGGT_CODE=~/work/OBVGGT

# 数据根目录（必须在大盘上；每台机器自选一个挂载点）
export STREAMVGGT_DATA=/mnt/XXX/obvggt_data

# 实验输出根目录（必须在大盘上）
export STREAMVGGT_RUNS=/mnt/XXX/obvggt_runs

# SwanLab 目录（必须在大盘上，避免写到 ~ 或系统盘）
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache

# 若需兼容 W&B，可同时设置
export WANDB_DIR=$STREAMVGGT_RUNS/wandb
export WANDB_CACHE_DIR=$STREAMVGGT_RUNS/wandb_cache
export WANDB_CONFIG_DIR=$STREAMVGGT_RUNS/wandb_config
```

> `amd_server` 特别规定：
> - 2T SSD **只允许**放 conda 环境与 conda/pip cache
> - 数据集、训练输出、eval_results、swanlab/wandb 目录 **必须**放到 5T HDD（挂载点先用 `df -h` 确认）

### 3.2 用软链接把 repo 变“轻量”

OBVGGT 的相对路径默认假设（从 `src/` 运行）：
- `../data/...`
- `../ckpt/...`

推荐做法：把真正的大数据/大输出放大盘，然后在 repo 根目录做链接：

```bash
cd $STREAMVGGT_CODE
ln -sfn $STREAMVGGT_DATA data
ln -sfn $STREAMVGGT_RUNS/checkpoints checkpoints
ln -sfn $STREAMVGGT_RUNS/eval_results eval_results
ln -sfn $STREAMVGGT_RUNS/swanlab swanlab
ln -sfn $STREAMVGGT_RUNS/wandb wandb
```

> **禁止**把 `data/`、`checkpoints/`、`eval_results/` 放在系统盘。

### 3.3 开跑前磁盘检查（强制）

```bash
nvidia-smi

df -h | sed -n '1,200p'

du -sh $STREAMVGGT_DATA 2>/dev/null || true

du -sh $STREAMVGGT_RUNS 2>/dev/null || true
```

---

## 4. Conda 环境（无 sudo）

### 4.1 创建/复用 conda 环境

> README 参考：python=3.11 + cmake=3.14 + requirements + `llvm-openmp<16`。

```bash
conda create -n obvggt python=3.11 cmake=3.14.0 -y
conda activate obvggt

# 强烈建议：pip/conda cache 放大盘或指定盘（尤其 amd_server）
export PIP_CACHE_DIR=$STREAMVGGT_RUNS/pip_cache
mkdir -p $PIP_CACHE_DIR

pip install -r $STREAMVGGT_CODE/requirements.txt
conda install 'llvm-openmp<16' -y
```

#### amd_server：conda 必须落 2T SSD（仅 conda 用）

先用 `df -h` 找到 2T SSD 的挂载点（示例写作 `$CONDA_SSD`），然后：

```bash
export CONDA_ENVS_PATH=$CONDA_SSD/conda_envs
export CONDA_PKGS_DIRS=$CONDA_SSD/conda_pkgs
mkdir -p $CONDA_ENVS_PATH $CONDA_PKGS_DIRS
```

### 4.2 SwanLab（必须，W&B 可选）

```bash
conda activate obvggt
pip install swanlab

# 不要把 key 写进脚本/仓库
# 用环境变量或交互式登录：
# export SWANLAB_API_KEY=...  (只在当前 shell 有效)
swanlab login

export SWANLAB_PROJECT=OBVGGT
# 若需兼容 W&B：
# pip install wandb && wandb login
# export WANDB_PROJECT=OBVGGT
```

**强制约定**：
- 每个 run 必须有：`run_name`、`group`、`tags`（至少包含 dataset、server、git_commit）。
- `SWANLAB_LOG_DIR/SWANLAB_CACHE_DIR` 必须在大盘。

---

## 5. Checkpoints（必须准备好）

Repo 默认读取：
- `ckpt/model.pt`（teacher / VGGT-1B）
- `ckpt/checkpoints.pth`（OBVGGT checkpoint）

建议把 checkpoint 实际存储放大盘，然后软链接：

```bash
mkdir -p $STREAMVGGT_RUNS/ckpt_store
cd $STREAMVGGT_CODE
mkdir -p ckpt

# 把真实文件放到 $STREAMVGGT_RUNS/ckpt_store 后，再链接到 ckpt/ 下
ln -sfn $STREAMVGGT_RUNS/ckpt_store/model.pt ckpt/model.pt
ln -sfn $STREAMVGGT_RUNS/ckpt_store/checkpoints.pth ckpt/checkpoints.pth
```

> 不要把 checkpoint 下载到系统盘或 /tmp。

---

## 6. 数据集准备（按 OBVGGT 原文/代码跑全）

### 6.1 目录结构（repo 根目录）

OBVGGT 代码默认：

```
OBVGGT/
├── ckpt/
├── data/
│   ├── train/
│   └── eval/
└── src/
```

### 6.2 评测数据集（Evaluation Datasets）

> README 要求：Sintel, Bonn, KITTI, NYU-v2, ScanNet, 7scenes, Neural-RGBD。

**代码里硬编码/默认期望路径**（从 `src/` 运行时）：

- **Sintel**：
  - `../data/eval/sintel/training/final/<seq>/*.png`
  - `../data/eval/sintel/training/camdata_left/<seq>/...`
- **Bonn**：
  - `../data/eval/bonn/rgbd_bonn_dataset/rgbd_bonn_<seq>/rgb_110/*.png`
  - `.../groundtruth_110.txt`
- **KITTI**：
  - `../data/eval/kitti/depth_selection/val_selection_cropped/image_gathered/<dir>/*.png`
- **NYU-v2**：
  - `../data/eval/nyu_v2/val/nyu_images/*.png`
- **ScanNetv2（monodepth 用）**：
  - `../data/eval/scannetv2/<scene>/color_90/*.jpg`
  - `../data/eval/scannetv2/<scene>/pose_90.txt`
- **7scenes（mv_recon 用）**：
  - `../data/eval/7scenes/...`
- **Neural-RGBD（mv_recon 用）**：
  - `../data/eval/neural_rgbd/...`

> ⚠️ 你必须保证“目录名”与代码一致：例如 NYU-v2 是 `nyu_v2`、ScanNet 是 `scannetv2`。

#### 6.2.1 评测覆盖矩阵（强制）

| Task | 必须覆盖数据集 | 必须产物 |
|---|---|---|
| monodepth | `sintel, bonn, kitti, nyu, scannet` | 每个数据集目录下都有 `metric.json` |
| video_depth | `sintel, bonn, kitti` | 每个数据集目录下都有 `result_scale.json` |
| mv_recon | `7scenes, neural_rgbd` | 对应结果目录非空，且日志无报错退出 |
| pose_evaluation | `co3d` | 评测日志成功结束且结果文件存在 |

> 判定规则：只要缺任一“必须产物”，本次状态只能写 `PARTIAL_DONE` 或 `FAILED`，**禁止写 `DONE`**。
> 若日志出现 `NotImplementedError`、`metrics failed`、`WARNING ... failed`，必须在 record 里单列“未完成数据集 + 原因 + 修复计划”。

#### 数据存在性快速检查（开跑前必做）

```bash
cd $STREAMVGGT_CODE/src
python - <<'PY'
import os
paths = [
  '../data/eval/sintel/training/final',
  '../data/eval/bonn/rgbd_bonn_dataset',
  '../data/eval/kitti/depth_selection/val_selection_cropped/image_gathered',
  '../data/eval/nyu_v2/val/nyu_images',
  '../data/eval/scannetv2',
  '../data/eval/7scenes',
  '../data/eval/neural_rgbd',
]
missing=[p for p in paths if not os.path.exists(p)]
print('MISSING:' if missing else 'OK: all eval roots exist')
for p in missing: print('  -', p)
PY
```

#### 6.2.2 跑后产物完整性检查（强制）

```bash
cd $STREAMVGGT_CODE/src
python - <<'PY'
import os, sys

required = [
  # monodepth
  '../eval_results/monodepth/sintel_OBVGGT/metric.json',
  '../eval_results/monodepth/bonn_OBVGGT/metric.json',
  '../eval_results/monodepth/kitti_OBVGGT/metric.json',
  '../eval_results/monodepth/nyu_OBVGGT/metric.json',
  '../eval_results/monodepth/scannet_OBVGGT/metric.json',
  # video_depth
  '../eval_results/video_depth/sintel_OBVGGT/result_scale.json',
  '../eval_results/video_depth/bonn_OBVGGT/result_scale.json',
  '../eval_results/video_depth/kitti_OBVGGT/result_scale.json',
]

missing = [p for p in required if not os.path.isfile(p)]
if missing:
    print('INCOMPLETE: missing outputs')
    for p in missing:
        print('  -', p)
    sys.exit(2)
print('OK: required outputs exist')
PY
```

> 若模型名不是 `OBVGGT`，把路径里的后缀替换成对应 `model_name` 后再检查。

### 6.3 训练数据集（Training Datasets）

> README 提到 14 个训练集；但 `config/train.yaml` 实际列出了 **15 个**（含 PointOdyssey）。

`config/train.yaml` / `config/finetune.yaml` 期望的训练根目录（从 `src/` 运行）：
- `../data/train/processed_co3d/`
- `../data/train/wildrgbd`
- `../data/train/processed_arkitscenes/`
- `../data/train/processed_arkitscenes_highres`
- `../data/train/processed_scannetpp/`
- `../data/train/processed_scannet/`
- `../data/train/hypersim`
- `../data/train/processed_blendedmvs/`
- `../data/train/processed_megadepth`
- `../data/train/waymo/`
- `../data/train/processed_vkitti`
- `../data/train/omniobject3d/`
- `../data/train/spring/`
- `../data/train/mvs_synth`
- `../data/train/point_odyssey`

> 训练数据预处理脚本在 `datasets_preprocess/`，但不同数据集往往受 license/格式影响，下载需从官方来源获取。

---

## 7. 跑实验的标准流程（必须照做）

### 7.1 开跑前（Pre-flight checklist）

1) 选机器，确认 GPU 空闲：
```bash
nvidia-smi
```

2) 确认磁盘空间（目标盘至少预留 300GB+，训练建议 1TB+）：
```bash
df -h
```

3) 建立本次 run 的目录（在 `$STREAMVGGT_RUNS`）：
```bash
export RUN_ID=$(date +%Y%m%d_%H%M%S)
export RUN_NAME=${RUN_ID}_<server>_<exp_tag>
export RUN_DIR=$STREAMVGGT_RUNS/runs/$RUN_NAME
mkdir -p $RUN_DIR
```

4) **创建实验记录 md（必须）**：
```bash
mkdir -p $STREAMVGGT_RUNS/records
cp -n $STREAMVGGT_CODE/docs/templates/record_template.md $STREAMVGGT_RUNS/records/${RUN_NAME}.md 2>/dev/null || true
# 如果模板不存在，就手动创建同名 md，并按本文末模板填写
```

5) 启动 tmux（强制建议）：
```bash
tmux new -s $RUN_NAME
```

6) 在 tmux 内导出关键环境变量并记录到 md：
```bash
conda activate obvggt
export CUDA_VISIBLE_DEVICES=0   # 视机器情况选择
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache
```

### 7.2 跑中（Running）

- 所有命令必须把 stdout/stderr 写到 run 目录：

```bash
cd $STREAMVGGT_CODE/src

# 示例：训练
# accelerate launch --multi_gpu --main_process_port 26902 ./train.py --config-name train \
#   2>&1 | tee $RUN_DIR/train.log

# 示例：评测
# bash eval/monodepth/run.sh 2>&1 | tee $RUN_DIR/monodepth.log
```

- 如果要后台跑，用 `nohup` 也可以，但仍建议 tmux：

```bash
nohup bash eval/monodepth/run.sh > $RUN_DIR/monodepth.log 2>&1 &
```

- 每次出现异常（loss nan / OOM / 卡死）必须：
  1) 先写入 record md（发生时间、日志定位行、推测原因）
  2) 再做修复动作

### 7.3 跑后（Post-run）

- 把以下信息补全到 record md：
  - 完整命令
  - git commit hash
  - 机器/显卡信息（`nvidia-smi` 摘要）
  - 输出路径（checkpoint/eval_results）
  - swanlab run 链接（如同时使用 W&B，可附 W&B 链接）
  - 关键指标（复制 metric.json 的摘要）

### 7.4 “跑完”与“可对比”判定（强制）

1) **跑完（DONE）判定**
- 只有在该 task 的“必须数据集”全部产出结果文件时，才能写 `DONE`。
- 缺任何一个数据集结果，统一写 `PARTIAL_DONE`，并写明缺失原因。

2) **模型对比判定**
- 两个模型必须使用相同数据集集合、相同评测脚本、相同 checkpoint 类型，才可给出“谁更好”的总体结论。
- 若一方缺数据集，只能给“交集数据集对比结论”，并明确标注“非全量结论”。

3) **日志异常兜底**
- 跑后必须执行一次：
```bash
grep -nE "NotImplementedError|metrics failed|WARNING .* failed|Traceback" $RUN_DIR/*.log || true
```
- 命中后必须在 record 的 `Notes / Failures` 中落盘，不得省略。

---

## 8. 标准命令（训练/评测按论文全量跑）

> 下列命令默认：checkpoint 在 `../ckpt/`，数据在 `../data/`，从 `src/` 执行。

### 8.1 训练（Distillation / OBVGGT Training）

```bash
cd $STREAMVGGT_CODE/src
NCCL_DEBUG=TRACE TORCH_DISTRIBUTED_DEBUG=DETAIL HYDRA_FULL_ERROR=1 \
accelerate launch --multi_gpu --main_process_port 26902 ./train.py --config-name train \
  2>&1 | tee $RUN_DIR/train.log
```

### 8.2 微调（Finetuning VGGT）

```bash
cd $STREAMVGGT_CODE/src
NCCL_DEBUG=TRACE TORCH_DISTRIBUTED_DEBUG=DETAIL HYDRA_FULL_ERROR=1 \
accelerate launch --multi_gpu --main_process_port 26902 ./finetune.py --config-name finetune \
  2>&1 | tee $RUN_DIR/finetune.log
```

### 8.3 Monodepth（建议补齐 scannet）

仓库自带 `eval/monodepth/run.sh` 默认只跑：`sintel bonn kitti nyu`。

**按论文“跑全”建议加上 scannet**：

```bash
cd $STREAMVGGT_CODE/src

# 先跑官方 run.sh
bash eval/monodepth/run.sh 2>&1 | tee $RUN_DIR/monodepth_runsh.log

# 再补一个 scannet
model_weights="../ckpt/checkpoints.pth"
output_dir="../eval_results/monodepth/scannet_OBVGGT"
CUDA_LAUNCH_BLOCKING=1 python ./eval/monodepth/launch.py \
  --weights "$model_weights" --output_dir "$output_dir" --eval_dataset scannet \
  2>&1 | tee $RUN_DIR/monodepth_scannet.log

CUDA_LAUNCH_BLOCKING=1 python ./eval/monodepth/eval_metrics.py \
  --output_dir "$output_dir" --eval_dataset scannet \
  2>&1 | tee -a $RUN_DIR/monodepth_scannet.log
```

结果目录：`eval_results/monodepth/${data}_${model_name}/metric.json`

### 8.4 VideoDepth（论文默认：sintel/bonn/kitti）

```bash
cd $STREAMVGGT_CODE/src
bash eval/video_depth/run.sh 2>&1 | tee $RUN_DIR/video_depth.log
```

结果目录：`eval_results/video_depth/${data}_${model_name}/result_scale.json`

### 8.5 Multi-view Reconstruction（mv_recon）

> 注意：仓库里的 `eval/mv_recon/run.sh` 末尾有一个多余的 `\`，可能导致 bash 语法错误。
> 建议直接用下面命令跑（不改源文件，避免污染主分支）：

```bash
cd $STREAMVGGT_CODE/src
model_weights="../ckpt/checkpoints.pth"
output_dir="../eval_results/mv_recon/OBVGGT_checkpoints"

accelerate launch --num_processes 1 --main_process_port 29602 ./eval/mv_recon/launch.py \
  --weights "$model_weights" \
  --output_dir "$output_dir" \
  --model_name "OBVGGT" \
  2>&1 | tee $RUN_DIR/mv_recon.log
```

结果目录：`eval_results/mv_recon/${model_name}_${ckpt_name}/...`

### 8.6 Camera Pose Estimation（CO3D）

依赖（conda env 内安装）：

```bash
pip install pycolmap==3.10.0 pyceres==2.3
git clone https://github.com/cvg/LightGlue.git
cd LightGlue && pip install -e . && cd ..
```

运行：

```bash
cd $STREAMVGGT_CODE/src
python eval/pose_evaluation/test_co3d.py \
  --co3d_dir /PATH/TO/CO3D \
  --co3d_anno_dir /PATH/TO/CO3D_ANNO \
  --seed 0 \
  2>&1 | tee $RUN_DIR/pose_co3d.log
```

### 8.7 KV 策略评测（防“评测不敏感”坑）

> 结论约束：**不要只看 monodepth 就判断 KV 策略有效/无效**。
> 原因：monodepth 常见实现是“单帧/短窗口逐次调用”，对 cache 命中率不敏感，容易出现“改了 KV，指标几乎不变”。

最小评测集合（KV 相关改动必须全跑）：
1. `monodepth`：只做精度回归，不作为 KV 优劣主结论。
2. `video_depth`：作为时序场景主指标。
3. `mv_recon`：作为多视角一致性补充指标。

推荐附加记录（写入 record）：
- KV 配置：`enable/size/policy/alpha/beta/window/stride` 等。
- 缓存行为日志：命中、淘汰、回退（若代码有打印）。
- 对比口径：同数据集、同权重、同分辨率、同随机种子。

---

## 9. SwanLab 记录规范（训练 + 评测）

### 9.1 必填字段

每次 run 必须在 SwanLab 里包含：
- `run_name`：`${RUN_NAME}`
- `group`：例如 `baseline` / `ablation_cache` / `longseq`
- `tags`：至少包含 `server:<name>`、`gpu:<type>`、`dataset:<name>`、`commit:<hash>`
- `config`：把核心超参/开关写进 config（可由 Hydra/argparse 自动采集）

### 9.2 评测结果也要上 SwanLab

如果评测脚本本身没有 SwanLab log：
- 最少做到：评测结束后把 `metric.json` / `result_scale.json` 的关键字段手工写入 record md
- 推荐：写一个 `tools/log_eval_to_swanlab.py` 读取结果文件并 `swanlab.log()`（若你已经实现过，确保所有 eval 都走这一步）

---

## 10. 每次实验必须写的记录（模板）

> **存放位置**：`$STREAMVGGT_RUNS/records/${RUN_NAME}.md`

把下面模板复制进去填写：

```md
# Experiment Record: <RUN_NAME>

## 0. Status
- Status: RUNNING / PARTIAL_DONE / FAILED / DONE
- Start: YYYY-MM-DD HH:MM
- End: YYYY-MM-DD HH:MM (if done)

## 1. Machine
- Server: <siton_server/amd_server/...>
- IP: <optional>
- GPU: (paste `nvidia-smi -L`)
- CUDA_VISIBLE_DEVICES: <...>

## 2. Disk & Paths (MUST)
- STREAMVGGT_CODE: <...>
- STREAMVGGT_DATA: <...>
- STREAMVGGT_RUNS: <...>
- Free space before run: (paste `df -h` relevant lines)

## 3. Code Version
- Git branch: <...>
- Git commit: <...>
- Local diff: (yes/no, brief)

## 4. Environment
- Conda env: obvggt
- Python: (python -V)
- Torch/CUDA: (python -c "import torch; print(torch.__version__, torch.version.cuda)")
- Key deps: flash-attn / accelerate / open3d / pycolmap ...

## 5. Goal
- What are we testing?
- Hypothesis

## 6. Command
```bash
<exact command>
```

## 7. SwanLab
- Project: <...>
- Run URL: <paste link>

## 8. Outputs
- Log file: <path>
- Checkpoints: <path>
- Eval results: <path>

## 9. Metrics (copy summary)
- <metric1>: <...>
- <metric2>: <...>
- Coverage: <expected datasets> / <finished datasets>
- Missing datasets (if any): <name + reason>

## 10. Notes / Failures
- If FAILED: paste error trace + root cause + fix plan
- If PARTIAL_DONE: list missing outputs + blocker + next action
- If RUNNING: current progress, ETA is NOT required, but last checkpoint step/time is
```

---

## 11. 最后提醒（避免事故）

- **任何不确定的删除/移动操作**：先 `ls` + `du -sh` + 写进 record，再执行。
- **磁盘快满**：先停任务（或迁移输出），不要硬跑把系统盘打爆。
- **多人共用**：开跑前确认 GPU 空闲，必要时在群里报备。
