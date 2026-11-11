# PVZH 启动器

PVZH 启动器是《植物大战僵尸：英雄》的第三方 Android Mod 工作台。它提供 Mod 管理、卡牌和美术编辑，以及游戏资源准备等入口。手机操作和版本能力见[启动器工作台指南](../Library-docs/24.启动器工作台与手机编辑/README.md)。

这里公开项目简介和启动器语言表。完整客户端与 Hook 实现由独立工程维护。

## 启动器本地化

| 语言表 | 对应开发候选 | 状态 |
| --- | --- | --- |
| [简体中文 `zh-CN`](i18n/zh-CN/) | r-2-29 RC2 | 翻译基准 |
| [English `en-US`](i18n/en-US/) | r-2-30 RC1 | 英文初稿，待审校 |

每套语言表包含 6 个 JSON 和 5,186 个键，覆盖导航、设置、编辑器、AI 工作台、资源进度和错误提示。r-2-30 RC1 在构建时选择英文，并通过了主要流程的 Android 功能抽查。

欢迎通过 Issue 反馈文案问题，或用 Pull Request 提交翻译建议。请保留 JSON 键以及 `{0}`、`{1}` 等占位符，按目标语言调整它们的位置。游戏本体与 Mod 自带文本各自使用自己的资源。许可范围见[许可证索引](../LICENSES.md)。

## About PvZH AM

PvZH AM (Advanced Modding) is a third-party Android Mod workbench for *Plants vs. Zombies Heroes*. The [English UI catalog](i18n/en-US/) is a draft from **r-2-30 RC1**, based on the [Simplified Chinese catalog](i18n/zh-CN/) from **r-2-29 RC2**. The English build passed Android smoke tests for key workflows. Terminology and wording are open for review.

Translation feedback is welcome via Issues or Pull Requests. Keep the JSON keys and numbered placeholders such as `{0}` when proposing changes.
