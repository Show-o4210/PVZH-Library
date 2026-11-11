# PvZ Heroes Advanced Modding Library

PVZH 启动器是《植物大战僵尸：英雄》的第三方 Android Mod 工作台。它提供 Mod 管理、卡牌和美术编辑，以及游戏资源准备等入口。手机操作和版本能力见[启动器工作台指南](../Library-docs/24.启动器工作台与手机编辑/README.md)。

这里公开项目简介和启动器语言表。完整客户端与 Hook 实现由独立工程维护。

## 启动器本地化

| 语言表 | 对应开发候选 | 状态 |
| --- | --- | --- |
| [简体中文 `zh-CN`](i18n/zh-CN/) | r-2-29 RC2 | 翻译基准 |
| [English `en-US`](i18n/en-US/) | r-2-30 RC1 | 英文初稿，待审校 |
| [Tiếng Việt `vi-VN`](i18n/vi-VN/) | r-2-32 RC1 | 越南语初稿，待审校 |

语言表覆盖导航、设置、编辑器、AI 工作台、资源进度和错误提示。三种语言均补齐了 r-2-32 RC1 的 `language.json`。该版本支持首次选择语言、在设置中切换以及下次打开时恢复选择，运行时每种语言使用 5,190 个键。r-2-30 RC1 曾完成英文界面的 Android 功能抽查，r-2-32 RC1 的越南语已完成本机检查，等待 Android 实机反馈。

欢迎通过 Issue 反馈文案问题，或用 Pull Request 提交翻译建议。请保留 JSON 键以及 `{0}`、`{1}` 等占位符，按目标语言调整它们的位置。游戏本体与 Mod 自带文本各自使用自己的资源。许可范围见[许可证索引](../LICENSES.md)。

## About PvZH AM

PvZH AM (Advanced Modding) is a third-party Android Mod workbench for *Plants vs. Zombies Heroes*. The [English UI catalog](i18n/en-US/) is a draft from **r-2-30 RC1**, based on the [Simplified Chinese catalog](i18n/zh-CN/) from **r-2-29 RC2**. The English build passed Android smoke tests for key workflows. Terminology and wording are open for review.

Translation feedback is welcome via Issues or Pull Requests. Keep the JSON keys and numbered placeholders such as `{0}` when proposing changes.

## Góp ý bản dịch tiếng Việt

Bản dịch tiếng Việt đang ở giai đoạn đầu. Bạn có thể xem các tệp JSON và góp ý nếu câu chữ khó hiểu hoặc thuật ngữ thiếu nhất quán. Khi góp ý, hãy gửi tên tệp, khóa JSON và cách diễn đạt đề xuất. [Bảng dịch tiếng Việt](i18n/vi-VN/) · [Gửi phản hồi trên GitHub](https://github.com/Show-o4210/PVZH-Library/issues/new)
