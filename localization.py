# localization.py
# Skill node / param / enum display names (zh + en). UI shell strings live in i18n.py.

from __future__ import annotations

from typing import Any, Dict, Optional, Union

# entry: str (legacy zh-only) or {"zh": str, "en": str}
LocEntry = Union[str, Dict[str, str]]


def _lang() -> str:
    try:
        import i18n
        return i18n.get_language()
    except Exception:
        return "zh"


def _resolve(entry: Optional[LocEntry], fallback: str) -> str:
    if entry is None:
        return fallback
    if isinstance(entry, dict):
        lang = _lang()
        return entry.get(lang) or entry.get("zh") or entry.get("en") or fallback
    return str(entry)


def _L(zh: str, en: str) -> Dict[str, str]:
    return {"zh": zh, "en": en}


# ---------------------------------------------------------------------------
# Node display names (palette / workspace / replace menu)
# ---------------------------------------------------------------------------
NODE_NAMES: Dict[str, LocEntry] = {
    # Framework
    "EffectEntityGrouping": _L("⚙️ 基础框架 (EffectEntityGrouping)", "⚙️ Framework (EffectEntityGrouping)"),

    # Triggers
    "PlayTrigger": _L("🟢 触发: 当打出时", "🟢 Trigger: When played"),
    "DiscardFromPlayTrigger": _L("🟢 触发: 当死亡时", "🟢 Trigger: When destroyed / leaves play"),
    "BuffTrigger": _L("🟢 触发: 当获得属性加成时", "🟢 Trigger: When buffed"),
    "CombatEndTrigger": _L("🟢 触发: 战斗结束时", "🟢 Trigger: Combat end"),
    "DamageTrigger": _L("🟢 触发: 受到伤害时", "🟢 Trigger: When damaged"),
    "DestroyCardTrigger": _L("🟢 触发: 消灭卡牌时", "🟢 Trigger: When destroying a card"),
    "DrawCardTrigger": _L("🟢 触发: 抽牌时", "🟢 Trigger: When drawing"),
    "DrawCardFromSubsetTrigger": _L("🟢 触发: 召唤卡牌触发", "🟢 Trigger: Draw from subset"),
    "EnterBoardTrigger": _L("🟢 触发: 进场时", "🟢 Trigger: When entering the board"),
    "ExtraAttackTrigger": _L("🟢 触发: 额外攻击时", "🟢 Trigger: Extra attack"),
    "HealTrigger": _L("🟢 触发: 治疗时", "🟢 Trigger: When healing"),
    "LaneCombatEndTrigger": _L("🟢 触发: 单路战斗结束时", "🟢 Trigger: Lane combat end"),
    "LaneCombatStartTrigger": _L("🟢 触发: 单路战斗开始时", "🟢 Trigger: Lane combat start"),
    "MoveTrigger": _L("🟢 触发: 移动时", "🟢 Trigger: When moved"),
    "ReturnToHandTrigger": _L("🟢 触发: 返回手牌时", "🟢 Trigger: When returned to hand"),
    "RevealPhaseEndTrigger": _L("🟢 触发: 揭示阶段结束时", "🟢 Trigger: Reveal phase end"),
    "RevealTrigger": _L("🟢 触发: 揭示时", "🟢 Trigger: When revealed"),
    "SlowedTrigger": _L("🟢 触发: 被冰冻时", "🟢 Trigger: When frozen (Slow)"),
    "SurprisePhaseStartTrigger": _L("🟢 触发: 奇袭阶段开始时", "🟢 Trigger: Surprise phase start"),
    "TurnStartTrigger": _L("🟢 触发: 回合开始时", "🟢 Trigger: Turn start"),

    # Filters
    "TriggerTargetFilter": _L("🟡 触发目标限制 (TriggerTargetFilter)", "🟡 Trigger target filter"),
    "TriggerSourceFilter": _L("🟡 触发来源限制 (TriggerSourceFilter)", "🟡 Trigger source filter"),
    "QueryEntityCondition": _L("🟡 实体条件判断 (QueryEntityCondition)", "🟡 Entity condition (QueryEntityCondition)"),
    "SelfEntityFilter": _L("🟡 自身实体过滤 (SelfEntityFilter)", "🟡 Self entity filter"),
    "PlayerInfoCondition": _L("🟡 玩家信息条件 (PlayerInfoCondition)", "🟡 Player info condition"),

    # Target selectors
    "PrimaryTargetFilter": _L("🟠 执行目标选取 (PrimaryTargetFilter)", "🟠 Primary target filter"),
    "SecondaryTargetFilter": _L("🎯 次要目标选取 (SecondaryTargetFilter)", "🎯 Secondary target filter"),

    # Conditions
    "OncePerGameCondition": _L("🟣 限制: 每局一次", "🟣 Limit: Once per game"),
    "OncePerTurnCondition": _L("🟣 限制: 每回合一次", "🟣 Limit: Once per turn"),
    "PersistsAfterTransform": _L(
        "🟣 限制: 变形后保留技能 (PersistsAfterTransform)",
        "🟣 Limit: Persists after transform",
    ),

    # Composite queries
    "CompositeAllQuery": _L("🔗 满足所有条件 [AND]", "🔗 All conditions [AND]"),
    "CompositeAnyQuery": _L("🔗 满足任一条件 [OR]", "🔗 Any condition [OR]"),
    "NotQuery": _L("🔗 否定 (NOT)", "🔗 Negation (NOT)"),

    # Queries — no params
    "AlwaysMatchesQuery": _L("🔵 条件: 永远匹配", "🔵 Query: Always matches"),
    "BehindSameLaneQuery": _L("🔵 范围: 在同行的后面", "🔵 Range: Behind in same lane"),
    "DrawnCardQuery": _L("🔵 对象: 抽到的卡牌", "🔵 Object: Drawn card"),
    "FighterQuery": _L("🔵 条件: 是斗士单位", "🔵 Query: Is a fighter"),
    "InEnvironmentQuery": _L("🔵 范围: 在场地上", "🔵 Range: On an environment"),
    "InHandQuery": _L("🔵 范围: 在手牌中", "🔵 Range: In hand"),
    "InLaneQuery": _L("🔵 范围: 在行内", "🔵 Range: In a lane"),
    "InOneTimeEffectZoneQuery": _L("🔵 范围: 在一次性效果区", "🔵 Range: One-time effect zone"),
    "InUnopposedLaneQuery": _L("🔵 条件: 在无对手的行", "🔵 Query: Unopposed lane"),
    "IsActiveQuery": _L("🔵 条件: 处于激活状态", "🔵 Query: Is active"),
    "IsAliveQuery": _L("🔵 条件: 存活状态", "🔵 Query: Is alive"),
    "LastLaneOfSelfQuery": _L("🔵 范围: 自身的最后一行", "🔵 Range: Self's last lane"),
    "OriginalTargetCardGuidQuery": _L("🔵 对象: 原始目标卡牌", "🔵 Object: Original target card"),
    "SameFactionQuery": _L("🔵 条件: 同阵营", "🔵 Query: Same faction"),
    "SameLaneAsTargetQuery": _L("🔵 范围: 与目标同行", "🔵 Range: Same lane as target"),
    "SameLaneQuery": _L("🔵 范围: 在同一行", "🔵 Range: Same lane"),
    "SelfQuery": _L("🔵 对象: 自己", "🔵 Object: Self"),
    "SourceQuery": _L("🔵 对象: 来源", "🔵 Object: Source"),
    "SpringboardedOnSelfQuery": _L("🔵 条件: 跳板作用于自身", "🔵 Query: Springboarded on self"),
    "TargetCardGuidQuery": _L("🔵 对象: 目标的卡牌", "🔵 Object: Target card"),
    "TargetQuery": _L("🔵 对象: 选中的目标", "🔵 Object: Selected target"),
    "TargetableInPlayFighterQuery": _L("🔵 条件: 场上可选中单位", "🔵 Query: Targetable fighter in play"),
    "TrickQuery": _L("🔵 条件: 是锦囊/法术", "🔵 Query: Is a trick"),
    "WasInSameLaneAsSelfQuery": _L("🔵 范围: 曾与自身同行", "🔵 Range: Was in same lane as self"),
    "WillTriggerEffectsQuery": _L("🔵 条件: 将触发效果", "🔵 Query: Will trigger effects"),
    "WillTriggerOnDeathEffectsQuery": _L("🔵 条件: 将触发死亡效果", "🔵 Query: Will trigger death effects"),

    # Queries — params
    "AdjacentLaneQuery": _L("🔵 范围: 相邻的行 (指定来源)", "🔵 Range: Adjacent lane (origin)"),
    "CardGuidQuery": _L("🔵 条件: 卡牌GUID匹配", "🔵 Query: Card GUID match"),
    "InAdjacentLaneQuery": _L("🔵 范围: 在相邻的行", "🔵 Range: In adjacent lane"),
    "InLaneAdjacentToLaneQuery": _L("🔵 范围: 在相邻的行", "🔵 Range: Lane adjacent to lane"),
    "InLaneSameAsLaneQuery": _L("🔵 范围: 行数相同匹配", "🔵 Range: Same lane index"),
    "InSameLaneQuery": _L("🔵 范围: 在同一行", "🔵 Range: In same lane"),
    "LaneOfIndexQuery": _L("🔵 范围: 指定索引的行", "🔵 Range: Lane by index"),
    "QueryMultiplier": _L("🔵 查询倍率 (QueryMultiplier)", "🔵 Query multiplier"),
    "SubsetQuery": _L("🔵 条件: 属于特定子集", "🔵 Query: In subset/tag"),
    "SubtypeQuery": _L("🔵 条件: 属于特定种族 (Subtype)", "🔵 Query: Subtype match"),

    # Comparison queries
    "AttackComparisonQuery": _L("🔵 条件: 攻击力数值判断", "🔵 Query: Attack comparison"),
    "BlockMeterValueQuery": _L("🔵 条件: 格挡值判断", "🔵 Query: Block meter comparison"),
    "DamageTakenComparisonQuery": _L("🔵 条件: 已受伤害判断", "🔵 Query: Damage taken comparison"),
    "HealthComparisonQuery": _L("🔵 条件: 生命值判断 (HealthComparison)", "🔵 Query: Health comparison"),
    "SunCostComparisonQuery": _L("🔵 条件: 阳光/脑子费用判断", "🔵 Query: Cost comparison"),
    "SunCostPlusNComparisonQuery": _L("🔵 条件: 费用+N 判断", "🔵 Query: Cost + N comparison"),
    "SunCounterComparisonQuery": _L("🔵 条件: 阳光计数器判断", "🔵 Query: Sun counter comparison"),
    "TurnCountQuery": _L("🔵 条件: 回合数判断", "🔵 Query: Turn count comparison"),

    # Component queries
    "HasComponentQuery": _L("🔵 条件: 拥有组件", "🔵 Query: Has component"),
    "LacksComponentQuery": _L("🔵 条件: 缺少组件", "🔵 Query: Lacks component"),
    "OnTerrainQuery": _L("🔵 条件: 在地形上", "🔵 Query: On terrain"),
    "OpenLaneQuery": _L("🔵 条件: 空行判断", "🔵 Query: Open lane"),

    # HasComponent shortcuts
    "HasZombiesComponent": _L("🔵 条件: 是僵尸", "🔵 Query: Is zombie"),
    "HasPlantsComponent": _L("🔵 条件: 是植物", "🔵 Query: Is plant"),
    "HasPlayerComponent": _L("🔵 条件: 是英雄/玩家 (Player)", "🔵 Query: Is hero/player"),
    "HasLaneComponent": _L("🔵 条件: 是一整行(地段)", "🔵 Query: Is a lane"),
    "HasFaceDownComponent": _L("🔵 条件: 是暗置/墓碑", "🔵 Query: Is face-down / gravestone"),
    "HasEnvironmentComponent": _L("🔵 条件: 是场地牌", "🔵 Query: Is environment"),
    "HasWaterTerrainComponent": _L("🔵 条件: 在水生地形", "🔵 Query: Water terrain"),
    "HasHighgroundTerrainComponent": _L("🔵 条件: 在高地地形", "🔵 Query: Heights terrain"),
    "HasUnhealableComponent": _L("🔵 条件: 不可治疗", "🔵 Query: Unhealable"),
    "HasSuperpowerComponent": _L("🔵 条件: 是英雄技能 (Superpower)", "🔵 Query: Is superpower"),

    # Effects — no params
    "CopyStatsEffect": _L("🔴 效果: 复制属性", "🔴 Effect: Copy stats"),
    "DestroyCardEffect": _L("🔴 效果: 直接消灭", "🔴 Effect: Destroy"),
    "ExtraAttackEffect": _L("🔴 效果: 额外攻击", "🔴 Effect: Extra attack"),
    "MixedUpGravediggerEffectDescriptor": _L("🔴 效果: 掘墓人墓碑", "🔴 Effect: Gravedigger mix-up"),
    "MoveCardToLanesEffectDescriptor": _L("🔴 效果: 移动", "🔴 Effect: Move to lanes"),
    "ReturnToHandEffect": _L("🔴 效果: 弹回手牌", "🔴 Effect: Return to hand"),
    "SlowEffect": _L("🔴 效果: 冰冻 (Slow)", "🔴 Effect: Freeze (Slow)"),
    "TurnIntoGravestoneEffectDescriptor": _L("🔴 效果: 回到墓碑", "🔴 Effect: Turn into gravestone"),

    # Effects — with params
    "AttackInLaneEffectDescriptor": _L("🔴 效果: 攻击本行 (AttackInLane)", "🔴 Effect: Attack in lane"),
    "BuffEffect": _L("🔴 效果: 属性改变 (Buff/Debuff)", "🔴 Effect: Buff / debuff"),
    "ChargeBlockMeterEffectDescriptor": _L("🔴 效果: 充能格挡值 (ChargeBlockMeter)", "🔴 Effect: Charge block meter"),
    "CopyCardEffectDescriptor": _L("🔴 效果: 复制卡牌 (CopyCard)", "🔴 Effect: Copy card"),
    "CreateCardEffect": _L("🔴 效果: 召唤特定卡牌 (GUID)", "🔴 Effect: Create card (GUID)"),
    "CreateCardInDeckEffect": _L("🔴 效果: 洗入牌库", "🔴 Effect: Shuffle into deck"),
    "DamageEffect": _L("🔴 效果: 造成伤害", "🔴 Effect: Deal damage"),
    "DrawCardEffect": _L("🔴 效果: 抽牌", "🔴 Effect: Draw cards"),
    "EffectValueDescriptor": _L("🔴 效果: 效果值映射 (EffectValueDescriptor)", "🔴 Effect: Value mapping"),
    "GainSunEffect": _L("🔴 效果: 获得阳光/脑子", "🔴 Effect: Gain sun / brains"),
    "GrantAbilityEffect": _L("🔴 效果: 赋予特殊能力 (关键字)", "🔴 Effect: Grant ability keyword"),
    "GrantTriggeredAbilityEffectDescriptor": _L(
        "🔴 效果: 赋予能力 (GrantTriggeredAbility)",
        "🔴 Effect: Grant triggered ability",
    ),
    "HealEffect": _L("🔴 效果: 治疗", "🔴 Effect: Heal"),
    "HeroHealthMultiplier": _L("🔴 效果: 英雄血量倍率 (HeroHealthMultiplier)", "🔴 Effect: Hero health multiplier"),
    "ModifySunCostEffect": _L("🔴 效果: 修改卡牌花费", "🔴 Effect: Modify cost"),
    "SetStatEffect": _L("🔴 效果: 属性数值强制设定 (SetStat)", "🔴 Effect: Set stat"),
    "SunGainedMultiplier": _L("🔴 效果: 获得阳光倍率 (SunGainedMultiplier)", "🔴 Effect: Sun gained multiplier"),
    "TargetAttackMultiplier": _L("🔴 效果: 攻击力翻倍/倍增", "🔴 Effect: Attack multiplier"),
    "TargetHealthMultiplier": _L("🔴 效果: 生命值翻倍/倍增", "🔴 Effect: Health multiplier"),

    # Complex effects
    "DrawCardFromSubsetEffect": _L("🟥 复合：召唤", "🟥 Complex: Draw from subset"),
    "CreateCardFromSubsetEffectDescriptor": _L(
        "🟥 效果: 生成卡牌 (CreateCardFromSubset)",
        "🟥 Effect: Create from subset",
    ),
    "TransformIntoCardFromSubsetEffectDescriptor": _L(
        "🟥 效果: 变身 (TransformIntoSubset)",
        "🟥 Effect: Transform into subset card",
    ),

    # Virtual / UI helpers
    "AdditionalTargetQuery": _L("📦 额外目标条件", "📦 Additional target query"),
    "FinderPlaceholder": _L("🔍 查找范围 (Finder)", "🔍 Finder scope"),
    "QueryPlaceholder": _L("📋 满足条件 (Query)", "📋 Query conditions"),

    # Misc labels (legacy / params reused as node labels)
    "AbilityGuid": _L(
        "能力 GUID (常用: 562=双重攻击, 564=先攻, 615=远古吸血, 668=狩猎场)",
        "Ability GUID (common: 562=Double Strike, 564=Overshoot, 615=Ancient Vampire, 668=Hunting Grounds)",
    ),
    "AbilityValueType": _L("能力数值类型", "Ability value type"),
    "AbilityValueAmount": _L("能力数值", "Ability value amount"),

    "CompositeQuery": _L("🔗 复合查询", "🔗 Composite query"),
    "Query": _L("🔵 查询条件", "🔵 Query"),
    "Effect": _L("🔴 效果", "🔴 Effect"),
    "Filter": _L("🟡 过滤器", "🟡 Filter"),
    "TargetSelector": _L("🎯 目标选择器", "🎯 Target selector"),

    "RawUnknownComponent": _L("⚠️ 未识别组件（导出时原样保留）", "⚠️ Unknown component (kept on export)"),

    # Ability keywords (display)
    "Multishot": _L("多重射击 (Multishot)", "Multishot"),
    "AttacksInAllLanes": _L("全路攻击 (AttacksInAllLanes)", "Attacks in all lanes"),
    "PlaysFaceDown": _L("暗置 (PlaysFaceDown)", "Plays face-down"),
    "Aquatic": _L("水生 (Aquatic)", "Aquatic"),
    "DoubleStrike": _L("连击 (DoubleStrike)", "Double Strike"),
    "AttackOverride": _L("攻击覆盖 (AttackOverride)", "Attack override"),
    "SplashDamage": _L("溅射伤害 (SplashDamage)", "Splash damage"),

    # Extra param/enum style keys sometimes shown as nodes
    "Divider": _L("倍数/除数", "Multiplier / divider"),
    "Amount": _L("数值", "Amount"),
    "ActivationTime": _L("执行时间", "Activation time"),
    "CardGuid": _L("卡牌 ID (GUID)", "Card ID (GUID)"),
    "AmountToCreate": _L("生成数量", "Amount to create"),
    "DeckPosition": _L("洗入位置", "Deck position"),
    "Immediate": _L("立即执行", "Immediate"),
    "NextTurn": _L("下回合开始", "Next turn"),
    "Top": _L("牌库顶", "Top of deck"),
    "Bottom": _L("牌库底", "Bottom of deck"),

    "GrantableAbilityType": _L("赋予的能力类型", "Granted ability type"),
    "StripNoncontinousModifiers": _L("剥离非持续性加成 (清空临时Buff)", "Strip non-continuous modifiers"),
    "StatType": _L("修改属性类型", "Stat type"),
    "AbilityValue": _L("特殊修正值 (如免疫类型)", "Ability value (e.g. immunity side)"),
    "ModifyOperation": _L("修改方式", "Modify operation"),
    "ForceFaceDown": _L("以墓碑/潜行方式召唤", "Create face-down / gravestone"),

    "Permanent": _L("永久", "Permanent"),
    "EndOfTurn": _L("回合结束", "End of turn"),
    "Either": _L("任意侧", "Either side"),
    "ToTheLeft": _L("左侧", "To the left"),
    "ToTheRight": _L("右侧", "To the right"),
    "Self": _L("自身", "Self"),
    "Source": _L("来源", "Source"),
    "Target": _L("目标", "Target"),
}

# Engine Descriptor class name -> canonical node id (display maintained once)
_NODE_NAME_ALIASES = {
    "BuffEffectDescriptor": "BuffEffect",
    "DamageEffectDescriptor": "DamageEffect",
    "DestroyCardEffectDescriptor": "DestroyCardEffect",
    "DrawCardEffectDescriptor": "DrawCardEffect",
    "HealEffectDescriptor": "HealEffect",
    "ExtraAttackEffectDescriptor": "ExtraAttackEffect",
    "ReturnToHandFromPlayEffectDescriptor": "ReturnToHandEffect",
    "SlowEffectDescriptor": "SlowEffect",
    "GainSunEffectDescriptor": "GainSunEffect",
    "ModifySunCostEffectDescriptor": "ModifySunCostEffect",
    "CreateCardInDeckEffectDescriptor": "CreateCardInDeckEffect",
    "GrantAbilityEffectDescriptor": "GrantAbilityEffect",
    "CreateCardEffectDescriptor": "CreateCardEffect",
    "SetStatEffectDescriptor": "SetStatEffect",
    "CopyStatsEffectDescriptor": "CopyStatsEffect",
    "DrawCardFromSubsetEffectDescriptor": "DrawCardFromSubsetEffect",
}
for _alias, _canon in _NODE_NAME_ALIASES.items():
    if _canon in NODE_NAMES and _alias not in NODE_NAMES:
        NODE_NAMES[_alias] = NODE_NAMES[_canon]


# ---------------------------------------------------------------------------
# Parameter labels (inspector form)
# ---------------------------------------------------------------------------
PARAM_NAMES: Dict[str, LocEntry] = {
    "MappingType": _L("映射类型", "Mapping type"),
    "DestToSourceMap": _L("目标到源映射 (如 HealAmount: DamageAmount)", "Dest→source map (e.g. HealAmount: DamageAmount)"),

    "AbilityGroupId": _L("技能组 ID", "Ability group ID"),
    "SelectionType": _L("选择目标方式", "Selection type"),
    "NumTargets": _L("目标数量", "Number of targets"),
    "TargetScopeType": _L("目标范围筛选", "Target scope type"),
    "TargetScopeSortValue": _L("排序参考数值", "Sort by"),
    "TargetScopeSortMethod": _L("排序方法", "Sort method"),
    "AdditionalTargetType": _L("额外目标类型", "Additional target type"),
    "OnlyApplyEffectsOnAdditionalTargets": _L("仅对额外目标生效", "Only affect additional targets"),
    "OriginEntityType": _L("基准实体", "Origin entity"),
    "Side": _L("相邻方向", "Side"),
    "ComparisonOperator": _L("比较符号", "Comparison"),
    "AttackValue": _L("攻击力比较值", "Attack value"),
    "DamageAmount": _L("伤害数值", "Damage amount"),
    "AttackAmount": _L("攻击力改变(Buff)", "Attack change (buff)"),
    "HealthAmount": _L("生命值改变(Buff)", "Health change (buff)"),
    "BuffDuration": _L("持续时间", "Buff duration"),

    "SunCost": _L("阳光/脑子费用", "Sun / brains cost"),
    "SunCostAmount": _L("费用改变量", "Cost change amount"),
    "DrawAmount": _L("抽牌数量", "Draw amount"),
    "HealAmount": _L("治疗量", "Heal amount"),
    "Divider": _L("倍数", "Divider / multiplier"),
    "Amount": _L("数值", "Amount"),
    "ActivationTime": _L("激活时机", "Activation time"),
    "CardGuid": _L("卡牌GUID", "Card GUID"),
    "AmountToCreate": _L("创建数量", "Amount to create"),
    "DeckPosition": _L("牌库位置", "Deck position"),
    "GrantableAbilityType": _L("赋予的能力", "Granted ability"),
    "AbilityValue": _L("能力参数", "Ability value"),
    "ModifyOperation": _L("修改操作", "Modify operation"),
    "Value": _L("数值", "Value"),
    "ForceFaceDown": _L("强制暗置", "Force face-down"),
    "StatType": _L("属性类型", "Stat type"),
    "StripNoncontinousModifiers": _L("移除非持续修正", "Strip non-continuous modifiers"),
    "Duration": _L("持续时间", "Duration"),
    "Subtype": _L("子类型/种族", "Subtype"),
    "Subset": _L("子集/标签", "Subset / tag"),
    "Guid": _L("卡牌 GUID", "Card GUID"),
    "LaneIndex": _L("行索引", "Lane index"),
    "ComponentType": _L("组件类型", "Component type"),
    "TerrainType": _L("地形类型", "Terrain type"),
    "PlayerFactionType": _L("阵营类型", "Faction type"),
    "IsForTeamupCard": _L("可用于组队卡", "For team-up card"),
    "Faction": _L("阵营", "Faction"),

    "ConditionEvaluationType": _L("满足规则的判定方式", "Condition evaluation"),
    "Finder": _L("查找器/来源", "Finder / source"),

    "ChargeAmount": _L("充能数值", "Charge amount"),
    "GrantTeamup": _L("赋予组队能力", "Grant team-up"),
    "CreateInFront": _L("在身前创建", "Create in front"),

    "AbilityGuid": _L("能力 GUID", "Ability GUID"),
    "AbilityValueType": _L("能力数值类型", "Ability value type"),
    "AbilityValueAmount": _L("能力数值", "Ability value amount"),

    "HealthValue": _L("生命值比较值", "Health value"),
    "BlockMeterValue": _L("格挡值比较", "Block meter value"),
    "DamageTakenValue": _L("已受伤害比较", "Damage taken value"),
    "AdditionalCost": _L("额外费用", "Additional cost"),
    "SunCounterValue": _L("阳光计数器值", "Sun counter value"),
    "TurnCount": _L("回合数", "Turn count"),
}


# ---------------------------------------------------------------------------
# Enum option labels (inspector comboboxes)
# ---------------------------------------------------------------------------
ENUM_NAMES: Dict[str, LocEntry] = {
    # EffectValueDescriptor
    "DamageToHeal": _L("伤害 → 治疗 (DamageAmount → HealAmount)", "Damage → Heal"),
    "HealToDamage": _L("治疗 → 伤害 (HealAmount → DamageAmount)", "Heal → Damage"),

    # Selection / scope (shared keys; labels cover common UI use)
    "Manual": _L("手动选取 (Manual)", "Manual"),
    "Random": _L("随机 (Random)", "Random"),
    "All": _L("全部 (All)", "All"),
    "Sorted": _L("按条件排序 (Sorted)", "Sorted"),
    "Any": _L("任意满足 (Any)", "Any"),
    "None": _L("无 (None)", "None"),
    "Attack": _L("攻击力 (Attack)", "Attack"),
    "Health": _L("生命值 (Health)", "Health"),
    "SunCost": _L("费用 (SunCost)", "Cost"),
    "Lowest": _L("最低的 (Lowest)", "Lowest"),
    "Highest": _L("最高的 (Highest)", "Highest"),
    "Query": _L("自定义查询 (Query)", "Query"),

    # Origin
    "Self": _L("自身 (Self)", "Self"),
    "Source": _L("来源 (Source)", "Source"),
    "Target": _L("目标 (Target)", "Target"),

    # Side
    "Either": _L("任意两侧 (Either)", "Either side"),
    "ToTheLeft": _L("左侧 (ToTheLeft)", "To the left"),
    "ToTheRight": _L("右侧 (ToTheRight)", "To the right"),

    # Comparison
    "LessOrEqual": _L("小于等于 (<=)", "Less or equal (<=)"),
    "Equal": _L("等于 (==)", "Equal (==)"),
    "GreaterOrEqual": _L("大于等于 (>=)", "Greater or equal (>=)"),

    # Duration
    "Permanent": _L("永久 (Permanent)", "Permanent"),
    "EndOfTurn": _L("回合结束时 (EndOfTurn)", "End of turn"),
    "NextFighter": _L("下一个单位 (NextFighter)", "Next fighter"),

    # Activation
    "Immediate": _L("立即 (Immediate)", "Immediate"),
    "NextTurn": _L("下回合 (NextTurn)", "Next turn"),

    # Deck
    "Top": _L("牌库顶 (Top)", "Top"),
    "Bottom": _L("牌库底 (Bottom)", "Bottom"),

    # Modify
    "Add": _L("增加 (Add)", "Add"),
    "Set": _L("设置为 (Set)", "Set"),

    # Grantable abilities
    "Unhurtable": _L("无敌 (Unhurtable)", "Unhurtable"),
    "Deadly": _L("致命 (Deadly)", "Deadly"),
    "Frenzy": _L("狂怒 (Frenzy)", "Frenzy"),
    "Truestrike": _L("精准打击 (Truestrike)", "Truestrike"),
    "Strikethrough": _L("穿透 (Strikethrough)", "Strikethrough"),
    "Afterlife": _L("来世 (Afterlife)", "Afterlife"),
    "MinHealth": _L("最小生命值 (MinHealth)", "Min health"),
    "NoExtraAttacks": _L("无法额外攻击 (NoExtraAttacks)", "No extra attacks"),
    "GravestoneSpy": _L("墓碑侦察 (GravestoneSpy)", "Gravestone spy"),
    "Teamup": _L("组队 (Teamup)", "Team-up"),
    "Aquatic": _L("水生 (Aquatic)", "Aquatic"),
    "CanPlayFighterInSurprisePhase": _L(
        "奇袭阶段可打出 (CanPlayFighterInSurprisePhase)",
        "Play fighter in surprise phase",
    ),
    "Mustache": _L("胡子 (Mustache)", "Mustache"),
    "AttackOverride": _L("攻击覆盖 (AttackOverride)", "Attack override"),
    "MultiplyDamage": _L("伤害翻倍 (MultiplyDamage)", "Multiply damage"),
    "Graveyard": _L("墓地 (Graveyard)", "Graveyard"),
    "Untrickable": _L("锦囊免疫 (Untrickable)", "Untrickable"),
    "Unhealable": _L("不可治疗 (Unhealable)", "Unhealable"),

    # Misc values
    "BlockMeterValue": _L("格挡值", "Block meter"),
    "DamageTakenValue": _L("已受伤害值", "Damage taken"),
    "AdditionalCost": _L("额外费用", "Additional cost"),
    "SunCounterValue": _L("阳光计数器值", "Sun counter"),
    "TurnCount": _L("回合数", "Turn count"),

    # Factions
    "Plants": _L("植物阵营", "Plants"),
    "Zombies": _L("僵尸阵营", "Zombies"),
    "PvZCards.Engine.Components.Plants, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null": _L(
        "植物阵营", "Plants"
    ),
    "PvZCards.Engine.Components.Zombies, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null": _L(
        "僵尸阵营", "Zombies"
    ),

    # Terrain / components short
    "GrassTerrain": _L("草地", "Grass"),
    "WaterTerrain": _L("水域", "Water"),
    "HighgroundTerrain": _L("高地", "Heights"),
    "Environment": _L("场地", "Environment"),
    "FaceDown": _L("暗置/墓碑", "Face-down / gravestone"),

    # Ability value type
    "Damage": _L("伤害 (Damage)", "Damage"),

    # Legacy option labels (if still shown somewhere)
    "562: 双重攻击 (DoubleStrike)": _L("562: 双重攻击 (DoubleStrike)", "562: Double Strike"),
    "564: 先攻 (FirstStrike)": _L("564: 先攻 (FirstStrike)", "564: Overshoot / First Strike"),
    "615: 远古吸血僵尸 (AncientVampireZombie)": _L(
        "615: 远古吸血僵尸 (AncientVampireZombie)",
        "615: Ancient Vampire Zombie",
    ),
    "668: 狩猎场 (HuntingGrounds)": _L("668: 狩猎场 (HuntingGrounds)", "668: Hunting Grounds"),
    "0: 自定义 GUID": _L("0: 自定义 GUID (手动输入)", "0: Custom GUID (manual)"),
}


# ---------------------------------------------------------------------------
# Palette subcategory keys (used by panel_main)
# ---------------------------------------------------------------------------
PALETTE_SUBCATS: Dict[str, LocEntry] = {
    "query_entity": _L("🧍 实体与阵营", "🧍 Entity & faction"),
    "query_terrain": _L("🗺️ 地形与位置", "🗺️ Terrain & position"),
    "query_hand": _L("🖐️ 手牌与卡牌", "🖐️ Hand & cards"),
    "query_stats": _L("📊 数值与状态", "📊 Stats & state"),
    "query_object": _L("🎯 对象与指针", "🎯 Objects & pointers"),
    "effect_damage": _L("⚔️ 伤害与消灭", "⚔️ Damage & destroy"),
    "effect_heal": _L("❤️ 治疗与增益", "❤️ Heal & buffs"),
    "effect_cards": _L("🃏 卡牌与生成", "🃏 Cards & creation"),
    "effect_control": _L("🏃 移动与控制", "🏃 Move & control"),
    "effect_sun": _L("☀️ 费用与阳光", "☀️ Cost & sun"),
    "effect_grant": _L("✨ 能力赋予", "✨ Grant abilities"),
    "trigger_play": _L("🃏 打出与离场", "🃏 Play & leave"),
    "trigger_combat": _L("⚔️ 战斗阶段", "⚔️ Combat phase"),
    "trigger_turn": _L("⏳ 回合阶段", "⏳ Turn phase"),
    "trigger_state": _L("✨ 状态改变", "✨ State changes"),
}


# ---------------------------------------------------------------------------
# Public getters
# ---------------------------------------------------------------------------
def get_node_name(key: str, default: Optional[str] = None) -> str:
    """Localized display name for a skill node / component id."""
    return _resolve(NODE_NAMES.get(key), default if default is not None else key)


def get_param_name(key: str, default: Optional[str] = None) -> str:
    """Localized parameter label."""
    return _resolve(PARAM_NAMES.get(key), default if default is not None else key)


def get_enum_name(key: str, default: Optional[str] = None) -> str:
    """Localized enum option label."""
    return _resolve(ENUM_NAMES.get(key), default if default is not None else key)


def get_palette_subcat(key: str, default: Optional[str] = None) -> str:
    """Localized palette subcategory title."""
    return _resolve(PALETTE_SUBCATS.get(key), default if default is not None else key)


# ---------------------------------------------------------------------------
# Effect description templates (optional helpers; logic_translator is primary)
# ---------------------------------------------------------------------------
EFFECT_DESCRIPTIONS: Dict[str, LocEntry] = {
    "DamageEffect": _L("造成 {damage} 点伤害", "Deal {damage} damage"),
    "BuffEffect": _L(
        "{duration}获得攻击力 {attack:+d} / 生命值 {health:+d}",
        "{duration} gain {attack:+d} attack / {health:+d} health",
    ),
    "DestroyCardEffect": _L("直接消灭目标", "Destroy the target"),
    "DrawCardEffect": _L("抽 {amount} 张牌", "Draw {amount} card(s)"),
    "HealEffect": _L("恢复 {amount} 点生命值", "Heal {amount}"),
    "ExtraAttackEffect": _L("获得额外一次攻击机会", "Gain an extra attack"),
    "TargetAttackMultiplier": _L("攻击力变为 {divider} 倍", "Attack becomes ×{divider}"),
    "TargetHealthMultiplier": _L("生命值变为 {divider} 倍", "Health becomes ×{divider}"),
    "ReturnToHandEffect": _L("将目标弹回手牌", "Return target to hand"),
    "SlowEffect": _L("冰冻目标", "Freeze (Slow) the target"),
    "GainSunEffect": _L("{when}获得 {amount} 点阳光/脑子", "{when} gain {amount} sun/brains"),
    "ModifySunCostEffect": _L("{duration}使卡牌花费改变 {amount}", "{duration} change cost by {amount}"),
    "CreateCardInDeckEffect": _L(
        "将 {amount} 张卡牌 (ID:{card_id}) 洗入牌库的 {position}",
        "Shuffle {amount} card(s) (ID:{card_id}) into deck ({position})",
    ),
    "GrantAbilityEffect": _L("{duration}赋予能力【{ability}】{extra}", "{duration} grant [{ability}]{extra}"),
    "CreateCardEffect": _L("{face_down}召唤卡牌 (ID:{card_id})", "{face_down}create card (ID:{card_id})"),
    "SetHeroHealthEffect": _L("{operation}英雄生命值 {amount} 点", "{operation} hero health by {amount}"),
    "CopyStatsEffect": _L("复制目标的属性数值", "Copy the target's stats"),
}


def get_effect_description(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    text = _resolve(EFFECT_DESCRIPTIONS.get(key), default if default is not None else key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
