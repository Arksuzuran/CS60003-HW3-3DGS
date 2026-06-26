#!/usr/bin/env bash
# COLMAP 完成后自动启动物体 A 的 3DGS 训练
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh" >/dev/null
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WS="${PROJECT_ROOT}/outputs/object_a/colmap_ws"
LOG="${PROJECT_ROOT}/outputs/object_a/colmap_resume.log"
TRAIN_LOG="${PROJECT_ROOT}/outputs/object_a/train.log"

echo "[wait] polling COLMAP completion..."
while pgrep -f "exhaustive_matcher.*object_a/colmap_ws" >/dev/null 2>&1; do
  sleep 30
done

if ! grep -q "COLMAP done\|\[colmap-resume\] done" "${LOG}" 2>/dev/null; then
  echo "[wait] matcher ended but log missing done marker; check ${LOG}"
  tail -20 "${LOG}"
  exit 1
fi

if [ ! -f "${WS}/sparse/0/cameras.bin" ]; then
  echo "[wait] sparse/0 not ready"
  exit 1
fi

echo "[wait] COLMAP ready; starting object A 3DGS"
mkdir -p "${PROJECT_ROOT}/outputs/object_a"
cd "${PROJECT_ROOT}/third_party/gaussian-splatting"
exec "${GS_ENV}/bin/python" train.py \
  -s "${WS}" \
  -m "${PROJECT_ROOT}/outputs/object_a" \
  -r 2 --data_device cpu --iterations 30000 \
  --test_iterations 7000 30000 --save_iterations 7000 30000 \
  2>&1 | tee "${TRAIN_LOG}"
