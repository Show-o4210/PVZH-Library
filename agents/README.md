# PVZH Agent任务路由

当前Android产品是 **正式v1／内部R51**，维护证据窗口为R42–R51与正式v1。先读[入口规则](../AGENTS.md)，看产品范围用[Agent22](22-mobile-workbench-and-release-scope.md)，按症状排障用[第24章06](../24.启动器工作台与手机编辑/06.故障排查与避坑.md)。全库专题、工具内部文档、旧参考和历史检查都在[文档总索引](../文档总索引.md)。

本目录是查资料的路由，不授权连接设备、调用真实模型、恢复数据、上传或关机。旧指南中的命令、当前状态和阶段授权只代表其历史上下文。

## 先按范围选择

| 任务范围 | 应采用的合同 |
| --- | --- |
| 手机启动器、手动积木、AI快速／专家、当前目录或关于页 | [第24章05当前能力](../24.启动器工作台与手机编辑/05.当前版本能力.md)与Agent22；再查专题来源 |
| 本库Python／静态工具 | 对应 `tools/` 或 `mods/` 的README、schema、代码及嵌套AGENTS；Android进展不自动扩展这些合同 |
| 原版卡牌、关卡、中文、贴图／动画／音频 | 从本次输入核对字段与类型；[基础示例](08-basic-mod-walkthrough.md)、[关卡索引](../09.关卡修改/INDEX.md)和原版主题章节 |
| 历史运行时／AI／新卡故障 | 下表10—21作定位与经验来源，编号、RVA、状态与测试结论仍绑定原版本；当前行为以05／06和实际实现为准 |

## 专题指南

| 编号 | 入口 | 用途与版本边界 |
| --- | --- | --- |
| 01 | [Bundle读写与范围](01-bundles-and-scope.md) | 原包定位、UnityPy、非目标差异检查 |
| 02 | [Fighter与BoardAbility](02-fighters-and-board-abilities.md) | 原版能力移植、双方与场景规则；实际类型从原包读取 |
| 03 | [关卡与中文](03-levels-and-localization.md) | 僵尸200为案例，其他关卡先走统一索引 |
| 04 | [设备验证](04-device-verification.md) | 分层验证与恢复方法；不继承旧设备操作授权 |
| 05 | [小范围卡牌重写](05-smarty-card-remix.md) | 冻结、消灭来源、双重打击等历史案例 |
| 06 | [多职业卡牌重写](06-large-card-remix.md) | 进化、召唤、目标、重定向与期限效果案例 |
| 07 | [健壮／狡猾改版](07-hearty-sneaky-remix.md) | 阶段、墓碑、增益接收者与延时动作 |
| 08 | [独立基础示例](08-basic-mod-walkthrough.md) | 自备原包→卡牌／单关／中文→离线构建；不依赖外部mod1/mod2 |
| 09 | [维护与证据](09-maintenance-and-evidence.md) | 原包身份、来源优先级、历史统计与验收区分 |
| 10 | [运行时技能工作流](10-runtime-skills-workflow.md) | 原版与扩展层选择、旧私有规则／缓存／ABI |
| 11 | [语义测试与证据](11-semantic-testing-and-evidence.md) | 原引擎合法出牌、抽卡／召唤、终局及失败隔离 |
| 12 | [组合动作与期限](12-composed-actions-and-duration.md) | 攻击后、手动目标、树所有权、期限与随机分支历史 |
| 13 | [自然语言原版制卡](13-natural-language-native-cards.md) | 原版受约束plan与独立Python核心，区别Android工作台 |
| 14 | [卡牌身份与资源](14-card-identity-and-assets.md) | GUID／文本／prefab、Manifest、旧新卡资源故障 |
| 15 | [多Mod与玩家生命周期](15-multimod-player-lifecycle.md) | 本地身份、拥有权、同号与冷启数量的阶段经验 |
| 16 | [实验能力与冷启](16-experimental-capabilities-and-launch.md) | 旧阶段许可来源；不把旧统计当当前能力清单 |
| 17 | [会话、审批与恢复](17-conversation-authoring-and-approval.md) | 历史Android会话／候选／取消／收据，非公开Python新增合同 |
| 18 | [批量属性与分类审查](18-batch-stats-and-typed-review.md) | 按真实diff审查、有限预演、属性与技能分别验证 |
| 19 | [版本历史与回归](19-version-history-and-regression.md) | 快照、索引、选择性回退与当轮普通表达验证 |
| 20 | [本地音乐](20-local-music-capability.md) | 登记曲目、许可、共享Hook与播放器／听验边界 |
| 21 | [变形与子效果](21-pharaoh-transform-and-child-effects.md) | R25同批快照／当前攻血／子效果案例，私有规则不能自由外推 |
| 22 | [手机工作台与发布](22-mobile-workbench-and-release-scope.md) | 当前v1／R51入口；R42–R51及R48界面参考 |

## 证据如何使用

历史 `verification-*.md` 全部保留并逐篇纳入[总索引](../文档总索引.md)。其日期、原包指纹、APK／脚本身份和实际层级限定结果，不能合并成当前版本全面通过。旧R专项文档可提供仍有效的字段、原因与负例，已取消的任务和过去的授权不重新执行。

本机／静态、AndroidUI、原引擎、正式对局、真实模型与逐帧视听分别记录；旧主界面启动成功不等于技能正确，同机回读不等于官方或跨设备同步。原始输入、候选、实际采纳与游戏加载保持可区分。保留具体失败和未测，不为整理目录补造通过。

资料库只保留脱敏摘要与可独立阅读的说明，不带完整Android运行时、游戏APK、凭证或账户备份。发生资料冲突时，先核对当前产品／本次原包和相应工具合同，再读版本匹配的专题记录，不依据文章中的“当前”二字选择实现。
