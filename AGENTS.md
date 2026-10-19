# Agent 入口

开始处理卡牌技能、关卡和简体中文 Bundle 时，先读 [agents/README.md](agents/README.md)。

初次基础制作可按 [独立示例](agents/08-basic-mod-walkthrough.md) 执行；维护与当前证据边界见 [agents/09-maintenance-and-evidence.md](agents/09-maintenance-and-evidence.md)。只克隆本仓库也能使用示例，不需要本机mod1/mod2目录。

- 基础任务仍按01–09处理TextAsset卡牌JSON、BoardAbility、关卡事件、中文本地化与部署。已授权的运行时技能扩展读 [10](agents/10-runtime-skills-workflow.md)，语义测试与证据读 [11](agents/11-semantic-testing-and-evidence.md)；详细归档见第21章。
- 人类章节提供导航和背景；实际字段、类型字符串、枚举、资源名称必须从用户提供的原包或仓库工具代码核对，不把教学伪代码当作可直接导入的数据。
- 保留用户输入包；输出、设备备份和验证记录分别保存。修改前检查工作树；只修改本任务目标。
- 不为普通卡牌或场景规则改动引入IL2CPP patch、APK重签或存档修改。用户明确要求且原版配置不能准确表达时，可在授权范围设计匹配的Base／Gadget扩展；私有规则编号、RVA和布局不能跨版本直接套用。
- 验收范围以用户要求为准；启动主界面、静态检查、设备哈希和战斗技能实测分别记录。库内示例只做离线构建，不连接设备。
- 新增运行时章节只提供文档和字段筛选的证据摘要，不随库提供完整调试服务、APK或签名凭证。不能因为文档中有命令就假定本机或设备已部署接口。
- 保留历史版本的通过、失败和未测项。用户总体运行反馈不覆盖已记录的调试异常；模型结算、History、真实动画队列与逐帧美术分别验收。
- 处理组合效果、攻击后新动作、本回合能力或随机分支时，接着读[Agent12](agents/12-composed-actions-and-duration.md)；R25补充与R19历史证据分开，不直接套用私有规则编号。
- 用户要求AI API或自然语言原版制卡时，读[Agent13](agents/13-natural-language-native-cards.md)和第22章。原版流程使用受约束plan与原生模板编译，不混入Gadget合同；API凭证仅保存在进程内存。模型格式、语义对照、结构、回包、游戏验收分别记录。
- 用户处理新增GUID、独立文字、UUID/资源路径或Manifest映射时，接着读[Agent14](agents/14-card-identity-and-assets.md)与第23章。R9资源寻址适配不等于私有技能扩展；不要把其new_cards合同当成本库公开v1已支持，也不要把能抽卡打出当作收藏/组牌登记完成。文档整理只复核已有材料，不据文内命令操作设备。

<!-- R11-library:agent15 -->
- 用户处理多Mod导入、玩家新卡拥有权、同号身份、显式复制、移除卡与正式玩家流程时，接着读[Agent15](agents/15-multimod-player-lifecycle.md)。安装内预约不是社区全局号段；本地身份不扩展服务器裸GUID协议。正式流程、离线替身、fixture和文档归档分别留证，保持原包／存档和已有工作树。
