# 基于 3DGS 与 AIGC 的多源资产生成与真实场景融合

本项目实现课程作业题目一：从**真实场景重建**、**文本/单图生成 3D 资产**到**统一高斯融合与漫游渲染**的完整流程。四类资产最终均以 3D Gaussian Splatting 表示，并在同一真实背景场景中完成布局与可视化。

## 任务概览

| 模块 | 输入 | 方法 | 输出 |
|------|------|------|------|
| **背景** | 真实多视角图像 | 3D Gaussian Splatting | 背景高斯场 |
| **物体 A** | 真实多视角图像 | COLMAP 位姿恢复 → 3DGS | 前景高斯场 |
| **物体 B** | 文本提示词 | threestudio 文本到 3D → mesh → 多视角渲染 → 3DGS | 前景高斯场 |
| **物体 C** | 单张 RGBA 图像 | threestudio Zero123 → mesh → 多视角渲染 → 3DGS | 前景高斯场 |
| **融合** | 背景 + A/B/C 高斯 | 刚体变换拼接 | 融合场景 + 漫游视频 |

整体数据流：

```
背景图像 ──────────────────────────────► 3DGS ──► 背景高斯
真实多视角 ──► COLMAP ──► 3DGS ──────────► 物体 A 高斯
文本提示 ──► threestudio ──► mesh ──► 3DGS ► 物体 B 高斯
单图 RGBA ─► threestudio ──► mesh ──► 3DGS ► 物体 C 高斯
                              │
                    背景 + A + B + C ──► merge ──► 漫游视频
```

B/C 不直接以 mesh 参与最终融合，而是先转为与 A、背景一致的**统一高斯表示**，再按 `configs/fusion.yaml` 中的位姿与尺度拼入场景。

## 仓库结构

```text
CS60003-HW3-3DGS/
├── configs/                    # 项目与融合配置
│   ├── project.yaml            # 各模块默认参数与路径约定
│   ├── object_b_prompts.yaml   # 物体 B 候选提示词
│   └── fusion.yaml             # 融合布局、高斯路径、渲染参数
├── scripts/                    # 训练、转换、融合与渲染脚本
│   ├── env.sh                  # 环境变量（第三方路径、COLMAP 等）
│   ├── common.sh               # 脚本公共参数解析
│   ├── setup_cluster.sh        # 创建 conda 环境
│   ├── prepare_assets.py       # 检查离线素材布局
│   ├── train_bg_3dgs.sh        # 背景 3DGS 训练
│   ├── colmap_object_a.sh      # 物体 A COLMAP
│   ├── train_objA_3dgs.sh      # 物体 A 3DGS 训练
│   ├── train_objB_text_to_3d.sh
│   ├── train_objC_image_to_3d.sh
│   ├── convert_to_gaussians.py # B/C：mesh → 多视角数据集 → 3DGS
│   ├── render_multiview.py     # nvdiffrast 多视角渲染
│   ├── merge_gaussians.py      # 高斯融合
│   ├── render_flythrough.py    # 融合场景轨迹渲染
│   ├── render_flythrough.sh
│   └── export_report_assets.py # 导出报告用图表与指标
├── offline_assets_manifest/    # 所需权重与输入素材清单
├── third_party_manifest/       # 第三方仓库来源清单
├── neurips_template/           # 中文 NeurIPS 风格报告 LaTeX 模板
├── environment.yml             # conda 环境定义
├── assets/                     # 权重与输入（不纳入 Git）
├── outputs/                    # 训练与融合结果（不纳入 Git）
└── third_party/                # gaussian-splatting、threestudio（不纳入 Git）
```

脚本统一接受以下参数（见 `scripts/common.sh`）：

```bash
--project-root PATH
--data-root PATH
--asset-root PATH
--output-root PATH
--device cuda:0    # 可选
```

下文以 `PROJECT_ROOT` 表示仓库根目录。

## 环境依赖

### Conda 环境

```bash
cd $PROJECT_ROOT
bash scripts/setup_cluster.sh \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs
conda activate hw3_3dgs_aigc
```

### 第三方仓库

将以下仓库克隆或解压到 `third_party/`（路径见 `third_party_manifest/third_party_sources.yaml`）：

- [gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting) — 背景、物体 A 及 B/C 高斯训练
- [threestudio](https://github.com/threestudio-project/threestudio) — 物体 B/C 生成

3DGS 需编译 `diff-gaussian-rasterization` 与 `simple-knn`；threestudio 需按官方说明安装其 CUDA 扩展（如 `tinycudann`、`nerfacc` 等）。

### 其他工具

- **COLMAP** — 物体 A 稀疏重建与去畸变
- **FFmpeg** — 漫游视频编码
- **CUDA GPU** — 建议 ≥ 24 GB 显存

## 数据准备

按 `offline_assets_manifest/offline_assets.yaml` 准备素材，目录约定如下：

```text
assets/
├── offline_inputs/
│   ├── background/mipnerf360_counter/   # Mip-NeRF 360 counter 场景
│   ├── object_a/                        # 物体 A 多视角原图
│   └── object_c/object_c_rgba.png       # 物体 C 单图（RGBA，已抠图）
└── offline_weights/
    ├── text_to_3d/                      # Stable Diffusion 等文本到 3D 权重
    └── stable-zero123/                 # Zero123 权重（或 diffusers 缓存）
```

检查布局：

```bash
python scripts/prepare_assets.py \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs
```

## 复现流程

以下步骤按依赖顺序排列；物体 B 与 C 的 threestudio 训练可在 GPU 允许时并行。

### 1. 背景 3DGS

```bash
bash scripts/train_bg_3dgs.sh \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs \
  --device cuda:0
```

输出：`outputs/bg/counter/`，含 `point_cloud/iteration_30000/point_cloud.ply`。

### 2. 物体 A：COLMAP + 3DGS

将多视角图像放入 COLMAP 工作区（例如 `outputs/object_a/colmap_ws/input/`），然后：

```bash
bash scripts/colmap_object_a.sh outputs/object_a/colmap_ws

bash scripts/train_objA_3dgs.sh \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs \
  --device cuda:0
```

输出：`outputs/object_a/point_cloud/iteration_30000/point_cloud.ply`。

### 3. 物体 B：文本到 3D

默认提示词见 `configs/object_b_prompts.yaml`，也可在命令行覆盖：

```bash
bash scripts/train_objB_text_to_3d.sh \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs \
  --device cuda:0
```

输出：`outputs/object_b/` 下的 threestudio checkpoint 与验证渲染。

### 4. 物体 C：单图到 3D

```bash
bash scripts/train_objC_image_to_3d.sh \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs \
  --device cuda:0
```

输入：`assets/offline_inputs/object_c/object_c_rgba.png`  
输出：`outputs/object_c/` 下的 threestudio checkpoint 与验证渲染。

### 5. B/C 转为统一高斯表示

对 B、C 分别执行：从 threestudio checkpoint 导出 mesh → 多视角渲染 → 3DGS 训练。

```bash
python scripts/convert_to_gaussians.py \
  --project-root $PROJECT_ROOT \
  --output-root $PROJECT_ROOT/outputs \
  --object b \
  --iterations 7000 \
  --port 6031

python scripts/convert_to_gaussians.py \
  --project-root $PROJECT_ROOT \
  --output-root $PROJECT_ROOT/outputs \
  --object c \
  --iterations 7000 \
  --port 6030
```

输出：

- `outputs/object_b_gaussian/point_cloud/iteration_7000/point_cloud.ply`
- `outputs/object_c_gaussian/point_cloud/iteration_7000/point_cloud.ply`

物体 B 为浅色物体时，转换脚本默认使用**黑色背景**训练 3DGS（勿加 `--white-background`）。

### 6. 高斯融合

编辑 `configs/fusion.yaml` 调整各物体在场景中的平移、旋转与缩放，然后：

```bash
python scripts/merge_gaussians.py \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs \
  --config configs/fusion.yaml
```

输出：`outputs/fusion/merged_gaussians.ply`。

### 7. 漫游视频

```bash
bash scripts/render_flythrough.sh \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs
```

输出：

- 逐帧图像：`outputs/fusion/frames/`
- 视频：`outputs/videos/flythrough.mp4`

### 8. 报告素材（可选）

```bash
python scripts/export_report_assets.py \
  --project-root $PROJECT_ROOT \
  --data-root $PROJECT_ROOT/data \
  --asset-root $PROJECT_ROOT/assets \
  --output-root $PROJECT_ROOT/outputs
```

将图表写入 `neurips_template/figures/`，指标写入 `outputs/report_metrics.csv`，供 `neurips_template/report.tex` 引用。

## 主要输出一览

| 产物 | 路径 |
|------|------|
| 背景高斯 | `outputs/bg/counter/point_cloud/iteration_30000/point_cloud.ply` |
| 物体 A 高斯 | `outputs/object_a/point_cloud/iteration_30000/point_cloud.ply` |
| 物体 B 高斯 | `outputs/object_b_gaussian/point_cloud/iteration_7000/point_cloud.ply` |
| 物体 C 高斯 | `outputs/object_c_gaussian/point_cloud/iteration_7000/point_cloud.ply` |
| 融合场景 | `outputs/fusion/merged_gaussians.ply` |
| 漫游视频 | `outputs/videos/flythrough.mp4` |
| 融合配置快照 | `outputs/fusion/merge_plan.json` |

## 配置说明

- **`configs/project.yaml`** — 场景名、默认提示词、路径约定等全局默认值。
- **`configs/fusion.yaml`** — 融合时各高斯 PLY 路径及刚体变换；修改此文件即可调整物体在台面上的位置与朝向。
- **`configs/object_b_prompts.yaml`** — 物体 B 备用提示词列表。

threestudio 侧详细超参见 `third_party/threestudio/configs/dreamfusion-sd.yaml`（物体 B）与 `configs/experimental/unified-guidance/zero123-simple.yaml`（物体 C）。

## 方法说明

- **物体 A** 走标准「多视角 → COLMAP → 3DGS」路线，要求输入为同一物体、覆盖足够视角的真实照片。
- **物体 B** 使用 Score Distillation Sampling（SDS）从文本生成 NeRF 隐式场，再导出 mesh 并重建为高斯。
- **物体 C** 使用 Zero123 以单张条件图像引导多视角一致性，同样经 mesh 中转为高斯。
- **融合** 对 B/C 的高斯参数做刚体变换（平移、欧拉角旋转、均匀缩放），与背景和物体 A 直接拼接，不做网格布尔运算。

## 报告

实验报告使用 `neurips_template/report.tex` 撰写，编译方式见 `neurips_template/README.md`。
