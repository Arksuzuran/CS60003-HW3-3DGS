# HW3 Task 1: 3DGS + AIGC 多源资产生成与真实场景融合

本仓库用于在 Windows 本地准备一个可交接的实验工程，并在 Linux 集群上完成正式训练、融合渲染与报告整理。

## 目标

本项目严格对应题目一，最终需要完成以下四类核心结果：

1. 物体 A：真实多视角素材 -> COLMAP -> 3D Gaussian Splatting
2. 物体 B：文本到 3D 生成
3. 物体 C：单图到 3D 生成
4. 独立背景：开源真实场景 -> 3D Gaussian Splatting

随后将 A/B/C 三类资产统一转换到高斯表示，在同一背景场景中融合，并导出漫游视频、图表和中文 NeurIPS 风格报告。

## 仓库结构

```text
configs/                  默认配置
docs/                     交接、资产、限制说明
neurips_template/         中文报告模板与参考文献
offline_assets_manifest/  离线权重、输入素材清单
scripts/                  Linux 集群执行脚本与 Python 工具
third_party_manifest/     第三方仓库、依赖与补丁说明
```

大型数据、权重和输出不纳入 Git：

- `data/`
- `assets/`
- `outputs/`
- `offline_bundles/`

## 推荐工作流

### 1. Windows 本地准备

1. 阅读 [docs/cluster_handoff.md](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/docs/cluster_handoff.md)
2. 根据 [offline_assets_manifest/offline_assets.yaml](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/offline_assets_manifest/offline_assets.yaml) 下载并整理离线素材
3. 将离线素材放到约定目录：
   - `assets/offline_weights/`
   - `assets/offline_inputs/`
   - `assets/offline_third_party/`
4. 运行 `scripts/prepare_assets.py --echo-config` 检查资产布局
5. 将仓库与离线素材包上传到集群

### 2. Linux 集群执行

1. `bash scripts/setup_cluster.sh --project-root ...`
2. `python scripts/prepare_assets.py --project-root ... --asset-root ...`
3. `bash scripts/train_bg_3dgs.sh ...`
4. `bash scripts/train_objA_3dgs.sh ...`
5. `bash scripts/train_objB_text_to_3d.sh ...`
6. `bash scripts/train_objC_image_to_3d.sh ...`
7. `python scripts/convert_to_gaussians.py ...`
8. `python scripts/merge_gaussians.py ...`
9. `bash scripts/render_flythrough.sh ...`
10. `python scripts/export_report_assets.py ...`

## 默认技术路线

- 背景：`Mip-NeRF 360/garden`
- 物体 A：公开真实多视角素材或后续替换为自采素材
- 物体 B：`threestudio` 文本到 3D
- 物体 C：`Stable Zero123`
- 融合：统一为高斯表示后做刚体拼接，不使用 Blender-only 作为主线

## 关键约束

- 远程集群不能依赖 Hugging Face、Pexels、GitLab INRIA、在线 TeX bundle。
- 不使用 WandB，统一写本地日志：
  - `train.log`
  - `metrics.json`
  - `curves.csv`
  - `gpu_mem.txt`
- B/C 必须是严格意义上的文本到 3D、单图到 3D 主线。fallback 只能发生在同类实现路径内部。

## 当前状态

当前版本已经提供：

- 工程目录结构
- 默认配置
- 集群脚本骨架
- 离线资产清单
- 第三方仓库清单
- 中文报告模板骨架

当前版本尚未包含：

- 实际下载好的大型数据和权重
- 正式训练输出
- 最终漫游视频与结果图

## 主要文档

- [docs/cluster_handoff.md](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/docs/cluster_handoff.md)
- [docs/asset_inventory.md](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/docs/asset_inventory.md)
- [docs/limitations.md](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/docs/limitations.md)
- [docs/source_selection.md](/E:/Code/Assignment/SpacialIntelligence/HW3_TASK1_3DGS/docs/source_selection.md)
