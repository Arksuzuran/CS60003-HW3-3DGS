# 资产清单

## 必传

### 1. 离线权重

- `assets/offline_weights/stable-zero123/stable-zero123.ckpt`
  - 用途：物体 C 单图到 3D
  - 必须上传：是
  - 预估体积：约 7GB 以内，按实际 checkpoint 为准
- `assets/offline_weights/text_to_3d/`
  - 用途：物体 B 文本到 3D guidance 权重
  - 必须上传：是
  - 预估体积：约 5GB 到 15GB，视所选 SD/IF 权重而定

### 2. 离线输入

- `assets/offline_inputs/object_a/`
  - 用途：物体 A 多视角真实素材
  - 必须上传：是
  - 预估体积：数百 MB 到数 GB，取决于帧数和分辨率
- `assets/offline_inputs/object_c/`
  - 用途：物体 C 原图与抠图
  - 必须上传：是
  - 预估体积：很小，通常小于 50MB
- `assets/offline_inputs/background/mipnerf360_counter/`
  - 用途：背景训练
  - 必须上传：建议是
  - 预估体积：数 GB 级

### 3. 离线第三方补件

- `assets/offline_third_party/`
  - 用途：集群不可直接访问的第三方源码或压缩包
  - 必须上传：按 manifest 执行
  - 预估体积：通常小于 2GB，除非打包完整 wheels

## 可选传输

- `assets/offline_inputs/object_a_raw_video/`
  - 仅在你需要重新抽帧时上传
- `outputs/checkpoints/`
  - 仅在需要断点续训时上传

## 不建议纳入仓库

- 训练日志
- 中间缓存
- 渲染视频原始中间帧
- Python/conda 缓存

## 20GB 预算建议

如果你希望首轮交接控制在 20GB 以内，优先上传：

1. 文本到 3D 与单图到 3D 必需权重
2. 背景单场景数据（默认 `counter`）
3. 物体 A 多视角素材
4. 物体 C 原图与 RGBA

不优先上传：

- 多个候选背景场景
- 重复 checkpoint
- 训练中间缓存
