# card_model.py
import uuid
import config
from typing import Dict, Any, List
from constants import (
    build_type_str, parse_type_str, COMP_ABILITY_MAP,
    TRIGGERED_ABILITY_GUIDS, DUAL_TRACK_ABILITIES,
)
from core_utils import safe_get


class CardModel:
    def __init__(self):
        """完全干净的初始化状态"""
        self.guid = 900000001
        self.prefab_name = str(uuid.uuid4())
        self.base_id = "Base"
        self.faction = "Plants"
        self.color = "Guardian"
        self.rarity_key = 4
        self.set_name = "Gold"
        self.set_and_rarity_key = "ShowCheer"
        self.crafting_buy = 50
        self.crafting_sell = 15

        self.cost = 1
        self.has_attack = True
        self.has_health = True
        self.attack = 1
        self.health = 1

        self.ignore_deck_limit = False
        self.is_power = False
        self.is_primary_power = False

        self.is_trick = False
        self.is_surprise = False
        self.is_environment = False
        self.is_board_ability = False

        self.logic_subtypes = []
        self.display_subtypes = []
        self.logic_tags = []
        self.display_tags = []

        self.components_abilities = {}
        self.triggered_abilities = []
        self.root_special_abilities = []
        self.logic_entities = []

        self.subtype_affinities = []
        self.subtype_affinity_weights = []
        self.tag_affinities = []
        self.tag_affinity_weights = []
        self.card_affinities = []
        self.card_affinity_weights = []

    def _create_counter_component(self, type_name: str, value: int = 0) -> Dict[str, Any]:
        """构建底层计数器结构"""
        return {
            "$type": build_type_str(type_name),
            "$data": {
                "Counters": {
                    "IsPersistent": True,
                    "Counters": [{"SourceId": -1, "Duration": 0, "Value": value}]
                }
            }
        }

    def sync_display_abilities(self):
        """
        将组件能力 / 触发能力 与 UI special_abilities 做轻量同步（只增不强制删，避免覆盖用户自定义标签）。
        """
        root = set(self.root_special_abilities or [])

        for key in DUAL_TRACK_ABILITIES:
            if key in self.components_abilities:
                root.add(key)

        for item in self.triggered_abilities or []:
            g = item.get("g")
            if g == TRIGGERED_ABILITY_GUIDS.get("DoubleStrike"):
                root.add("Repeater")
            elif g == TRIGGERED_ABILITY_GUIDS.get("Overshoot"):
                root.add("Overshoot")

        self.root_special_abilities = list(root)

    def _generate_board_ability_dict(self) -> Dict[str, Any]:
        """场景能力固定模板"""
        components = [
            {"$type": build_type_str("Card"), "$data": {"Guid": self.guid}},
            {"$type": build_type_str("BoardAbility"), "$data": {}},
            {"$type": build_type_str("SunCost"), "$data": {"SunCostValue": {"BaseValue": 0}}},
            {"$type": build_type_str("Rarity"), "$data": {"Value": "R1"}}
        ]

        if self.logic_entities:
            components.append({
                "$type": build_type_str("EffectEntitiesDescriptor"),
                "$data": {"entities": self.logic_entities}
            })

        entity_data = {
            "entity": {"components": components},
            "prefabName": "BoardAbilityView",
            "baseId": "BasePlantOneTimeEffect",
            "color": "0",
            "set": "Board",
            "rarity": 0,
            "setAndRarityKey": None,
            "displayHealth": 0,
            "displayAttack": 0,
            "displaySunCost": 0,
            "faction": "All",
            "ignoreDeckLimit": False,
            "isPower": False,
            "isPrimaryPower": False,
            "isFighter": False,
            "isEnv": False,
            "isAquatic": False,
            "isTeamup": False,
            "subtypes": [],
            "tags": [],
            "subtype_affinities": [],
            "subtype_affinity_weights": [],
            "tag_affinities": [],
            "tag_affinity_weights": [],
            "card_affinities": [],
            "card_affinity_weights": [],
            "usable": True,
            "special_abilities": []
        }
        return {str(self.guid): entity_data}

    def generate_json_dict(self) -> Dict[str, Any]:
        """序列化：Model -> JSON Dict"""
        if self.base_id == "BoardAbility":
            return self._generate_board_ability_dict()

        rarity_info = config.RARITIES.get(self.rarity_key, {"value": "R0"})

        # 固定顺序组装，避免 insert 导致仅血量时顺序错乱
        components: List[Dict[str, Any]] = [
            {"$type": build_type_str("Card"), "$data": {"Guid": self.guid}},
        ]
        if self.has_attack:
            components.append({
                "$type": build_type_str("Attack"),
                "$data": {"AttackValue": {"BaseValue": self.attack}}
            })
        if self.has_health:
            components.append({
                "$type": build_type_str("Health"),
                "$data": {"MaxHealth": {"BaseValue": self.health}, "CurrentDamage": 0}
            })
        components.append({
            "$type": build_type_str("SunCost"),
            "$data": {"SunCostValue": {"BaseValue": self.cost}}
        })
        components.append({"$type": build_type_str(self.faction), "$data": {}})
        components.append({
            "$type": build_type_str("Rarity"),
            "$data": {"Value": rarity_info["value"]}
        })

        if self.logic_subtypes:
            components.append({
                "$type": build_type_str("Subtypes"),
                "$data": {"subtypes": self.logic_subtypes}
            })
        if self.logic_tags:
            components.append({
                "$type": build_type_str("Tags"),
                "$data": {"tags": self.logic_tags}
            })

        if self.is_trick:
            components.append({"$type": build_type_str("Burst"), "$data": {}})
        if self.is_surprise:
            components.append({"$type": build_type_str("Surprise"), "$data": {}})
        if self.is_board_ability:
            components.append({"$type": build_type_str("BoardAbility"), "$data": {}})
        if self.is_environment:
            components.append({"$type": build_type_str("Environment"), "$data": {}})
        if self.is_power:
            components.append({"$type": build_type_str("Superpower"), "$data": {}})
        if self.is_primary_power:
            components.append({"$type": build_type_str("PrimarySuperpower"), "$data": {}})

        if self.triggered_abilities:
            components.append({
                "$type": build_type_str("GrantedTriggeredAbilities"),
                "$data": {"a": self.triggered_abilities}
            })

        for ability_key, param_val in self.components_abilities.items():
            if ability_key in ["Multishot", "AttacksInAllLanes", "PlaysFaceDown"]:
                components.append({"$type": build_type_str(ability_key), "$data": {}})
            elif ability_key == "SplashDamage":
                components.append({
                    "$type": build_type_str("SplashDamage"),
                    "$data": {"DamageAmount": param_val}
                })
            elif ability_key in ["Aquatic", "Truestrike", "Strikethrough", "Deadly", "Frenzy"]:
                components.append(self._create_counter_component(ability_key, 0))
            elif ability_key == "AttackOverride":
                components.append(self._create_counter_component(ability_key, 2))
            elif ability_key == "Untrickable":
                components.append(self._create_counter_component(ability_key, param_val))
            elif ability_key == "Armor":
                components.append({
                    "$type": build_type_str("Armor"),
                    "$data": {"ArmorAmount": {"BaseValue": param_val}}
                })
            elif ability_key == "Teamup":
                components.append(self._create_counter_component("Teamup", 0))
                if param_val is True:
                    components.append({"$type": build_type_str("CreateInFront"), "$data": {}})

        if self.logic_entities:
            components.append({
                "$type": build_type_str("EffectEntitiesDescriptor"),
                "$data": {"entities": self.logic_entities}
            })

        entity_data = {
            "entity": {"components": components},
            "prefabName": self.prefab_name,
            "baseId": self.base_id,
            "color": self.color,
            "set": self.set_name,
            "rarity": self.rarity_key,
            "setAndRarityKey": self.set_and_rarity_key,
            "craftingBuy": self.crafting_buy,
            "craftingSell": self.crafting_sell,
            "displaySunCost": self.cost,
            "faction": self.faction,
            "ignoreDeckLimit": self.ignore_deck_limit,
            "isPower": self.is_power,
            "isPrimaryPower": self.is_primary_power,
            "isFighter": "OneTimeEffect" not in self.base_id and "Environment" not in self.base_id,
            "isEnv": "Environment" in self.base_id,
            "isAquatic": "Aquatic" in self.components_abilities,
            "isTeamup": "Teamup" in self.components_abilities,
            "subtypes": self.display_subtypes,
            "tags": self.display_tags,
            "subtype_affinities": self.subtype_affinities,
            "subtype_affinity_weights": self.subtype_affinity_weights,
            "tag_affinities": self.tag_affinities,
            "tag_affinity_weights": self.tag_affinity_weights,
            "card_affinities": self.card_affinities,
            "card_affinity_weights": self.card_affinity_weights,
            "usable": True,
            "special_abilities": self.root_special_abilities
        }

        if self.has_health:
            entity_data["displayHealth"] = self.health
        if self.has_attack:
            entity_data["displayAttack"] = self.attack

        return {str(self.guid): entity_data}

    @classmethod
    def from_json(cls, data: dict) -> 'CardModel':
        """反向解析引擎"""
        instance = cls()
        instance.prefab_name = data.get("prefabName", str(uuid.uuid4()))
        instance.base_id = data.get("baseId", "Base")
        instance.color = data.get("color", "Guardian")
        instance.set_name = data.get("set", "Gold")
        instance.rarity_key = data.get("rarity", 4)
        instance.set_and_rarity_key = data.get("setAndRarityKey", "Bloom_Common")
        instance.crafting_buy = data.get("craftingBuy", 50)
        instance.crafting_sell = data.get("craftingSell", 15)
        instance.cost = data.get("displaySunCost", 1)

        instance.faction = data.get("faction", "Plants")
        instance.ignore_deck_limit = data.get("ignoreDeckLimit", False)

        instance.is_power = data.get("isPower", False)
        instance.is_primary_power = data.get("isPrimaryPower", False)

        instance.display_subtypes = data.get("subtypes", [])
        instance.display_tags = data.get("tags", [])
        instance.root_special_abilities = list(data.get("special_abilities", []) or [])

        instance.subtype_affinities = data.get("subtype_affinities", [])
        instance.subtype_affinity_weights = data.get("subtype_affinity_weights", [])
        instance.tag_affinities = data.get("tag_affinities", [])
        instance.tag_affinity_weights = data.get("tag_affinity_weights", [])
        instance.card_affinities = data.get("card_affinities", [])
        instance.card_affinity_weights = data.get("card_affinity_weights", [])

        instance.has_attack, instance.has_health = False, False
        components = safe_get(data, "entity", "components", default=[]) or []

        # 两遍扫描：先收集标记类，避免 Teamup / CreateInFront 顺序问题
        has_teamup = False
        create_in_front = False

        for comp in components:
            ctype = comp.get("$type", "")
            cdata = comp.get("$data", {}) or {}
            comp_name = parse_type_str(ctype)

            if comp_name == "Card":
                instance.guid = cdata.get("Guid", instance.guid)
            elif comp_name == "Attack":
                instance.has_attack = True
                instance.attack = safe_get(cdata, "AttackValue", "BaseValue", default=1)
            elif comp_name == "Health":
                instance.has_health = True
                instance.health = safe_get(cdata, "MaxHealth", "BaseValue", default=1)
            elif comp_name == "SunCost":
                cost_val = safe_get(cdata, "SunCostValue", "BaseValue", default=None)
                if cost_val is not None:
                    instance.cost = cost_val
            elif comp_name == "Subtypes":
                instance.logic_subtypes = cdata.get("subtypes", [])
            elif comp_name == "Tags":
                instance.logic_tags = cdata.get("tags", [])
            elif comp_name == "EffectEntitiesDescriptor":
                instance.logic_entities = cdata.get("entities", [])
            elif comp_name == "Plants":
                instance.faction = "Plants"
            elif comp_name == "Zombies":
                instance.faction = "Zombies"
            elif comp_name == "Burst":
                instance.is_trick = True
            elif comp_name == "Surprise":
                instance.is_surprise = True
            elif comp_name == "Environment":
                instance.is_environment = True
            elif comp_name == "BoardAbility":
                instance.is_board_ability = True
            elif comp_name == "Superpower":
                instance.is_power = True
            elif comp_name == "PrimarySuperpower":
                instance.is_primary_power = True
            elif comp_name == "SplashDamage":
                instance.components_abilities["SplashDamage"] = cdata.get("DamageAmount", 1)
            elif comp_name == "Armor":
                instance.components_abilities["Armor"] = safe_get(
                    cdata, "ArmorAmount", "BaseValue", default=1
                )
            elif comp_name == "Untrickable":
                instance.components_abilities["Untrickable"] = safe_get(
                    cdata, "Counters", "Counters", 0, "Value", default=1
                )
            elif comp_name == "Teamup":
                has_teamup = True
            elif comp_name == "CreateInFront":
                create_in_front = True
            elif comp_name == "GrantedTriggeredAbilities":
                instance.triggered_abilities = cdata.get("a", []) or []
            elif comp_name in COMP_ABILITY_MAP:
                ability_key = COMP_ABILITY_MAP[comp_name]
                if ability_key not in ("SplashDamage", "Armor", "Untrickable", "Teamup"):
                    instance.components_abilities[ability_key] = True

        if has_teamup or create_in_front:
            instance.components_abilities["Teamup"] = bool(create_in_front)

        if instance.is_board_ability and instance.base_id == "BasePlantOneTimeEffect" and data.get("set") == "Board":
            instance.base_id = "BoardAbility"

        return instance
