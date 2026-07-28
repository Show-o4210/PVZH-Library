#!/usr/bin/env python3
"""
Clone an existing card inside a UnityFS card_data_* bundle (TextAsset JSON),
assign a new Guid + prefabName, and write a new bundle.

Example:
  python scripts/clone_card_into_card_data.py \\
    --src reference/samples/card_data_5_device \\
    --out dist/card_mods/card_data_5 \\
    --from-id 10 --to-id 90001
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import UnityPy
from UnityPy.enums import ClassIDType


def _script_to_text(script) -> str:
    if isinstance(script, str):
        return script
    if isinstance(script, bytes):
        return script.decode("utf-8")
    # array.array('B') / memoryview
    return bytes(script).decode("utf-8")


def load_cards_from_bundle(path: Path) -> tuple[object, object, dict]:
    env = UnityPy.load(str(path))
    for obj in env.objects:
        if obj.type != ClassIDType.TextAsset and obj.type.name != "TextAsset":
            continue
        data = obj.read()
        text = _script_to_text(data.m_Script)
        cards = json.loads(text)
        return env, data, cards
    raise RuntimeError(f"no TextAsset in {path}")


def clone_card(cards: dict, from_id: int, to_id: int, prefab_name: str | None) -> dict:
    src_key = str(from_id)
    dst_key = str(to_id)
    if src_key not in cards:
        raise KeyError(f"source card {from_id} not in card_data")
    if dst_key in cards:
        print(f"WARN: overwriting existing card {to_id}", file=sys.stderr)

    card = copy.deepcopy(cards[src_key])

    # entity.components[*].Card.Guid
    entity = card.get("entity") or {}
    for comp in entity.get("components") or []:
        typ = comp.get("$type") or ""
        if ".Card," in typ or typ.endswith(".Card"):
            data = comp.setdefault("$data", {})
            data["Guid"] = int(to_id)

    # top-level distinguishers
    old_prefab = card.get("prefabName")
    if prefab_name is None:
        prefab_name = f"mod-custom-{to_id}"
    card["prefabName"] = prefab_name

    # Make stats obviously different if fighter-like fields exist
    if "displayAttack" in card:
        card["displayAttack"] = 9
    if "displayHealth" in card:
        card["displayHealth"] = 9
    if "displaySunCost" in card:
        card["displaySunCost"] = 1

    # Mirror into components Attack/Health/SunCost when present
    for comp in entity.get("components") or []:
        typ = comp.get("$type") or ""
        data = comp.setdefault("$data", {})
        if ".Attack," in typ:
            data.setdefault("AttackValue", {})["BaseValue"] = 9
        elif ".Health," in typ:
            data.setdefault("MaxHealth", {})["BaseValue"] = 9
            data["CurrentDamage"] = 0
        elif ".SunCost," in typ:
            data.setdefault("SunCostValue", {})["BaseValue"] = 1
        elif ".Tags," in typ:
            tags = list(data.get("tags") or [])
            marker = f"modcard{to_id}"
            if marker not in tags:
                tags.append(marker)
            data["tags"] = tags

    # top-level tags list if present
    if isinstance(card.get("tags"), list):
        marker = f"modcard{to_id}"
        if marker not in card["tags"]:
            card["tags"] = list(card["tags"]) + [marker]

    cards[dst_key] = card
    print(f"cloned {from_id} -> {to_id}")
    print(f"  prefabName: {old_prefab!r} -> {prefab_name!r}")
    return card


def save_bundle(env, text_asset, cards: dict, out_path: Path) -> None:
    # Compact JSON (game sample is compact).
    new_text = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
    text_asset.m_Script = new_text
    text_asset.save()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Prefer lz4 (common for UnityFS game bundles); fall back to default.
    data = None
    used = "default"
    for packer in ("lz4", "original", None):
        try:
            data = env.file.save() if packer is None else env.file.save(packer=packer)
            used = str(packer)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: save(packer={packer!r}) failed: {exc}", file=sys.stderr)
    if data is None:
        raise RuntimeError("failed to serialize AssetBundle")
    out_path.write_bytes(data)
    print(
        f"wrote {out_path} ({out_path.stat().st_size} bytes, packer={used}), "
        f"cards={len(cards)}, json_chars={len(new_text)}"
    )

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, required=True, help="source card_data_* UnityFS")
    ap.add_argument("--out", type=Path, required=True, help="output card_data_* path")
    ap.add_argument("--from-id", type=int, default=10, help="template card id")
    ap.add_argument("--to-id", type=int, default=90001, help="new card id / Guid")
    ap.add_argument(
        "--prefab",
        default=None,
        help="new prefabName (default: mod-custom-<to-id>)",
    )
    ap.add_argument(
        "--dump-json",
        type=Path,
        default=None,
        help="optional path to dump only the new card JSON for inspection",
    )
    args = ap.parse_args()

    env, text_asset, cards = load_cards_from_bundle(args.src)
    card = clone_card(cards, args.from_id, args.to_id, args.prefab)
    if args.dump_json:
        args.dump_json.parent.mkdir(parents=True, exist_ok=True)
        args.dump_json.write_text(
            json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"dumped card JSON -> {args.dump_json}")

    save_bundle(env, text_asset, cards, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
