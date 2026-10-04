#!/usr/bin/env python3
"""
Safe card_data variants: clone ONE known-good simple template (official id 10,
same lineage as working 90001) and only change "surface" fields.

Avoids copying complex EffectEntitiesDescriptor / skill trees from other cards,
which often make the client fail to load definitions.
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
        return env, data, json.loads(script_to_text(data.m_Script))
    raise RuntimeError("no TextAsset")


def set_guid(card: dict, new_id: int) -> None:
    for comp in card.get("entity", {}).get("components", []):
        typ = comp.get("$type") or ""
        if ".Card," in typ:
            comp.setdefault("$data", {})["Guid"] = int(new_id)


def set_fighter_stats(card: dict, atk: int, hp: int, cost: int) -> None:
    card["displayAttack"] = atk
    card["displayHealth"] = hp
    card["displaySunCost"] = cost
    for comp in card.get("entity", {}).get("components", []):
        typ = comp.get("$type") or ""
        data = comp.setdefault("$data", {})
        if ".Attack," in typ:
            data.setdefault("AttackValue", {})["BaseValue"] = atk
        elif ".Health," in typ:
            data.setdefault("MaxHealth", {})["BaseValue"] = hp
            data["CurrentDamage"] = 0
        elif ".SunCost," in typ:
            data.setdefault("SunCostValue", {})["BaseValue"] = cost


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


def make_variant(
    base: dict,
    *,
    to_id: int,
    prefab: str,
    atk: int,
    hp: int,
    cost: int,
    faction: str | None = None,
    color: str | None = None,
    rarity: int | None = None,
    set_name: str | None = None,
    is_teamup: bool | None = None,
    is_aquatic: bool | None = None,
    extra_tags: list[str] | None = None,
) -> dict:
    """Deep-copy base card; never touch EffectEntitiesDescriptor / skill trees."""
    card = copy.deepcopy(base)
    set_guid(card, to_id)
    card["prefabName"] = prefab
    set_fighter_stats(card, atk, hp, cost)

    if faction is not None:
        # Top-level only. Do NOT rewrite Plants/Zombies entity components
        # (skill trees / baseId stay exactly as template #10).
        card["faction"] = faction
        if faction == "Zombies":
            card["baseId"] = "BaseZombie"
        elif faction == "Plants":
            card["baseId"] = "Base"

    if color is not None:
        card["color"] = color
    if rarity is not None:
        card["rarity"] = int(rarity)
        # do NOT rewrite component Rarity codes — leave as template to avoid mismatch
    if set_name is not None:
        card["set"] = set_name
    if is_teamup is not None:
        card["isTeamup"] = bool(is_teamup)
    if is_aquatic is not None:
        card["isAquatic"] = bool(is_aquatic)
        # do NOT inject Aquatic component / skills — flag only

    append_tag(card, f"modcard{to_id}")
    for t in extra_tags or []:
        append_tag(card, t)
    return card


# All variants from official #10 only (simple fighter, no fancy triggers in template)
# 90001 = known-good; others = surface field variants only
VARIANTS = [
    dict(
        to_id=90001,
        prefab="mod-custom-90001-localtest",
        atk=9,
        hp=9,
        cost=1,
        faction="Plants",
        color="MegaGro",
        extra_tags=["mod_safe", "mod_base"],
    ),
    dict(
        to_id=90002,
        prefab="mod-safe-90002-zombie-faction",
        atk=9,
        hp=9,
        cost=1,
        faction="Zombies",
        color="Brainy",
        extra_tags=["mod_safe", "mod_faction_zombie"],
    ),
    dict(
        to_id=90003,
        prefab="mod-safe-90003-stats-3-5-2",
        atk=3,
        hp=5,
        cost=2,
        faction="Plants",
        color="Guardian",
        extra_tags=["mod_safe", "mod_stats"],
    ),
    dict(
        to_id=90004,
        prefab="mod-safe-90004-kabloom-burst",
        atk=7,
        hp=2,
        cost=2,
        faction="Plants",
        color="Kabloom",
        rarity=1,
        extra_tags=["mod_safe", "mod_color_kabloom"],
    ),
    dict(
        to_id=90005,
        prefab="mod-safe-90005-hearty-tank",
        atk=1,
        hp=10,
        cost=3,
        faction="Zombies",
        color="Hearty",
        rarity=0,
        extra_tags=["mod_safe", "mod_tank_stats"],
    ),
]


def save_bundle(env, text_asset, cards: dict, out: Path) -> None:
    text = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
    text_asset.m_Script = text
    text_asset.save()
    out.parent.mkdir(parents=True, exist_ok=True)
    data = None
    used = None
    for packer in ("lz4", "original", None):
        try:
            data = env.file.save() if packer is None else env.file.save(packer=packer)
            used = packer
            break
        except Exception as exc:  # noqa: BLE001
            print(f"WARN save {packer}: {exc}", file=sys.stderr)
    if data is None:
        raise RuntimeError("save failed")
    out.write_bytes(data)
    print(f"wrote {out} size={out.stat().st_size} packer={used} cards={len(cards)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=Path("reference/samples/card_data_5_device"))
    ap.add_argument("--out", type=Path, default=Path("dist/card_mods/card_data_5"))
    ap.add_argument(
        "--inventory-out",
        type=Path,
        default=Path("dist/card_mods/inventory_extra.json"),
    )
    ap.add_argument(
        "--template-id",
        type=int,
        default=10,
        help="official card to clone (default 10 = simple peashooter lineage)",
    )
    ap.add_argument(
        "--dump-dir",
        type=Path,
        default=Path("dist/card_mods/safe_variants"),
    )
    args = ap.parse_args()

    env, text_asset, cards = load_bundle(args.src)
    tid = str(args.template_id)
    if tid not in cards:
        print(f"ERROR: template {tid} missing", file=sys.stderr)
        return 1
    base = cards[tid]
    # Strip nothing from skills: keep exact entity skill tree of template #10 for all variants
    print(f"template={tid} components={len(base['entity']['components'])} prefab={base.get('prefabName')}")

    dump_dir = args.dump_dir
    dump_dir.mkdir(parents=True, exist_ok=True)
    owned: dict[str, int] = {}

    for spec in VARIANTS:
        card = make_variant(base, **spec)
        # Sanity: effect tree size unchanged vs template
        n_base = len(json.dumps(base["entity"]))
        n_new = len(json.dumps(card["entity"]))
        # Guid string length difference only (~ few bytes)
        if abs(n_new - n_base) > 80:
            print(
                f"WARN {spec['to_id']}: entity JSON size delta {n_new - n_base} "
                f"(expected ~0 if only Guid/stats in components)",
                file=sys.stderr,
            )
        cards[str(spec["to_id"])] = card
        owned[str(spec["to_id"])] = 4
        (dump_dir / f"card_{spec['to_id']}.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"  + {spec['to_id']}: {spec['atk']}/{spec['hp']}/{spec['cost']} "
            f"faction={spec.get('faction')} color={spec.get('color')} "
            f"prefab={spec['prefab']}"
        )

    save_bundle(env, text_asset, cards, args.out)
    inv = {"schemaVersion": 1, "Cards": owned, "Heroes": {}}
    args.inventory_out.write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")
    print(f"inventory -> {args.inventory_out} ids={list(owned)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
