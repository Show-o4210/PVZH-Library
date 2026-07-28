#!/usr/bin/env python3
"""
Clone a non-basic template (ignoreDeckLimit=false, rarity != basic)
and own them at counts other than 4.

Template default: official #32 (Plants/Smarty, rar=0, 8 simple comps, no Effect tree).
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


def make_variant(base: dict, *, to_id: int, prefab: str, atk: int, hp: int, cost: int, color: str | None = None) -> dict:
    card = copy.deepcopy(base)
    set_guid(card, to_id)
    card["prefabName"] = prefab
    set_fighter_stats(card, atk, hp, cost)
    # Critical: do not inherit basic-card unlimited/locked stack behavior
    card["ignoreDeckLimit"] = False
    if color is not None:
        card["color"] = color
    append_tag(card, f"modcard{to_id}")
    append_tag(card, "mod_countable")
    return card


# Own counts deliberately not 4
VARIANTS = [
    # id, atk, hp, cost, color, own_count
    (90010, 4, 4, 2, "Smarty", 1),
    (90011, 5, 3, 2, "Smarty", 2),
    (90012, 2, 6, 3, "Smarty", 3),
    (90013, 6, 2, 3, "Kabloom", 1),  # color change only + count 1
]


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=Path("reference/samples/card_data_5_device"))
    ap.add_argument("--out", type=Path, default=Path("dist/card_mods/card_data_5"))
    ap.add_argument("--inventory-out", type=Path, default=Path("dist/card_mods/inventory_extra.json"))
    ap.add_argument("--template-id", type=int, default=32)
    ap.add_argument("--dump-dir", type=Path, default=Path("dist/card_mods/countable_variants"))
    args = ap.parse_args()

    env, text_asset, cards = load_bundle(args.src)
    tid = str(args.template_id)
    if tid not in cards:
        print(f"ERROR missing template {tid}", file=sys.stderr)
        return 1
    base = cards[tid]
    print(
        f"template={tid} rarity={base.get('rarity')} ignoreDeckLimit={base.get('ignoreDeckLimit')} "
        f"faction={base.get('faction')} color={base.get('color')} "
        f"comps={len(base['entity']['components'])}"
    )
    if base.get("ignoreDeckLimit"):
        print("ERROR: template has ignoreDeckLimit=true (stack locked)", file=sys.stderr)
        return 1

    dump_dir = args.dump_dir
    dump_dir.mkdir(parents=True, exist_ok=True)
    owned: dict[str, int] = {}

    for to_id, atk, hp, cost, color, own in VARIANTS:
        card = make_variant(
            base,
            to_id=to_id,
            prefab=f"mod-count-{to_id}",
            atk=atk,
            hp=hp,
            cost=cost,
            color=color,
        )
        # keep template rarity (non-basic)
        card["rarity"] = base.get("rarity")
        cards[str(to_id)] = card
        owned[str(to_id)] = own
        (dump_dir / f"card_{to_id}.json").write_text(
            json.dumps(
                {
                    "id": to_id,
                    "own": own,
                    "ignoreDeckLimit": card.get("ignoreDeckLimit"),
                    "rarity": card.get("rarity"),
                    "displayAttack": card.get("displayAttack"),
                    "displayHealth": card.get("displayHealth"),
                    "displaySunCost": card.get("displaySunCost"),
                    "prefabName": card.get("prefabName"),
                    "faction": card.get("faction"),
                    "color": card.get("color"),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"  + {to_id}: stats {atk}/{hp}/{cost} own={own} "
            f"ignoreDeckLimit={card.get('ignoreDeckLimit')} rarity={card.get('rarity')}"
        )

    # Optional: keep 90001 from old basic template for contrast (locked 4)
    # Not included unless present — user tests countable set only.

    save_bundle(env, text_asset, cards, args.out)
    inv = {"schemaVersion": 1, "Cards": owned, "Heroes": {}}
    args.inventory_out.write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")
    print(f"inventory -> {owned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
