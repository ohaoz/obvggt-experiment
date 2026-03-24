#!/bin/bash
# Watch all GPUs and launch baseline monodepth on the first free card.
set -u

BATCH_ROOT=/mnt/data5/OBVGGT/runs/batch_runs
SCRIPT_NAME="20260316_wait_and_run_baseline_monodepth"

source /mnt/data0/anaconda3/etc/profile.d/conda.sh
conda activate obvggt
export PYTHONNOUSERSITE=1
export STREAMVGGT_CODE=/mnt/data5/OBVGGT/code/OBVGGT
export STREAMVGGT_DATA=/mnt/data5/OBVGGT/data
export STREAMVGGT_RUNS=/mnt/data5/OBVGGT/runs
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache
mkdir -p "$BATCH_ROOT" "$SWANLAB_LOG_DIR" "$SWANLAB_CACHE_DIR"

LOG_FILE="$BATCH_ROOT/${SCRIPT_NAME}.log"
SUMMARY_FILE="$BATCH_ROOT/${SCRIPT_NAME}.summary.txt"
GPU_ALL="0 1 2 3"

echo "[WAIT] $(date '+%F %T') Watching GPUs: $GPU_ALL for baseline monodepth..." | tee "$SUMMARY_FILE"

FOUND_GPU=""
while [ -z "$FOUND_GPU" ]; do
  for gpu in $GPU_ALL; do
    MEM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $gpu | tr -d ' ')
    if [ "$MEM_USED" -lt 500 ]; then
      FOUND_GPU=$gpu
      break
    fi
  done
  if [ -z "$FOUND_GPU" ]; then
    sleep 60
  fi
done

export CUDA_VISIBLE_DEVICES=$FOUND_GPU
echo "[READY] $(date '+%F %T') GPU $FOUND_GPU is free" | tee -a "$SUMMARY_FILE"

cd "$STREAMVGGT_CODE/experiments"
echo "[START] $(date '+%F %T') baseline monodepth" | tee -a "$SUMMARY_FILE"
bash quick_run.sh baseline monodepth 2>&1 | tee -a "$LOG_FILE"
RC=${PIPESTATUS[0]}
echo "[DONE] $(date '+%F %T') baseline monodepth rc=$RC" | tee -a "$SUMMARY_FILE"
exit "$RC"
