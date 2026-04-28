# OBVGGT Demo

答辩演示应用，对比 StreamVGGT（全缓存基线）与 OBVGGT（压缩缓存）的效果差异。

## 环境要求

- NVIDIA GPU（推荐 24 GB 以上显存）
- CUDA 11.8+
- Python 3.10+
- 模型权重 `ckpt/checkpoints.pth`（约 2 GB）

## 安装

```bash
cd OBVGGT
pip install -r demo_a/requirements.txt
```

如果没有模型权重：

```bash
pip install huggingface_hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('lch01/StreamVGGT', 'checkpoints.pth', local_dir='ckpt')"
```

## 启动

```bash
cd OBVGGT
python demo_a/app.py
```

可选参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--port` | 7860 | 服务端口 |
| `--share` | off | 生成 Gradio 公网链接 |

## 远程访问（SSH 隧道）

服务器端启动 demo 后，本地通过 Tailscale 跳板机建立隧道：

```bash
ssh -L 7860:localhost:7860 user@<tailscale-ip>
```

然后浏览器打开 http://localhost:7860

## 功能

### Tab 1: 3D Reconstruction Comparison

上传多张图片（或使用内置 example_building 样例），同时运行 baseline 和 OBVGGT，并排展示：

- 两个可交互的 3D 点云查看器
- 峰值显存对比
- FPS 对比

可选择不同 OBVGGT 配置（默认 `p1_no_recent_ctrl` 最优配置）。

### Tab 2: Video Depth Estimation

上传视频，提取帧后分别用 baseline 和 OBVGGT 进行流式深度估计：

- 横向对比：原始帧 | 基线深度图 | OBVGGT 深度图
- 显存曲线（baseline 红线 vs OBVGGT 蓝线）
- 长序列下 baseline OOM 时显示红色占位

### Tab 3: Ablation Experiments

从 `ablation_video_depth_20260324.csv` 加载预计算消融数据，展示交互式 Plotly 图表：

- 缓存预算 vs 精度（KITTI Abs Rel）
- 评分方法对比（V+K Joint / V Only / K Only / Random / Sliding Window）

## 环境检测

启动时自动检测并在页面顶部显示：

- GPU 型号和显存
- 模型权重是否存在
- 依赖包是否齐全
- 可用磁盘空间

也可单独运行检测：

```bash
python demo_a/check_env.py
```

## 文件结构

```
demo_a/
├── app.py            # Gradio 主应用（3 个 Tab）
├── inference.py      # 模型加载 + baseline/OBVGGT 推理封装
├── monitor.py        # GPU 显存和 FPS 监控
├── viz.py            # 深度图着色、显存曲线、消融图表
├── check_env.py      # 启动前环境检测
├── requirements.txt  # 依赖列表
└── README.md         # 本文件
```
