# PvZ Heroes Advanced Modding Library

PVZH 启动器是《植物大战僵尸：英雄》的第三方 Android Mod 工作台。它提供 Mod 管理、关卡、卡牌和美术编辑，以及游戏资源准备等入口。手机操作和版本能力见 [v4 功能与验收](../Library-docs/24.启动器工作台与手机编辑/05.当前版本能力.md#v4)。

这里公开项目简介、界面词表、卡名和部分离线工具源码。完整客户端与 Hook 实现由独立工程维护。

## R73 RC1 源码预览

首批公开 7 个离线美术与编辑器辅助模块。PvZH AM 是面向国际版《植物大战僵尸：英雄》的非官方社区 Mod 项目。发布范围、源码状态及 EA 政策说明见[源码预览](source-preview/r73-rc1/README.md)。

## v4 更新日志

[中文](releases/v4/changelog-zh.json) · [English](releases/v4/changelog-en.json)

## 翻译修正

翻译来源、已知问题和 R73 RC1 编辑器采纳结果见[翻译修正交接包](translation-fixes/README.md)。

## 启动器本地化

以下词表为 **r-2-64 RC1** 与 **r-2-44 RC1** 的版本资料。

| 语言 | r-2-64 RC1 | r-2-44 RC1 |
| --- | --- | --- |
| 简体中文 | [zh-CN](i18n/r-2-64/zh-CN/) | [zh-CN](i18n/r-2-44/zh-CN/) |
| English | [en-US](i18n/r-2-64/en-US/) | [en-US · 含社区修订](i18n/r-2-44/en-US/) |
| Tiếng Việt | [vi-VN](i18n/r-2-64/vi-VN/) | [vi-VN · 含社区审校稿](i18n/r-2-44/vi-VN/) |

R64 每种语言包含 `launcher/` 的 6,119 个启动器词条、`floating-tools/` 的 412 个悬浮工具词条和 5 个与启动器共用的社区入口词条，以及 `card-names.json` 中按 GUID 索引的 579 个原版卡名。启动器词条从冻结构建输入还原，并在候选 APK 的 DEX 字符串表核对。悬浮工具和卡名来自该 APK。

R44 收录参考越南语 LawnStrings 整理的文案和卡名，以及后续英越社区修订。查阅社区译稿时请使用上表的 R44 链接。R64 目录对应已构建的开发包。

欢迎通过 Issue 或 Pull Request 反馈。请注明语言、文件名及 JSON 键或卡牌 GUID，并保留键、`{0}` 等占位符和游戏标记。游戏本体与 Mod 自带文本使用各自的资源。许可范围见[许可证索引](../LICENSES.md)。

历史词表仍可查阅：[简体中文](i18n/zh-CN/) · [English](i18n/en-US/) · [Tiếng Việt](i18n/vi-VN/)。

## About PvZH AM

PvZH AM (Advanced Modding) is a third-party Android Mod workbench for *Plants vs. Zombies Heroes*. The **r-2-64 RC1** development catalogs cover the launcher, in-game floating tools, and stock card names in [Simplified Chinese](i18n/r-2-64/zh-CN/), [English](i18n/r-2-64/en-US/), and [Vietnamese](i18n/r-2-64/vi-VN/). The r-2-44 catalogs retain community edits in [English](i18n/r-2-44/en-US/) and reviewed wording and card names in [Vietnamese](i18n/r-2-44/vi-VN/).

The [v4 guide](../Library-docs/24.启动器工作台与手机编辑/05.当前版本能力.md#v4) (in Chinese) covers the mobile level editor, card class and rarity, stock artwork restoration, and swipe navigation. See the [English changelog](releases/v4/changelog-en.json) for release details.

For translation feedback, include the locale, file, and JSON key or card GUID. Keep placeholders such as `{0}` and in-game markup intact.

## Góp ý bản dịch tiếng Việt

[Bộ dữ liệu tiếng Việt của r-2-64 RC1](i18n/r-2-64/vi-VN/) gồm văn bản trình khởi chạy, công cụ nổi trong trò chơi và tên thẻ gốc trong bản dựng phát triển. [Bộ dữ liệu r-2-44 RC1](i18n/r-2-44/vi-VN/) lưu các chỉnh sửa của cộng đồng và tên thẻ đã rà soát theo LawnStrings tiếng Việt. Khi góp ý, vui lòng gửi tên tệp, khóa JSON hoặc GUID của thẻ và cách diễn đạt đề xuất. [Gửi phản hồi trên GitHub](https://github.com/Show-o4210/PvZH-AML/issues/new)
