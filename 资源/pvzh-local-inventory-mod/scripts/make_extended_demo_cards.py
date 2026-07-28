#!/usr/bin/env python3
"""
Build card_data_5 with multiple extended custom cards for load testing.

Clones official templates and mutates many top-level + component fields so
they are easy to tell apart in collection UI.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import UnityPy
from UnityPy.enums import ClassIDType


def script_to_text(script) -> str:
    if isinstance(script, str):
        return script
    if isinstance(script, bytes):
        return script.decode("utf-8")
    return bytes(script).decode("utf-8")


def load_bundle(path: Path):
    env = UnityPy.load(str(path))
    for obj in env.objects:
        if obj.type != ClassIDType.TextAsset and obj.type.name != "TextAsset":
            continue
        data = obj.read()
        cards = json.loads(script_to_text(data.m_Script))
        return env, data, cards
    raise RuntimeError("no TextAsset")


def set_guid(card: dict, new_id: int) -> None:
    for comp in card.get("entity", {}).get("components", []):
        typ = comp.get("$type") or ""
        if ".Card," in typ:
            comp.setdefault("$data", {})["Guid"] = int(new_id)


def set_stat_components(
    card: dict,
    atk: int | None,
    hp: int | None,
    cost: int | None,
    rarity_code: str | None = None,
) -> None:
    for comp in card.get("entity", {}).get("components", []):
        typ = comp.get("$type") or ""
        data = comp.setdefault("$data", {})
        if atk is not None and ".Attack," in typ:
            data.setdefault("AttackValue", {})["BaseValue"] = atk
        if hp is not None and ".Health," in typ:
            data.setdefault("MaxHealth", {})["BaseValue"] = hp
            data["CurrentDamage"] = 0
        if cost is not None and ".SunCost," in typ:
            data.setdefault("SunCostValue", {})["BaseValue"] = cost
        # Component Rarity uses codes like "R0".."R5"; top-level uses int 0..5
        if rarity_code is not None and ".Rarity," in typ:
            data["Value"] = rarity_code

def append_tag(card: dict, tag: str) -> None:
    for comp in card.get("entity", {}).get("components", []):
        typ = comp.get("$type") or ""
        if ".Tags," in typ:
            tags = list(comp.setdefault("$data", {}).get("tags") or [])
            if tag not in tags:
                tags.append(tag)
            comp["$data"]["tags"] = tags
    if isinstance(card.get("tags"), list) and tag not in card["tags"]:
        card["tags"] = list(card["tags"]) + [tag]


def clone_extended(
    cards: dict,
    *,
    from_id: int,
    to_id: int,
    prefab: str,
    atk: int,
    hp: int,
    cost: int,
    rarity: int,
    rarity_code: str,
    color: str | None = None,
    faction: str | None = None,
    set_name: str | None = None,
    is_teamup: bool | None = None,
    is_aquatic: bool | None = None,
    subtypes: list | None = None,
    crafting_buy: int | None = None,
    set_and_rarity_key: str | None = None,
    extra_tags: list[str] | None = None,
) -> dict:
    src = str(from_id)
    if src not in cards:
        raise KeyError(from_id)
    card = copy.deepcopy(cards[src])
    set_guid(card, to_id)
    card["prefabName"] = prefab
    card["displayAttack"] = atk
    card["displayHealth"] = hp
    card["displaySunCost"] = cost
    card["rarity"] = int(rarity)
    if color is not None:
        card["color"] = color
    if faction is not None:
        card["faction"] = faction
    if set_name is not None:
        card["set"] = set_name
    if is_teamup is not None:
        card["isTeamup"] = bool(is_teamup)
    if is_aquatic is not None:
        card["isAquatic"] = bool(is_aquatic)
    if subtypes is not None:
        # top-level uses string subtype names (e.g. "Peashooter")
        card["subtypes"] = list(subtypes)
    if crafting_buy is not None:
        card["craftingBuy"] = crafting_buy
    if set_and_rarity_key is not None:
        card["setAndRarityKey"] = set_and_rarity_key
    elif "setAndRarityKey" in card:
        card["setAndRarityKey"] = f"Mod_{rarity_code}"
    set_stat_components(card, atk, hp, cost, rarity_code=rarity_code)
    append_tag(card, f"modcard{to_id}")
    for t in extra_tags or []:
        append_tag(card, t)
    cards[str(to_id)] = card
    return card

def save_bundle(env, text_asset, cards: dict, out: Path) -> None:
    text = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
    text_asset.m_Script = text
    text_asset.save()
    out.parent.mkdir(parents=True, exist_ok=True)
    data = None
    for packer in ("lz4", "original", None):
        try:
            data = env.file.save() if packer is None else env.file.save(packer=packer)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"WARN save {packer}: {exc}", file=sys.stderr)
    if data is None:
        raise RuntimeError("save failed")
    out.write_bytes(data)
    print(f"wrote {out} size={out.stat().st_size} cards={len(cards)}")


# Demo set: several real attribute axes (values match official enums)
DEMOS = [
    dict(
        from_id=10,
        to_id=90001,
        prefab="mod-custom-90001-localtest",
        atk=9,
        hp=9,
        cost=1,
        rarity=4,
        rarity_code="R0",
        color="MegaGro",
        faction="Plants",
        set_name="Silver",
        extra_tags=["mod_basic_clone"],
    ),
    dict(
        from_id=1,
        to_id=90002,
        prefab="mod-ext-90002-super-aquatic",
        atk=5,
        hp=5,
        cost=3,
        rarity=2,
        rarity_code="R2",
        color="Guardian",
        faction="Plants",
        set_name="Gold",
        is_aquatic=True,
        subtypes=["Fruit", "Animal"],
        crafting_buy=1000,
        set_and_rarity_key="Mod_SuperRare",
        extra_tags=["mod_extended", "mod_aquatic", "mod_super_rare"],
    ),
    dict(
        from_id=2,
        to_id=90003,
        prefab="mod-ext-90003-zombie-tank",
        atk=2,
        hp=12,
        cost=4,
        rarity=0,
        rarity_code="R3",
        color="Hearty",
        faction="Zombies",
        set_name="Gold",
        is_teamup=False,
        is_aquatic=False,
        subtypes=["Professional"],
        crafting_buy=50,
        set_and_rarity_key="Mod_ZombieTank",
        extra_tags=["mod_extended", "mod_tank", "mod_zombie"],
    ),
    dict(
        from_id=10,
        to_id=90004,
        prefab="mod-ext-90004-glass-cannon",
        atk=8,
        hp=1,
        cost=2,
        rarity=1,
        rarity_code="R1",
        color="Kabloom",
        faction="Plants",
        set_name="Set2",
        subtypes=["Peashooter"],
        crafting_buy=250,
        set_and_rarity_key="Mod_Glass",
        extra_tags=["mod_extended", "mod_glass", "mod_burst"],
    ),
    dict(
        from_id=10,
        to_id=90005,
        prefab="mod-ext-90005-teamup-expensive",
        atk=6,
        hp=6,
        cost=7,
        rarity=5,
        rarity_code="R5",
        color="Solar",
        faction="Plants",
        set_name="Event",
        is_teamup=True,
        is_aquatic=False,
        subtypes=["Flower"],
        crafting_buy=2000,
        set_and_rarity_key="Mod_LegendaryTeamup",
        extra_tags=["mod_extended", "mod_cost7", "mod_teamup", "mod_legendary"],
    ),
]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=Path("reference/samples/card_data_5_device"))
    ap.add_argument("--out", type=Path, default=Path("dist/card_mods/card_data_5"))
    ap.add_argument(
        "--inventory-out",
        type=Path,
        default=Path("dist/card_mods/inventory_extra.json"),
    )
    ap.add_argument(
        "--dump-dir",
        type=Path,
        default=Path("dist/card_mods/extended_cards"),
    )
    args = ap.parse_args()

    env, text_asset, cards = load_bundle(args.src)
    dump_dir = args.dump_dir
    dump_dir.mkdir(parents=True, exist_ok=True)

    owned: dict[str, int] = {}
    for spec in DEMOS:
        card = clone_extended(cards, **spec)
        tid = spec["to_id"]
        owned[str(tid)] = 4
        (dump_dir / f"card_{tid}.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"  + {tid} from {spec['from_id']}: "
            f"atk={spec['atk']} hp={spec['hp']} cost={spec['cost']} "
            f"rarity={spec['rarity']} prefab={spec['prefab']}"
        )

    save_bundle(env, text_asset, cards, args.out)
    inv = {"schemaVersion": 1, "Cards": owned, "Heroes": {}}
    args.inventory_out.write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.inventory_out}: {list(owned.keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
