# 换当前生命与下一回合阳光债务：原版结算核对

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/actions-native-semantics.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

本页依据 B4 APK 内 ARM64 `libil2cpp.so` 的实际指令和对应 `D:/Codex/PVZH/dump/dump.cs`。二进制 SHA-256 为 `18178b2f35959bc3954378a9778cddd67aab8a7ef22579ea59d736521eec8c91`。这里只核对原版语义，不修改资源配置，也不操作 ADB；功能验收另见本工程候选包的实测证据。

## 202：SetStat Health Set 如何影响受伤后的生命

SetStatEffect 的 Health=2、Set=1。原版 `SetStatSystem.ProcessEffect`（RVA `0x21B8288`）先取得相应 ModifiableInt，再可选清除非连续 modifier，调用 StatUtils.ModifyStat，最后生成 SetStatRecord。

字段布局：

| 对象 | 字段 | 偏移 |
|---|---|---|
| SetStatEffect | StatType | 0x48 |
| SetStatEffect | Value | 0x4C |
| SetStatEffect | ModifyOperation | 0x50 |
| SetStatEffect | StripNoncontinuousModifiers | 0x54 |
| Health | MaxHealth（ModifiableInt 指针） | 0x10 |
| Health | CurrentDamage | 0x18 |
| ModifiableInt | BaseValue | 0x10 |
| ModifiableInt | Modifiers | 0x18 |

`StatUtils.ModifyStat`（`0x21D3B74`）在 Health 分支取得 Health.MaxHealth，交给 ModifyStatBaseValue（`0x21D3C9C`）设置基础值，然后调用 SpecialHealthHandling（`0x21D3CD8`）。后者对 Set 明确清零旧伤害：

```text
0x21D3CDC  cmp w0, #1       ; operation == Set
0x21D3CE0  b.eq 0x21D3D00
0x21D3D04  str wzr, [x2, #0x18]  ; Health.CurrentDamage = 0
```

因此它并非“只改最大生命，旧伤害保留”。**无 modifier 时，Set Health Value=目标当前生命，就会使当前生命变为该数值。不要再把旧 CurrentDamage 加进去。**

保留 modifier 时，当前生命为 `BaseValue + 活跃modifier总额 - CurrentDamage`。Set 会使最后一项归零，故所需基础值为 `desiredCurrentHealth - activeModifierSum`。

原版查询接口：

- `Health.CalculateHealth()`：`0x226EC5C`，读取实际当前生命，含当前伤害及 modifier。
- `Health.GetInternalInt()`：`0x226EC80`，返回 MaxHealth。
- `PvZCards.Engine.ModifiableIntCalculator.CalculateBuffAmount(ModifiableInt)`：静态方法，`0x2250018`。
- `ModifiableIntCalculator.CalculateValue(ModifiableInt)`：静态方法，`0x224FFF8`，基础值加活跃 modifier。

CalculateBuffAmount 逐项遍历 modifier，仅累加 `ActivationTime==Immediate(0)` 的 AdditiveAmount；未激活的 NextTurn modifier 不参与。

建议效果序列：

1. 在处理 1014 动作时，同时快照脑残粉与僵尸英雄的当前 HP，并各自计算活跃生命 modifier 总额。
2. 生成原版 SetStatEffect，脑残粉目标：StatType=2、ModifyOperation=1、Value=`heroCurrentHp - minionModifierSum`、StripNoncontinuousModifiers=false。
3. 生成原版 SetStatEffect，僵尸英雄目标：同样参数，Value=`minionCurrentHp - heroModifierSum`。
4. 将这两个效果作为同一连续响应序列排入队列，再放 StateCheckEffect；不要在两次快照之间先执行第一个效果。

两者都复用原版系统，生成 SetStatRecord，不引入伤害或治疗事件。原版 record 包含 source、target、effect entity、CardStat、新基础值、实际当前值及 buff 展示量。

这会重新设定基础生命并清零已受伤害，保留所有原 modifier 的来源及期限。交换的瞬时结果是两者的当前 HP，而非原最大生命。原版 Health 数据只有 MaxHealth 和 CurrentDamage 两部分；受伤后用 Set 来指定当前生命会同时改变新的最大生命。后续原增益／光环消失后的变化仍由原版 modifier 规则决定。带生命光环、负 modifier 的情况需要专门实测，不能仅凭无 buff 的换血案例宣称全部覆盖。

建议验收至少包括：双方都受伤且 HP 不同；脑残粉带已有生命增益；英雄带增益；连续多次换血；两次 SetStatRecord 的实际 CurrentValue 与最终 Entity.CalculateHealth 一致；换血不触发 DamageTrigger／HealTrigger。

## 106：原版 NextTurn + EndOfTurn 为何不可用

GainSunEffect 的字段为 Duration `0x48`、Amount `0x4C`、GroupId 字符串 `0x50`、ActivationTime `0x58`。枚举：Duration Permanent=0、EndOfTurn=1；Activation Immediate=0、NextTurn=1。

`GainSunSystem.ProcessEffect`（`0x21C44AC`）**通过 TargetId 选择 SunCounter，不通过 PlayerId**：

```text
0x21C44BC  ldr w1, [effect, #0x28]  ; Effect.TargetId
0x21C44C4  bl 0x21C4514            ; GetSunCounter(entityId)
```

GetSunCounter 从 EntityModel 取该目标实体，再取得 SunCounter。因此目标为植物玩家／英雄实体即可；PlayerId 用于效果所属元数据，不能代替目标。目标找不到或没有 SunCounter 时，原版不会修改资源。

`GainSunSystem.AddSun`（`0x21C4588`）经原版 InstanceManager 创建 IntModifier，写入：

| IntModifier 字段 | 偏移 | 来源 |
|---|---|---|
| GroupId | 0x10 | Effect.GroupId |
| OriginalAmount | 0x18 | Effect.Amount |
| AdditiveAmount | 0x1C | 考虑当前 available 下限 0 后的实际数量 |
| Duration | 0x20 | Effect.Duration |
| ActivationTime | 0x24 | Effect.ActivationTime |

负数会按当前可用资源截断：实际加成相当于 `max(0, currentAvailable + requestedAmount) - currentAvailable`。例如刷新后只有 2 阳光，Amount=-3 的实际 modifier 为 -2。它不是允许负资源的直接写内存路径。

只有 Immediate 会进入 `RecordSunAdded`（`0x21C4690`），产生 GainSunRecord；NextTurn 只是登记 inactive modifier，不立即产生资源动画记录。

回合资源刷新由 `SunCountSystem.ProcessEffect(TurnEndEffect)`（`0x21D0DF8`）执行，遍历所有 SunCounter。每个玩家的 `ResetAndIncrement`（`0x21D0FF8`）严格按如下顺序：

1. `0x21D105C` 调用 `ModifiableInt.ActivateAllModifiers()`（`0x22740BC`），把所有 modifier 的 ActivationTime 写为 0。
2. `0x21D1074` 调用 SunCountBuffRemover.RemoveBuffs，使用 ExpiredIntModifierMatcher。
3. 调用 IncrementSunCount（`0x21D10AC`），添加本回合资源增长的 Permanent / Immediate modifier，GroupId 为原版 "turn"；把 SunCounter.AmountUsed 清为 0，并产生 SunCountIncrementedRecord。

ExpiredIntModifierMatcher.Matches（`0x224F63C`）仅检查 `Duration==EndOfTurn(1)`，不检查此前是否 inactive。于是 `NextTurn + EndOfTurn` 会在一次刷新中**先激活、紧接删除**，玩家根本无法使用。`NextTurn + Permanent` 会保留以后每回合的负 modifier，也不符合只扣一次；并且 negative amount 在最初登记时按当时 available 截断，可能在低资源施放时提前缩小债务。

## 106：正确的延迟执行边界

原版 EffectSystemBinder.AddSystems 中确认的创建／注册次序为：

| 注册位置 RVA | 系统 |
|---|---|
| 0x21F8E78 | EndOfTurnBuffRemovalSystem |
| 0x21F9038 | TurnCountSystem |
| 0x21F9068 | TurnSystem |
| 0x21F9098 | MessageSystem |
| 0x21F91E8 | SunCountSystem |
| 0x21F9248 | DrawCardsEachTurnSystem |

TurnCountSystem.ProcessEffect（`0x21D26F4`）将所有 TurnCounter.Count 增加 1。TurnSystem.ProcessEffect（`0x21D2A88`）随后排入下回合 TurnStartEffect、TurnStartCompleteEffect、各阶段及末尾 TurnEndEffect。它排队时取到的 TurnCount 已是下一回合。SunCountSystem 再同步完成双方资源刷新；下一批排队效果仍未开始处理。

因此 **SunCountSystem.ProcessEffect 的 onLeave 是可靠的资源已刷新边界**。在该边界消费上回合登记的每个独立 debt，再把原版 GainSunEffect 放入 current response queue：

```text
TargetId = plantsPlayerId
PlayerId = plantsPlayerId（建议元数据也使用植物方）
SourceId = 登记时的技能来源
Amount = -3
Duration = EndOfTurn（1）
ActivationTime = Immediate（0）
GroupId = 每次施放独立的追踪字符串
```

每次 1012 注册一个任务，可记录 `dueTurn=currentTurn+1`，或者记录“下一次完整 SunCountSystem 刷新”。消费前一次性从 pending 列表移除，再逐项生成 GainSunEffect；不要把 source 仍在场作为条件。这样可支持同回合重复施放、来源已离场，以及再次施放的新债务。Modifier.AddModifier（`0x2273A10`）是普通 List.Add，本身没有按 GroupId 合并；独立 GroupId 用于来源与任务追踪。

Hook 必须排除 AI 使用的预测 EntityModel。SunCountSystem 的 Finder 在 `self+0x18`，EntityFinder 的实际 Model 在 `finder+0x18`；它必须与当前真实 `g.entities` 相同才消费 pending。reserved GrantAbility 动作同样应检查 GrantAbilitySystem.Model（`self+0x10`）一致。仅检查“mod2 资源已启用”不足以排除同进程内预测战斗，否则 AI 模拟回合可能提前消费真实债务或登记模拟施放。

当前 `queueEffects(...,{placement:'current'})` 正好适合该边界。EffectQueue 的 ResponseEffects 为 `0x18`。Shift（`0x224B810`）先调用 MergeResponseEffects（`0x224B854`），后者把响应效果插入普通 Effects 的 index 1，然后移除当前 front。故执行顺序为：

```text
当前 TurnEnd 的全部原版处理
→ 双方资源刷新完成
→ current response 中的逐笔扣阳光
→ 原版下回合 TurnStart／技能触发／阶段推进
```

不要在 EffectRouter 正处理 TurnEnd 时直接 InterruptQueue 替换 front，否则原版 CompleteEffect 可能移除刚插入的新效果。

这次产生的负 modifier 为 EndOfTurn；再下一次刷新会按原版流程清除。任务已经消费且移除，因此不会再次添加扣费，实现“下一回合扣一次”，不会永久扣费。原版 -3 数值下限仍保留。

建议验收：施放当回合资源不额外改变；下一回合准确扣 3；再下一回合恢复正常增长；同回合两次施放扣 6 且只一次；下回合不足 3 时归零而不欠债；无僵尸方资源变化；来源离场仍结算；模式／对局重置清除 pending；实际 GainSunRecord 与资源状态一致。

## 队列分组旁证

EffectQueue.GetCurrentGroupId（`0x224C6D0`）及 GetNextGroupId（`0x224C6D8`）都是只读 getter，分别读取 `0x28` 和 `0x2C`。它们不分配新组。

PushEffectToList（`0x224BB7C`）把效果加入指定列表，随后在 `0x224BC24` 将 Effect.EffectGroupId 写成调用参数。因此 current response 包装只能使用当前原版 group。mod2-animation helper 已改为 GetCurrentGroupId，使用 source 与 Start/End 闭合保证分组，不再宣称分配独立组；不创建额外计数器。
