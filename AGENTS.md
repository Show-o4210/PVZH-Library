# Agent 入口

开始处理卡牌技能、关卡和简体中文 Bundle 时，先读 [agents/README.md](agents/README.md)。

初次基础制作可按 [独立示例](agents/08-basic-mod-walkthrough.md) 执行；维护与当前证据边界见 [agents/09-maintenance-and-evidence.md](agents/09-maintenance-and-evidence.md)。只克隆本仓库也能使用示例，不需要本机mod1/mod2目录。

- 本次 Agent 指南只覆盖 TextAsset 卡牌 JSON、BoardAbility、关卡事件、中文本地化与 ADB 验证。
- 人类章节提供导航和背景；实际字段、类型字符串、枚举、资源名称必须从用户提供的原包或仓库工具代码核对，不把教学伪代码当作可直接导入的数据。
- 保留用户输入包；输出、设备备份和验证记录分别保存。修改前检查工作树；只修改本任务目标。
- 不为普通卡牌或场景规则改动引入 IL2CPP patch、APK 重签或存档修改。
- 验收范围以用户要求为准；启动主界面、静态检查、设备哈希和战斗技能实测分别记录。库内示例只做离线构建，不连接设备。
