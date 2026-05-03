#!/bin/bash
set -euo pipefail
cd "/mnt/data5/OBVGGT/code/branches/2026-0503-fps-verify"
python -m accelerate.commands.launch --num_processes 1 ../src/eval/video_depth/launch.py --weights /mnt/data5/OBVGGT/code/OBVGGT/ckpt/checkpoints.pth --output_dir /mnt/data3/OBVGGT/fps_verify_20260503/eval_results/by_run/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4 --eval_dataset bonn --size 518 --kv_cache_enable true --kv_cache_cfg_json '{"enable":true,"method":"obcvk","p":1,"use_vnorm":true,"num_sink_frames":1,"num_recent_frames":0,"num_heavy_frames":4,"probe_mode":true,"num_patch_probes":8}'
python ../src/eval/video_depth/eval_depth.py --output_dir /mnt/data3/OBVGGT/fps_verify_20260503/eval_results/by_run/20260503_105845_obcache_p1_no_recent_ctrl_joint_s1r0h4_video_depth/video_depth/obcache_p1_no_recent_ctrl/bonn_obcache_p1_no_recent_ctrl_joint_s1r0h4 --eval_dataset bonn --align scale
