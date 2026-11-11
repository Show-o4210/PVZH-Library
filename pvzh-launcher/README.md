# PvZ Heroes Advanced Modding Library

PVZH 启动器是《植物大战僵尸：英雄》的第三方 Android Mod 工作台。它提供 Mod 管理、卡牌和美术编辑，以及游戏资源准备等入口。手机操作和版本能力见[启动器工作台指南](../Library-docs/24.启动器工作台与手机编辑/README.md)。

这里公开项目简介、界面词表和卡名。完整客户端与 Hook 实现由独立工程维护。

## 启动器本地化

**r-2-44 RC1** 是 development 测试候选。当前三语词表按同一版本维护。

| 语言 | 词表 | 来源 |
| --- | --- | --- |
| 简体中文 | [zh-CN](i18n/r-2-44/zh-CN/) | RC1 生效词表与原版中文卡名 |
| English | [en-US](i18n/r-2-44/en-US/) | RC1 生效词表与英文卡名 |
| Tiếng Việt | [vi-VN](i18n/r-2-44/vi-VN/) | 基于 RC1，参考越南语 LawnStrings 审校文案和卡名 |

每种语言包含 `launcher/` 的 5,706 个启动器词条、`floating-tools/` 的 417 个游戏内工具词条，以及 `card-names.json` 中按 GUID 索引的 579 个原版卡名。越南语修订用于后续构建，已核对键、占位符、游戏标记和卡名 GUID，等待构建与 Android 实机检查。

欢迎通过 Issue 或 Pull Request 反馈。请注明语言、文件名及 JSON 键或卡牌 GUID，并保留键、`{0}` 等占位符和游戏标记。游戏本体与 Mod 自带文本使用各自的资源。许可范围见[许可证索引](../LICENSES.md)。

历史词表仍可查阅：[简体中文](i18n/zh-CN/) · [English](i18n/en-US/) · [Tiếng Việt](i18n/vi-VN/)。

## About PvZH AM

PvZH AM (Advanced Modding) is a third-party Android Mod workbench for *Plants vs. Zombies Heroes*. The **r-2-44 RC1** development catalogs cover the launcher, in-game floating tools, and stock card names in [Simplified Chinese](i18n/r-2-44/zh-CN/), [English](i18n/r-2-44/en-US/), and [Vietnamese](i18n/r-2-44/vi-VN/). The Vietnamese catalog includes wording and card-name revisions for a later build.

For translation feedback, include the locale, file, and JSON key or card GUID. Keep placeholders such as `{0}` and in-game markup intact.

## Góp ý bản dịch tiếng Việt

[Bộ dữ liệu tiếng Việt dựa trên r-2-44 RC1](i18n/r-2-44/vi-VN/) gồm văn bản trình khởi chạy, công cụ nổi trong trò chơi và tên thẻ gốc. Các chỉnh sửa dựa trên LawnStrings tiếng Việt và dành cho bản dựng sau. Khi góp ý, vui lòng gửi tên tệp, khóa JSON hoặc GUID của thẻ và cách diễn đạt đề xuất. [Gửi phản hồi trên GitHub](https://github.com/Show-o4210/PvZH-AML/issues/new)
