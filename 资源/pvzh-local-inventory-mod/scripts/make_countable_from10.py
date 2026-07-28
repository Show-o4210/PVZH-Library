#!/usr/bin/env python3
"""
Countable custom cards based ONLY on official #10 (known-good load path).

Root cause of "stuck at 4": template #10 has ignoreDeckLimit=true.
We keep the entire #10 entity skill/component tree, only change:
  Guid, prefabName, display/stats, tags, and force ignoreDeckLimit=false.

Do NOT switch to rarer templates with different component sets for quantity tests.
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


def make_from_10(
    base: dict,
    *,
    to_id: int,
    prefab: str,
    atk: int,
    hp: int,
    cost: int,
) -> dict:
    card = copy.deepcopy(base)
    set_guid(card, to_id)
    card["prefabName"] = prefab
    set_fighter_stats(card, atk, hp, cost)
    # Unlock variable stack counts (basic #10 is locked true)
    card["ignoreDeckLimit"] = False
    append_tag(card, f"modcard{to_id}")
    append_tag(card, "mod_countable_from10")
    return card


# Distinct stats + own counts 1/2/3 (not 4)
VARIANTS = [
    # to_id, atk, hp, cost, own
    (90020, 9, 9, 1, 1),
    (90021, 5, 5, 2, 2),
    (90022, 3, 7, 2, 3),
    (90023, 8, 2, 3, 1),
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
    args = ap.parse_args()

    env, text_asset, cards = load_bundle(args.src)
    base = cards["10"]
    print(
        f"template=10 rarity={base.get('rarity')} "
        f"ignoreDeckLimit={base.get('ignoreDeckLimit')} "
        f"comps={len(base['entity']['components'])}"
    )

    owned: dict[str, int] = {}
    dump = Path("dist/card_mods/countable_from10")
    dump.mkdir(parents=True, exist_ok=True)

    for to_id, atk, hp, cost, own in VARIANTS:
        card = make_from_10(
            base,
            to_id=to_id,
            prefab=f"mod-from10-{to_id}",
            atk=atk,
            hp=hp,
            cost=cost,
        )
        # entity component type list must match #10
        t0 = [c.get("$type") for c in base["entity"]["components"]]
        t1 = [c.get("$type") for c in card["entity"]["components"]]
        if t0 != t1:
            print(f"ERROR {to_id}: component types diverged", file=sys.stderr)
            return 1
        cards[str(to_id)] = card
        owned[str(to_id)] = own
        meta = {
            "id": to_id,
            "own": own,
            "ignoreDeckLimit": card["ignoreDeckLimit"],
            "rarity": card.get("rarity"),
            "atk_hp_cost": [atk, hp, cost],
            "prefabName": card["prefabName"],
            "template": 10,
        }
        (dump / f"card_{to_id}.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
        print(f"  + {to_id}: {atk}/{hp}/{cost} own={own} ignoreDeckLimit=False")

    save_bundle(env, text_asset, cards, args.out)
    inv = {"schemaVersion": 1, "Cards": owned, "Heroes": {}}
    args.inventory_out.write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")
    print("inventory", owned)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
