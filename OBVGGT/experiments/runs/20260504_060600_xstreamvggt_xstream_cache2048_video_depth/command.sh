#!/bin/bash
set -euo pipefail
cd "/mnt/data3/OBVGGT/infra_runtime_20260503/code/2026-0503-infra-runtime-accel-6fc9571/XStreamVGGT"
export KV_POOL_SIZE=16
export KV_CACHE_SIZE=2048
python -m accelerate.commands.launch --num_processes 1 ../src/eval/video_depth/launch.py --weights /mnt/data5/OBVGGT/code/OBVGGT/ckpt/checkpoints.pth --output_dir /mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060600_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/sintel_xstreamvggt_xstream_cache2048 --eval_dataset sintel --size 518 --max_frames 2
python ../src/eval/video_depth/eval_depth.py --output_dir /mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060600_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/sintel_xstreamvggt_xstream_cache2048 --eval_dataset sintel --align scale
python -m accelerate.commands.launch --num_processes 1 ../src/eval/video_depth/launch.py --weights /mnt/data5/OBVGGT/code/OBVGGT/ckpt/checkpoints.pth --output_dir /mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060600_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/bonn_xstreamvggt_xstream_cache2048 --eval_dataset bonn --size 518 --max_frames 2
python ../src/eval/video_depth/eval_depth.py --output_dir /mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060600_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/bonn_xstreamvggt_xstream_cache2048 --eval_dataset bonn --align scale
python -m accelerate.commands.launch --num_processes 1 ../src/eval/video_depth/launch.py --weights /mnt/data5/OBVGGT/code/OBVGGT/ckpt/checkpoints.pth --output_dir /mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060600_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/kitti_xstreamvggt_xstream_cache2048 --eval_dataset kitti --size 518 --max_frames 2
python ../src/eval/video_depth/eval_depth.py --output_dir /mnt/data3/OBVGGT/infra_runtime_20260503/runs/eval_results/by_run/20260504_060600_xstreamvggt_xstream_cache2048_video_depth/video_depth/xstreamvggt/kitti_xstreamvggt_xstream_cache2048 --eval_dataset kitti --align scale
