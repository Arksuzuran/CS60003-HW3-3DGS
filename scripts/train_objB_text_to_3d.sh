#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
source "${SCRIPT_DIR}/env.sh" 2>/dev/null || true
parse_common_args "$@"
echo_config

PROMPT="a compact adjustable desk lamp with matte white shade and round base"
WORK_ROOT="${OUTPUT_ROOT}/object_b"
WEIGHT_ROOT="${ASSET_ROOT}/offline_weights/text_to_3d"
THREESTUDIO_ROOT="$(resolve_third_party_root THREESTUDIO_ROOT "${PROJECT_ROOT}/third_party/threestudio")"

maybe_run "mkdir -p \"${WORK_ROOT}\""
echo "Using prompt: ${PROMPT}"
echo "Offline weight root: ${WEIGHT_ROOT}"
echo "threestudio root: ${THREESTUDIO_ROOT}"

maybe_run "cd \"${THREESTUDIO_ROOT}\" && ${T3D_ENV}/bin/python launch.py --config configs/dreamfusion-sd.yaml --train --gpu 0 system.prompt_processor.prompt='${PROMPT}' system.loggers.wandb.enable=false exp_root_dir='${WORK_ROOT}' | tee \"${WORK_ROOT}/train.log\""
