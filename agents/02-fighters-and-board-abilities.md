# 02 · Fighter 技能移植与场景能力

## 数据入口

`cards` 是按字符串 GUID 索引的字典。内部 `Card.$data.Guid` 是整数。实际逻辑在 `entity.components`，显示和分类在根层字段。

本次共 651 条卡牌定义，其中 `isFighter == true` 的有 415 条，包括不可收集的单位。不要用稀有度、是否可购买或 GUID 区间替代 Fighter 筛选。

所有引擎组件的完整类型后缀：

```text
, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null
```

常用组件命名空间为 `PvZCards.Engine.Components`；查询为 `PvZCards.Engine.Queries`。也有例外，如GrantTriggeredAbilityEffectDescriptor在 `PvZCards.Engine.Effects`，见[06章](06-large-card-remix.md)。以原包完整$type为准，不能统一猜命名空间或写入教程省略号。

## 快乐的冬青：GUID 409

真实 `prefabName` 是 `Jolly Holly`。仅深拷贝其 `EffectEntitiesDescriptor.$data.entities`，不要复制费用、身材、两栖组件或种族。

该技能链：

```text
EffectEntityGrouping
PlayTrigger
TriggerTargetFilter: SelfQuery AND WillTriggerEffectsQuery AND IsAliveQuery
PrimaryTargetFilter:
  InAdjacentLaneQuery(Side=Either)
  AND HasComponentQuery(ComponentType=...Zombies,...)
  AND TargetableInPlayFighterQuery
SlowEffectDescriptor
```

植物副本保留 `Zombies`；僵尸副本仅将**新追加技能中的**敌方 ComponentType 改为 `Plants`。相邻路线不包含自身路线。冻结使用 `SlowEffectDescriptor`。

追加算法：

1. 先保存未修改的冬青模板；遍历原始卡牌集合。
2. 筛选 `isFighter`，跳过 409，保留其原生技能一次。
3. 原卡已有 EffectEntitiesDescriptor 就向 entities 追加；没有则新建一个组件。
4. 新技能的 `AbilityGroupId` 使用该卡已有组编号最大值加一（没有则为 0），不重编号旧技能。
5. 只对新技能做阵营映射。
6. 验证原卡所有字段、所有旧技能与顺序保留。

本次新增 414 张：211 张植物、203 张僵尸，加上原版冬青，覆盖全部 415 张 Fighter。

## “打出时生命值设为 1”场景规则

先明确用户要的是登场生命值，而非攻击力、伤害或永久生命上限。该机制允许之后正常加血、受伤；不是每帧或每回合强行锁血。

参考来源：

- 场景卡 370：`BoardAbilityView`、`BoardAbility` 组件和监听 PlayTrigger 的可用结构。
- 三头花生 597：`SetStatEffectDescriptor` 的 Set/Strip 字段和 TargetQuery。
- 红针花 411、洋葱圈 448：实际使用 `StatType: "Health"` 的佐证。

场景实体没有 Fighter 身份。不能直接保留三头花生的 `SelfEntityFilter(FighterQuery...)`，否则场景技能会被自身过滤条件拦截。也应删除三头花生原有的“植物阵营”和“攻击力不等于 3”条件。

正确的核心链：

```text
EffectEntityGrouping(AbilityGroupId=0)
PlayTrigger
TriggerTargetFilter(TargetableInPlayFighterQuery)
PrimaryTargetFilter(TargetQuery, SelectionType=All)
SetStatEffectDescriptor:
  StatType=Health
  Value=1
  ModifyOperation=Set
  StripNoncontinousModifiers=true
```

`StripNoncontinousModifiers` 的拼写来自原包，不要“纠正”为 continuous。规则面向双方，没有 Plants/Zombies 限制。克隆 370 的元数据和 Unusable 标记，选取无冲突的新整数 GUID，再挂到目标关卡 `BoardAbilities`。本次用 900000101。

`PlayTrigger` 与三头花生一致。“登场”的更广义情况（召唤、变形、墓碑、融合等）须逐项实测；不要仅凭静态 JSON 就宣称所有进入场地路径均已验证。需要改变时机时应先查看原卡的实际触发器并复测，不凭名称推断。
