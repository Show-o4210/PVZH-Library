# 13 · 用AI API制作原版卡牌

适用：用户要求整理自然语言制卡知识、接外部模型API或制作原版卡牌生成工具。只改普通卡牌时不要因关键词联想到R19／R25扩展。

1. 读[第22章](../22.自然语言原版制卡/README.md)与[工具README](../tools/natural-card-author/README.md)。识别原包、现有改动、目标单位和制作范围；不覆盖前一轮Library文件。
2. 原始数据是事实来源。版本按规范化卡表指纹核对；API密钥仅保存在进程内。给模型的是需求、原包卡名索引和能力合同，没有key、文件操作或native调用权限。
3. 模型只输出[plan合同](../tools/natural-card-author/plan.schema.json)，程序通过原版模板编译。unknown字段、私有规则、重复组件、不合法目标／阵营及未知引用均拒绝。
4. 保留ready、clarify、unsupported三种结果。unsupported可能只是工具缺少配方，不是引擎不可能。还要测误拒绝，不能仅看没有编造新类型。
5. 原版复杂能力优先同阵营完整复制；重组时区分Self／事件Target、伤害后／攻击后、回合／本线战斗、打出／召唤。不要导入1001及以上规则或把两个Manual当成一次目标。
6. 先写中文用例和预期，再调用模型。记录原始响应、提示词版本、校准与未见样本，不能用自己改过的答案冒充模型输出。
7. 结构和回包检查包括所有嵌套实体类型唯一、中文增量、引用、显示字段、每个Bundle的非目标对象字节与目标回读；内容没变时允许零对象变化并保留原Bundle。
8. 本库公开v1每次是独立单卡输出，累计工程必须按patch合并并维护中文／历史，不能轮换完整Bundle假定累计。后续R9独立产品支持累计编辑与new_cards，但没有同步升级此处plan.schema.json，见[Agent14](14-card-identity-and-assets.md)。
9. 初轮32例及415来源复制均是离线／API证据；用户后来授权的游戏抽样见[第22章04](../22.自然语言原版制卡/04.API卡牌独立真机抽测.md)。测试运行时不随库附带；设备、游戏结果与动画仍按[04](04-device-verification.md)和[11](11-semantic-testing-and-evidence.md)另行授权、分层记录，不能把少量抽测扩展到整个能力空间。

可执行`benchmark.py`默认只测离线预期；`--replay`回放已脱敏的模型计划，`--live`才调用DeepSeek且最多8个四例批次。凭证不入库，不自动推送、安装或改变当前游戏。

新增GUID、独立文本与资源寻址的完整关系见[第23章](../23.卡牌身份与资源映射/README.md)。R9资源适配与原版技能合同分层；不要把仅原版组件技能理解成新卡在未适配APK中也必能显示。

<!-- R11-library:player-product-followup -->
后续Android产品的玩家拥有权、同号身份和正式流程见[Agent15](15-multimod-player-lifecycle.md)。这些资料没有升级本库公开Python v1的plan合同，也不改变原API／离线成绩。
