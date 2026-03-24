#!/bin/bash
set -euo pipefail

source /mnt/data0/anaconda3/etc/profile.d/conda.sh
conda activate obvggt

export PYTHONNOUSERSITE=1
export STREAMVGGT_CODE=/mnt/data5/OBVGGT/code/OBVGGT
export STREAMVGGT_DATA=/mnt/data5/OBVGGT/data
export STREAMVGGT_RUNS=/mnt/data5/OBVGGT/runs
export SWANLAB_LOG_DIR=$STREAMVGGT_RUNS/swanlab
export SWANLAB_CACHE_DIR=$STREAMVGGT_RUNS/swanlab_cache

mkdir -p "$STREAMVGGT_RUNS/batch_runs" "$SWANLAB_LOG_DIR" "$SWANLAB_CACHE_DIR"

SCRIPT_TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$STREAMVGGT_RUNS/batch_runs/${SCRIPT_TS}_wait_for_co3d_and_run_pose.log"
CO3D_DIR="$STREAMVGGT_DATA/eval/co3d_raw_data"
CO3D_ANNO_DIR="$STREAMVGGT_DATA/co3d_v2_annotations"
REQUIRED_CATEGORY_COUNT=50

log() {
  echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"
}

count_categories() {
  find "$CO3D_DIR" -maxdepth 2 -name frame_annotations.jgz 2>/dev/null | wc -l
}

wait_for_co3d_data() {
  log "Waiting for CO3D raw data under $CO3D_DIR"
  while true; do
    count=$(count_categories)
    log "Detected CO3D categories: $count"
    if [[ "$count" -ge "$REQUIRED_CATEGORY_COUNT" ]]; then
      break
    fi
    sleep 300
  done
}

ensure_pose_deps() {
  python - <<'PY'
mods = ['pycolmap', 'pyceres', 'lightglue']
missing = []
for mod in mods:
    try:
        __import__(mod)
    except Exception:
        missing.append(mod)
if missing:
    raise SystemExit("missing pose deps: " + ",".join(missing))
PY
}

prepare_annotations() {
  mkdir -p "$CO3D_ANNO_DIR"
  log "Generating CO3D annotations into $CO3D_ANNO_DIR"
  python "$STREAMVGGT_CODE/datasets_preprocess/preprocess_co3d.py" \
    --co3d_dir "$CO3D_DIR" \
    --output_dir "$CO3D_ANNO_DIR" \
    | tee -a "$LOG_FILE"
}

find_free_gpu() {
  for gpu in 1 3; do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i "$gpu" | tr -d ' ')
    if [[ "$free" -ge 40000 ]]; then
      echo "$gpu"
      return 0
    fi
  done
  return 1
}

run_pose_variant() {
  local variant="$1"
  local gpu=""
  while [[ -z "$gpu" ]]; do
    if gpu=$(find_free_gpu); then
      break
    fi
    log "No free 48G GPU for $variant pose_co3d yet; sleeping 120s"
    sleep 120
  done

  log "Launching $variant pose_co3d on GPU $gpu"
  export CUDA_VISIBLE_DEVICES="$gpu"
  cd "$STREAMVGGT_CODE/experiments"
  bash quick_run.sh "$variant" pose_co3d \
    --pose-co3d-dir "$CO3D_DIR" \
    --pose-co3d-anno-dir "$CO3D_ANNO_DIR" \
    2>&1 | tee -a "$LOG_FILE"
}

main() {
  log "=== pose queue started ==="
  ensure_pose_deps
  wait_for_co3d_data
  prepare_annotations
  run_pose_variant baseline
  run_pose_variant obcache
  run_pose_variant xstreamvggt
  run_pose_variant infinitevggt
  log "=== pose queue finished ==="
}

main "$@"
