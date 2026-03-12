#!/bin/bash
# Unified experiment launcher.
# Usage: bash quick_run.sh <variant> <task> [task-specific args...]

set -euo pipefail

VARIANT=${1:-}
TASK=${2:-}
shift $(( $# >= 2 ? 2 : $# ))
EXTRA_ARGS=("$@")

if [[ -z "${VARIANT}" || -z "${TASK}" ]]; then
    echo "Usage: bash quick_run.sh <variant> <task> [task-specific args...]"
    echo ""
    echo "Runnable variants:"
    echo "  baseline      - StreamVGGT full-cache baseline"
    echo "  obcache       - OBVGGT / your KV-compressed method"
    echo "  xstreamvggt   - pruning (+ optional quantization) baseline"
    echo "  infinitevggt  - rolling-memory long-stream baseline"
    echo ""
    echo "Tasks:"
    echo "  monodepth     - regression-only"
    echo "  video_depth   - primary short/medium streaming benchmark"
    echo "  mv_recon      - primary multiview benchmark"
    echo "  pose_co3d     - camera pose benchmark"
    echo "  long_stream   - long-horizon / endless-stream benchmark"
    echo ""
    echo "Example:"
    echo "  bash quick_run.sh baseline video_depth --seq_list alley_2"
    echo "  bash quick_run.sh infinitevggt long_stream --input-dir /path/to/frames"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNS_DIR="${SCRIPT_DIR}/runs"
SCRIPTS_DIR="${SCRIPT_DIR}/scripts"
CONFIG_FILE="${SCRIPT_DIR}/configs/${VARIANT}.json"

if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "Error: missing config ${CONFIG_FILE}"
    exit 1
fi

if [[ -z "${STREAMVGGT_CODE:-}" ]]; then
    echo "Error: please export STREAMVGGT_CODE before running quick_run.sh"
    exit 1
fi

mapfile -t CONFIG_VALUES < <(
    python - "${CONFIG_FILE}" "${TASK}" <<'PY'
import json
import sys

config_path, task = sys.argv[1], sys.argv[2]
with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

variant = cfg.get("variant", "unknown")
runnable = bool(cfg.get("runnable", False))
supported = cfg.get("supported_tasks", [])
if not runnable:
    print("ERROR")
    print(f"Variant `{variant}` is literature-only / not runnable in this workspace.")
    sys.exit(0)
if task not in supported:
    print("ERROR")
    print(f"Task `{task}` is not supported by variant `{variant}`. Supported: {supported}")
    sys.exit(0)

repo_path = cfg.get("repo_path", ".")
env_name = cfg.get("env_name", "")
adapter = cfg.get("adapter", "")
checkpoint = cfg.get("checkpoint", "ckpt/checkpoints.pth")
model_name = cfg.get("model_name", cfg.get("model", "StreamVGGT"))
model_family = cfg.get("model_family", model_name)
kv_enabled = bool(cfg.get("kv_cache_enable", False))
kv_cfg = cfg.get("kv_cache_cfg") or {}
kv_summary = cfg.get("kv_policy_summary", "")
method = str(kv_cfg.get("method", "disabled")).lower() if kv_enabled else "disabled"
canonical = {
    "obcvk": "joint",
    "vk": "joint",
    "joint": "joint",
    "obcv": "v",
    "v": "v",
    "obck": "key",
    "k": "key",
    "key": "key",
    "rolling_memory": "rolling_memory",
    "xstream": "xstream",
}.get(method, method)

parts = [variant]
if kv_enabled:
    parts.append(canonical)
    if "num_sink_frames" in kv_cfg and "num_recent_frames" in kv_cfg and "num_heavy_frames" in kv_cfg:
        parts.append(f"s{kv_cfg['num_sink_frames']}r{kv_cfg['num_recent_frames']}h{kv_cfg['num_heavy_frames']}")
    if "kv_cache_size" in kv_cfg:
        parts.append(f"cache{kv_cfg['kv_cache_size']}")
    if "total_budget" in kv_cfg:
        parts.append(f"budget{kv_cfg['total_budget']}")
result_tag = "_".join(parts)

print("OK")
for value in (
    variant,
    repo_path,
    env_name,
    adapter,
    checkpoint,
    model_name,
    model_family,
    "true" if kv_enabled else "false",
    json.dumps(kv_cfg, ensure_ascii=False, separators=(",", ":")) if kv_cfg else "",
    kv_summary,
    result_tag,
):
    print(value)
PY
)

if [[ "${CONFIG_VALUES[0]}" != "OK" ]]; then
    echo "${CONFIG_VALUES[1]}"
    exit 1
fi

VARIANT_NAME="${CONFIG_VALUES[1]}"
REPO_PATH="${CONFIG_VALUES[2]}"
ENV_NAME="${CONFIG_VALUES[3]}"
ADAPTER="${CONFIG_VALUES[4]}"
CHECKPOINT="${CONFIG_VALUES[5]}"
MODEL_NAME="${CONFIG_VALUES[6]}"
MODEL_FAMILY="${CONFIG_VALUES[7]}"
KV_CACHE_ENABLE="${CONFIG_VALUES[8]}"
KV_CACHE_CFG_JSON="${CONFIG_VALUES[9]}"
KV_POLICY_SUMMARY="${CONFIG_VALUES[10]}"
RESULT_TAG="${CONFIG_VALUES[11]}"

ADAPTER_SCRIPT="${SCRIPTS_DIR}/${ADAPTER}"
if [[ ! -f "${ADAPTER_SCRIPT}" ]]; then
    echo "Error: missing adapter ${ADAPTER_SCRIPT}"
    exit 1
fi

BENCHMARK_ROLE="streaming_benchmark"
case "${TASK}" in
    monodepth)
        BENCHMARK_ROLE="regression_only"
        ;;
    long_stream)
        BENCHMARK_ROLE="long_horizon"
        ;;
esac

if [[ -n "${STREAMVGGT_RUNS:-}" ]]; then
    OUTPUT_BASE="${STREAMVGGT_RUNS}/eval_results"
else
    OUTPUT_BASE="${STREAMVGGT_CODE}/eval_results"
fi
OUTPUT_ROOT="${OUTPUT_BASE}/by_run"
RUN_ID="$(date +%Y%m%d_%H%M%S)_${RESULT_TAG}_${TASK}"
RUN_DIR="${RUNS_DIR}/${RUN_ID}"
TASK_OUTPUT_ROOT="${OUTPUT_ROOT}/${RUN_ID}/${TASK}/${VARIANT}"
LOG_FILE="${RUN_DIR}/stdout.log"
COMMAND_FILE="${RUN_DIR}/command.sh"
ENV_FILE="${RUN_DIR}/env_snapshot.txt"

mkdir -p "${RUN_DIR}"
mkdir -p "${TASK_OUTPUT_ROOT}"

CONDA_ENV_NAME="${CONDA_DEFAULT_ENV:-}"

ADAPTER_ARGS=(
    --repo-path "${REPO_PATH}"
    --checkpoint "${CHECKPOINT}"
    --task "${TASK}"
    --variant "${VARIANT}"
    --model-name "${MODEL_NAME}"
    --output-root "${TASK_OUTPUT_ROOT}"
    --result-tag "${RESULT_TAG}"
    --env-name "${ENV_NAME}"
    --kv-cache-enable "${KV_CACHE_ENABLE}"
    --kv-cache-cfg-json "${KV_CACHE_CFG_JSON}"
)
if (( ${#EXTRA_ARGS[@]} > 0 )); then
    ADAPTER_ARGS+=("${EXTRA_ARGS[@]}")
fi

DRY_RUN_JSON="$(python "${ADAPTER_SCRIPT}" "${ADAPTER_ARGS[@]}" --dry-run)"
mapfile -t RESOLVED_VALUES < <(
    python - "${DRY_RUN_JSON}" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
print(payload["repo_root"])
print(payload["env_name"])
print(json.dumps(payload.get("env_overrides", {}), ensure_ascii=False, separators=(",", ":")))
for cmd in payload.get("commands", []):
    print(cmd)
PY
)

REPO_ROOT_RESOLVED="${RESOLVED_VALUES[0]}"
ENV_NAME_RESOLVED="${RESOLVED_VALUES[1]}"
ENV_OVERRIDES_JSON="${RESOLVED_VALUES[2]}"
COMMANDS=("${RESOLVED_VALUES[@]:3}")
TARGET_GIT_BRANCH="$(git -C "${REPO_ROOT_RESOLVED}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
TARGET_GIT_COMMIT="$(git -C "${REPO_ROOT_RESOLVED}" rev-parse HEAD 2>/dev/null || echo unknown)"
CONTROLLER_GIT_BRANCH="$(git -C "${STREAMVGGT_CODE}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
CONTROLLER_GIT_COMMIT="$(git -C "${STREAMVGGT_CODE}" rev-parse HEAD 2>/dev/null || echo unknown)"

printf '%s\n' "#!/bin/bash" "set -euo pipefail" "cd \"${REPO_ROOT_RESOLVED}\"" > "${COMMAND_FILE}"
if [[ -n "${ENV_OVERRIDES_JSON}" && "${ENV_OVERRIDES_JSON}" != "{}" ]]; then
    python - "${ENV_OVERRIDES_JSON}" <<'PY' >> "${COMMAND_FILE}"
import json
import shlex
import sys
payload = json.loads(sys.argv[1])
for key, value in payload.items():
    print(f"export {key}={shlex.quote(str(value))}")
PY
fi
for command in "${COMMANDS[@]}"; do
    printf '%s\n' "${command}" >> "${COMMAND_FILE}"
done
chmod +x "${COMMAND_FILE}"

{
    echo "STREAMVGGT_CODE=${STREAMVGGT_CODE}"
    echo "RUN_ID=${RUN_ID}"
    echo "RUN_DIR=${RUN_DIR}"
    echo "OUTPUT_BASE=${OUTPUT_BASE}"
    echo "TASK_OUTPUT_ROOT=${TASK_OUTPUT_ROOT}"
    echo "REPO_ROOT=${REPO_ROOT_RESOLVED}"
    echo "VARIANT=${VARIANT_NAME}"
    echo "TASK=${TASK}"
    echo "MODEL_NAME=${MODEL_NAME}"
    echo "MODEL_FAMILY=${MODEL_FAMILY}"
    echo "CHECKPOINT=${CHECKPOINT}"
    echo "ENV_NAME=${ENV_NAME_RESOLVED}"
    echo "CURRENT_CONDA_ENV=${CONDA_ENV_NAME}"
    echo "ENV_OVERRIDES_JSON=${ENV_OVERRIDES_JSON}"
    echo "KV_CACHE_ENABLE=${KV_CACHE_ENABLE}"
    echo "KV_CACHE_CFG_JSON=${KV_CACHE_CFG_JSON}"
    echo "KV_POLICY_SUMMARY=${KV_POLICY_SUMMARY}"
    echo "TARGET_GIT_BRANCH=${TARGET_GIT_BRANCH}"
    echo "TARGET_GIT_COMMIT=${TARGET_GIT_COMMIT}"
    echo "CONTROLLER_GIT_BRANCH=${CONTROLLER_GIT_BRANCH}"
    echo "CONTROLLER_GIT_COMMIT=${CONTROLLER_GIT_COMMIT}"
} > "${ENV_FILE}"

INIT_RECORD_ARGS=(
    init
    --run-dir "${RUN_DIR}"
    --run-id "${RUN_ID}"
    --variant "${VARIANT_NAME}"
    --task "${TASK}"
    --benchmark-role "${BENCHMARK_ROLE}"
    --model-name "${MODEL_NAME}"
    --checkpoint "${CHECKPOINT}"
    --result-tag "${RESULT_TAG}"
    --repo-path "${REPO_ROOT_RESOLVED}"
    --env-name "${ENV_NAME_RESOLVED}"
    --adapter "${ADAPTER}"
    --output-root "${TASK_OUTPUT_ROOT}"
    --config-file "${CONFIG_FILE}"
    --git-branch "${TARGET_GIT_BRANCH}"
    --git-commit "${TARGET_GIT_COMMIT}"
    --kv-cache-cfg-json "${KV_CACHE_CFG_JSON}"
)
if [[ "${KV_CACHE_ENABLE}" == "true" ]]; then
    INIT_RECORD_ARGS+=(--kv-cache-enabled)
fi
python "${SCRIPTS_DIR}/run_record.py" "${INIT_RECORD_ARGS[@]}"

STATUS="FAILED"
EXIT_CODE=1
finish_run() {
    python "${SCRIPTS_DIR}/run_record.py" finalize \
        --run-dir "${RUN_DIR}" \
        --status "${STATUS}" \
        --exit-code "${EXIT_CODE}" \
        --output-root "${TASK_OUTPUT_ROOT}" >/dev/null 2>&1 || true
}
trap finish_run EXIT

echo "========================================="
echo "Run ID: ${RUN_ID}"
echo "Variant: ${VARIANT_NAME}"
echo "Task: ${TASK}"
echo "Model family: ${MODEL_FAMILY}"
echo "Model name arg: ${MODEL_NAME}"
echo "Repo root: ${REPO_ROOT_RESOLVED}"
echo "Checkpoint: ${CHECKPOINT}"
echo "Adapter: ${ADAPTER}"
echo "Expected env: ${ENV_NAME_RESOLVED}"
echo "Current env: ${CONDA_ENV_NAME:-<none>}"
if [[ -n "${ENV_OVERRIDES_JSON}" && "${ENV_OVERRIDES_JSON}" != "{}" ]]; then
    echo "Env overrides: ${ENV_OVERRIDES_JSON}"
fi
echo "KV cache enabled: ${KV_CACHE_ENABLE}"
if [[ -n "${KV_CACHE_CFG_JSON}" ]]; then
    echo "KV cache cfg: ${KV_CACHE_CFG_JSON}"
fi
echo "KV policy: ${KV_POLICY_SUMMARY}"
echo "Run dir: ${RUN_DIR}"
echo "Output root: ${TASK_OUTPUT_ROOT}"
echo "Log file: ${LOG_FILE}"
echo "========================================="

if [[ "${TASK}" == "monodepth" ]]; then
    echo "Note: monodepth is regression-only and should not be used as the primary KV-effectiveness benchmark."
fi
if [[ -n "${ENV_NAME_RESOLVED}" && "${CONDA_ENV_NAME:-}" != "${ENV_NAME_RESOLVED}" ]]; then
    echo "Warning: current conda env (${CONDA_ENV_NAME:-<none>}) does not match config env (${ENV_NAME_RESOLVED})."
fi
echo "Commands:"
printf '  - %s\n' "${COMMANDS[@]}"

set +e
python "${ADAPTER_SCRIPT}" "${ADAPTER_ARGS[@]}" 2>&1 | tee "${LOG_FILE}"
EXIT_CODE=${PIPESTATUS[0]}
set -e

if [[ ${EXIT_CODE} -eq 0 ]]; then
    STATUS="DONE"
else
    STATUS="FAILED"
fi

echo ""
echo "========================================="
echo "Experiment finished: ${STATUS}"
echo "Run ID: ${RUN_ID}"
echo "Run record: ${RUN_DIR}/record.md"
echo "Artifacts index: ${RUN_DIR}/artifacts.json"
echo "========================================="

exit "${EXIT_CODE}"
