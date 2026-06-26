#!/usr/bin/env bash
# 从已有 database.db 续跑 matcher → mapper → undistorter（跳过 feature_extractor）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh" >/dev/null

WS="${1:-${SCRIPT_DIR}/../outputs/object_a/colmap_ws}"
WS="$(cd "$(dirname "$WS")" && pwd)/$(basename "$WS")"
COLMAP="${COLMAP_BIN}"
DB="${WS}/distorted/database.db"
USE_GPU="${USE_GPU:-1}"

mkdir -p "${WS}/distorted/sparse" "${WS}/sparse/0"

echo "[colmap-resume] exhaustive_matcher"
"${COLMAP}" exhaustive_matcher \
  --database_path "${DB}" \
  --FeatureMatching.use_gpu "${USE_GPU}"

echo "[colmap-resume] mapper"
"${COLMAP}" mapper \
  --database_path "${DB}" \
  --image_path "${WS}/input" \
  --output_path "${WS}/distorted/sparse" \
  --Mapper.ba_global_function_tolerance=0.000001

echo "[colmap-resume] image_undistorter"
"${COLMAP}" image_undistorter \
  --image_path "${WS}/input" \
  --input_path "${WS}/distorted/sparse/0" \
  --output_path "${WS}" \
  --output_type COLMAP

for f in "${WS}"/sparse/*; do
  base="$(basename "$f")"
  [ "$base" = "0" ] && continue
  mv "$f" "${WS}/sparse/0/"
done

echo "[colmap-resume] done"
ls "${WS}/sparse/0"
