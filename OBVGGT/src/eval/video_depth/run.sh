#!/bin/bash
set -euo pipefail

workdir='..'
variant='baseline'
model_name='streamvggt'
ckpt_name='checkpoints'
model_weights="${workdir}/ckpt/${ckpt_name}.pth"
result_tag=''
output_root="${workdir}/eval_results/video_depth"
extra_args=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --variant)
            variant="$2"
            shift 2
            ;;
        --model_name)
            model_name="$2"
            shift 2
            ;;
        --weights)
            model_weights="$2"
            shift 2
            ;;
        --result_tag)
            result_tag="$2"
            shift 2
            ;;
        --output_root)
            output_root="$2"
            shift 2
            ;;
        *)
            extra_args+=("$1")
            shift
            ;;
    esac
done

if [[ -z "$result_tag" ]]; then
    result_tag="${model_name}_${variant}"
fi

datasets=('sintel' 'bonn' 'kitti')

for data in "${datasets[@]}"; do
    output_dir="${output_root}/${data}_${result_tag}"
    echo "[video_depth] launch -> ${output_dir}"
    CUDA_LAUNCH_BLOCKING=1 accelerate launch --num_processes 1 ../src/eval/video_depth/launch.py \
        --weights "$model_weights" \
        --output_dir "$output_dir" \
        --eval_dataset "$data" \
        --size 518 \
        "${extra_args[@]}"
    echo "[video_depth] metrics -> ${output_dir}"
    python ../src/eval/video_depth/eval_depth.py \
        --output_dir "$output_dir" \
        --eval_dataset "$data" \
        --align "scale"
done
