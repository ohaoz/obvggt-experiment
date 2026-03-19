#!/bin/bash
# Smart GPU watcher: polls all GPUs, grabs the first free one.
# - Any GPU: run InfiniteVGGT video_depth + mv_recon
# - 48G GPU (1 or 3): also run baseline + OBVGGT video_depth
set -u

BATCH_ROOT=/mnt/data5/OBVGGT/runs/batch_runs
SCRIPT_NAME="20260315_smart_wait_and_run"
source /mnt/data0/anaconda3/etc/profile.d/conda.sh
conda activate obvggt
export PYTHONNOUSERSITE=1
export STREAMVGGT_CODE=/mnt/data5/OBVGGT/code/OBVGGT
export STREAMVGGT_DATA=/mnt/data5/OBVGGT/data
export STREAMVGGT_RUNS=/mnt/data5/OBVGGT/runs
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache
mkdir -p "$SWANLAB_LOG_DIR" "$SWANLAB_CACHE_DIR"

LOG_FILE="$BATCH_ROOT/${SCRIPT_NAME}.log"
SUMMARY_FILE="$BATCH_ROOT/${SCRIPT_NAME}.summary.txt"
BATCH_FAILED=0

# 48G GPUs
GPU_48G="1 3"
# All GPUs to watch
GPU_ALL="0 1 2 3"

echo "[WAIT] $(date '+%F %T') Watching GPUs: $GPU_ALL for first free slot..." | tee "$SUMMARY_FILE"

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
MEM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i $FOUND_GPU | tr -d ' ')

echo "[READY] $(date '+%F %T') GPU $FOUND_GPU is free (${MEM_TOTAL}MiB total)" | tee -a "$SUMMARY_FILE"

IS_48G=false
for g48 in $GPU_48G; do
  if [ "$FOUND_GPU" = "$g48" ]; then
    IS_48G=true
    break
  fi
done

{
  echo "[BATCH] start $(date '+%F %T')"
  echo "[BATCH] env $CONDA_DEFAULT_ENV"
  echo "[BATCH] cuda $CUDA_VISIBLE_DEVICES"
  echo "[BATCH] is_48g $IS_48G"
  nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu --format=csv,noheader -i $FOUND_GPU
  df -h /mnt/data5 | sed -n '1,5p'
} | tee -a "$SUMMARY_FILE"

cd "$STREAMVGGT_CODE/experiments"

run_one() {
  local variant="$1"
  local task="$2"
  echo "[START] $(date '+%F %T') $variant $task" | tee -a "$SUMMARY_FILE"
  bash quick_run.sh "$variant" "$task" 2>&1 | tee -a "$LOG_FILE"
  local rc=${PIPESTATUS[0]}
  echo "[DONE] $(date '+%F %T') $variant $task rc=$rc" | tee -a "$SUMMARY_FILE"
  return "$rc"
}

# Always run InfiniteVGGT
run_one infinitevggt video_depth || BATCH_FAILED=1
run_one infinitevggt mv_recon || BATCH_FAILED=1

# If 48G card, also run the OOM-failed video_depth tasks
if [ "$IS_48G" = "true" ]; then
  echo "[INFO] 48G card detected, running baseline + OBVGGT video_depth" | tee -a "$SUMMARY_FILE"
  run_one baseline video_depth || BATCH_FAILED=1
  run_one obcache video_depth || BATCH_FAILED=1
fi

echo "[BATCH] finish $(date '+%F %T') rc=$BATCH_FAILED" | tee -a "$SUMMARY_FILE"
exit "$BATCH_FAILED"
