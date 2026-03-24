#!/bin/bash
set -euo pipefail

source /mnt/data0/anaconda3/etc/profile.d/conda.sh
conda activate obvggt

LOG_ROOT=/mnt/data5/OBVGGT/runs/batch_runs
mkdir -p "$LOG_ROOT"
LOG_FILE="$LOG_ROOT/continuous_watch_amd.log"

RUN_ROOT=/mnt/data5/OBVGGT/code/OBVGGT/experiments/runs
CO3D_ROOT=/mnt/data5/OBVGGT/data/eval/co3d_raw_data
ANNO_ROOT=/mnt/data5/OBVGGT/data/co3d_v2_annotations

log() {
  echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"
}

tail_safe() {
  local file="$1"
  local lines="${2:-20}"
  if [[ -f "$file" ]]; then
    tail -n "$lines" "$file" | tee -a "$LOG_FILE"
  else
    log "missing file: $file"
  fi
}

while true; do
  log "===== heartbeat ====="
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | tee -a "$LOG_FILE"

  log "===== recent run records ====="
  for run_dir in \
    "$RUN_ROOT/20260318_200314_infinitevggt_rolling_memory_budget1200000_mv_recon" \
    "$RUN_ROOT/20260318_202918_infinitevggt_rolling_memory_budget1200000_monodepth"; do
    if [[ -f "$run_dir/record.md" ]]; then
      echo "--- $(basename "$run_dir")" | tee -a "$LOG_FILE"
      grep -nE "Status:|Start:|End:|Exit code:" "$run_dir/record.md" | tee -a "$LOG_FILE" || true
    fi
  done

  log "===== pose queue ====="
  tail_safe "$LOG_ROOT/20260318_203359_wait_for_co3d_and_run_pose.log" 20

  log "===== co3d roots ====="
  du -sh "$CO3D_ROOT" 2>/dev/null | tee -a "$LOG_FILE" || log "co3d root missing"
  find "$CO3D_ROOT" -maxdepth 2 -name frame_annotations.jgz 2>/dev/null | wc -l | awk '{print "frame_annotation_categories=" $1}' | tee -a "$LOG_FILE"
  du -sh "$ANNO_ROOT" 2>/dev/null | tee -a "$LOG_FILE" || log "anno root missing"
  find "$ANNO_ROOT" -maxdepth 1 -name '*_test.jgz' 2>/dev/null | wc -l | awk '{print "generated_test_jgz=" $1}' | tee -a "$LOG_FILE"

  log "===== batch logs ====="
  tail_safe "$LOG_ROOT/20260318_infinitevggt_mv_recon_gpu3.log" 15
  tail_safe "$LOG_ROOT/20260318_infinitevggt_monodepth_gpu1.log" 15

  sleep 60
done
