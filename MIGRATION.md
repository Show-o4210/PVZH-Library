# 项目迁移记录

2026-10-05 将四个独立仓库的默认分支导入 PVZH-Library。各项目保持独立，未抽取公共模块或合并运行环境。

| 原仓库 | 新目录 | 导入的原始提交 | 原始提交数 |
| --- | --- | --- | --- |
| [PVZH-Card-Editor](https://github.com/Show-o4210/PVZH-Card-Editor) | [tools/card-editor](tools/card-editor/README.md) | `378ab4a2e78ac30b92b9c30ab84c9a98a7a8da3e` | 3 |
| [PVZH-Level-Editor](https://github.com/Show-o4210/PVZH-Level-Editor) | [tools/level-editor](tools/level-editor/README.md) | `5bccb7746340c3c8d913f38c4cd842f9ee5a6504` | 4 |
| [PVZH-audio-tool](https://github.com/Show-o4210/PVZH-audio-tool) | [tools/audio-tool](tools/audio-tool/README.md) | `e1cb637fdf5fe00bad7fbe61ff60d478d6eb9bdf` | 3 |
| [pvzh-local-inventory-mod](https://github.com/Show-o4210/pvzh-local-inventory-mod) | [mods/local-inventory](mods/local-inventory/README.md) | `14976838c19041623186201126547a633455eaf7` | 2 |

每次导入提交的第二父节点是该项目原始分支的提交，所有祖先提交、作者、日期和提交编号完整保留。源码、数据、构建脚本与各项目 LICENSE 按原 Git 树迁移；只为项目 README 增加新入口说明。

普通路径历史跟踪会在目录导入边界停止；需要查看搬迁前记录时，直接使用上表中的原始提交编号：

```bash
git log --format=fuller 378ab4a2e78ac30b92b9c30ab84c9a98a7a8da3e -- main.py
git show 14976838c19041623186201126547a633455eaf7:native/merge_inventory_extra.c
```

原资料章节保留原目录。涉及这四个项目的导航和源码链接已指向新位置。旧仓库保留为历史入口；Issue、Pull Request、Star 与 Release 不是 Git 对象，不随源码导入。后续维护集中在 PVZH-Library。

## 音频工具完整包

原标签 `完整` 指向 `f3d719e8523849822993abc866eca977c3637a64`；已迁入的源码历史包含这个提交。原 [完整 Windows 工具包 Release](https://github.com/Show-o4210/PVZH-audio-tool/releases/tag/%E5%AE%8C%E6%95%B4) 保留下载入口；约 115 MB 的 `mod.zip` 不加入源码树。BAT、zSound2wem、FFmpeg 与 vgmstream 来自该包，详情见 [音频 README](tools/audio-tool/README.md)。
