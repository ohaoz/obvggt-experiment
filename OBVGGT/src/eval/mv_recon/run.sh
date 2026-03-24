#!/bin/bash
set -euo pipefail

workdir='..'
variant='baseline'
model_name='StreamVGGT'
ckpt_name='checkpoints'
model_weights="${workdir}/ckpt/${ckpt_name}.pth"
result_tag=''
output_root="${workdir}/eval_results/mv_recon"
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

output_dir="${output_root}/${result_tag}"
echo "[mv_recon] launch -> ${output_dir}"
accelerate launch --num_processes 1 --main_process_port 29602 ./eval/mv_recon/launch.py \
    --weights "$model_weights" \
    --output_dir "$output_dir" \
    --model_name "$model_name" \
    "${extra_args[@]}"
