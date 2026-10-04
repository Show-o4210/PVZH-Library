# logic_translator.py
# Natural-language description of ability entities (zh / en).

from core_utils import safe_get
from constants import parse_type_str, normalize_engine_type_name
import localization
import logic_library


def _is_en() -> bool:
    try:
        import i18n
        return i18n.get_language() == "en"
    except Exception:
        return False


def _p(zh: str, en: str) -> str:
    return en if _is_en() else zh


def parse_query(query_data):
    if not query_data:
        return ""
    raw_type = query_data.get("$type", "")
    d = query_data.get("$data", {}) or {}
    comp_name = logic_library.resolve_node_id_from_type(raw_type, d) or \
                normalize_engine_type_name(parse_type_str(raw_type))

    # ========= Composite =========
    if comp_name == "CompositeAllQuery":
        parts = list(filter(None, [parse_query(q) for q in d.get("queries", [])]))
        joiner = " and " if _is_en() else " 且 "
        return joiner.join(parts)
    if comp_name == "CompositeAnyQuery":
        parts = list(filter(None, [parse_query(q) for q in d.get("queries", [])]))
        joiner = " or " if _is_en() else " 或 "
        return joiner.join(parts)
    if comp_name == "NotQuery":
        inner = parse_query(d.get("Query", {}))
        if inner:
            return _p(f"不满足【{inner}】", f"not ({inner})")
        return _p("否定条件", "negated condition")

    # ========= Atomic lookup =========
    query_map = {
        "SelfQuery": _p("其自身", "itself"),
        "TargetQuery": _p("目标", "the target"),
        "InSameLaneQuery": _p("同一行的", "in the same lane"),
        "InLaneSameAsLaneQuery": _p("相同指定行的", "in the same lane index"),
        "TargetableInPlayFighterQuery": _p("场上的斗士", "a targetable fighter in play"),
        "WillTriggerOnDeathEffectsQuery": _p("具备死亡效果的", "with death effects"),
        "AlwaysMatchesQuery": _p("所有目标", "anything"),
        "BehindSameLaneQuery": _p("同行的后面", "behind in the same lane"),
        "DrawnCardQuery": _p("抽到的卡牌", "the drawn card"),
        "FighterQuery": _p("斗士单位", "a fighter"),
        "InEnvironmentQuery": _p("场地上的", "on an environment"),
        "InHandQuery": _p("手牌中的", "in hand"),
        "InLaneQuery": _p("行内的", "in a lane"),
        "InOneTimeEffectZoneQuery": _p("一次性效果区的", "in the one-time effect zone"),
        "InUnopposedLaneQuery": _p("无对手的行中的", "in an unopposed lane"),
        "IsActiveQuery": _p("激活状态的", "active"),
        "IsAliveQuery": _p("存活状态的", "alive"),
        "LastLaneOfSelfQuery": _p("自身的最后一行", "self's last lane"),
        "OriginalTargetCardGuidQuery": _p("原始目标卡牌", "the original target card"),
        "SameFactionQuery": _p("同阵营的", "same faction"),
        "SameLaneAsTargetQuery": _p("与目标同行的", "same lane as the target"),
        "SameLaneQuery": _p("同一行的", "same lane"),
        "SourceQuery": _p("来源", "the source"),
        "SpringboardedOnSelfQuery": _p("跳板作用于自身的", "springboarded onto self"),
        "TargetCardGuidQuery": _p("目标的卡牌", "the target card"),
        "TrickQuery": _p("锦囊/法术", "a trick"),
        "WasInSameLaneAsSelfQuery": _p("曾与自身同行的", "was in the same lane as self"),
        "WillTriggerEffectsQuery": _p("将触发效果的", "will trigger effects"),
        "HasZombiesComponent": _p("僵尸", "a zombie"),
        "HasPlantsComponent": _p("植物", "a plant"),
        "HasPlayerComponent": _p("英雄/玩家", "a hero/player"),
        "HasLaneComponent": _p("整行(地段)", "a lane"),
        "HasSuperpowerComponent": _p("英雄技能", "a superpower"),
        "HasFaceDownComponent": _p("暗置/墓碑", "face-down / gravestone"),
        "HasEnvironmentComponent": _p("场地牌", "an environment"),
        "HasWaterTerrainComponent": _p("水域地形", "water terrain"),
        "HasHighgroundTerrainComponent": _p("高地地形", "heights terrain"),
        "HasUnhealableComponent": _p("不可治疗", "unhealable"),
    }
    if comp_name in query_map:
        return query_map[comp_name]

    # ========= Parameterized =========
    origin_map = {
        "Self": _p("自身", "self"),
        "Source": _p("来源", "source"),
        "Target": _p("目标", "target"),
    }
    side_map = {
        "ToTheLeft": _p("左侧", "left"),
        "ToTheRight": _p("右侧", "right"),
        "Either": _p("任意侧", "either side"),
    }

    if comp_name == "AdjacentLaneQuery":
        side = d.get("Side", "Either")
        origin = d.get("OriginEntityType", "Self")
        side_str = side_map.get(side, _p("相邻", "adjacent"))
        origin_str = origin_map.get(origin, origin_map["Self"])
        return _p(f"{origin_str}的{side_str}相邻行", f"lane adjacent ({side_str}) to {origin_str}")

    if comp_name == "InAdjacentLaneQuery":
        side = d.get("Side", "Either")
        return {
            "ToTheLeft": _p("左侧相邻行", "left adjacent lane"),
            "ToTheRight": _p("右侧相邻行", "right adjacent lane"),
            "Either": _p("相邻行", "adjacent lane"),
        }.get(side, _p("相邻行", "adjacent lane"))

    if comp_name == "InLaneAdjacentToLaneQuery":
        side = d.get("Side", "Either")
        return {
            "ToTheLeft": _p("左侧相邻行的", "in the left-adjacent lane"),
            "ToTheRight": _p("右侧相邻行的", "in the right-adjacent lane"),
        }.get(side, _p("相邻行的", "in an adjacent lane"))

    if comp_name == "InSameLaneQuery":
        origin = d.get("OriginEntityType", "Self")
        origin_str = origin_map.get(origin, origin_map["Self"])
        return _p(f"与{origin_str}同一行的", f"same lane as {origin_str}")

    if comp_name == "LaneOfIndexQuery":
        idx = d.get("LaneIndex", 0)
        return _p(f"第{idx + 1}行的", f"lane #{idx + 1}")

    if comp_name == "SubsetQuery":
        subset = d.get("Subset", "")
        if subset:
            return _p(f"属于【{subset}】标签的", f"with tag/subset [{subset}]")
        return _p("特定标签的", "with a specific tag/subset")

    if comp_name == "SubtypeQuery":
        subtype = d.get("Subtype", 0)
        return _p(f"种族ID为{subtype}的", f"subtype id {subtype}")

    if comp_name == "CardGuidQuery":
        guid = d.get("Guid", 0)
        return _p(f"卡牌GUID为{guid}的", f"card GUID {guid}")

    if comp_name == "QueryMultiplier":
        divider = d.get("Divider", 1)
        inner = parse_query(d.get("Query", {}))
        if inner:
            return _p(f"({inner}) 的数值除以 {divider}", f"({inner}) divided by {divider}")
        return _p(f"查询结果除以 {divider}", f"query result ÷ {divider}")

    if comp_name == "HasComponentQuery" or comp_name in logic_library.HAS_COMPONENT_SHORTCUTS:
        shortcut_labels = {
            "HasZombiesComponent": _p("僵尸", "zombie"),
            "HasPlantsComponent": _p("植物", "plant"),
            "HasLaneComponent": _p("地段(整行)", "lane"),
            "HasPlayerComponent": _p("英雄/玩家", "hero/player"),
            "HasSuperpowerComponent": _p("英雄技能", "superpower"),
            "HasEnvironmentComponent": _p("场地", "environment"),
            "HasFaceDownComponent": _p("暗置/墓碑", "face-down / gravestone"),
            "HasWaterTerrainComponent": _p("水域地形", "water terrain"),
            "HasHighgroundTerrainComponent": _p("高地地形", "heights terrain"),
            "HasUnhealableComponent": _p("不可治疗", "unhealable"),
        }
        if comp_name in shortcut_labels:
            return shortcut_labels[comp_name]
        comp_type = d.get("ComponentType", "")
        short = parse_type_str(comp_type) if comp_type else ""
        if short:
            return _p(f"拥有组件[{short}]", f"has component [{short}]")
        return _p("特定实体", "specific entity")

    if comp_name == "LacksComponentQuery":
        return _p("缺少特定组件的", "lacking a specific component")

    if comp_name == "OnTerrainQuery":
        terrain_type = d.get("TerrainType", "")
        if "Water" in terrain_type:
            return _p("在水域地形上", "on water terrain")
        if "Highground" in terrain_type:
            return _p("在高地地形上", "on heights terrain")
        return _p("在特定地形上", "on specific terrain")

    if comp_name == "OpenLaneQuery":
        faction = d.get("PlayerFactionType", "Plants")
        faction_str = _p("植物", "Plant") if "Plants" in str(faction) else _p("僵尸", "Zombie")
        is_teamup = d.get("IsForTeamupCard", False)
        teamup_str = _p("（可为组队卡）", " (team-up OK)") if is_teamup else ""
        return _p(f"{faction_str}方的空行{teamup_str}", f"open {faction_str} lane{teamup_str}")

    # ========= Comparisons =========
    op_sym = {
        "LessOrEqual": "≤",
        "Equal": "=",
        "GreaterOrEqual": "≥",
    }

    if comp_name == "AttackComparisonQuery":
        op = d.get("ComparisonOperator", "LessOrEqual")
        val = d.get("AttackValue", 0)
        return _p(f"攻击力{op_sym.get(op, '≤')}{val}的", f"attack {op_sym.get(op, '≤')} {val}")

    if comp_name == "HealthComparisonQuery":
        op = d.get("ComparisonOperator", "LessOrEqual")
        val = d.get("HealthValue", 0)
        return _p(f"生命值{op_sym.get(op, '≤')}{val}的", f"health {op_sym.get(op, '≤')} {val}")

    if comp_name == "BlockMeterValueQuery":
        op = d.get("ComparisonOperator", "GreaterOrEqual")
        val = d.get("BlockMeterValue", 0)
        return _p(f"格挡值{op_sym.get(op, '≥')}{val}的", f"block meter {op_sym.get(op, '≥')} {val}")

    if comp_name == "DamageTakenComparisonQuery":
        op = d.get("ComparisonOperator", "GreaterOrEqual")
        val = d.get("DamageTakenValue", 0)
        return _p(f"已受伤害{op_sym.get(op, '≥')}{val}的", f"damage taken {op_sym.get(op, '≥')} {val}")

    if comp_name == "SunCostComparisonQuery":
        op = d.get("ComparisonOperator", "LessOrEqual")
        val = d.get("SunCost", 0)
        return _p(f"费用{op_sym.get(op, '≤')}{val}的", f"cost {op_sym.get(op, '≤')} {val}")

    if comp_name == "SunCostPlusNComparisonQuery":
        op = d.get("ComparisonOperator", "Equal")
        val = d.get("AdditionalCost", 0)
        return _p(f"费用+{val}{op_sym.get(op, '=')}比较的", f"cost + {val} {op_sym.get(op, '=')}")

    if comp_name == "SunCounterComparisonQuery":
        op = d.get("ComparisonOperator", "GreaterOrEqual")
        val = d.get("SunCounterValue", 0)
        return _p(f"阳光计数器{op_sym.get(op, '≥')}{val}的", f"sun counter {op_sym.get(op, '≥')} {val}")

    if comp_name == "TurnCountQuery":
        op = d.get("ComparisonOperator", "GreaterOrEqual")
        val = d.get("TurnCount", 0)
        return _p(f"回合数{op_sym.get(op, '≥')}{val}的", f"turn count {op_sym.get(op, '≥')} {val}")

    return ""


def translate_entities_to_text(entities):
    if not entities:
        try:
            import i18n
            return i18n.t("logic.empty_desc")
        except Exception:
            return _p(
                "暂无技能配置。\n(请在左侧双击组件添加，或在上方新建技能组)",
                "No abilities yet.\n(Double-click palette items or create an ability group)",
            )

    descriptions = []
    for i, entity in enumerate(entities):
        comps = entity.get("components", [])
        trigger_actions, trigger_targets, effects, targets, conditions = [], [], [], [], []

        for comp in comps:
            raw_type = comp.get("$type", "")
            d = comp.get("$data", {}) or {}
            comp_name = logic_library.resolve_node_id_from_type(raw_type, d) or \
                        normalize_engine_type_name(parse_type_str(raw_type))

            # ========= Triggers =========
            if comp_name == "PlayTrigger":
                trigger_actions.append(_p("打出", "is played"))
            elif comp_name == "DiscardFromPlayTrigger":
                trigger_actions.append(_p("被消灭/离场", "is destroyed / leaves play"))
            elif comp_name == "BuffTrigger":
                trigger_actions.append(_p("获得属性提升", "is buffed"))
            elif comp_name == "DamageTrigger":
                trigger_actions.append(_p("受到伤害", "takes damage"))
            elif comp_name == "HealTrigger":
                trigger_actions.append(_p("治疗", "is healed"))
            elif comp_name == "DrawCardTrigger":
                trigger_actions.append(_p("抽牌", "draws a card"))
            elif comp_name == "DrawCardFromSubsetTrigger":
                trigger_actions.append(_p("从特定子集抽牌", "draws from a subset"))
            elif comp_name == "EnterBoardTrigger":
                trigger_actions.append(_p("进场", "enters the board"))
            elif comp_name == "ExtraAttackTrigger":
                trigger_actions.append(_p("额外攻击", "makes an extra attack"))
            elif comp_name == "TurnStartTrigger":
                trigger_actions.append(_p("回合开始", "turn starts"))
            elif comp_name == "CombatEndTrigger":
                trigger_actions.append(_p("战斗结束", "combat ends"))
            elif comp_name == "LaneCombatEndTrigger":
                trigger_actions.append(_p("单路战斗结束", "lane combat ends"))
            elif comp_name == "LaneCombatStartTrigger":
                trigger_actions.append(_p("单路战斗开始", "lane combat starts"))
            elif comp_name == "MoveTrigger":
                trigger_actions.append(_p("移动", "moves"))
            elif comp_name == "ReturnToHandTrigger":
                trigger_actions.append(_p("返回手牌", "returns to hand"))
            elif comp_name == "RevealTrigger":
                trigger_actions.append(_p("揭示", "is revealed"))
            elif comp_name == "RevealPhaseEndTrigger":
                trigger_actions.append(_p("揭示阶段结束", "reveal phase ends"))
            elif comp_name == "SlowedTrigger":
                trigger_actions.append(_p("被冰冻", "is frozen"))
            elif comp_name == "SurprisePhaseStartTrigger":
                trigger_actions.append(_p("奇袭阶段开始", "surprise phase starts"))
            elif comp_name == "DestroyCardTrigger":
                trigger_actions.append(_p("消灭卡牌", "destroys a card"))

            # ========= Filters =========
            elif comp_name in ("TriggerTargetFilter", "TriggerSourceFilter"):
                q = parse_query(d.get("Query", {}))
                if q:
                    trigger_targets.append(q)
            elif comp_name == "SelfEntityFilter":
                q = parse_query(d.get("Query", {}))
                if q:
                    trigger_targets.append(_p(f"自身满足【{q}】", f"self matching ({q})"))
            elif comp_name == "PlayerInfoCondition":
                faction = d.get("Faction", "Plants")
                faction_str = _p("植物", "Plant") if faction == "Plants" else _p("僵尸", "Zombie")
                q = parse_query(d.get("Query", {}))
                if q:
                    trigger_targets.append(
                        _p(f"{faction_str}方满足【{q}】", f"{faction_str} side matching ({q})")
                    )
                else:
                    trigger_targets.append(_p(f"{faction_str}方", f"{faction_str} side"))
            elif comp_name == "QueryEntityCondition":
                eval_type = d.get("ConditionEvaluationType", "All")
                eval_str = (
                    _p("全部满足", "all") if eval_type == "All" else _p("任意满足", "any")
                )
                trigger_targets.append(
                    _p(f"实体条件判断({eval_str})", f"entity condition ({eval_str})")
                )

            # ========= Limits =========
            elif comp_name == "OncePerGameCondition":
                conditions.append(_p("每局游戏只能触发一次", "once per game"))
            elif comp_name == "OncePerTurnCondition":
                conditions.append(_p("每回合只能触发一次", "once per turn"))
            elif comp_name == "PersistsAfterTransform":
                conditions.append(_p("变形后保留此技能", "persists after transform"))

            # ========= Targets =========
            elif comp_name in ("PrimaryTargetFilter", "SecondaryTargetFilter"):
                sel = d.get("SelectionType", "All")
                num = d.get("NumTargets", 0)
                query_str = parse_query(d.get("Query", {})) or _p("目标", "target")
                if sel == "Manual":
                    targets.append(
                        _p(
                            f"玩家手动选择的 1 个【{query_str}】",
                            f"1 player-chosen [{query_str}]",
                        )
                    )
                elif sel == "Random":
                    targets.append(
                        _p(
                            f"随机选择的 {num} 个【{query_str}】",
                            f"{num} random [{query_str}]",
                        )
                    )
                else:
                    targets.append(_p(f"所有【{query_str}】", f"all [{query_str}]"))

                if d.get("AdditionalTargetType") == "Query":
                    targets.append(
                        _p("（额外目标条件已启用）", "(additional target query on)")
                    )

            # ========= Effects =========
            elif comp_name == "DamageEffect":
                effects.append(
                    _p(
                        f"造成 {d.get('DamageAmount', 0)} 点伤害",
                        f"deal {d.get('DamageAmount', 0)} damage",
                    )
                )

            elif comp_name == "BuffEffect":
                dur = (
                    _p("永久", "permanently")
                    if d.get("BuffDuration", "Permanent") == "Permanent"
                    else _p("本回合", "this turn")
                )
                try:
                    effects.append(
                        _p(
                            f"{dur}获得 {int(d.get('AttackAmount', 0)):+d} 攻击力 / "
                            f"{int(d.get('HealthAmount', 0)):+d} 生命值",
                            f"{dur} gain {int(d.get('AttackAmount', 0)):+d} attack / "
                            f"{int(d.get('HealthAmount', 0)):+d} health",
                        )
                    )
                except (ValueError, TypeError):
                    effects.append(_p(f"{dur}获得属性改变", f"{dur} change stats"))

            elif comp_name == "DestroyCardEffect":
                effects.append(_p("将其直接消灭", "destroy it"))

            elif comp_name == "AttackInLaneEffectDescriptor":
                effects.append(
                    _p(
                        f"对本行造成 {d.get('DamageAmount', 0)} 点伤害",
                        f"deal {d.get('DamageAmount', 0)} damage to the lane",
                    )
                )

            elif comp_name == "ChargeBlockMeterEffectDescriptor":
                effects.append(
                    _p(
                        f"充能格挡值 {d.get('ChargeAmount', 0)}",
                        f"charge block meter by {d.get('ChargeAmount', 0)}",
                    )
                )

            elif comp_name == "CopyCardEffectDescriptor":
                parts = []
                if d.get("GrantTeamup"):
                    parts.append(_p("赋予组队能力", "grant team-up"))
                if d.get("ForceFaceDown"):
                    parts.append(_p("强制暗置", "force face-down"))
                if d.get("CreateInFront"):
                    parts.append(_p("在身前创建", "create in front"))
                extra = f"({', '.join(parts)})" if parts else ""
                effects.append(_p(f"复制卡牌{extra}", f"copy card{extra}"))

            elif comp_name == "CopyStatsEffect":
                effects.append(_p("复制目标的属性数值", "copy the target's stats"))

            elif comp_name == "CreateCardEffect":
                face_down = (
                    _p("以墓碑/潜行方式", "face-down / gravestone ")
                    if d.get("ForceFaceDown")
                    else ""
                )
                effects.append(
                    _p(
                        f"{face_down}召唤卡牌 ID:{d.get('CardGuid', 0)}",
                        f"{face_down}create card ID:{d.get('CardGuid', 0)}",
                    )
                )

            elif comp_name == "CreateCardInDeckEffect":
                effects.append(
                    _p(
                        f"将 {d.get('AmountToCreate', 1)} 张 ID 为 {d.get('CardGuid', 0)} 的卡牌洗入牌库",
                        f"shuffle {d.get('AmountToCreate', 1)} card(s) ID {d.get('CardGuid', 0)} into the deck",
                    )
                )

            elif comp_name == "CreateCardFromSubsetEffectDescriptor":
                face_down = _p("（强制暗置）", " (face-down)") if d.get("ForceFaceDown") else ""
                effects.append(
                    _p(f"从指定子集生成卡牌{face_down}", f"create card from subset{face_down}")
                )

            elif comp_name == "TransformIntoCardFromSubsetEffectDescriptor":
                effects.append(
                    _p("变身为指定子集中的卡牌", "transform into a card from the subset")
                )

            elif comp_name == "DrawCardEffect":
                effects.append(
                    _p(
                        f"抽 {d.get('DrawAmount', 1)} 张牌",
                        f"draw {d.get('DrawAmount', 1)} card(s)",
                    )
                )

            elif comp_name == "DrawCardFromSubsetEffect":
                effects.append(
                    _p(
                        f"从指定子集中抽 {d.get('DrawAmount', 1)} 张牌",
                        f"draw {d.get('DrawAmount', 1)} card(s) from subset",
                    )
                )

            elif comp_name == "ExtraAttackEffect":
                effects.append(_p("获得额外一次攻击机会", "gain an extra attack"))

            elif comp_name == "GainSunEffect":
                act_time = (
                    _p("立即", "immediately")
                    if d.get("ActivationTime") == "Immediate"
                    else _p("下回合", "next turn")
                )
                effects.append(
                    _p(
                        f"{act_time}获得 {d.get('Amount', 0)} 点阳光/脑子",
                        f"{act_time} gain {d.get('Amount', 0)} sun/brains",
                    )
                )

            elif comp_name == "GrantAbilityEffect":
                ability = localization.get_enum_name(
                    d.get("GrantableAbilityType"), d.get("GrantableAbilityType")
                )
                dur = (
                    _p("永久", "permanently")
                    if d.get("Duration") == "Permanent"
                    else _p("本回合", "this turn")
                )
                val_note = ""
                if d.get("GrantableAbilityType") == "Untrickable":
                    if d.get("AbilityValue") == 1:
                        val_note = _p(" (免疫植物)", " (vs plants)")
                    elif d.get("AbilityValue") == 2:
                        val_note = _p(" (免疫僵尸)", " (vs zombies)")
                effects.append(
                    _p(
                        f"{dur}赋予技能【{ability}】{val_note}",
                        f"{dur} grant [{ability}]{val_note}",
                    )
                )

            elif comp_name == "GrantTriggeredAbilityEffectDescriptor":
                guid = d.get("AbilityGuid", 0)
                val_type = d.get("AbilityValueType", "None")
                val_amount = d.get("AbilityValueAmount", 0)
                if val_type == "Damage":
                    effects.append(
                        _p(
                            f"赋予触发能力 GUID:{guid}，伤害值 {val_amount}",
                            f"grant triggered ability GUID:{guid}, damage {val_amount}",
                        )
                    )
                else:
                    effects.append(
                        _p(
                            f"赋予触发能力 GUID:{guid}",
                            f"grant triggered ability GUID:{guid}",
                        )
                    )

            elif comp_name == "HealEffect":
                effects.append(
                    _p(
                        f"治疗 {d.get('HealAmount', 0)} 点生命值",
                        f"heal {d.get('HealAmount', 0)}",
                    )
                )

            elif comp_name == "HeroHealthMultiplier":
                faction = d.get("Faction", "Plants")
                faction_str = _p("植物", "Plant") if faction == "Plants" else _p("僵尸", "Zombie")
                divider = d.get("Divider", 1)
                effects.append(
                    _p(
                        f"{faction_str}英雄血量变为原来的 1/{divider}",
                        f"{faction_str} hero health becomes 1/{divider}",
                    )
                )

            elif comp_name == "ModifySunCostEffect":
                dur = (
                    _p("永久", "permanently")
                    if d.get("BuffDuration") == "Permanent"
                    else _p("本回合", "this turn")
                )
                amount = d.get("SunCostAmount", d.get("SunCost", 0))
                effects.append(
                    _p(
                        f"{dur}使卡牌花费改变 {amount}",
                        f"{dur} change cost by {amount}",
                    )
                )

            elif comp_name == "MixedUpGravediggerEffectDescriptor":
                effects.append(_p("触发掘墓人效果", "trigger gravedigger mix-up"))

            elif comp_name == "MoveCardToLanesEffectDescriptor":
                effects.append(_p("移动卡牌到指定行", "move card to target lane(s)"))

            elif comp_name == "ReturnToHandEffect":
                effects.append(_p("将其弹回手牌", "return it to hand"))

            elif comp_name == "SetStatEffect":
                stat = d.get("StatType", "Health")
                stat_str = {
                    "Attack": _p("攻击力", "attack"),
                    "Health": _p("生命值", "health"),
                    "SunCost": _p("费用", "cost"),
                }.get(stat, stat)
                op = _p("增加", "increase by") if d.get("ModifyOperation") == "Add" else _p("重置为", "set to")
                val = d.get("Value", 0)
                effects.append(
                    _p(f"将{stat_str}{op} {val}", f"{op} {stat_str} {val}")
                )

            elif comp_name == "SlowEffect":
                effects.append(_p("冰冻目标", "freeze (Slow) the target"))

            elif comp_name == "SunGainedMultiplier":
                faction = d.get("Faction", "Plants")
                faction_str = _p("植物", "Plant") if faction == "Plants" else _p("僵尸", "Zombie")
                divider = d.get("Divider", 1)
                effects.append(
                    _p(
                        f"{faction_str}方获得的阳光变为原来的 1/{divider}",
                        f"{faction_str} sun gained becomes 1/{divider}",
                    )
                )

            elif comp_name == "TargetAttackMultiplier":
                effects.append(
                    _p(
                        f"攻击力变为 {d.get('Divider', 1)} 倍",
                        f"attack becomes ×{d.get('Divider', 1)}",
                    )
                )

            elif comp_name == "TargetHealthMultiplier":
                effects.append(
                    _p(
                        f"生命值变为 {d.get('Divider', 1)} 倍",
                        f"health becomes ×{d.get('Divider', 1)}",
                    )
                )

            elif comp_name == "TurnIntoGravestoneEffectDescriptor":
                effects.append(_p("转化为墓碑", "turn into a gravestone"))

            elif comp_name == "EffectValueDescriptor":
                mapping = d.get("MappingType", "DamageToHeal")
                if mapping == "DamageToHeal":
                    effects.append(
                        _p("数值映射：伤害量 → 治疗量", "map: damage amount → heal amount")
                    )
                elif mapping == "HealToDamage":
                    effects.append(
                        _p("数值映射：治疗量 → 伤害量", "map: heal amount → damage amount")
                    )
                else:
                    effects.append(_p("数值映射", "value mapping"))

        # ========= Assemble =========
        if conditions:
            joiner = ", " if _is_en() else "，"
            cond_str = _p(
                f"【限制】{joiner.join(conditions)}。",
                f"[Limit] {joiner.join(conditions)}. ",
            )
        else:
            cond_str = ""

        if trigger_actions:
            tgt = (
                (" / " if _is_en() else "、").join(trigger_targets)
                if trigger_targets
                else _p("此卡牌", "this card")
            )
            act_join = " or " if _is_en() else "或"
            trigger_str = _p(
                f"当【{tgt}】{act_join.join(trigger_actions)}时，",
                f"When [{tgt}] {act_join.join(trigger_actions)}, ",
            )
        else:
            trigger_str = _p("【被动生效】", "[Passive] ")

        if targets:
            tgt_join = " / " if _is_en() else "、"
            target_str = _p(
                f"对 {tgt_join.join(targets)}，",
                f"to {tgt_join.join(targets)}, ",
            )
        else:
            target_str = ""

        if effects:
            effect_str = (
                f"{'; '.join(effects)}."
                if _is_en()
                else f"{'、'.join(effects)}。"
            )
        else:
            effect_str = _p("未配置实际效果。", "No effect configured.")

        descriptions.append(
            _p(
                f"🔹 技能组 {i + 1}：\n{cond_str}{trigger_str}{target_str}{effect_str}",
                f"🔹 Ability group {i + 1}:\n{cond_str}{trigger_str}{target_str}{effect_str}",
            )
        )

    return "\n\n".join(descriptions)
