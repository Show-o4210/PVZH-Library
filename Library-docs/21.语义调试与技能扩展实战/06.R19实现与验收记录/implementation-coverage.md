# mod2 实现覆盖与验收边界

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/implementation-coverage.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](工程资料索引.md)，所收检查摘要不替代完整原始证据。

本页更新至 **已安装R19／profile_revision=4，本次分项技能验收套件均PASS**：攻击14case/21checks、属性8case/39checks、601承伤9case/17checks及交互2case/6checks、真实渲染动作8checks、动作逻辑7checks、最终继承静态8case/37checks。同候选原版17checks／36步完整胜利与规则隔离已通过，普通初始牌组再give601／202的改版23步战斗审计也确认真实game_over。

这些通过不覆盖所有边界：含601／202的自定义初始牌组在冷建局时0x0 AV失败，终局after-marker未处理使原整局测试报告FAIL；两份失败原样保留。5秒等待不是严格销毁屏障，异常也不能仅称温重开风险。全99张及所有复杂组合没有完成全量矩阵。

## 来源与实际集合

需求来源是 [第一批](工程资料索引.md#ref-a5715dae6952)、[第二批及确认](工程资料索引.md#ref-766ae70120c3)、[第三批及确认](工程资料索引.md#ref-11138936eda2)。原先18项缺口见 [舍弃名单](工程资料索引.md#ref-caa772cee70f)，GUID及原制作选择见 [第二批结果](工程资料索引.md#ref-d6281ddb2b37)、[第三批结果](工程资料索引.md#ref-d1582006e8f9)。实际 v3 基线为 mod2/out/card_data_1，完整覆盖三批。

资源由 [manifest](工程资料索引.md#ref-7e27af4d34ef)、[validation](工程资料索引.md#ref-66664b5dc72d)、[扩展卡数据](工程资料索引.md#ref-7c9743561e3b)、[构建脚本](工程资料索引.md#ref-0ad5f50067bb)定义。Rev4构建解包B4、v3及此前Rev3实际卡表并严格比较：

| 集合 | 数量 / 结论 |
| --- | --- |
| 三批不同需求 GUID | 101：第一批7、第二批74、第三批20 |
| B4 干净原版 | 650个定义 |
| mod2 v3 | 656个定义；相对 B4 改93张原卡 |
| Rev4 mod2 | 656个定义；相对B4改99张原卡 |
| Rev4 与 v3 不同的卡 | 19：17张扩展配置，另修静态97、547 |
| 完全沿用 v3 的已变更原卡 | 80：此前82张，减本轮另修的97、547 |
| 内部技能 / 副本定义 | 原有5个全部逐项保留 |

与v3不同的实际GUID为 **87、97、106、114、139、148、202、221、253、326、422、464、518、547、588、600、601、658、675**。其他v3定义没有改变。656包含原有额外卡GUID1001和5个内部定义；卡GUID1001与reserved规则编号1001是不同字段。

内部定义：900000201肥料阶段自毁、900000203双人菇的1费小喷菇副本、900000204直升机瞬态自毁副本、900000301陆行船0费0/1两栖水兵、900000302咖啡接收者阶段自毁。本轮没有给咖啡隐藏卡新增错误的RevealPhaseEndTrigger。

Rev4 mod2 card_data为 **135330字节**，SHA-256 `964b20aa9b4933e348d5fab93fc7f242236e2a2d6a294bcf53df9a87d13274c5`。B4 original card_data仍为 `e0682de0135a77bcd15c73072dc3221c0e25b1ac694ebc86bd7965e1d56d57b7`，与mod2/input的 `e2579da5...` 不同。严格Rev3对比只有601及两条伞叶中文说明改变，其他655定义和原版三份资源逐项不变；data_assets_29与原版相同。serializer schema与扩展contract均为1。

## 原生配置与后续静态修补

80张完整沿用v3的已变更原卡如下。配置保留不代表每张都完成实战矩阵。

| 批次 | GUID |
| --- | --- |
| 第一批4张 | 134、140、143、333 |
| 第二批59张 | 18、36、39、40、41、46、49、51、84、95、98、111、118、122、131、154、160、177、180、213、214、217、220、223、226、286、287、296、306、312、313、316、330、339、346、350、409、411、413、427、433、434、472、473、479、492、493、496、499、514、521、546、586、594、605、639、640、642、663 |
| 第三批17张 | 15、186、187、196、199、209、239、252、257、328、404、506、530、545、550、683、686 |

部分原生分支已有额外抽测：冬瓜 / 冻窝瓜联动、反射坚果有限连锁及死亡后生成77、香蕉分身、直升机瞬态召唤与自毁。详见 [冬瓜联动](工程资料索引.md#ref-d3b0a632e553)、[反射坚果追验](工程资料索引.md#ref-cd33e9bfe10f)、[召唤与自毁](工程资料索引.md#ref-62ed861e2529)。这些不组成80张全量回归。

| 修补 / 交互 | 最新实际证据 |
| --- | --- |
| 675只保留本线植物禁攻 | Rev2去掉旧GrantedTriggeredAbilities(564越线伤害)及Springboard；实际仍为2费0/3 fighter、isEnv=false。R14最新缓存下本线禁攻 / 异线攻击对照通过，不再只是静态清理。 |
| 97副本筛选 | Rev3将用于单位的SameLaneQuery改成InSameLaneQuery(OriginEntityType=Self)。R15 [5项全部PASS](工程资料索引.md#ref-36124b640f28)，包括真实额外攻击只转移一次及无副本正常承伤。 |
| 547原生能力拆分 | Rev3拆开GrantAquatic、Move、移动后水路-2/-2，保留PlaysFaceDown及原版Reveal重放PlayTrigger。R15 [PARTIAL报告保留](工程资料索引.md#ref-b3e8ca9ac5b6)：自然死亡旧断言误要Destroy。R16 [10项PASS](工程资料索引.md#ref-489676be124f)，包括正常墓碑揭示后两栖 / 移动 / 准确减益、2HP实际CardMove→Buff→Discard严格链及满水路反例。 |
| 252自现身重藏 | R15 [合法87路径3项PASS](工程资料索引.md#ref-e7cb45147bbe)。R16 [response分组追验](工程资料索引.md#ref-638768656c7f)进一步确认：揭别人不触发，直接扩展揭自身后同一次响应就重藏全部；native MixedUp从3变4恰一次，随后正常phase仍为4。此前直接fixture延至下一阶段来自响应分组时机，R16按当前原生response group修正；不是简单靠等待掩盖。 |
| 209咖啡墓碑接收者 | R14 / R15失败与bool FFI修正保留。新 [窄Gadget保护](../02.缓存契约与扩展规则/coffee-grave-preserve.md) 只在墓碑转换期间保护，返回恢复Count/Persistent，弹回仍原版清除。R16 [5项PASS](工程资料索引.md#ref-0b10c78290a3)：在场含墓碑接收者自毁，后登场及手牌单位保留；preserved1/restored1/errors0/roots0。隐藏卡配置未改。 |

## 舍弃名单中补入的17张扩展配置

这些配置使用原版GrantAbilityEffectDescriptor与reserved编号1001–1014，由匹配Gadget解释，没有未知IL2CPP `$type`。14种规则覆盖17张卡；Rev4按用户确认启用原先预留的1011，定义语义与contract版本不变。

R19最新 [攻击套件](工程资料索引.md#ref-087d9bf2cf78) **14case/21checks全PASS**，[属性与伤害套件](工程资料索引.md#ref-c7316d38eff0) **8case/39checks全PASS**，[601承伤](工程资料索引.md#ref-f4dc6c721c73) **9case/17checks全PASS**，[601交互](工程资料索引.md#ref-ab90c34fdc90) **2case/6checks全PASS**，[真实渲染动作](工程资料索引.md#ref-ef2c38fd047f) **8checks全PASS、unverified=[]**。

动作逻辑 [R19冷恢复后复测](工程资料索引.md#ref-968e3f334f71)7checks全PASS，保留原 [无等待重开中断FAIL](工程资料索引.md#ref-58cc13c6ce6d)及日志。[R19旧静态](工程资料索引.md#ref-0602f9dd6fe6)自然2秒等待后仍FAIL：前五case共18checks及banana前2checks通过，第三branch新局native AV立即停止，后续copter／diver未执行。随后独立新冷进程起点、fixture_delay_seconds=5的 [R19最终静态](工程资料索引.md#ref-c20afe3dbf73) **8case/37checks全PASS，全部unverified=[]**，覆盖freeze、reflection、coffee、grave、redirect97、banana472、copter286、diver547。R16历史完整报告仍保留。以上不是99张全量回归，旧R18使用Rev3、R19才使用Rev4。

| 卡牌 / GUID | 技能与主要边界 | 最新逻辑验收 |
| --- | --- | --- |
| 忧郁菇600、山胡桃石422、无脑坚果588、绿叶贤者148 | 1001自身禁攻；不是攻击力设0，保留对应进化、免伤、技能伤害 | R19禁攻／普通伤害对照PASS |
| 大喷菇139 | 1002本线僵尸禁攻；保留穿透与打出僵尸移入本线 | R19同线／异线对照PASS |
| 迪斯科舞池675 | 1003本线植物禁攻；旧越线伤害及被踩组件已清除 | R19最新profile对照PASS |
| 读报僵尸221 | 1004实际正伤害后解锁；加生命不解锁，回手／重置清状态 | R19解锁／加生命反例PASS |
| 暗物质火龙果464 | 1005每次攻击结束，左右邻线全部植物打6，不打本线 | R19原生额外攻击后邻线结算PASS |
| 原始豌豆658 | 1006攻击结束弹射自身，保留原生路线战斗前额外攻击 | R19原生回手结算PASS |
| 火炬树桩114 | 1007后排火炬在前方植物攻击开始时打本次攻击力量值；致死取消该次攻击 | R19致死／存活两项PASS |
| 狗头253 | 1008攻击植物英雄结束后-3/-3，即使未造成伤害；非攻击伤害不触发 | R19英雄攻击／非攻击对照PASS；旧DamageTrigger已移除 |
| 豆神326 | 1009禁止正力量增益、力量计算封顶；生命增益可发生，覆盖Buff／SetStat／modifier | R19手中、合法打出、持续光环与替换、回手矩阵PASS |
| 双子星518 | 1010僵尸正伤害变1，倍率后、护甲／免伤前；未现身不生效，离场恢复伤害 | R19真实墓碑／来源／倍率／护甲／免疫／最低生命／合法锦囊矩阵PASS |
| 伞叶601 | 1011每笔自身伤害从自身及左右邻线植物随机一株承受；自身直结，只转一次。1费0/2，保留组队／站位，旧免锦囊光环移除 | R19承伤9case/17checks/225笔Damage请求；交互2case/6checks/96笔，全PASS，具体未测边界见下文 |
| 太阳风暴106 | 1012保留本线／邻线植物伤害5；独立下回合-3债务，一次结清，来源退场不取消 | R19冷恢复动作逻辑叠加-6／次轮恢复／0下限PASS；R19当场及延期-3真实反馈／完整回合PASS |
| 墓碑克星87 | 1013选原生墓碑立即现身，不消灭目标 | R16同APK开启5checks PASS／关闭hang；R19合法现身逻辑及真实原bookends／队列结束PASS；新局初始化异常独立保留 |
| 英雄脑残粉202 | 1014交换当前HP、保留生命modifier、清旧CurrentDamage、末尾StateCheck | R19冷恢复后合法手牌增益／受伤双方逻辑PASS；R19真实SetStat及队列结束PASS |

601主套件实际发送225笔DamageEffect，最终selections/rng_calls均220；其中5笔零伤害不重新选人，不把225误写成225次随机。候选按单株采样：自身、左右各两株共5个个体；覆盖无邻株、两伞叶不循环、同线／敌人排除、真实护甲／免伤与518倍率后规范为1。另96笔交互覆盖原97转伤至900000203副本、2乘2恰为4且不重乘、左右边路不环绕。最后errors=0、pending_packets=0、pending_contexts=0；实际观察到各合法候选，但不是随机分布均匀性的统计证明。

交互报告明确未测target-dependent EffectEntityMultiplier与被沉默601：现有合法卡／fixture无法构造相应路径，未为测试额外改缓存或原生源码。AI推演、绕过DamageEffect直接调用Health.TakeDamage及所有原生redirector组合仍不在已验证矩阵内。

PASS只覆盖报告中的实际断言。普通 / 多重攻击的全部组合、所有英雄及AI推演未全面覆盖；手动双方fixture不能替代正常PvE / AI行为矩阵。

## 原版History与动画边界

87、202保留原PlayTrigger与group0；106保留伤害组并增加group1登记债务。原版TriggeredEffectGrouper（0x21DD880 / 0x21DDA34）提供Start/End，扩展结果进入当前原response队列。R14合法87实际取得 **Start→Reveal→End→Discard→PhaseResume**；这不再只是静态可达路径，也没有解决动画等待。

R14 [可见模式失败](工程资料索引.md#ref-fa3960f3d6b5)与R16 [关闭回退的冷对照](工程资料索引.md#ref-9f607301bb64)确认87旧special timeline未结束，Null actions已激活、子动画为空、并非等待加载。原结果分派没有RevealRecord。新 [87窄回退](../04.History与原版动画/reveal-animation-compatibility.md)只对当前mod2 / 来源87 / 严格Reveal+End组，让真正Reveal走独立原版消费者并保留书挡。**同R16 APK开启回退冷对照5项PASS**，见 [报告](工程资料索引.md#ref-b13ca6941d6b)：真实队列busy→empty、handler applied1/errors0/roots0、Start→Reveal→End保留及完整回合结束。R17据此默认开启；R18重新验证真实87出牌／Start→Reveal→End／自然队列结束通过。未截图，不能声称逐帧美术已完整验收。

R17 [真实渲染动作报告](工程资料索引.md#ref-f943c76eabaa)的前6项实际通过，包含202原生换血、87现身和106当场反馈；报告随后整体FAIL。106真实GainSunRecord在下回合资源刷新后产生，不能假称仍被上轮End包住；该记录源卡已Discard，原CardView粒子检索报错。异常后记录和模型均确认正确资源48，失败历史保留。

[R18最终真实渲染动作报告](工程资料索引.md#ref-9523bd8649ae)8checks全PASS、unverified=[]，完整覆盖202／87／106当场效果、延期扣阳光及完整回合。原SunCountIncrementedRecord使植物基础资源到51，随后源31／卡106、目标0的GainSun attempted=-3、actual=-3、available48；源卡保持Discard，模型资源48。窄 [PlayerView.LoseSun反馈](../04.History与原版动画/sun-animation-compatibility.md)保持引擎效果／来源／记录，sun handler applied1/errors0/roots0；实际采到busy→empty，最终原动画队列两表都0，动作errors0/pending_sun0。没有强制清队列、模拟点击或截图；opponent_ai=false及complete_visible_art_verified=false仍明确限制证据范围。

Rev4实际安装后的 [R19渲染复验](工程资料索引.md#ref-ef2c38fd047f)同样8checks PASS、unverified=[]，原87与sun handler均applied1/errors0/roots0，原记录和资源48保留，实际busy→empty、最终两队列0。它复验的是渲染局内动作与完整回合；不抵消随后无等待温重开reveal的新局初始化异常。

新增攻击 / 状态被动为直接marker，不自动产生自己的special Start/End。默认额外bookends仍禁用：借用已结束PlayTrigger曾让手动202结果被原生条件验证取消。被动结果仍走Damage、Buff、ReturnToHand等真实记录和通用消费者；缺少独立special不取消结算路径，也不等同画面已通过。Unique13只是卡面说明。

[History观察器](../04.History与原版动画/history-observation.md)只显式快照，已消费记录可能缺失，始终 `complete_history:false`。它不发新记录，不能证明屏幕播放；动画容器快照、技能逻辑与History分别验收。

## 稳定性已修正的范围

旧连续建局崩溃的坏引用根因已通过匹配native ABI确认：旧赋值把原生buffer写成C# String引用，GC可将非对象地址当对象。R14改用 `il2cpp_field_set_value_object` 直接传托管对象并执行写屏障，见 [引用字段ABI](../03.托管内存与效果所有权/il2cpp-reference-field-abi.md)。同进程攻击连续达到generation14通过、临时effect roots归零，随后属性和动作完整通过。机器码与设备结果共同支持已修正该可复现坏引用路径。

cache-only查找、临时GC根与原版效果所有权继续作为独立改进保留，不再当作该坏引用根因。早期禁观察器／加等待不足以证明修复。无等待及自然2秒温重开仍有EnterCheatGame空地址访问；含601／202初始牌组的冷建局也失败，因此不能把未定位的建局问题仅称温重开风险，不承诺所有启动／长时间重开均稳定。

R19再次限定此边界：stats套件后立即重开reveal发生0x0 AV，原子进程停止并冷恢复；测试加自然2秒后动作7项通过，但同样2秒的静态套件又在banana第三branch／previous_generation15重开时AV停止。运行时／APK没有因此修改，等待只是缓解；严格旧root／Context销毁屏障及held旧代释放仍未实现。详见 [生命周期复核](../05.实测与建局边界/fixture-lifecycle-review.md)。原版有限证据已有 [R18冷起17checks／36步胜利](工程资料索引.md#ref-8848769e6b44)及R12原版／改版各三局温重开，但不证明任意批量重开都稳定。

## 最终候选的资源隔离与整局范围

[R19原版回归](工程资料索引.md#ref-a23302579545)17checks全PASS，resource_profile=original、cold_started=true、固定seed1337。21次play及15次end_phase，共36步完整原版胜利；无模拟点击或截图。设备实际APK SHA-256为 `c7e48e0ae694d9fbf1b9c0e59d7fd73311fb880a4b56dc13ac1656c4cc6652cf`，安装script为 `3cc23604419967c87e89186a260dfa039ad9286389ba468a71c3f9c410efe32b`。[原版隔离快照](工程资料索引.md#ref-a062986f539c)PASS：改版active=false、attack.generated=0、umbrella.selections=0、temporary_effect_roots=0；同APK实际原版模式没有执行改版规则。

改版整局有三份必须分开的证据：[首次冷建局](工程资料索引.md#ref-64fbbefb4214)的初始牌组直接含601／202，cold_started=true但start_test发生0x0 AV，报告FAIL，不能计作初始牌组初始化通过。改为普通347／350初始牌组、再give601／202后，原 [整局测试报告](工程资料索引.md#ref-898a6b792046)仍FAIL，失败是终局要求after-marker排空的断言。

基于同一原命令日志和真实终态的 [战斗审计](工程资料索引.md#ref-8fe05f7e69d0)PASS：14次合法play、9次end_phase，共23步，game_over=true，僵尸玩家5胜／植物0败；601真实combat selections=2（自身1、转移1），技能errors=0、temporary_effect_roots=0。但attack.generated/started/completed=19/19/18，pending_attacks=1、pending_markers=1，after_marker_processed=false。原版效果队列停在终局LoseEffect，末笔after-marker及元数据保留至重置；审计只确认战斗胜利和实际承伤，不把原测试改写成全PASS，也不证明终局队列排空或生命周期清理。双方由命令合法操作，opponent_ai=false；不是全部正常AI实战矩阵。

失败历史保留：[R5攻击](工程资料索引.md#ref-875633a5877f)、[R5属性](工程资料索引.md#ref-e838f3db9b6b)、[R5动作与旧包装失败](工程资料索引.md#ref-0bdcdb0dad59)、[R12崩溃](工程资料索引.md#ref-9fdd5c10f6a9)。R14属性的中间失败也保留，最终以 [完整8case结果](工程资料索引.md#ref-8cb74c657ce5)为准；修正的是墓碑、免伤组件和死亡检查阶段等测试前提，不删掉失败后假称从未发生。

## 范围排除及待验收

| 项目 | 当前状态 |
| --- | --- |
| 伞叶601 | Rev4启用1011，保留组队；R19主9case/17checks及交互2case/6checks全PASS。沉默、目标依赖倍率、全部redirector／AI组合仍未全面验证。 |
| 胆小猫640哈气音效 | 用户本轮排除音频；v3植物方出牌后随机移动玩法保留。 |
| 224、432 | 原版已分别满足有空位召伴舞、回合开始获得香蕉炸弹需求，原版保留不属于遗漏。 |
| Coffee墓碑保护 | R16本次边界5项真机PASS；多次咖啡 / 回手重打等完整组合仍未全部跑完。 |
| 87动画回退 | R16同APK offFAIL/on5checks PASS；R18及R19默认开启真实现身、记录及队列自然结束均通过。 |
| 106延期阳光反馈 | R17CardView异常保留；R18／R19原生玩家LoseSun使延期-3／资源48及完整回合自然结束。多债务／0下限可见表现仍未形成完整矩阵。 |
| 547及继承静态R19复验 | R19最终独立冷进程起点／5秒局间等待，8case/37checks全PASS，其中547移动／减益／自然Discard等10项PASS。旧R15 PARTIAL及R19两秒FAIL保留。 |
| 建局／温重开生命周期 | R19自然2秒后静态仍AV，含601／202初始自定义牌组的冷建局也AV；不能仅称warm风险。严格销毁屏障及旧长期根释放未实现，自然等待不是根治。 |
| 原版与改版整局 | R19 original17checks／36步胜利及隔离PASS；mod2普通初始牌组再give601／202的23步实际胜利审计PASS。自定义初始牌组失败及终局after-marker原测试FAIL均保留，未证明终局清理。 |
| 正常PvE与AI | 核心主要为手动双方fixture；AI模拟 / 自动选牌 / 各英雄实战未全面验证。 |
| 全99张卡及复杂组合 | 未做全量矩阵；墓碑、进化、沉默、复制、变形、多个控制者叠加及长局稳定性仍有未测交互。 |
| 专属动画 / 音频 / 素材 | 复用原资源，未新增模型、骨骼、专用动画或音频；逻辑PASS不是全画面PASS。 |

18项旧舍弃中，17项已有配置、运行时代码及核心逻辑实测，640音频按用户范围排除。99张变更包含原98张及新增601；R19分项套件、原版完整胜利与隔离、改版实际胜利审计分别通过，冷建局／温重开AV与原终局断言FAIL仍保留。全量复杂组合、任意初始牌组及生命周期清理未全部验收。本页没有操作ADB；原B4、mod2来源与历史证据未改。
