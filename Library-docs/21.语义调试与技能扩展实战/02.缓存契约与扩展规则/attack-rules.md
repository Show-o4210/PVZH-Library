# mod2 攻击规则扩展

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/attack-rules.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

本模块为 `src/mod2-attack.js`，仅在资源选择为 mod2、处理当前真实对局的 EntityModel 时生效。实现以缓存 `card_data` 内原版 `GrantAbilityEffectDescriptor` 组件的保留数字配置为开关，未用卡牌 GUID 硬编码技能。原版模式不修改任何攻击列表。

## 配置契约

| AbilityType | 规则 | 现有配置目标 |
|---|---|---|
| 1001 | 自己无法攻击 | 600、422、588、148 |
| 1002 | 同路线僵尸无法攻击 | 139 |
| 1003 | 同路线植物无法攻击 | 675 |
| 1004 | 真正受到伤害前无法攻击 | 221 |
| 1005 | 攻击后伤害相邻路线上的植物，AbilityValue 为伤害 | 464，6 |
| 1006 | 攻击后弹回自己的手牌 | 658 |
| 1007 | 前方植物攻击时，对该植物造成等同本次攻击量的伤害 | 114 |
| 1008 | 攻击植物英雄后获得负力量/生命，AbilityValue 为减少量 | 253，3 |

组件使用原版序列化类型，Duration 为 Permanent。数字配置是本底座的扩展协议；不能交给原版 `GrantAbilitySystem` 当作普通能力授予，也不能用作界面图标的 `SpecialAbilityType`。

## 核对的原版调用链

原版正常路线战斗并非只走 `AttackInLaneSystem`。`CombatEffectCreator.CreateEffectsForFighters` 会直接调用 `FighterDamageEffectCreator.CreateEffectsForFighterInLane`。普通攻击、额外攻击最终共同进入私有的 `CreateEffectsForAttackingInLane(Entity, int, AttackData)`，它一次生成主伤害、穿透/多目标伤害与溅射伤害，返回原版 `PoolableList<Effect>`。

本模块在这一返回列表的头尾加入从原版 `InstanceManager` 获取的 `StateCheckEffect` 书签。`EffectRouter.ProcessEffect` 真正执行这些书签时，才分别报告攻击开始与攻击结束。书签进入路由时会调用原版 `Cancel()`，只保留队列位置，不运行原版状态检查处理器，避免在双方同步战斗中间插入死亡检查。

- 攻击列表生成函数的 `onLeave` **只代表生成完毕**，未作为攻击结束。
- 多个伤害效果共用一次攻击身份，溅射、穿透不会让攻击后技能多次触发。
- 原版 `EffectQueue` 将 `ResponseEffects` 插在当前效果之后；伤害造成的原版响应先执行，再执行下一条原攻击效果。
- 前书签可加入火炬伤害与状态检查，原攻击的每个伤害进入路由时再次检查攻击者仍是原实体、实际仍在路线中、当前路线是否禁攻。火炬的前置伤害包另外登记，在原版 DamageRecorder 确认真实正伤害之后，该次攻击的后续伤害包还会检查攻击者生命；生命已到 0 时取消，即使原版状态检查将实际死亡移除排到当前分组之后。
- 后书签位于全部攻击伤害后，技能伤害/减益/弹回动作继续进入原版响应队列，随后添加状态检查。

禁攻不通过冻结或力量归零实现，因此不会与 mod2 冬窝瓜的“消灭被冻结单位”产生替代规则交互；独立锦囊、能力 `DamageEffect` 不属于原攻击列表，不会被禁攻误取消。

正常同步战斗会预先生成双方的伤害。植物先将僵尸打到 0 生命时，若原版尚未把僵尸移出路线，它已经生成的还击仍按原时序处理。本模块不通过提前读取 0 生命取消这种还击；场上有效性以实际 Lane 成员关系为准。

火炬的攻击前伤害是例外：只有确认火炬前置伤害已经真实结算的那次攻击，才增加 0 生命取消判断；普通同步战斗的 0 生命还击不受影响。免伤/护甲使火炬伤害为 0 时不建立这个判断，伤害后原版反应把生命恢复为正时也可正常出手。`front-damage-resolved` 和 `front-packet-check` 记录这条边界的实际伤害、剩余生命、是否仍在路线及取消结果。

读报的许可状态由 `DamageRecorder.RecordDamage` 的实际正伤害量解锁。护甲完全挡住或免伤未造成实际伤害不会解锁；治疗后不会重新禁攻。原版卡牌重置、弹回后的重置及实体回收清除解锁状态；新的对局/效果队列重置也清除全部运行时书签。

火炬的前后顺序使用 `Lane.GetFightersForPlayer`，原版 `FRONT_POSITION_ORDER=0`。只有攻击者后方的火炬才会对其触发。其伤害使用原版 `AttackData.DamageAmount`，包含攻击覆盖的本次攻击量。

狗头在构建原攻击时记住攻击目标包含植物英雄。正力量攻击即使最后被格挡或护甲减到 0，仍触发后书签；原版把 0 力量视为没有攻击并返回空伤害列表，本模块不伪造这种“攻击”。必须删除第三版原有 DamageTrigger 的 -3/-3，以免重复触发。

## 绑定版本与安全挂载

绑定版本为 1.67.8 ARM64，参考 `D:\Codex\PVZH\dump\libil2cpp.so`，SHA256 开头 `18178b2f`。每个挂钩在安装前校验原机器码的 8 字节。

| 方法 | RVA |
|---|---|
| FighterDamageEffectCreator.CreateEffectsForAttackingInLane(Entity,int,AttackData) | 0x21DA558 |
| EffectRouter.ProcessEffect | 0x2249E74 |
| DamageRecorder.RecordDamage | 0x21D5890 |
| Entity.HandleReturnToPool | 0x224CF78 |
| EffectQueue.Reset | 0x224C2E0 |
| InstanceManager.Return | 0x224EC7C |
| CardResetter.Reset(Entity,int) | 0x21DE058 |
| CardResetter.ResetWithoutRecord | 0x21DE290 |

`Effect` 的源/目标/分组字段分别是 0x24/0x28/0x3C，`DamageEffect.LaneId` 为 0x48，`ShowParticleEffect` 为 0x4C。`Entity.Id` 为 0x18，`Lane.CombatOrderIndex` 为 0x18，`Lane.EnvironmentId` 为 0x1C。

所有新效果由原版实例池创建，原列表通过托管 `Insert`/`Add` 操作，不手工拼托管 List 或直接追加数组槽位。R13 阻止已生成攻击时，保留原列表及其中所有效果，由原版 `Cancel()` 逐项取消，包括附带效果；随后由原队列按正常路由、结算及返池时序处理。本模块在该分支不执行 Clear/Return、不插入攻击书签，也不触发攻击后能力；prevented 计数仍记录禁攻原因。运行时 Map 仅保存原版队列仍持有的效果身份；效果回收、卡牌重置及对局结束后清理身份，防止池化指针被复用时继承旧攻击。

R12 增加临时 IL2CPP strong GCHandle 保活。`Pool.Acquire` 的 `shouldInject` 是依赖注入开关；池只保留已返还对象的 Queue/HashSet 和使用数量，不保存已取出对象的托管引用。JavaScript 数组、Map 与 NativePointer 也不是托管 GC 根。因此新效果必须由 runtime.effect() 立即保活，直到原版 List/EffectQueue 真正接管；攻击列表的 `onLeave` 入口另保活返回的原版 List 本身，退出时释放。

书签每次成功 `Insert`/`Add` 后调用 `releaseEffect`。技能效果按原顺序逐条入队，每条成功后释放临时根，避免后续 Push 失败时把已经入队的前缀错误返池。作用域退出将尚未入队的已知效果交还同一个 InstanceManager，并在 finally 释放临时根；已经插入原列表的书签遇到后续错误时只 Cancel，由原队列负责返池。后书签出现错误仍会 retire 攻击身份。

禁攻列表在回调期间继续由返回 List 的临时根保活，回调结束后仍保持原版创建者/队列所有权。R12 的 Clear 后自行逐项 Return 路径已移除，R13 仅取消效果，避免提前返池改变原版生命周期。R14 已连续完成 14 个攻击用例，但不能把这项所有权调整单独称为历史崩溃的根因；引用字段 ABI 错误另有独立二进制证据与修正。`retainEffect`/`releaseEffect` 必须按对象指针幂等管理同一 strong handle，可保活普通托管对象，不要求对象一定是 Effect；这也用于返回 List。临时保活与永久 pin 分离，不应随重复对局无限追加永久句柄。

新建狗头减益 Buff 的 GroupId 使用数字实体 ID 字符串；原版 `StatUtils.StripNonContinuousModifiers` 会用 `Int32.Parse(GroupId)` 识别持续技能来源，池化 BuffEffect 默认的空字符串不能作为新的独立 Buff 分组，否则后续属性重置/复制的 strip 路径可能解析失败。R14 的字符串字段通过 `il2cpp_field_set_value_object` 传入真实托管对象指针并执行原版写屏障；此前把对象指针放进原生缓冲区、再传缓冲区地址的写法会把非托管地址写入 String 字段。详见 [IL2CPP 引用字段 ABI](../03.托管内存与效果所有权/il2cpp-reference-field-abi.md)。

## 接入与可观测性

导出 `install(api)`，需要主运行时的 `mod/live/call/component/list/i32/integer/boolean/resolve/effect/queueEffects/event/type/activeMode/ownsRule/retainEffect/releaseEffect`，狗头 Buff 另需 `setField/string`。`queueEffects(g,array,{placement:'current'})` 应使用原版 `AddToCurrentGroup` 的管理容器。可选 `animationWrap(g,source,rule,effects)` 为每个技能动作封闭正确的原版触发能力队列，返回 Start/native-effects/End；不得在实际结算前立即写一对空 History 起止记录。动画包装器在返回前自己创建而尚未交给调用方的效果，也须在异常分支返池并释放临时根。

事件使用 `mod2-attack-*` 前缀，记录独立 attack_id、实体 ID、GUID、路线、攻击量、初始目标、是否攻击英雄。`before`/`after` 是真实队列书签，不是函数返回日志。`prevented`、`wounded-unlocked`、`front-damage-queued`、`adjacent-damage-queued`、`bounce-queued`、`hero-debuff-queued` 记录相应行为；`error` 不能算技能验收通过。

普通伤害、增减属性和弹回会产生原版 DamageRecord/BuffRecord/CardMoveRecord，由原版记录处理器播放对应通用动画。新增能力尚不能仅凭这些记录保证播放角色的 special 动画：那还需要原版 TriggeredAbilityStart/EndRecord、匹配的 AbilityGroupId、正确的结果 EffectGroupId。不能通过任意数字能力图标蒙混匹配。

## 验收目标与覆盖边界

下列是完整验收目标，已有实机覆盖见下一节。R14 的 14 个用例不代表已穷尽普通战斗、免伤、格挡、溅射、穿透、疯狂和带渲染动画的所有组合。

1. 四种自己禁攻单位分别在加攻后正常战斗与额外攻击均不出手；其技能伤害仍生效。
2. 大喷菇/迪斯科舞池分别限制同线指定阵营，其他路线仍攻击；移动、消灭来源或移除环境后恢复。环境是按实际 Lane.EnvironmentId 查询。
3. 读报初始不攻击；实际伤害后可攻击；0 伤害不解锁；治疗不重新禁攻；弹回再打重新禁攻。
4. 火炬后排对前排植物在正常/额外攻击前造成对应攻击量伤害；前排植物死亡则其攻击取消；火炬在前排不倒向后排触发。
5. 暗物质火龙果每次正常/额外攻击后，相邻线双方植物受到一次 6 点伤害；teamup 双植物都命中；同一次溅射/穿透不重复触发。
6. 原始豌豆攻击后回手；回手动作有原版 History；其战斗前额外攻击应让它在正常攻击之前离场。
7. 狗头正常攻击英雄后仅一次 -3/-3；被超级格挡/护甲挡住也触发；仅技能伤害英雄不触发；攻击植物不触发。
8. 疯狂产生的连锁额外攻击与一次攻击多个目标不出现重复书签或遗留身份；死亡与战斗胜负正常。
9. 切回原版资源后相同单位恢复原规则，并完成一局游戏；多次开始新测试局 pending_markers/pending_attacks 应清零。
10. 逻辑验收与带视图正常对局的 History/动画验收分别记录；headless fixture 通过不能代替画面验收。

AI 的独立预测 EntityModel 不执行本模块，只在真实结算时执行规则，AI 对新技能的预测策略目前未扩展。真机操作及下列证据由主代理完成，本代理只读核对二进制、实现所属模块及测试、整理证据。

## R14–R16 验证进展

| 候选 | 实测范围 | 结论与证据 |
|---|---|---|
| R14 | 14 个核心攻击用例、连续独立建局 | 全部 PASS；截至 generation 14，扩展错误为 0，临时 effect GC 根归零。[汇总](../06.R19实现与验收记录/工程资料索引.md#ref-d6548fddf8d4)、[完整命令](../06.R19实现与验收记录/工程资料索引.md#ref-3172b0ddeb04) |
| R14 | 一次性动作 7 条断言 | 全部 PASS：合法 87 现身、106 双次施放与下回合扣费/恢复/零下限、202 合法与带伤害修饰的当前生命交换。[动作结果](../06.R19实现与验收记录/工程资料索引.md#ref-99f2c9deb5d7) |
| R15 | 合法 252 入场、两次合法 87 现身 | 三项严格检查 PASS：入场 MixedUp 一次；揭示其他僵尸不触发；同一 PlantMain 再揭示自己，原生 MixedUp 恰一次，三张僵尸全部重藏。[结果](../06.R19实现与验收记录/工程资料索引.md#ref-e7cb45147bbe)、[命令与窄观察记录](../06.R19实现与验收记录/工程资料索引.md#ref-2aff858000a5) |
| R16 | 自定义动作响应继承原动作的 EffectGroupId | 源码已修正并冻结构建；手工 fixture 和合法 87 的实机回归尚待完成，不能记为 PASS |

R14 攻击用例实际覆盖：原版 1/1 同步互杀；四张自己禁攻单位的正力量额外攻击与独立技能伤害；139/675 的同线禁止与异线对照；221 未受伤时加生命仍禁攻、实际伤害解锁；464 相邻两线各受一次 6 点伤害；658 攻击后回手；114 前置伤害致死取消攻击与存活继续；253 攻击英雄只减一次 -3/-3，普通技能伤害英雄不减益。未把这些断言扩写成尚未测试的格挡、免伤、全套连击或角色专属动画通过。

R14 的 ABI 修正、R12 临时保活和 R13 原攻击效果交由队列返池是三项独立改进。引用字段曾被写成原生缓冲区地址的事实已由匹配 ELF 确认；R14 连续回归通过支持修正后的实际稳定性，不为每一份历史 R6–R13 崩溃记录赋予未经独立验证的同一原因。

### 252 手工 fixture 延迟与响应分组

[R15 窄观察](../06.R19实现与验收记录/工程资料索引.md#ref-09359dc4dd1e) 显示，手工 Grant1013 揭示自己时，真实 RevealTrigger 实体 28 的两个 condition 与 ShouldTrigger 均为 true，但当时 MixedUp 调用数未增加。下一次正常 end_phase 后，原生 MixedUp28 执行恰一次并重藏三张僵尸。Source 使用自身或英雄的 A/B 同样延迟，不能归为 252 条件或来源写错。

原版 `InterruptQueue`（0x224B724）给注入 Grant 分配新的 `NextGroupId`，却不会立即修改 `CurrentGroupId`；后者在 `DoShift`（0x224B9A4）移走当前效果后按下一实际效果更新。此前 custom action 的 `queueEffects` 只取旧 `CurrentGroupId`，把 Reveal 归进尚未结束的 MainPhaseBlocking 组。`ShiftWillChangeGroup`（0x224BAB8）看到 Reveal 与后续 blocking 同组，暂缓处理已通过条件的 TriggerData；正常阶段结束才出现可处理的组边界。这是测试接口的错误归组，正式合法 87 路径已通过，不能据此修改 252 的技能条件。

R16 在 custom action 末尾传入 `groupId=p.EffectGroupId`；`queueEffects` 有明确 groupId 时使用它，否则仍用 CurrentGroupId。原版 `PushEffectToList`（0x224BB7C）接受调用方传入的组号，并在 0x224BC24 写入 Effect+0x3C；原版响应合并保持顺序、不重写组号。因此让响应继承真正的原动作组符合该队列约定。正常合法 87 的原动作与 CurrentGroupId 一致，现有 Start/End bookend 仍夹住响应，没有新增或伪造能力起止记录，也不改变卡表 AbilityGroupId 或 Once 条件。R16 仍须实机核对手工现身立即完成、合法出牌无重复与残留。

### 87 逻辑通过与动画待测

R14 动作与 R15 合法 252 测试使用 headless fixture，证明技能逻辑及原生触发次数。另一次[带渲染对照](../06.R19实现与验收记录/工程资料索引.md#ref-fa3960f3d6b5) 中，合法 87 已真正移除 FaceDown、保留目标生命与路线，History 的 Start→Reveal→End→Discard→PhaseResume 完整，但 EffectAnimationQueue 持续非空，测试超时。它是已知动画卡住，不能因技能 PASS 改记成画面 PASS。

独立 [87 动画兼容回退](../04.History与原版动画/reveal-animation-compatibility.md) 默认关闭，仅对严格匹配的 87 原版记录组尝试交给普通 RevealRecordProcessor；没有清空动画队列或伪造完成标志。主代理将做关闭/开启的窄对照。R16 构建中的回退和响应分组修正均尚待实机，动画结论单独记录。
