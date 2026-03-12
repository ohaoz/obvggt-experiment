#!/bin/bash
set -euo pipefail

workdir='..'
variant='baseline'
model_name='StreamVGGT'
ckpt_name='checkpoints'
model_weights="${workdir}/ckpt/${ckpt_name}.pth"
result_tag=''
output_root="${workdir}/eval_results/monodepth"
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

datasets=('sintel' 'bonn' 'kitti' 'nyu')

for data in "${datasets[@]}"; do
    output_dir="${output_root}/${data}_${result_tag}"
    echo "[monodepth] launch -> ${output_dir}"
    CUDA_LAUNCH_BLOCKING=1 python ./eval/monodepth/launch.py \
        --weights "$model_weights" \
        --output_dir "$output_dir" \
        --eval_dataset "$data" \
        "${extra_args[@]}"
done

for data in "${datasets[@]}"; do
    output_dir="${output_root}/${data}_${result_tag}"
    echo "[monodepth] metrics -> ${output_dir}"
    CUDA_LAUNCH_BLOCKING=1 python ./eval/monodepth/eval_metrics.py \
        --output_dir "$output_dir" \
        --eval_dataset "$data"
done
