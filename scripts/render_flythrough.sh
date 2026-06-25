#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
parse_common_args "$@"
echo_config

FUSED_ROOT="${OUTPUT_ROOT}/fusion"
VIDEO_ROOT="${OUTPUT_ROOT}/videos"
GS_ROOT="$(resolve_third_party_root GAUSSIAN_SPLATTING_ROOT "${PROJECT_ROOT}/third_party/gaussian-splatting")"

maybe_run "mkdir -p \"${VIDEO_ROOT}\""
echo "Assumes fused gaussian asset already exists under ${FUSED_ROOT}"
echo "Gaussian Splatting root: ${GS_ROOT}"

CMD="python render.py -m \"${FUSED_ROOT}\" --skip_train --skip_test"
maybe_run "cd \"${GS_ROOT}\" && ${CMD} | tee \"${FUSED_ROOT}/render.log\""

FFMPEG_CMD="ffmpeg -y -framerate 24 -i \"${FUSED_ROOT}/frames/%05d.png\" -c:v libx264 -pix_fmt yuv420p \"${VIDEO_ROOT}/flythrough.mp4\""
maybe_run "${FFMPEG_CMD}"
