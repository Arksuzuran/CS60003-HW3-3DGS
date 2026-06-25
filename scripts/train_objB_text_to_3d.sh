#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
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

CMD="python launch.py --config configs/magic3d-coarse-sd.yaml --train --gpu 0 system.prompt_processor.prompt='${PROMPT}' system.loggers.wandb.enable=false"
maybe_run "cd \"${THREESTUDIO_ROOT}\" && ${CMD} | tee \"${WORK_ROOT}/train.log\""
