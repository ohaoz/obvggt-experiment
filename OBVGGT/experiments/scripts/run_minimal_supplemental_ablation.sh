#!/bin/bash
# Minimal supplemental ablation package for expert-facing evidence closure.
#
# Phases:
#   baseline  - clean baseline rerun
#   stability - 3-seed repeats for default / p1_small / random
#   controls  - local controls around p=1
#   length    - prefix-length sweeps on Bonn (+ optional KITTI)
#   all       - everything above
#
# Usage:
#   bash experiments/scripts/run_minimal_supplemental_ablation.sh all
#   KITTI_SEQ=<kitti_dir_name> bash experiments/scripts/run_minimal_supplemental_ablation.sh length

set -euo pipefail

PHASE="${1:-all}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXP_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
MANIFEST_PATH="${EXP_ROOT}/runs/supplemental_ablation_${TIMESTAMP}.tsv"
FRAME_CAPS=(${FRAME_CAPS:-10 22 37 55 110})
BONN_SEQ="${BONN_SEQ:-balloon2}"
KITTI_SEQ="${KITTI_SEQ:-}"
BASELINE_ENV="${BASELINE_ENV:-obvggt}"

resolve_conda() {
    if command -v conda >/dev/null 2>&1; then
        command -v conda
        return 0
    fi
    local candidate
    for candidate in \
        /mnt/data0/anaconda3/bin/conda \
        "$HOME/anaconda3/bin/conda" \
        "$HOME/miniconda3/bin/conda"
    do
        if [[ -x "${candidate}" ]]; then
            echo "${candidate}"
            return 0
        fi
    done
    return 1
}

mkdir -p "${EXP_ROOT}/runs"
printf "label\trun_id\texit_code\tvariant\ttask\targs\n" > "${MANIFEST_PATH}"

run_and_capture() {
    local label="$1"
    local variant="$2"
    local task="$3"
    shift 3

    local tmp_log
    tmp_log="$(mktemp)"

    set +e
    local env_name="obvggt"
    if [[ "${variant}" == "baseline" ]]; then
        env_name="${BASELINE_ENV}"
    fi

    (
        cd "${EXP_ROOT}"
        local conda_cmd
        if ! conda_cmd="$(resolve_conda)"; then
            echo "[ERROR] conda command not found while preparing env ${env_name}"
            exit 1
        fi
        "${conda_cmd}" run --no-capture-output -n "${env_name}" \
            bash quick_run.sh "${variant}" "${task}" "$@"
    ) 2>&1 | tee "${tmp_log}"
    local exit_code=${PIPESTATUS[0]}
    set -e

    local run_id
    run_id="$(grep -m1 '^Run ID:' "${tmp_log}" | awk '{print $3}')"
    rm -f "${tmp_log}"

    printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
        "${label}" \
        "${run_id:-unknown}" \
        "${exit_code}" \
        "${variant}" \
        "${task}" \
        "$*" >> "${MANIFEST_PATH}"

    if [[ "${exit_code}" -ne 0 ]]; then
        echo "[ERROR] ${label} failed (variant=${variant}, task=${task})"
        exit "${exit_code}"
    fi
}

run_baseline_phase() {
    run_and_capture "baseline_clean_rerun" baseline video_depth --seed 0
}

run_stability_phase() {
    local variants=(
        obcache_default_s1
        obcache_default_s2
        obcache_default_s3
        obcache_p1_small_s1
        obcache_p1_small_s2
        obcache_p1_small_s3
        obcache_random_s1
        obcache_random_s2
        obcache_random_s3
    )
    local variant
    for variant in "${variants[@]}"; do
        run_and_capture "stability_${variant}" "${variant}" video_depth
    done
}

run_controls_phase() {
    run_and_capture "control_obcache_p1_tight" obcache_p1_tight video_depth
    run_and_capture "control_obcache_p1_no_recent_ctrl" obcache_p1_no_recent_ctrl video_depth
}

run_length_phase() {
    local variants=(baseline obcache obcache_p1 obcache_p1_small obcache_sliding_window)
    local variant
    local max_frames

    for max_frames in "${FRAME_CAPS[@]}"; do
        for variant in "${variants[@]}"; do
            run_and_capture \
                "length_bonn_${variant}_${BONN_SEQ}_${max_frames}" \
                "${variant}" \
                video_depth \
                --dataset-filter bonn \
                --seq_list "${BONN_SEQ}" \
                --max_frames "${max_frames}" \
                --seed 0
        done
    done

    if [[ -z "${KITTI_SEQ}" ]]; then
        echo "[WARN] KITTI_SEQ is not set; skipping KITTI length sweep."
        echo "[WARN] Re-run with KITTI_SEQ=<directory_name> to collect the second curve family."
        return
    fi

    for max_frames in "${FRAME_CAPS[@]}"; do
        for variant in "${variants[@]}"; do
            run_and_capture \
                "length_kitti_${variant}_${KITTI_SEQ}_${max_frames}" \
                "${variant}" \
                video_depth \
                --dataset-filter kitti \
                --seq_list "${KITTI_SEQ}" \
                --max_frames "${max_frames}" \
                --seed 0
        done
    done
}

case "${PHASE}" in
    baseline)
        run_baseline_phase
        ;;
    stability)
        run_stability_phase
        ;;
    controls)
        run_controls_phase
        ;;
    length)
        run_length_phase
        ;;
    all)
        run_baseline_phase
        run_stability_phase
        run_controls_phase
        run_length_phase
        ;;
    *)
        echo "Usage: bash experiments/scripts/run_minimal_supplemental_ablation.sh [baseline|stability|controls|length|all]"
        exit 1
        ;;
esac

echo "[OK] supplemental ablation manifest: ${MANIFEST_PATH}"
