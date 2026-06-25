#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
parse_common_args "$@"
echo_config

SCENE_ROOT="${ASSET_ROOT}/offline_inputs/background/mipnerf360_counter"
MODEL_ROOT="${OUTPUT_ROOT}/bg/counter"
GS_ROOT="$(resolve_third_party_root GAUSSIAN_SPLATTING_ROOT "${PROJECT_ROOT}/third_party/gaussian-splatting")"

CMD="python train.py -s \"${SCENE_ROOT}\" -m \"${MODEL_ROOT}\" --eval --data_device cpu --iterations 30000"

echo "Background scene root: ${SCENE_ROOT}"
echo "Output model root: ${MODEL_ROOT}"
echo "Gaussian Splatting root: ${GS_ROOT}"
maybe_run "mkdir -p \"${MODEL_ROOT}\""
maybe_run "cd \"${GS_ROOT}\" && ${CMD} | tee \"${MODEL_ROOT}/train.log\""
