# 11 · Mod内能力与启动健康恢复

本节整理2026-10-25 Android R29的实现与阶段证据。它接续[08的R12全局登记](../08.实验能力登记与冷启动许可/README.md)，将运行选择改为每个Mod的本机偏好，并加入本次启动确认和恢复入口。R12当时“安全启动只有前置”的结论保留；本节也不把R29实现完成、主机通过或旧版本战斗成绩当作稳定版本验收完成。

**当前状态：已补RC4的真实AI、加载及手动恢复结果，不能称为全技能稳定验收通过。** 用户要求跳过当前对局后，打出新卡和精确下回合结算标为USER_SKIPPED；自动回到启动器受Android限制仍失败。各层按本节后续表分别判断，最终发行状态以R29交付收据为准。Syndrome专项不在本轮。新卡连续性另见[第23章08](../../23.卡牌身份与资源映射/08.本地新卡连续性与同账户保护.md)。

## 1. 三层信息仍要分开

| 层 | 内容 | 能证明什么 |
| --- | --- | --- |
| Mod数据 | 实际资源文件、已登记能力声明、卡表中的私有规则 | 该内容需要哪些内置能力；不能因此执行附件脚本或so |
| 本机偏好与加载快照 | 每Mod的auto/on/off、全局安全模式、本次实际获胜资源及冻结能力 | 本次应当采用什么；不能冒充Hook已经安装 |
| 运行时报告 | 当前事务／PID的模块状态、阶段和错误 | 本进程初始化是否确认；不等于技能、动画或完整对局已验 |

`NativeModOptions`将偏好存于应用私有`files/native-mod-options.json`，不放进Mod ZIP、卡表或作者登记簿。每个稳定Mod ID分别保存`extensions / music / ai_extensions`，值为`auto / on / off`。缺省均为auto；`show_launch_details=false`、`safe_mode=false`。保存相同值不增加revision；损坏文件只报告错误，不以默认值覆盖原件。显式重置先备份旧字节，只重置启动器偏好，保留Mod、对话、项目与玩家数据。

## 2. 先选资源赢家，再算依赖

多Mod仍按顺序**整文件优先**，不合并各卡表GUID。能力解析在资源选择完成之后执行：

1. 扫描真正获胜卡表中的已登记私有规则；被完全覆盖且没有任何资源赢家的Mod不参与聚合。
2. 一个Mod只贡献中文、其卡表被覆盖时，已知具体卡牌规则声明列入`ignored_declarations`，不能据此假设这张技能已采用。模块级依赖声明仍可说明实际资源包需要的模块。
3. 无游戏资源的能力包可显式选择已有内置模块；不会获得附件代码执行权。
4. 只有登记版本足够、标记支持的能力才能auto启用；未知能力、陌生编号或过高版本保留`unavailable`，不能猜测映射。

同一进程共用一组模块，因而`on`优先于`off`，之后才判断auto依赖；冲突必须记录双方Mod来源及结果。显式off阻断真实依赖时保留诊断，不改写卡牌来掩盖缺失。音乐还依赖扩展模块，扩展显式关闭时不能宣称音乐有效。

全局安全模式优先级最高，关闭扩展、音乐、六路、托管及AI私有扩展许可；原版入口也关闭这些能力。它们不改写各Mod已保存偏好。六路与托管保留独立玩法开关，不因某张卡需要扩展自动开启。

旧全局`extensions_enabled / music_enabled`保留历史记录，不再暗中否决Mod的auto。计划中的`experiments_saved`保存旧全局值，`experiments_loaded`表示本次有效采用值；两者不同可能是正常解析结果。

## 3. 游戏可运行不等于AI可编写

`authoring(Context,modId)`只针对当前编辑项目，不借用其他勾选Mod的许可。AI的auto继承旧全局显式AI许可，Mod的on/off明确覆盖；运行auto开启不会自动开放AI配方。原版技能制作不受这份私有许可限制。

已获AI许可的纯原版项目可取得“添加第一条已登记扩展”的前瞻权限，避免必须先含扩展才能创作扩展的循环。采纳之后仍须按真正保存的卡表重新扫描，并完整启动游戏。前瞻权限不是当前进程正在执行的证明。音乐继续只引用当前项目已登记曲目和既有配方。

UI需分别使用`modStatus.effective`展示游戏预览、`authoring_preview`展示创作许可，不能把“项目现在无需扩展”显示为“AI没有权限”。保存、采纳、冻结采用和真实执行分别留证。

## 4. 说明默认收起，错误保持可见

普通启动默认不弹文件来源、组合及音乐说明，设置可重新打开；手动来源入口保留。该偏好只管理普通说明，不静默吞掉Bundle部署、策略解析或必需能力初始化错误。

`NativeLaunchHealth.begin`在资源事务提交且即将释放Unity时记录prepared。报告绑定独立attempt、资源transaction和PID；begin本身只证明资源准备，不能直接记为成功。运行时先安装记录器，再调用原入口，因此资源别名阶段先失败、后续补卡未安装，也能留下失败阶段。

| 状态 | 解释 |
| --- | --- |
| prepared / starting | 当前事务和PID等待运行时确认 |
| ready | 核心及本次必需模块已确认初始化；不是对局或技能验收 |
| partial | 核心已进入，但必需模块缺失、不可用，或启动后发生明确必需能力错误 |
| failed | 捕获到明确启动异常，保留阶段 |
| unconfirmed | 旧PID／事务未走到确认，或报告无法读取；主动退出也可能如此，不能直接称为崩溃 |

有新增收藏资源绑定时，收藏资源模块属于必需模块；无绑定的原版入口中同类辅助失败可记warning。player-flow辅助导航失败也不自动称为游戏崩溃。ready之后真实库存保存／读回错误可降为partial；账号切换、显式0等正常保护性skip不降级。

## 5. 恢复是显式操作，不能替玩家删数据

恢复页可检查Mod、安全模式、完整重启、原版入口及备份后重置损坏偏好。健康组件不部署旧资源、不回填整份账户、不自动更改Mod选择。确认忽略某次提示也不删除原失败报告；新失败不被旧确认遮住。

自动重启先安排本应用入口，再结束当前Unity进程；安排失败时不结束进程。Android 12以上只有已具备许可时才用精确闹钟，否则普通闹钟可能被系统延迟，需保留“完整退出后重开”的手动路径。主机桩验证顺序和失败保护，不能证明所有Android设备都能自动回到启动器。

库存保护亦有独立边界：若早期替换已发生、资源初始化又在接管前失败，旧快照保留供明确恢复，但本轮没有自动跨PID重放旧库存；详见[连续性章节](../../23.卡牌身份与资源映射/08.本地新卡连续性与同账户保护.md)。不能据“安全模式”三个字承诺所有存档事故自动救回。

## 6. 证据及实现边界

阶段证据见[筛选摘要](R29阶段验收摘要.json)。能力策略59项主机检查；早期健康JS为29场景56断言、Java为30项主机检查。它们分别验证策略、文件生命周期及Android桩，不相加成真实设备对局数；后续RC4真实结果独立列于下节，不回写这些早期报告。

统一补丁从冻结R28 RC2生成，只允许player_cards、runtime及最终入口三段变化，独立边界检查还原原脚本并核对source-map。健康记录本身不增加native Hook；库存保护另增3个观察Hook，因此不能把整份R29称作“没有新增Hook”。这不改变卡牌私有技能的规则编号或公开Python原版合同。

工作区来源：Mod策略（`pvzh-launcher/native-r29/docs/MOD-RUNTIME-OPTIONS.md`）、健康与恢复（`pvzh-launcher/native-r29/docs/LAUNCH-HEALTH-AND-RECOVERY.md`）、验收矩阵（`pvzh-launcher/native-r29/docs/ACCEPTANCE-MATRIX.md`）。原工程路径供历史追溯。可直接阅读本节和筛选摘要。

## 7. RC4真实结果与停止边界

本节RC4结果绑定APK SHA256 `42c084fce94bdbf8dae5b9ecc623502e02f23a7d63d016363d2175b80115ec62`，不将此前RC2库存恢复单次观察拼成同一APK已经全测。

| 层级 | 实际结论 |
| --- | --- |
| 手机直连真实AI工作台 | card、refine、reject、level-confirmed经UI发送及采纳／拒绝通过，非PC relay；拒绝前后已保存ZIP相同，继续修改只把新卡血量3改4 |
| 新卡独立实读 | 900002复用可收藏模板653，1费2/3，后续2/4；卡表、独立文本、美术身份与技能树实读通过，650原卡保留 |
| 关卡独立实读及加载 | `PVE_Soft_Node_Plant_001`采用僵尸英雄40血、植物10初始阳光及BoardAbilities 359／356；正式原进度入口实际进入，非fixture／headless，已核对40张正式牌组、场景实体及新卡sprite／库存4张 |
| 普通“植物第1关”自动定位 | 原请求只拿到3份预选关卡样本，未定位而要求澄清；保存Mod未变。补充实际NodeID后再调用真实AI并采纳，不能把前次澄清改写为一次自动完成 |
| 实际新卡打出及下回合精确差值 | USER_SKIPPED：用户要求跳过当前对局；3点英雄伤害＋抽1、僵尸成长的精确下一回合delta没有获得正式结算PASS |
| 自动重启 | FAIL：RC4在Android37仍被BAL_BLOCK；闹钟安排／旧PID退出不等于新界面出现 |
| 手动后备恢复 | PASS：退出前有明确手动提示，实际打开应用抽屉点击PvZ图标返回主页；安全模式保存，41份玩家／工作台文件逐字节保留。不能称自动重启已修好 |

真实AI手机直连证明应用有可用HTTPS路径，仍保留系统`android_validated=false / partial_connectivity=true`；不由此推断EA库存服务已同步成功。

独立卡牌检查最初曾因检查器强求额外IsAlive／WillTriggerEffects条件而FAIL；后续改按真实自触发范围与目标真值表核对，`card-rc4-selfscope`通过，原FAIL保留。检查器修正不是游戏技能结算证明，也不是为了通过而改写卡牌。

来源：真实制卡（`pvzh-launcher/native-r29/evidence/ai-workflow-rc4/card-result.json`）、继续修改（`pvzh-launcher/native-r29/evidence/ai-workflow-rc4/refine-result.json`）、拒绝（`pvzh-launcher/native-r29/evidence/ai-workflow-rc4/reject-result.json`）、关卡澄清（`pvzh-launcher/native-r29/evidence/ai-workflow-rc4/level-clarification.json`）、确认关卡后采纳（`pvzh-launcher/native-r29/evidence/ai-workflow-rc4/level-confirmed-result.json`）、卡牌独立复核（`pvzh-launcher/native-r29/evidence/independent-ai-assets-card-rc4-selfscope.json`）、关卡独立复核（`pvzh-launcher/native-r29/evidence/independent-ai-assets-level-rc4.json`）、正式入口初始状态（`pvzh-launcher/native-r29/evidence/formal-rc4/initial.json`）、自动恢复失败（`pvzh-launcher/native-r29/evidence/qa-fault-recovery/rc4-card-assets-invalid-binding-r2/ui-recovery.json`）与手动恢复（`pvzh-launcher/native-r29/evidence/qa-fault-recovery/rc4-card-assets-invalid-binding-r2/manual-recovery.json`）。

上述旧工程已退役，文件名保留作出处。可查仍保留的 [R29 阶段验收摘要](R29阶段验收摘要.json)。
