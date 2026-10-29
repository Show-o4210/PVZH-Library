# PVZH Agent 工作指南（按任务逐步扩展）

2026-10-29后续手机产品资料：阅读[22 · 手机工作台与发布范围](22-mobile-workbench-and-release-scope.md)及[第24章](../24.启动器工作台与手机编辑/README.md)，了解R48的手动／组件编辑、AI模式、手动资源检查、媒体和文字包；历史章节及公开Python工具能力继续按各自版本理解。

本目录为执行任务的Agent提供最短资料路径、已核对字段和验证要求。基础覆盖属性、原版技能复用／重写、场景规则、单关、中文和回包部署；2026-10-15新增运行时技能契约与语义测试入口，2026-10-18追加第四批组合动作与期限状态。基础示例仍自包含；高级指南分别标明R19和独立R25案例，完整测试运行时不随库提供。

## 阅读顺序

初次接手先读 [08独立基础示例](08-basic-mod-walkthrough.md) 和 [09维护与证据](09-maintenance-and-evidence.md)，再按任务选择：

关卡任务优先从[关卡统一索引](../09.关卡修改/INDEX.md)进入，再读对应专题。当前限定植物／僵尸任务1～200；旧僵尸200指南是案例，不能替代400关定位、事件／场景构建和新实测状态。已纠错字段与按需工具资料规则集中在[第09章05](../09.关卡修改/05.资料纠错与按需调用规则.md)。

1. [01-bundles-and-scope.md](01-bundles-and-scope.md)：输入定位、UnityPy 读写、差异校验。
2. [02-fighters-and-board-abilities.md](02-fighters-and-board-abilities.md)：冬青技能移植、双方阵营、三头花生式生命值覆盖。
3. [03-levels-and-localization.md](03-levels-and-localization.md)：僵尸任务 200、真实对话结构、CSV 增量编辑；2026-10-16补充共享标记与全量翻译，完整流程见[第03章04](../03.本地化说明/04.复用引用与批量翻译工作流.md)。
4. [04-device-verification.md](04-device-verification.md)：ADB 部署、回退和实测证据。
5. [05-smarty-card-remix.md](05-smarty-card-remix.md)：七张聪明卡改版、冻结状态筛选、消灭来源、双重打击结构、无法精确表达的效果与启动验收。
6. [06-large-card-remix.md](06-large-card-remix.md)：74项多职业追加、进化与友方伤害、授予定时自毁、召唤副本、路线附加目标、伤害重定向、延迟资源修正陷阱、版本备份与启动验收。
7. [07-hearty-sneaky-remix.md](07-hearty-sneaky-remix.md)：20项健壮与狡猾追加、增益接收者阶段自毁、负资源、高地互斥、墓碑现身事件、换血备选、召唤副本、前版保留与启动证据。
8. [08-basic-mod-walkthrough.md](08-basic-mod-walkthrough.md)：用户原包→单卡属性与技能→单关→中文→静态验证；[可执行示例](examples/basic_mod.py)不需要本机mod1/mod2脚本。
9. [09-maintenance-and-evidence.md](09-maintenance-and-evidence.md)：当前案例统计、资料优先级、维护与证据边界；[2026-10-11检查记录](verification-2026-10-11.md)。
10. [10-runtime-skills-workflow.md](10-runtime-skills-workflow.md)：JSON与Gadget实现层选择、私有规则契约、效果池与引用ABI、窄动画兼容。
11. [11-semantic-testing-and-evidence.md](11-semantic-testing-and-evidence.md)：实际profile、无坐标出牌／抽卡／召唤、合法流程、原生异常停止、终局与验收分层。
12. [12-composed-actions-and-duration.md](12-composed-actions-and-duration.md)：第四批组合动作、单次手动目标、递归组件唯一性、攻击后、查询树所有权、期限状态与随机分支。
13. [13-natural-language-native-cards.md](13-natural-language-native-cards.md)：纯原版自然语言制卡、AI API合同、受约束编译、澄清与拒绝、实际API评测、后续UI／hook边界。
14. [14-card-identity-and-assets.md](14-card-identity-and-assets.md)：数字GUID与prefab/text身份、Manifest与包内资产、R9原版资源复用、累计编辑、多Mod别名与证据边界。
15. [15-multimod-player-lifecycle.md](15-multimod-player-lifecycle.md)：多Mod资源族、安装内新号预约、namespace／clone、同号过渡、正式玩家流程与服务器裸GUID边界。
16. [16-experimental-capabilities-and-launch.md](16-experimental-capabilities-and-launch.md)：全局能力登记、保存/冻结/实际三层、23项运行与3项AI配方、冷启动、缺失警告及安全启动前置边界。
17. [17-conversation-authoring-and-approval.md](17-conversation-authoring-and-approval.md)：Android R13长期会话、同意/拒绝、对话内真实卡片、累计候选、异步输入保护、取消与采纳收据恢复；公开Python v1合同不变。
18. [18-batch-stats-and-typed-review.md](18-batch-stats-and-typed-review.md)：Android R23批量属性、有限程序预演、0攻组件补全与按真实字段分类型审查；全量证据留本地，技能/结构变化仍强制全文，设备状态独立登记。

第四批归档入口及证据边界见[2026-10-18检查记录](verification-2026-10-18.md)。

同日自然语言原版制卡是独立新任务，见[第22章](../22.自然语言原版制卡/README.md)与[专门检查记录](verification-2026-10-18-native-authoring.md)，不将API／离线成绩计入R25战斗成绩。

随后获用户授权的六份API卡牌独立真机抽测见[设备检查记录](verification-2026-10-18-native-device.md)；使用纯原版B4和独立候选，未合并mod2。

此次提交／推送前的单测与归档回放检查见[发布前检查](verification-2026-10-18-publication.md)，不将离线复查写成新战斗或新在线API结果。

2026-10-19资源关系与R9经验归档见[第23章](../23.卡牌身份与资源映射/README.md)及[归档检查](verification-2026-10-19-card-assets.md)。3次真实API、70项游戏检查来自此前产品验收；这次文档整理没有新API或设备操作。

2026-10-20 R12后续实验能力整理见[第21章08](../21.语义调试与技能扩展实战/08.实验能力登记与冷启动许可/README.md)及[归档检查](verification-2026-10-20-experimental-capabilities.md)。原版公开Python v1没有因此升级；API、fixture结算、启动失败与后续修正分别留证。

2026-10-20 R13会话式制卡经验见[第22章05](../22.自然语言原版制卡/05.会话式制卡与提案审批.md)与[Agent17](17-conversation-authoring-and-approval.md)。服务/存储/项目锁离线成绩、RC1真实API成败和RC2连续修改/实际审批分列；headless合法出牌9项、恢复48项通过。自然完整玩家对局、逐帧动画和中文组合输入本轮未重验，不从已验层级外推。

只做基础改版时不必通读高级章节。处理新技能或已有语义接口时先读10／11，再按链接查[第21章](../21.语义调试与技能扩展实战/README.md)；资源切换查[第20章05](../20.工程体验跃迁-资源门卫与教程跳过/05.必选资源切换实战/README.md)。运行时归档校验见[2026-10-15检查记录](verification-2026-10-15.md)，本地化经验归档见[2026-10-16检查记录](verification-2026-10-16.md)。

## 证据范围

2026-10-08 针对用户提供的 `card_data_1`、`data_assets_29`、`cn_8` 解包核对，UnityPy 1.25.0。相同文件名不保证版本相同；换一批输入必须重新读取并记录 SHA-256。

| 输入 | SHA-256 |
|---|---|
| card_data_1 | e2579da5636125f82b86a85fba829459810b4ca41b1980528771b80da9c80201 |
| data_assets_29 | 37fd5f5af67dda86664b76e9bfefe1878b281cf8a1af05afec7a4282bf7b3007 |
| cn_8 | 950fc91396daf74f0a8e93b78d57662b8580818e8ffa38f5f74838a7ceed2bd7 |

mod1与mod2是用户工作区中的交付工程，不是本仓库依赖。[examples/basic_mod.py](examples/basic_mod.py)提供仓库内独立入口；其他章节中的工程路径只用于标识当时的证据位置。

R19证据另绑定其APK、脚本、Rev4资源和ARM64库，不沿用上表输入指纹。原mod2第三版的93张变更与18条舍弃是历史统计；R19追加运行时后为99张原卡变更、17张扩展卡／14类规则，音频仍排除。不要把新结果回写成旧第三版已逐项战斗通过。

<!-- R24-library:continuous-and-music -->
## R24后续入口（2026-10-24）

19. [19-version-history-and-regression.md](19-version-history-and-regression.md)：真实历史快照与索引、待审回退、验证输入的选择性撤销、动态筛选目录和30普通话术；8条真实API最终通过，保留修订和低堆边界。
20. [20-local-music-capability.md](20-local-music-capability.md)：当前Mod登记曲目、1024/1025配方、独立许可、RTPC/MediaPlayer握手与共享Hook owner；静态/协议、RC3拒绝、RC4恢复失败和RC5分层通过分开登记。

<!-- R25-library:pharaoh-transform -->
## Android R25 法老后续（2026-10-24）

21. [21-pharaoh-transform-and-child-effects.md](21-pharaoh-transform-and-child-effects.md)：全场同批当前攻血快照、私有1026与子效果验证、指定GUID50/NotCheats、原router复用及连续Buff一次补偿；RC5原引擎221检查与RC1–4失败/未测分别登记，视觉/听验不外推。

<!-- R28-library:original-resource-names -->
## R28 原版资源名与补卡启动故障（2026-10-25）

资源绑定或“新GUID已加载但没有获取”继续读[Agent14后续](14-card-identity-and-assets.md#r28-原版资源名校验后续)、[Agent15后续](15-multimod-player-lifecycle.md#r28-获取故障的启动前置)与[第23章07](../23.卡牌身份与资源映射/07.原版资源名校验与自动获取启动故障.md)。区分别名与原版资源名、650/646/4分类和模块初始化前置；固定可信模板白名单保留合法空格／单引号，实际APK、主机与冷重启拥有权分别验收。

<!-- R29-library:mod-runtime-and-continuity -->
## R29 Mod内能力与库存连续性（阶段归档）

按真实获胜资源计算auto/on/off、单项目AI许可、说明默认隐藏、启动健康与显式恢复，读[Agent16后续](16-experimental-capabilities-and-launch.md#r29-mod内偏好与健康恢复后续)和[第21章11](../21.语义调试与技能扩展实战/11.Mod内能力与启动健康恢复/README.md)。预Unity已有数量证明、同账户缓存路径、缺键／显式0及精确Sync边界，读[Agent15后续](15-multimod-player-lifecycle.md#r29-已有数量连续性后续)和[第23章08](../23.卡牌身份与资源映射/08.本地新卡连续性与同账户保护.md)。本轮仍在候选验收，不把主机通过或RC2单次恢复观察称作最终稳定／官方云同步已验。
