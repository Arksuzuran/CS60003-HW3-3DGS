#!/usr/bin/env bash
# 统一环境配置（集群离线执行）。用法： source scripts/env.sh
# 记录第一轮核查后确定的可用资源，见 docs/cluster_execution_log.md。

PUB=/inspire/hdd/project/fdu-aidake-cfff/public

# 3DGS 主环境：torch 2.4.1+cu124 + nvcc 12.4 + diff_gaussian_rasterization + simple_knn
export GS_ENV="${PUB}/.conda/envs/gsbg2"
# 文本/单图到 3D 环境：threestudio 依赖（torch 2.1.0+cu121）
export T3D_ENV="${PUB}/.conda/envs/gen3d"
# COLMAP 所在环境（仅取其 colmap 可执行文件）
export COLMAP_BIN="${PUB}/.conda/envs/task1-tools/bin/colmap"

# 编译/运行 CUDA 扩展所需
export CUDA_HOME="${GS_ENV}"
export PATH="${GS_ENV}/bin:${PATH}"

# 离线 HuggingFace 缓存（SD-v1-5 文本到3D、zero123-diffusers 单图到3D）
export HF_HOME="${PUB}/.huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1

# rembg 抠图用 u2net（集群无网时需软链共享盘模型到 ~/.u2net/u2net.onnx）
export U2NET_HOME="${U2NET_HOME:-/inspire/hdd/project/fdu-aidake-cfff/public/.local/share/.u2net}"

# 第三方仓库根
export GAUSSIAN_SPLATTING_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/third_party/gaussian-splatting"
export THREESTUDIO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/third_party/threestudio"

echo "[env] GS_ENV=${GS_ENV}"
echo "[env] T3D_ENV=${T3D_ENV}"
echo "[env] COLMAP_BIN=${COLMAP_BIN}"
echo "[env] HF_HOME=${HF_HOME}"
echo "[env] GAUSSIAN_SPLATTING_ROOT=${GAUSSIAN_SPLATTING_ROOT}"
echo "[env] THREESTUDIO_ROOT=${THREESTUDIO_ROOT}"
