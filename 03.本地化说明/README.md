# 03. 本地化说明 (Localization)

本章节深入解析《植物大战僵尸：英雄》（PVZH）的多语言文本包资源、本地化键值对（Key-Value）存储格式、富文本与图标标记语法，以及如何使用 UABEA 提取和替换 `cn.csv` 文本。

---

## 目录导航

| 序号 | 专题文档 | 核心涵盖内容 |
| :---: | :--- | :--- |
| **01** | [01. 文件结构与 UABEA 导出](01.文件结构与UABEA导出.md) | 详解游戏 `files/loc/` 语言包存放路径、TextAsset 在 Bundle 中的存储形式、使用 UABEA 导出 CSV（如根目录 [cn.csv](../cn.csv)）与重打包导入。 |
| **02** | [02. 键名规范与后缀索引](02.键名规范与后缀索引.md) | 详解 CSV 中的 Key 命名规则：卡牌 GUID + 后缀（`_name`, `_shortDesc`, `_longDesc`, `_flavorText`）以及游戏系统 UI 通用文本 Key。 |
| **03** | [03. 富文本与图标标记语法](03.富文本与图标标记语法.md) | 详解文本中控制数值与图形渲染的内联标记：攻防数值图标（`[+1a]`, `[+1h]`）、关键字图标（`[frenzy]`, `[armor1]` 等）、`\n` 换行及动态插值。 |

---

## 核心要点概览

1. **资源存放路径**：
   多语言资源存放于设备路径：
   `/storage/emulated/0/Android/data/com.ea.gp.pvzheroes/files/cache/bundles/files/loc/`
   其中 `cn` 为简体中文语言包，`en` 为英文语言包。
2. **Key-Value 组织形式**：
   解包后为 CSV 逗号分隔文件（如根目录 [cn.csv](../cn.csv)），每条文本项由独立的键名（Key）和本地化文本（Value）组成。
3. **卡牌与 UI 双重解耦**：
   卡牌的数值与逻辑存放在 `cards/card_data_X` 数据包中，而卡牌在手牌/卡册中显示的中文名称、简短描述、详细说明与风味故事均从 `loc/cn` 语言包中通过卡牌 GUID 读取。
