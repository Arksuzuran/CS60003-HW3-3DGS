#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
source "${SCRIPT_DIR}/env.sh" 2>/dev/null || true
parse_common_args "$@"
echo_config

INPUT_IMAGE="${ASSET_ROOT}/offline_inputs/object_c/object_c_rgba.png"
ZERO123_ROOT="${ASSET_ROOT}/offline_weights/stable-zero123"
WORK_ROOT="${OUTPUT_ROOT}/object_c"
THREESTUDIO_ROOT="$(resolve_third_party_root THREESTUDIO_ROOT "${PROJECT_ROOT}/third_party/threestudio")"

maybe_run "mkdir -p \"${WORK_ROOT}\""
maybe_run "python \"${SCRIPT_DIR}/prepare_object_c.py\" --project-root \"${PROJECT_ROOT}\" --data-root \"${DATA_ROOT}\" --asset-root \"${ASSET_ROOT}\" --output-root \"${OUTPUT_ROOT}\" --device \"${DEVICE}\""
echo "Input image: ${INPUT_IMAGE}"
echo "Stable Zero123 root: ${ZERO123_ROOT}"
echo "threestudio root: ${THREESTUDIO_ROOT}"

CMD="${T3D_ENV}/bin/python launch.py --config configs/experimental/unified-guidance/zero123-simple.yaml --train --gpu 0 data.image_path='${INPUT_IMAGE}' system.loggers.wandb.enable=false exp_root_dir='${WORK_ROOT}'"
maybe_run "cd \"${THREESTUDIO_ROOT}\" && ${CMD} | tee \"${WORK_ROOT}/train.log\""
