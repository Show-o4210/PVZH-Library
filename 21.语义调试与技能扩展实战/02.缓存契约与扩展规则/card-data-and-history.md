# card_data 双资源配置与原版特殊动画链

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/card-data-and-history.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

本页记录本次卡表构建的静态证据、扩展契约和动画边界。静态构建已通过；技能是否实际生效以及真机画面，应以本工程 `evidence/` 中对应候选 APK 的运行报告为准。原 mod2 第三版仅有启动验收，不能把其 93 张改卡直接视为战斗验收通过。

## 输入与资源身份

构建脚本为 [build_card_profiles.py](../06.R19实现与验收记录/工程资料索引.md#ref-0ad5f50067bb)，输出位于 [mod2_profiles](../06.R19实现与验收记录/工程资料索引.md#ref-7e27af4d34ef)。脚本只读取 B4 APK、mod2 第三版输出及报告，不重建或修改这些来源工程。

原版配置从 B4 APK 的 `assets/AssetBundles/` 精确提取。B4 指纹：`9af06d613c55644e1bbc9558f0108f0c61e0b37830da29525d5935c54fef97bc`。同时核对其内置索引 `ManifestVersion=11056`、`EntryCount=2880` 及每项的大小和 SHA-256。

| 配置文件 | APK 原版资源入口 | 缓存相对路径 | 原版 SHA-256 |
|---|---|---|---|
| card_data_1 | assets/AssetBundles/cards/card_data | cards/card_data_1 | e0682de0135a77bcd15c73072dc3221c0e25b1ac694ebc86bd7965e1d56d57b7 |
| data_assets_29 | assets/AssetBundles/data_assets | data_assets_29 | 37fd5f5af67dda86664b76e9bfefe1878b281cf8a1af05afec7a4282bf7b3007 |
| cn_8 | assets/AssetBundles/loc/cn | loc/cn_8 | d40408353ec001f84fc56b56dff6417e883048090d78a3cee712c11cefdd9aab |

不能用 `loc/cn_assets` 替代中文 TextAsset 包；它是另一份资产。

mod2 来源为 `../mod2/out/`：卡包指纹 `faeacce729bff6f8f9e67c269a19901789e4c27f10f1dc9042db396c6598dee0`，中文指纹 `51cc38e32ff33e55c6f6e0b3f4a98842a5d834fae9373a480fd38c62cefeabf0`，关卡包与上述原版相同。源报告须为 revision 3、静态 PASS。

B4 原版有 650 个定义；mod2 原输入有 651 个定义。两者共同的 650 个定义完全相同，mod2 原输入额外带 GUID 1001。mod2 第三版又增加了 5 个内部定义，合计 656 个；本次 mod2 配置完整保留这些定义，原版配置仍使用 B4 的 650 个清洁定义。

## 扩展契约 v1

采用当前游戏确有的 `PvZCards.Engine.Components.GrantAbilityEffectDescriptor`，不新增 IL2CPP `$type`。保留完整的 EngineLib 类型串。原版可授予枚举为 0–18；本工程保留 1001–1014，避开资料库中 19–23 的历史社区实验值。

```json
{
  "$type": "PvZCards.Engine.Components.GrantAbilityEffectDescriptor, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
  "$data": {
    "GrantableAbilityType": "1005",
    "Duration": "Permanent",
    "AbilityValue": 6
  }
}
```

`AbilityValue` 是技能参数，版本号位于配置 manifest/contract 中。持续规则的描述器直接加入卡牌 `entity.components`，作为可序列化和可深复制的配置标记，Gadget 在相关结算入口读取它。它不通过原版 GrantAbilitySystem 执行。一次性动作放进真实 PlayTrigger 的 effect entity，Gadget 必须在原版 GrantAbilitySystem 识别未知枚举之前截获其效果。运行时规则只在选择 mod2 配置时启用。

| 标签 | 卡牌 GUID | 语义／参数 |
|---|---|---|
| 1001 | 600、422、588、148 | 自身无法攻击 |
| 1002 | 139 | 所在路线的僵尸无法攻击 |
| 1003 | 675 | 所在路线的植物无法攻击 |
| 1004 | 221 | 真正受伤前无法攻击，受伤后解除 |
| 1005 | 464 | 每次攻击结算结束后，对相邻路线植物造成 AbilityValue=6 伤害 |
| 1006 | 658 | 每次攻击结算结束后，弹射自身 |
| 1007 | 114 | 前方植物攻击时，对其造成本次攻击力量的伤害 |
| 1008 | 253 | 每次攻击植物英雄结束后，获得 -AbilityValue/-AbilityValue，值为 3 |
| 1009 | 326 | 无法获得力量 |
| 1010 | 518 | 僵尸造成的正伤害规范为 AbilityValue=1，随后走原版护甲和免伤 |
| 1011 | 601 | 每笔打自身的伤害，从自身及左右相邻路线植物中随机一株承受；自身直接结算，最多转一次 |
| 1012 | 106 | 每次施放登记独立的下回合阳光债务，AbilityValue=3 |
| 1013 | 87 | 原版墓碑目标选择后，立即现身 |
| 1014 | 202 | 与僵尸英雄交换当前生命 |

保持 v3 已有技能及身材；只有此前整项保留原版的 588、148、675、518 被替换为完整新设计，清除其原版抽牌、加费、跳板与倍伤能力。87 继续使用原版墓碑目标选择，Destroy 描述器替换为 1013；202 继续使用原版僵尸英雄目标，设为 1 生命的备选替换为 1014。253 清除旧 DamageTrigger，避免实际造成英雄伤害时重复减属性。106 保留原版路线选择与伤害效果，再添加目标为植物玩家的第二个 PlayTrigger。

用户随后确认601的单次随机承伤规则，Rev4启用此前保留的1011；contract/schema仍为1，编号意义没有改变。原 [第二批需求](../06.R19实现与验收记录/工程资料索引.md#ref-766ae70120c3) 只提出技能变化，因此保持伞叶1费0/2及原版Teamup、CreateInFront、isTeamup=true。只清除原Continuous免锦囊光环，加入卡体direct1011及Unique13。候选集合包含伞叶自身与左右直接相邻路线的植物，不加入同线其他植物；每笔打自身的伤害独立随机一株，选自身直接结算，转给其他株后也不再次转移。R19安装Rev4后的具体真机范围见下文，配置通过与实测通过分别记录。

profile_revision=2 补清675的 GrantedTriggeredAbilities(564) 与 Springboard：它实际是2费0/3单位，原始新设计只要求本线植物禁攻，不保留越线伤害或可被踩。与R12包的卡表比较，恰好只删除675这两组件；新card_data SHA为 `0c754c359a93e1d4498f725dde9e773e18e4d65d0a726f166ae694435ab02796`（135381字节），原版profile及其他文件不变。schema／扩展contract仍为1。

新增规则使用原版 `ShowTriggeredIcon abilities:[13]` 和 `special_abilities:["Unique"]` 显示特殊技能标识；326 同时保留原有 Repeater 等关键词。不写入 100x 的 SpecialAbilityType。

当前Rev4相对v3改变19个卡定义：17张扩展配置及97、547两项静态修补；34条扩展中文长／短说明。相对B4清洁卡表共有99张原卡改变，80张已变更原卡完整沿用v3，5个隐藏定义逐项保留。音频保持来源原状。完整契约、增量和验证结果分别在 `extension-contract.json`、`extension-cards.json`、`localization-changes.json`、`validation.json`。

Rev4 mod2 card_data SHA-256为 `964b20aa9b4933e348d5fab93fc7f242236e2a2d6a294bcf53df9a87d13274c5`（135330字节），cn为 `9ec87683b88424f6407b7c7adcc69e4747ab4cfca7f01e3f360d5d29029f3733`（245145字节）。严格比较此前Rev3实际资源，恰好只有601定义及 `Umbrella Leaf_shortDesc`、`Umbrella Leaf_longDesc` 两条记录改变；其余655定义、所有原版资源与mod2 data_assets字节不变。资源白名单仍只有card_data_1、data_assets_29、cn_8。

## 静态验证范围

构建使用现有 UnityPy 1.25.0。卡包和中文包重新加载后核对 payload，再比较所有序列化对象的原始字节：仅 `cards` TextAsset（path_id `-79917718294181953`）与 `LocalizedStrings` TextAsset（path_id `-2978648870419362077`）允许改变。关卡包字节保持原版。

验证还检查：输出 GUID 集合不变；非扩展及静态修补目标卡定义与v3一致；5个内部定义完整一致；新卡表全部 `$type` 均来自原包；每个reserved tag的GUID、数值和位置精确匹配；253不再有旧DamageTrigger；675不再有旧授予能力／Springboard；601旧光环清除而组队／站位组件与来源完全相同；非目标中文CSV记录逐项保留。Rev4另核对上一版manifest全部资源SHA／大小，再比较完整卡定义及所有中文CSV行，验证只有已授权601增量。

这些检查证明配置与打包一致，尚不证明 Unity 原生反序列化、效果结算、交互或画面。原生反序列化须在候选包启动后检查实际实体中的标签；实际技能须走合法出牌与原版队列验收。

## 原版特殊技能的动画入口

本次只读核对资料库 [赋甲实现](../../12.静态高级实战2/02.GrantAbility赋甲ProcessEffect特判与组件安全挂载.md)、[History 与 Sprite 映射](../../12.静态高级实战2/03.装甲UI双轨History发报与Sprite映射.md)，以及当前 `D:/Codex/PVZH/dump/dump.cs`。进一步在 B4 APK 中的 ARM64 libil2cpp 原始字节上反汇编关键入口，库指纹为 `18178b2f35959bc3954378a9778cddd67aab8a7ef22579ea59d736521eec8c91`。以下 RVA 是本次库的地址，不沿用历史资料库快照地址。

三条展示通道需要区别：

1. 卡面关键词：`special_abilities` 与 ShowTriggeredIcon 决定能力标识，Unique 的原版枚举值为 13。
2. 动态授予能力：AbilityGrantedRecord → AbilityGrantedRecordProcessor → Grantable 到 SpecialAbility/Sprite 映射。reserved 100x 不属于这个映射，不能直接发给它。
3. 技能发动：TriggeredAbilityStartRecord → 找同来源、同结算组的结果记录 → TriggeredAbilityAnimationFactory → 原卡 CardView 的特殊动画状态及结果动作。

关键消费者为：

| 入口 | 当前 RVA | 已核对行为 |
|---|---|---|
| TriggeredAbilityStartRecordProcessor.ProcessRecord | 0x1FC9B0C | 读取 SourceId=0、EffectGroupId=26，查找后续同组记录 |
| AbilityRecordGroupFinder.FindAbilityRecords | 0x1ED301C | 按结算组与来源搜集原版结果记录 |
| TriggeredAbilityStartRecordProcessor.AddAbilityAnimation | 0x1FCA228 | 读取 AbilityGroupId=3、IsOnSelfPlay=51 |
| TriggeredAbilityAnimationFactory.CreateAbilityAnimation | 0x1FC8074 | 原版构建技能动画 |
| TriggeredAbilityEffectAnimation.ApplyCorrectAbilityAnimationState | 0x1FC926C | 只对 AbilityGroupId 0、1 设置两组原版动画状态 |
| AbilityGrantedRecordProcessor.ProcessRecord | 0x1ED2B4C | 动态授予能力的另一条展示入口 |

这里 `AbilityGroupId` 是原卡动画组，只能选实际存在的 0 或 1。`EffectGroupId` 则用于组织结算的 History，不能把两者混为一谈，也不能把标签 100x 当成动画组。EffectQueue.GetNextGroupId 只是只读 getter；原版 AddGroup 才管理新结算组。helper 接受本次原版队列的 current group，不自行写计数器。

复用原版 DamageEffect、BuffEffect、ReturnToHandFromPlayEffect、GainSunEffect、SetStatEffect、RevealEffect 的系统，会生成对应的 DamageRecord、BuffRecord、ReturnToHandFromPlayRecord、GainSunRecord、SetStatRecord、RevealRecord。这些结果记录有原版消费者，因此正常游戏中具备通用伤害、属性、弹射、资源、生命和现身表现的路径。仅直接修改数值／移除 FaceDown 则缺少这条路径。

例如 RevealSystem.ProcessEffect 为 `0x21D0580`，RevealRecordProcessor 为 `0x1FB7380`；SetStatSystem.ProcessEffect 为 `0x21B8288`，SetStatRecordProcessor 为 `0x1FBBAC4`；GainSunSystem.ProcessEffect 为 `0x21C44AC`，GainSunRecordProcessor 为 `0x1F41AB8`；ReturnToHandFromPlaySystem.ProcessEffect 为 `0x21C761C`，对应 RecordProcessor 为 `0x1FB6314`。

但原版 special 发动动画需要包住结果效果的 Start/End bookend。marker 本身、Unique 图标或“日志显示发动”均不会自动生成它。新增禁攻之类持续状态也没有对应的全新原版常驻图标，本次不发明额外图标。

## 额外动画封装的已知失败与默认禁用

[mod2-animation.js](../06.R19实现与验收记录/工程资料索引.md#ref-8594f8358918) 保留 `create(api).wrapEffects(g, source, ruleId, effects, options)` 的实验实现。当前运行时默认不调用该包装，`animationWrap` 直接返回原生结果数组。它不创建全局可监听的 trigger shell，也不添加 Java/悬浮 UI。

早期实现尝试复用同 source、group 0/1、本回合已经完成的真实能力实体，用原版实例池组成 `[TriggeredAbilityStartEffect, ...结果效果, TriggeredAbilityEndEffect]`。R5 真机的 202 受伤双方 fixture 证明：这并非纯展示操作。wrapper 重写所有结果效果的 EffectEntityId 和 Context.TargetId，使结果重新接受借用能力的条件与目标验证；已完成标记不足以保证结果仍合法。

202 的 PlayTrigger 实体带 `TriggerTargetFilter(SelfQuery)` 与 `PrimaryTargetFilter(Player && Zombies)`。源卡 SetStat 的 Context.TargetId 被写成源卡，能满足 SelfQuery，却不符合原版主目标过滤器；英雄 SetStat 的 Context.TargetId 是英雄，又不满足 SelfQuery。两条结果都会被取消，而 Start/End 在验证黑名单中，可能仍产生一条没有结果的发动记录链。202 没有 OncePerTurnCondition，因此此次不能简单归因于本回合重复触发。

反汇编确认的验证入口为：

| 入口 | RVA | 与本次失败相关的行为 |
|---|---|---|
| EffectValidationSystem.ProcessEffect | 0x21B39E0 | ShouldCancel 为真时调用 Effect.Cancel，不抛出技能异常 |
| EffectEntityValidator.HasValidEffectEntity | 0x21B3AD4 | EffectEntityId 非 -1 且不在黑名单时，创建上下文并验证借用实体 |
| EffectEntityValidator.IsValid | 0x21B3D04 | 先 TriggerValidator.ShouldTriggerEffect，再验证目标 |
| TriggerValidator.ShouldTriggerEffect | 0x21E5A54 | 检查实体全部 Condition；TriggerTargetFilter 也实现 Condition |
| ConditionEvaluatorBinder.AddContextEntityEvaluators | 0x21F782C | TriggerTargetFilter 使用 TargetEntityProvider，SelfEntityFilter 使用 SelfEntityProvider |
| EffectTargetValidator.HasValidTarget | 0x21B3DA0 | RequiresTargetValidation 为真时应用 PrimaryTargetFilter |
| Effect 构造／回池 | 0x224B198／0x224B06C | RequiresTargetValidation 字段 0x44 默认重置为 true |

所以默认对所有被动、手动 fixture 和延期技能只追加原生结果，不制造额外 Start/End，也不借用已完成的触发实体。合法 PlayTrigger 原有的外层 Start/End 保持，由本次原版结算组围绕响应结果自然记录。不能通过关闭全部目标验证来掩盖错误包装；复杂的特殊发动表现留待有真实原生触发上下文的独立方案。

两个原版 bookend 的布局与入口：

- Effect：Context 指针 `0x18`，PlayerId `0x20`，SourceId `0x24`，TargetId `0x28`，SpringboardId `0x2C`，EffectEntityId `0x30`，EffectGroupId `0x3C`。
- TriggeredAbilityStartEffect：AbilityGroupId `0x48`；构造函数 `0x225FA44`，StartSystem.ProcessEffect `0x21C8398`。
- TriggeredAbilityEndEffect：无新增字段；构造函数 `0x225EF50`，EndSystem.ProcessEffect `0x21BDC68`。
- EffectContext：TargetId `0x10`，SourceId `0x14`，EffectEntityId `0x18`，SpringboardId `0x1C`。

原版 StartSystem 按 SourceId、EffectEntityId、AbilityGroupId、EffectGroupId 写 History，并调用 SetTriggerType。该方法必需一个真实的 trigger effect entity；不能把普通卡实体 ID 填入 EffectEntityId 假装通过。EndSystem 会记录结束并更新该 effect entity 的触发状态。已有真实实体只能满足这些入口的存在要求，不能证明其条件和目标适用于另一批结果。

新增持续能力保留原版结果记录链，不自动创造独立special动作。headless调试局缺少CardView，不适合作为画面通过证据；History生成、原版视图消费、实际画面应分别记录。合法87、202、106的正常可见例已有下面R18证据，复杂新special、全量动画组与专用表现仍未全部验证。

## 已确认的设备记录与可见模式

[R16继承静态完整套件](../06.R19实现与验收记录/工程资料索引.md#ref-cafe9d491e00)为8case/37checks全PASS：freeze2、reflection3、coffee5、grave3、redirect97共5、banana472共6、copter286共3、diver547共10。来源为真实mod2 fixture，未使用模拟点击或截图；这些逻辑／History断言不是99张卡全量或完整美术验收。

252与87的合法交互证据实际位于 [r15-grave-legal87](../06.R19实现与验收记录/工程资料索引.md#ref-e7cb45147bbe)，3checks全PASS。另 [R16同response组快照](../06.R19实现与验收记录/工程资料索引.md#ref-638768656c7f)确认直接fixture现身的时机修正：揭别人MixedUp calls/completed保持3，揭自身后同响应立即变4并重藏全部，下一原生阶段仍4，不重复。该文件是具体快照证据，没有额外虚构PASS字段。

[R16关闭87回退冷对照](../06.R19实现与验收记录/工程资料索引.md#ref-9f607301bb64)确认原special timeline卡住；[同APK开启冷对照](../06.R19实现与验收记录/工程资料索引.md#ref-b13ca6941d6b)5checks全PASS。兼容器只让真正RevealRecord由独立消费者处理，保留原Start／Reveal／End，没有开启已弃用的额外bookends。细节见 [87动画兼容](../04.History与原版动画/reveal-animation-compatibility.md)。

[R18最终真实渲染动作报告](../06.R19实现与验收记录/工程资料索引.md#ref-9523bd8649ae)8checks全PASS、unverified=[]，覆盖普通双方单位出牌、202、87、106当场动作、下回合阳光及完整回合。实际采到busy→empty，最终原动画队列两表为0，extra_bookends_enabled=false、wrapped=0、动作errors=0、pending_sun=0、临时effect roots=0。

同一真实History快照包含：202 source26／effect27／group60的Start→两个SetStat→End；87 source29／effect30／group79的Start→Reveal目标25→End；106 source31的伤害group0 Start→Damage5→End与登记债务group1 Start→End。下回合资源是随后独立GainSun：植物SunCountIncrementedRecord到51，106已Discard但Source仍31，GainSun attempted=-3／actual=-3／available48。真实模型资源48，sun handler applied=1／errors=0／active_gc_roots=0，见 [阳光反馈兼容](../04.History与原版动画/sun-animation-compatibility.md)。原效果和来源未更改，不把下回合结果虚构为仍包在上回合End里面。

R17延期反馈的CardView异常报告保留；R18走正式PlayerView.LoseSun反应，避开已删除来源CardView的粒子。测试render=true、opponent_ai=false，未截图，complete_visible_art_verified=false；已证明这些可见例的正常队列结束，不宣称逐帧美术、全99张或AI复杂组合均通过。R18使用当时Rev3卡表，新增601由R19安装Rev4后独立验收。

[R19承伤套件](../06.R19实现与验收记录/工程资料索引.md#ref-f4dc6c721c73)9case/17checks全PASS，命令日志有225笔真实DamageEffect请求，最终220次选择／原生RNG调用，5笔0伤害不重新随机。覆盖自身、左右邻线按单株候选、两伞叶只转一次、同线／敌人排除、护甲／免伤、518及来源倍率；[R19交互套件](../06.R19实现与验收记录/工程资料索引.md#ref-ab90c34fdc90)2case/6checks全PASS、96笔伤害，覆盖原97副本转伤及边路不环绕。模型来源及英雄保留，最终errors=0、pending_packets=0、pending_contexts=0。目标依赖EffectEntityMultiplier、沉默控制者、全部原版redirector与AI组合未全面验证，不把样本观察写成均匀分布证明。

同一R19的 [攻击14case/21checks](../06.R19实现与验收记录/工程资料索引.md#ref-087d9bf2cf78)、[属性8case/39checks](../06.R19实现与验收记录/工程资料索引.md#ref-c7316d38eff0)、[渲染动作8checks](../06.R19实现与验收记录/工程资料索引.md#ref-ef2c38fd047f)全部PASS；渲染unverified=[]、busy→empty、最终两队列0，87和sun兼容器分别applied1/errors0/roots0。独立冷恢复后 [动作逻辑7checks](../06.R19实现与验收记录/工程资料索引.md#ref-968e3f334f71)也通过。原 [无等待新局中断](../06.R19实现与验收记录/工程资料索引.md#ref-58cc13c6ce6d)保留；继承 [R19旧静态](../06.R19实现与验收记录/工程资料索引.md#ref-0602f9dd6fe6)自然2秒后因banana第三branch新局0x0 AV停止、整体FAIL。随后独立新冷进程起点、局间自然等待5秒的 [R19最终静态](../06.R19实现与验收记录/工程资料索引.md#ref-c20afe3dbf73)8case/37checks全部PASS、全部unverified=[]，包含咖啡墓碑保护、252现身重藏、97转伤、香蕉、直升机、547等。严格销毁屏障和旧长期根释放未实现，不能把此次等待后通过当生命周期根治。详见 [生命周期复核](../05.实测与建局边界/fixture-lifecycle-review.md)。

## History 观察的当前边界

[mod2-history.js](../06.R19实现与验收记录/工程资料索引.md#ref-fe1f0a1936e9) 已改为显式 `records()` 命令读取当前真实 History.Records 的快照；默认零 native hooks，install／status／reset／dispose 不查 live、Resources 或 DI。R8 的早期全局回调方案在首个建局产生空地址访问错误，具体指令尚未获得 backtrace；该方案不再默认使用。

快照只包含查询时 History 仍持有的记录。已被原版消费者清空的记录可能缺失，因此始终标记 `complete_history:false`，不把跨快照拼接当作完整结算链。记录缺失不代表效果没执行；须结合状态与技能事件。若同一快照中保留 Start／结果／End，可说明原版实际记录的可见顺序，仍不等价于画面验收。详细接口与降级证据见 [History 观察](../04.History与原版动画/history-observation.md)。
