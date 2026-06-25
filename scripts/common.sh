#!/usr/bin/env bash
set -euo pipefail

print_usage_common() {
  cat <<'EOF'
Required arguments:
  --project-root PATH
  --data-root PATH
  --asset-root PATH
  --output-root PATH
Optional arguments:
  --device ID
  --resume
  --dry-run
EOF
}

parse_common_args() {
  PROJECT_ROOT=""
  DATA_ROOT=""
  ASSET_ROOT=""
  OUTPUT_ROOT=""
  DEVICE="cuda:0"
  RESUME=0
  DRY_RUN=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --project-root) PROJECT_ROOT="$2"; shift 2 ;;
      --data-root) DATA_ROOT="$2"; shift 2 ;;
      --asset-root) ASSET_ROOT="$2"; shift 2 ;;
      --output-root) OUTPUT_ROOT="$2"; shift 2 ;;
      --device) DEVICE="$2"; shift 2 ;;
      --resume) RESUME=1; shift 1 ;;
      --dry-run) DRY_RUN=1; shift 1 ;;
      --help|-h)
        print_usage_common
        exit 0
        ;;
      *)
        echo "Unknown argument: $1" >&2
        print_usage_common
        exit 1
        ;;
    esac
  done

  if [[ -z "${PROJECT_ROOT}" || -z "${DATA_ROOT}" || -z "${ASSET_ROOT}" || -z "${OUTPUT_ROOT}" ]]; then
    echo "Missing required arguments." >&2
    print_usage_common
    exit 1
  fi
}

echo_config() {
  cat <<EOF
PROJECT_ROOT=${PROJECT_ROOT}
DATA_ROOT=${DATA_ROOT}
ASSET_ROOT=${ASSET_ROOT}
OUTPUT_ROOT=${OUTPUT_ROOT}
DEVICE=${DEVICE}
RESUME=${RESUME}
DRY_RUN=${DRY_RUN}
EOF
}

maybe_run() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[DRY-RUN] $*"
  else
    eval "$@"
  fi
}

resolve_third_party_root() {
  local env_name="$1"
  local default_path="$2"
  local resolved="${!env_name:-${default_path}}"
  echo "${resolved}"
}
