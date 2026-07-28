# 04. 贴图简单修改

本章节专门讲解《植物大战僵尸：英雄》（PVZH）中卡牌与单位贴图的定位、解包提取、图像修改与 UABEA 重打包替换流程。

---

## 目录导航

| 序号 | 专题文档 | 核心涵盖内容 |
| :---: | :--- | :--- |
| **01** | [01. 定位卡牌贴图 AssetBundle](01.定位卡牌贴图AssetBundle.md) | 讲解两种快捷定位卡牌贴图包的方法：通过 `index_new.json` 索引库精确定位，以及使用 AssetStudio 图形化批量预览抓取。 |
| **02** | [02. 贴图 Bundle 解构与实例分析](02.贴图Bundle解构与实例分析.md) | 以真实文件 [1f826228d36c6f0478c72b56f17541d2_1](../1f826228d36c6f0478c72b56f17541d2_1)（康加僵尸）为例，解构单位贴图包内的 `Texture2D`（头、身、手臂部件与图集）及 `Sprite` 精灵节点。 |
| **03** | [03. UABEA 贴图导出与替换教程](03.UABEA贴图导出与替换教程.md) | 步骤化讲解如何使用 UABEA 的 `Plugins` 插件功能，进行 `Export to .png` 导出与 `Edit / Import .png` 快捷替换导入。 |
| **04** | [04. 规格尺寸与避坑指南](04.规格尺寸与避坑指南.md) | 贴图替换中的 PNG 尺寸与比例规范、RGBA32 透明通道保持以及游戏内贴图异常问题排查。 |

---

## 核心要点概览

1. **贴图资源存放目录**：
   单位卡牌与场景特效贴图均存放于：
   `/storage/emulated/0/Android/data/com.ea.gp.pvzheroes/files/cache/bundles/files/autotagged/`
2. **底层存储形式 (`Texture2D` 与 `Sprite`)**：
   在 AssetBundle 内部，图像原始像素数据存储为 **`Texture2D`**；而引擎场景渲染引用的是包裹了坐标与轴心的 **`Sprite`**（精灵图）。修改简单贴图时，只需替换 `Texture2D` 即可。
3. **极简替换体验**：
   借助 UABEA 的 `Plugins` 按钮，无需关心复杂的压缩编码算法，一键式完成 PNG 图片的导出与覆盖导入。
