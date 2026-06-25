# 第三方仓库布局约定

推荐将第三方源码放到如下目录：

```text
third_party/
├── gaussian-splatting/
└── threestudio/
```

如果你改用了其他目录，请在执行脚本前导出环境变量：

- `GAUSSIAN_SPLATTING_ROOT`
- `THREESTUDIO_ROOT`

默认情况下，脚本会按上述相对路径查找源码仓库。
