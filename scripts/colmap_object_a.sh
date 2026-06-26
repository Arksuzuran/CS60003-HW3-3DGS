#!/usr/bin/env bash
# 物体 A：真实多视角 -> COLMAP 位姿恢复 -> 3DGS 就绪布局
# 适配较新版 COLMAP（选项 --FeatureExtraction.use_gpu / --FeatureMatching.use_gpu）。
# 产物：<WS>/images, <WS>/sparse/0  （供 gaussian-splatting train.py 使用）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh" >/dev/null

WS="${1:-${SCRIPT_DIR}/../outputs/object_a/colmap_ws}"
WS="$(cd "$(dirname "$WS")" && pwd)/$(basename "$WS")"
COLMAP="${COLMAP_BIN}"
DB="${WS}/distorted/database.db"
USE_GPU="${USE_GPU:-1}"

mkdir -p "${WS}/distorted/sparse"

echo "[colmap] feature_extractor"
"${COLMAP}" feature_extractor \
  --database_path "${DB}" \
  --image_path "${WS}/input" \
  --ImageReader.single_camera 1 \
  --ImageReader.camera_model OPENCV \
  --FeatureExtraction.use_gpu "${USE_GPU}"

echo "[colmap] exhaustive_matcher"
"${COLMAP}" exhaustive_matcher \
  --database_path "${DB}" \
  --FeatureMatching.use_gpu "${USE_GPU}"

echo "[colmap] mapper"
"${COLMAP}" mapper \
  --database_path "${DB}" \
  --image_path "${WS}/input" \
  --output_path "${WS}/distorted/sparse" \
  --Mapper.ba_global_function_tolerance=0.000001

echo "[colmap] image_undistorter"
"${COLMAP}" image_undistorter \
  --image_path "${WS}/input" \
  --input_path "${WS}/distorted/sparse/0" \
  --output_path "${WS}" \
  --output_type COLMAP

# 规整 sparse 到 sparse/0
mkdir -p "${WS}/sparse/0"
for f in "${WS}"/sparse/*; do
  base="$(basename "$f")"
  [ "$base" = "0" ] && continue
  mv "$f" "${WS}/sparse/0/"
done

echo "[colmap] done -> ${WS}/images, ${WS}/sparse/0"
ls "${WS}/sparse/0"
