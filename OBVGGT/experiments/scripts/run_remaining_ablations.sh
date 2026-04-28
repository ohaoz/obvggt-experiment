#!/bin/bash
# Run all remaining ablation experiments on GPU 2
# Phase 3: controls + Phase 4: length sweeps
set -euo pipefail

export CUDA_VISIBLE_DEVICES=2
REPO="/mnt/data5/OBVGGT/code/OBVGGT"
export STREAMVGGT_CODE="$REPO"
EXP_DIR="${REPO}/experiments"
LOG_DIR="/mnt/data5/OBVGGT/runs/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="${LOG_DIR}/remaining_ablations_${TIMESTAMP}.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$MAIN_LOG"; }

log "=== REMAINING ABLATION EXPERIMENTS ==="
log "GPU: $CUDA_VISIBLE_DEVICES"
log "Repo: $REPO"
nvidia-smi --query-gpu=index,name,memory.free --format=csv,noheader 2>/dev/null | tee -a "$MAIN_LOG"

# Resolve conda
CONDA_CMD=""
for c in /mnt/data0/anaconda3/bin/conda "$HOME/anaconda3/bin/conda" "$HOME/miniconda3/bin/conda"; do
    if [[ -x "$c" ]]; then CONDA_CMD="$c"; break; fi
done
if [[ -z "$CONDA_CMD" ]]; then
    log "ERROR: conda not found"
    exit 1
fi
log "Conda: $CONDA_CMD"

run_experiment() {
    local variant="$1"
    local task="$2"
    shift 2
    local label="${variant}_${task}"
    log "--- START: $label ($*) ---"
    local start_ts=$(date +%s)

    local env_name="obvggt"
    if [[ "$variant" == "baseline" ]]; then
        env_name="obvggt"
    fi

    cd "$EXP_DIR"
    set +e
    "$CONDA_CMD" run --no-capture-output -n "$env_name" \
        bash quick_run.sh "$variant" "$task" "$@" 2>&1 | tee -a "$MAIN_LOG"
    local exit_code=${PIPESTATUS[0]}
    set -e

    local end_ts=$(date +%s)
    local elapsed=$(( end_ts - start_ts ))
    log "--- END: $label | exit=$exit_code | elapsed=${elapsed}s ---"
    return $exit_code
}

##############################################
# PHASE 3: Local controls around p=1
##############################################
log ""
log "=========================================="
log "PHASE 3: LOCAL CONTROLS"
log "=========================================="

# 3a. obcache_p1_tight (video_depth)
log "Phase 3a: obcache_p1_tight video_depth"
run_experiment obcache_p1_tight video_depth --seed 0 || log "WARN: obcache_p1_tight failed"

# 3b. obcache_p1_no_recent_ctrl (video_depth)
log "Phase 3b: obcache_p1_no_recent_ctrl video_depth"
run_experiment obcache_p1_no_recent_ctrl video_depth --seed 0 || log "WARN: obcache_p1_no_recent_ctrl failed"

##############################################
# PHASE 4: Prefix-length sweeps
##############################################
log ""
log "=========================================="
log "PHASE 4: PREFIX-LENGTH SWEEPS"
log "=========================================="

FRAME_CAPS=(10 22 37 55 110)
BONN_SEQ="balloon2"
# Only run obcache variants first (baseline may OOM on 24GB)
SWEEP_VARIANTS=(obcache obcache_p1 obcache_p1_small obcache_sliding_window)

for max_frames in "${FRAME_CAPS[@]}"; do
    for variant in "${SWEEP_VARIANTS[@]}"; do
        log "Length sweep: $variant framecap=$max_frames (Bonn $BONN_SEQ)"
        run_experiment "$variant" video_depth \
            --dataset-filter bonn \
            --seq_list "$BONN_SEQ" \
            --max_frames "$max_frames" \
            --seed 0 \
            || log "WARN: $variant framecap=$max_frames failed"
    done
done

# Try baseline length sweeps (may OOM on 24GB for larger caps)
for max_frames in "${FRAME_CAPS[@]}"; do
    log "Length sweep: baseline framecap=$max_frames (Bonn $BONN_SEQ)"
    run_experiment baseline video_depth \
        --dataset-filter bonn \
        --seq_list "$BONN_SEQ" \
        --max_frames "$max_frames" \
        --seed 0 \
        || log "WARN: baseline framecap=$max_frames failed (expected on 24GB for large caps)"
done

##############################################
# BONUS: Baseline full video_depth rerun
##############################################
log ""
log "=========================================="
log "BONUS: BASELINE VIDEO_DEPTH RERUN"
log "=========================================="
log "Attempting baseline video_depth full on 24GB GPU..."
run_experiment baseline video_depth --seed 0 \
    || log "WARN: baseline full rerun failed (expected on 24GB - Bonn may OOM)"

log ""
log "=========================================="
log "ALL EXPERIMENTS COMPLETE"
log "=========================================="
log "Main log: $MAIN_LOG"
