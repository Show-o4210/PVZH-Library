# constants.py
"""常量定义模块 - 引用主题系统"""

from typing import Dict
from theme_preset import GLASS_QSS, build_qss_from_theme, get_theme, get_theme_list, set_current_theme, get_current_theme

# ================= 基础命名空间 =================
NAMESPACE_ENGINE = "PvZCards.Engine.Components."
NAMESPACE_QUERY = "PvZCards.Engine.Queries."
ASSEMBLY_SUFFIX = ", EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null"

# 触发类能力常用 GUID（与游戏引擎一致）
TRIGGERED_ABILITY_GUIDS = {
    "DoubleStrike": 562,  # 双重攻击 / Repeater UI 标签
    "Overshoot": 564,     # 先攻
}

# 组件能力 ↔ UI special_abilities 双轨可同步的键
DUAL_TRACK_ABILITIES = frozenset({
    "Armor", "AttackOverride", "Deadly", "Frenzy",
    "Strikethrough", "Truestrike", "Untrickable",
})


def build_type_str(comp_name: str, is_query: bool = False) -> str:
    """构建组件类型字符串"""
    prefix = NAMESPACE_QUERY if is_query else NAMESPACE_ENGINE
    return f"{prefix}{comp_name}{ASSEMBLY_SUFFIX}"


def parse_type_str(type_str: str) -> str:
    """从类型字符串中解析出组件名"""
    if not type_str:
        return ""
    return type_str.split(',')[0].split('.')[-1]


def normalize_engine_type_name(type_name: str) -> str:
    """
    将引擎类名归一为逻辑库节点 ID 风格。
    例如 DamageEffectDescriptor -> DamageEffect
    """
    if not type_name:
        return ""
    aliases = {
        "ReturnToHandFromPlayEffectDescriptor": "ReturnToHandEffect",
        "DrawCardFromSubsetEffectDescriptor": "DrawCardFromSubsetEffect",
    }
    if type_name in aliases:
        return aliases[type_name]
    if type_name.endswith("Descriptor"):
        base = type_name[: -len("Descriptor")]
        # CreateCardFromSubsetEffectDescriptor 等保持带 Descriptor 的 node_id
        # 优先：去掉 Descriptor 后的短名（与 NODE_DEF 多数键一致）
        return base
    return type_name


# ================= 独立能力组件映射（1:1，不含触发类） =================
ABILITY_COMP_MAP: Dict[str, str] = {
    "Multishot": "Multishot",
    "AttacksInAllLanes": "AttacksInAllLanes",
    "PlaysFaceDown": "PlaysFaceDown",
    "Aquatic": "Aquatic",
    "Truestrike": "Truestrike",
    "Strikethrough": "Strikethrough",
    "Deadly": "Deadly",
    "Frenzy": "Frenzy",
    "AttackOverride": "AttackOverride",
    "SplashDamage": "SplashDamage",
    "Armor": "Armor",
    "Untrickable": "Untrickable",
    "Teamup": "Teamup",
}

# 组件短名 -> 能力键（仅独立组件；Teamup/CreateInFront 在 from_json 中特殊处理）
COMP_ABILITY_MAP: Dict[str, str] = {v: k for k, v in ABILITY_COMP_MAP.items()}


# ================= 重新导出主题相关函数 =================
__all__ = [
    'GLASS_QSS',
    'build_qss_from_theme',
    'get_theme',
    'get_theme_list',
    'set_current_theme',
    'get_current_theme',
    'build_type_str',
    'parse_type_str',
    'normalize_engine_type_name',
    'ABILITY_COMP_MAP',
    'COMP_ABILITY_MAP',
    'NAMESPACE_ENGINE',
    'NAMESPACE_QUERY',
    'ASSEMBLY_SUFFIX',
    'TRIGGERED_ABILITY_GUIDS',
    'DUAL_TRACK_ABILITIES',
]
