#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
parse_common_args "$@"
echo_config

OBJECT_ROOT="${ASSET_ROOT}/offline_inputs/object_a"
WORK_ROOT="${OUTPUT_ROOT}/object_a"
GS_ROOT="$(resolve_third_party_root GAUSSIAN_SPLATTING_ROOT "${PROJECT_ROOT}/third_party/gaussian-splatting")"

echo "Object A source: ${OBJECT_ROOT}"
echo "Object A work root: ${WORK_ROOT}"
echo "Gaussian Splatting root: ${GS_ROOT}"

maybe_run "mkdir -p \"${WORK_ROOT}\""
maybe_run "python \"${SCRIPT_DIR}/prepare_object_a.py\" --project-root \"${PROJECT_ROOT}\" --data-root \"${DATA_ROOT}\" --asset-root \"${ASSET_ROOT}\" --output-root \"${OUTPUT_ROOT}\" --device \"${DEVICE}\""
maybe_run "cd \"${GS_ROOT}\" && python train.py -s \"${WORK_ROOT}/dataset\" -m \"${WORK_ROOT}\" --data_device cpu --iterations 30000 | tee \"${WORK_ROOT}/train.log\""
