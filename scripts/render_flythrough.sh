#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
source "${SCRIPT_DIR}/env.sh" 2>/dev/null || true
parse_common_args "$@"
echo_config

FUSED_ROOT="${OUTPUT_ROOT}/fusion"
VIDEO_ROOT="${OUTPUT_ROOT}/videos"
CAMERAS_JSON="${OUTPUT_ROOT}/bg/counter/cameras.json"
GS_ENV_PY="${GS_ENV:-/inspire/hdd/project/fdu-aidake-cfff/public/.conda/envs/gsbg2}/bin/python"

maybe_run "mkdir -p \"${VIDEO_ROOT}\""
echo "Fused gaussian asset: ${FUSED_ROOT}/merged_gaussians.ply"
echo "Background cameras (scale/fov reference): ${CAMERAS_JSON}"

CMD="${GS_ENV_PY} \"${SCRIPT_DIR}/render_flythrough.py\" \
  --ply \"${FUSED_ROOT}/merged_gaussians.ply\" \
  --cameras \"${CAMERAS_JSON}\" \
  --out-frames \"${FUSED_ROOT}/frames\" \
  --out-video \"${VIDEO_ROOT}/flythrough.mp4\""
maybe_run "${CMD} | tee \"${FUSED_ROOT}/render.log\""
