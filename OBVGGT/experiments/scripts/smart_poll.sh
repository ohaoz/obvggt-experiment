#!/bin/bash
# Smart GPU polling script for OBVGGT experiment catch-up.
# Watches GPU free memory and dispatches tasks that fit.
#
# Usage:
#   bash smart_poll.sh              # default: poll every 2 min
#   bash smart_poll.sh --interval 120  # custom interval in seconds
#   bash smart_poll.sh --dry-run    # show what would run without executing
#
# Task queue is defined inline below. Edit TASK_QUEUE to add/remove tasks.
# Each entry: "variant task min_free_mib preferred_gpus"
#   - min_free_mib: minimum free VRAM (MiB) required on the GPU
#   - preferred_gpus: comma-separated GPU indices (or "any")

set -uo pipefail

# ── Configuration ──────────────────────────────────────────────
POLL_INTERVAL=120   # seconds between polls
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval) POLL_INTERVAL="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ── Environment ────────────────────────────────────────────────
source /mnt/data0/anaconda3/etc/profile.d/conda.sh
conda activate obvggt
export PYTHONNOUSERSITE=1
export STREAMVGGT_CODE=/mnt/data5/OBVGGT/code/OBVGGT
export STREAMVGGT_DATA=/mnt/data5/OBVGGT/data
export STREAMVGGT_RUNS=/mnt/data5/OBVGGT/runs
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache
mkdir -p "$SWANLAB_LOG_DIR" "$SWANLAB_CACHE_DIR"

BATCH_ROOT=/mnt/data5/OBVGGT/runs/batch_runs
SCRIPT_TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BATCH_ROOT/${SCRIPT_TS}_smart_poll.log"
SUMMARY_FILE="$BATCH_ROOT/${SCRIPT_TS}_smart_poll.summary.txt"
STATE_FILE="$BATCH_ROOT/.smart_poll_state"

# ── Task Queue ─────────────────────────────────────────────────
# Format: "variant|task|min_free_mib|preferred_gpus"
# Tasks are tried in order. Completed tasks are skipped.
#
# 48G tasks: baseline/obcache video_depth, infinitevggt mv_recon
# These need a mostly-free 48G card (GPU 1 or 3).
TASK_QUEUE=(
  "baseline|video_depth|40000|1,3"
  "obcache|video_depth|40000|1,3"
  "infinitevggt|mv_recon|40000|1,3"
)

# ── Helpers ────────────────────────────────────────────────────
ts() { date '+%Y-%m-%d %H:%M:%S'; }

log() {
  echo "[$(ts)] $*" | tee -a "$LOG_FILE"
}

log_summary() {
  echo "[$(ts)] $*" | tee -a "$LOG_FILE" >> "$SUMMARY_FILE"
}

# Load completed tasks from state file
declare -A COMPLETED
if [[ -f "$STATE_FILE" ]]; then
  while IFS= read -r line; do
    COMPLETED["$line"]=1
  done < "$STATE_FILE"
fi

mark_done() {
  local key="$1"
  COMPLETED["$key"]=1
  echo "$key" >> "$STATE_FILE"
}

is_done() {
  local key="$1"
  [[ "${COMPLETED[$key]:-}" == "1" ]]
}

# Get free VRAM (MiB) for a GPU index
gpu_free_mib() {
  local gpu_idx="$1"
  local used total
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$gpu_idx" | tr -d ' ')
  total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i "$gpu_idx" | tr -d ' ')
  echo $(( total - used ))
}

# Find a suitable GPU for a task
find_gpu() {
  local min_free="$1"
  local preferred="$2"
  local gpu_list

  if [[ "$preferred" == "any" ]]; then
    gpu_list="0 1 2 3"
  else
    gpu_list="${preferred//,/ }"
  fi

  for gpu in $gpu_list; do
    local free
    free=$(gpu_free_mib "$gpu")
    if [[ "$free" -ge "$min_free" ]]; then
      echo "$gpu"
      return 0
    fi
  done
  return 1
}

# Run one experiment
run_task() {
  local variant="$1" task="$2" gpu="$3"
  local task_key="${variant}|${task}"

  export CUDA_VISIBLE_DEVICES="$gpu"
  log_summary "START $variant $task on GPU $gpu (free: $(gpu_free_mib "$gpu") MiB)"

  if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY-RUN] Would run: quick_run.sh $variant $task on GPU $gpu"
    mark_done "$task_key"
    return 0
  fi

  cd "$STREAMVGGT_CODE/experiments"
  bash quick_run.sh "$variant" "$task" 2>&1 | tee -a "$LOG_FILE"
  local rc=${PIPESTATUS[0]}

  if [[ $rc -eq 0 ]]; then
    log_summary "OK    $variant $task rc=0"
    mark_done "$task_key"
  else
    log_summary "FAIL  $variant $task rc=$rc"
  fi

  return "$rc"
}

# ── GPU status report ──────────────────────────────────────────
gpu_status() {
  for gpu in 0 1 2 3; do
    local used total free
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$gpu" | tr -d ' ')
    total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i "$gpu" | tr -d ' ')
    free=$(( total - used ))
    echo "  GPU$gpu: ${used}/${total} MiB used, ${free} MiB free"
  done
}

# ── Main Loop ──────────────────────────────────────────────────
log_summary "=== smart_poll started ==="
log_summary "Poll interval: ${POLL_INTERVAL}s"
log_summary "Tasks in queue: ${#TASK_QUEUE[@]}"
log "DRY_RUN=$DRY_RUN"

# Print queue
for entry in "${TASK_QUEUE[@]}"; do
  IFS='|' read -r v t m g <<< "$entry"
  local_key="${v}|${t}"
  status="PENDING"
  is_done "$local_key" && status="DONE (skipped)"
  log "  $v $t  min_free=${m}MiB  gpus=$g  [$status]"
done

BATCH_FAILED=0

while true; do
  # Check if all tasks are done
  all_done=true
  for entry in "${TASK_QUEUE[@]}"; do
    IFS='|' read -r v t m g <<< "$entry"
    is_done "${v}|${t}" || { all_done=false; break; }
  done
  if [[ "$all_done" == "true" ]]; then
    log_summary "All tasks completed. Exiting."
    break
  fi

  # Show GPU status
  log "--- Poll ---"
  gpu_status | while read -r line; do log "$line"; done

  # Try to find a runnable task
  ran_something=false
  for entry in "${TASK_QUEUE[@]}"; do
    IFS='|' read -r v t min_free preferred <<< "$entry"
    local_key="${v}|${t}"

    # Skip completed
    is_done "$local_key" && continue

    # Find a GPU
    gpu=$(find_gpu "$min_free" "$preferred") || continue

    # Run it
    run_task "$v" "$t" "$gpu" || BATCH_FAILED=1
    ran_something=true
    break  # Re-poll after each task
  done

  if [[ "$ran_something" == "false" ]]; then
    log "No GPU available for pending tasks. Sleeping ${POLL_INTERVAL}s..."
    sleep "$POLL_INTERVAL"
  fi
done

log_summary "=== smart_poll finished (rc=$BATCH_FAILED) ==="
exit "$BATCH_FAILED"
