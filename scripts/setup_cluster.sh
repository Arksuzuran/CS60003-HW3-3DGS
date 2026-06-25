#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
parse_common_args "$@"

echo_config

ENV_NAME="hw3_3dgs_aigc"
ENV_FILE="${PROJECT_ROOT}/environment.yml"
THIRD_PARTY_ROOT="${PROJECT_ROOT}/third_party"

maybe_run "mkdir -p \"${DATA_ROOT}\" \"${ASSET_ROOT}\" \"${OUTPUT_ROOT}\""
maybe_run "mkdir -p \"${THIRD_PARTY_ROOT}\""
maybe_run "conda env create -n ${ENV_NAME} -f \"${ENV_FILE}\" || conda env update -n ${ENV_NAME} -f \"${ENV_FILE}\""

cat <<EOF
Next steps:
1. conda activate ${ENV_NAME}
2. Clone or unpack third-party repositories under ${THIRD_PARTY_ROOT}.
3. Ensure CUDA, nvcc, cmake and ninja are visible in PATH.
EOF
