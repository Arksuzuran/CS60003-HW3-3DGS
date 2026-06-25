# 集群交接指南

本指南面向你或后续接手的 agent，目标是在 Linux + A100 40GB 环境中执行完整实验。

## 1. 交接内容

你需要向集群上传两类内容：

1. 本仓库源码
2. 离线资产目录
   - `assets/offline_weights/`
   - `assets/offline_inputs/`
   - `assets/offline_third_party/`
3. 素材选择说明见 [docs/source_selection.md](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/docs/source_selection.md)
3. 建议同步查看 [docs/source_selection.md](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/docs/source_selection.md)

不要上传：

- `tmp/`
- 本地缓存
- Windows 特有环境

## 2. 推荐目录布局

```text
PROJECT_ROOT/
├── assets/
│   ├── offline_inputs/
│   ├── offline_third_party/
│   └── offline_weights/
├── configs/
├── data/
├── neurips_template/
├── outputs/
└── scripts/
```

## 3. 执行顺序

### 第一步：环境准备

```bash
bash scripts/setup_cluster.sh \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0
```

### 第二步：校验离线资产

```bash
python scripts/prepare_assets.py \
  --project-root "$PWD" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs"
```

### 第三步：背景训练

```bash
bash scripts/train_bg_3dgs.sh \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0
```

### 第四步：物体 A

```bash
bash scripts/train_objA_3dgs.sh \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0
```

### 第五步：物体 B

```bash
bash scripts/train_objB_text_to_3d.sh \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0
```

### 第六步：物体 C

```bash
bash scripts/train_objC_image_to_3d.sh \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0
```

### 第七步：统一高斯表示

```bash
python scripts/convert_to_gaussians.py \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0
```

### 第八步：融合与渲染

```bash
python scripts/merge_gaussians.py \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0

bash scripts/render_flythrough.sh \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs" \
  --device cuda:0
```

### 第九步：导出报告资产

```bash
python scripts/export_report_assets.py \
  --project-root "$PWD" \
  --data-root "$PWD/data" \
  --asset-root "$PWD/assets" \
  --output-root "$PWD/outputs"
```

## 4. 常见失败点

- `threestudio` 找不到模型权重：
  - 检查 `assets/offline_weights/` 与 manifest 的相对路径是否一致。
- `tiny-cuda-nn` 或扩展编译失败：
  - 先确认 `CUDA_HOME`、`nvcc`、`ninja` 和 `cmake` 可用。
- `COLMAP` 路径不一致：
  - 用 `which colmap` 确认已安装版本。
- `Tectonic` 无法联网拉 bundle：
  - 先在可联网机器生成 PDF，或改用本地完整 TeX 发行版。
- Objectron 素材没有整理好：
  - 先用 `scripts/download_offline_assets.py` 查看目标结构
  - 再执行 `scripts/prepare_object_a.py` 和 `scripts/prepare_object_c.py`
- Objectron 素材未整理成统一目录：
  - 先运行 `scripts/download_offline_assets.py --echo-config`
  - 再执行 `scripts/prepare_object_a.py` 和 `scripts/prepare_object_c.py`

## 5. 日志与结果

所有主脚本都应该在对应输出目录下写入：

- `train.log`
- `metrics.json`
- `curves.csv`
- `gpu_mem.txt`

报告素材统一导出到：

- `neurips_template/figures/`
