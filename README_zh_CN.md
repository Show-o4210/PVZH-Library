# PvZ Heroes Advanced Modding Library

[English](README.md) | 简体中文 | [Tiếng Việt](README_vi_VN.md)

一份面向《植物大战僵尸：英雄》Mod 开发者的中文资料、工具与经验库。

当前手机正式版为 **v3.1（功能基线 r-2-22 RC1）**。开发候选 **r-2-44 RC1** 的[中英越本地化资料](pvzh-launcher/README.md)涵盖启动器、悬浮工具和卡名，包含越南语审校稿。能力与排障指南记录至 r-2-28 RC1 的验收范围。资料库收录中文教程、公开工具和筛选后的证据。标为「工作区」的路径用于在完整工作区追溯交付记录。

## 从这里开始

| 需求 | 最短入口 |
| --- | --- |
| 查找任一文档，包括旧参考、工具内部说明和检查记录 | [文档总索引](文档总索引.md) · [机器目录](DOCUMENT-CATALOG.json) |
| 查正式版、开发候选和实测范围 | [当前版本能力](Library-docs/24.启动器工作台与手机编辑/05.当前版本能力.md) |
| 进不去游戏、闪退、报错或功能不生效 | [故障排查与避坑](Library-docs/24.启动器工作台与手机编辑/06.故障排查与避坑.md) |
| 手机制卡、外观编辑、AI 和资源管理 | [第24章](Library-docs/24.启动器工作台与手机编辑/README.md) |
| 了解启动器项目或参与界面翻译 | [PVZH 启动器](pvzh-launcher/README.md) |
| 第一次制作Mod | [前言](Library-docs/前言.md) → [工具链](Library-docs/01.工具链介绍/README.md) → [独立基础示例](Library-docs/08-basic-mod-walkthrough.md) |
| 作为Agent执行任务 | [Agent入口规则](AGENTS.md) → [任务路由](agents/README.md) |
| 查原版卡牌／关卡／本地化数据 | [卡牌数据](Library-docs/02.卡牌数据说明/README.md) · [关卡统一索引](Library-docs/09.关卡修改/INDEX.md) · [本地化](Library-docs/03.本地化说明/README.md) |
| 查许可、作者和迁移来源 | [许可证索引](LICENSES.md) · [使用条款](许可与使用条款.md) · [迁移记录](MIGRATION.md) |

Android产品、公开Python工具、游戏原版能力是三个范围。手动编辑可表达的组件不等于AI工具已开放；某工具尚不支持也不等于原版引擎做不到。静态／本机、真实Android UI、原引擎、正式对局与真实模型测试分别记载。

## 工具与 Mod

| 项目 | 入口 | 合同范围 |
| --- | --- | --- |
| Card Editor／幻影引擎 | [tools/card-editor](tools/card-editor/README.md) | Python桌面卡牌JSON、技能树与Bundle；不等于手机编辑器 |
| Level Editor | [tools/level-editor](tools/level-editor/README.md) | Python关卡配置、事件与Bundle |
| Audio Tool | [tools/audio-tool](tools/audio-tool/README.md) | 音频提取、转换和替换，外部工具按该项目说明准备 |
| 纸片人资源工具 | [tools/auto-paper-doll](tools/auto-paper-doll/README.md) | Unity角色资源换皮实验原型；完整引用验证尚未通过 |
| Local Inventory Mod | [mods/local-inventory](mods/local-inventory/README.md) | 独立静态补丁与本地卡库合同，不等于启动器runtime |
| 自然语言原版制卡核心 | [tools/natural-card-author](tools/natural-card-author/README.md) | 受约束plan→原版组件／中文／Bundle；按自身v1合同判断 |

各工具保留独立依赖、输入输出和许可。先进入相应子目录并阅读README，再按需安装；原版游戏数据由使用者自行提供。

## 教程和参考资料

- [Library-docs 教程目录](Library-docs/README.md)收录 00–24 章、入门示例与历史教程。
- [资源](资源/)收录数据索引、实战素材和旧参考笔记。
- [Agent 工作指南](agents/README.md)提供任务路由、语义测试和验收边界。

## 使用说明

本仓库以技术研究、学习交流和资料保存为目的，与 EA、PopCap 或《植物大战僵尸：英雄》官方无关。仓库中的游戏名称、角色和相关素材，其权利归原权利人所有。请勿将资料用于破坏游戏服务、影响他人体验或其他违规用途。

如果文档中的步骤与你的环境不一致，优先确认游戏版本、Unity 版本、工具版本和目标文件是否匹配。欢迎通过 Issue 或 Pull Request 补充资料、修正文档。

## 许可协议

本仓库原资料库部分的**原创文档与整理结构**采用  
[知识共享 署名—非商业性使用—相同方式共享 4.0 国际 (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 许可。

| 文件 | 说明 |
| --- | --- |
| [LICENSES.md](LICENSES.md) | 多许可证目录边界；四个导入项目保留 MIT 许可与原作者声明 |
| [LICENSE](LICENSE) | 正式许可声明（CC BY-NC-SA 4.0） |
| [许可与使用条款.md](许可与使用条款.md) | **中文详细条款**（署名方式、非商业边界、禁止换皮与收款码顶替等） |

**你可以**：学习自用、非商业转载与分享、在署名并采用相同许可的前提下修改后再发布。  
**你必须**：保留作者署名（休切尔 / Show-o4210）、作品名「PVZH 图书馆」、官方仓库链接与许可声明。  
**你不可以**：删除署名后整包换皮、冒充原作者、将本文档作为付费主体出售，或去掉来源后单独挂自己的收款码夺走署名成果。

`tools/card-editor/`、`tools/level-editor/`、`tools/audio-tool/` 和 `mods/local-inventory/` 中的项目原创内容分别采用各目录内的 MIT 许可；上面的非商业与相同方式共享条件仅适用于资料库 CC 许可覆盖的内容。

游戏官方资源、导出数据与第三方工具**不在**本许可授权范围内。完整约定以 [许可与使用条款.md](许可与使用条款.md) 为准。

```text
作者：休切尔（Show-o4210）
许可：CC BY-NC-SA 4.0
官方仓库：https://github.com/Show-o4210/PVZH-Library
主页：https://github.com/Show-o4210
```

## 支持作者

整理、验证和编写这些内容花费了大量时间。如果这座小小的图书馆帮到了你，欢迎请作者喝杯饮料。赞赏完全自愿，感谢你的支持！

<p align="center">
  <img src="support.png" alt="作者赞赏码" width="360">
</p>

> 上图赞赏渠道仅属于原作者。第三方镜像若展示收款信息，必须同时清晰标注原作者与官方仓库，不得冒充原作者。详见 [许可与使用条款.md](许可与使用条款.md)。

---

愿每一次踩坑，最后都能变成后来者脚下的一块路标。
