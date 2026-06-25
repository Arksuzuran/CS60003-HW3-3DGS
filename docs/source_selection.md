# 素材选择说明

本项目优先选择“学校宿舍/工位常见场景或物品”，同时保证可复现和适合 3D 重建。

## 最终选定

### 背景场景

- 数据集：Mip-NeRF 360
- 场景：`counter`
- 选择原因：室内台面、桌面和周边物体更接近宿舍或工位环境。
- 官方来源：[Mip-NeRF 360](https://jonbarron.info/mipnerf360/)

### 物体 A：真实多视角重建

- 数据集：Objectron
- 类别：`cereal_box`
- 选择原因：
  - 多视角对象短视频形式天然适合 COLMAP
  - 纸盒纹理和棱边清晰，便于特征匹配
  - 属于校园生活中常见的桌面/宿舍物品
- 官方来源：[Objectron README](https://github.com/google-research-datasets/Objectron)

### 物体 B：文本到 3D

- 主提示词：`a compact adjustable desk lamp with matte white shade and round base`
- 选择原因：
  - 宿舍/工位常见
  - 结构简单但不失细节
  - 相比键盘等复杂细长结构更利于文本到 3D 稳定收敛

### 物体 C：单图到 3D

- 数据集：Objectron
- 类别：`shoe`
- 选择原因：
  - 校园环境高频物品
  - 外轮廓清晰
  - 前景抠图和 Zero123 输入更稳定
- 官方来源：[Objectron README](https://github.com/google-research-datasets/Objectron)

## 允许替换的部分

- 物体 A 可以在后续替换为你自己的手机环拍视频或多视角照片。
- 物体 C 可以替换成你自己的单张真实照片，只要保持前景清晰并提供 RGBA。
- 背景如需更贴近寝室，也可将 `counter` 替换为你自采宿舍环拍数据，但默认计划先使用公开场景。
