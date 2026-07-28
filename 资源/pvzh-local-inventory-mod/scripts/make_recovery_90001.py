#!/usr/bin/env python3
"""Recovery: inject card 90001 as a pure Guid-only clone of template #10.

Use when local/cloud decks still reference 90001 and FixupDecksCommand NRE's
because official card_data no longer contains the definition.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import UnityPy
from UnityPy.enums import ClassIDType


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    src = root / "reference" / "samples" / "card_data_5_device"
    out = root / "dist" / "card_mods" / "card_data_5_recovery_90001"

    env = UnityPy.load(str(src))
    text_asset = None
    cards = None
    for obj in env.objects:
        if obj.type != ClassIDType.TextAsset and obj.type.name != "TextAsset":
            continue
        data = obj.read()
        script = data.m_Script
        text = script if isinstance(script, str) else bytes(script).decode("utf-8")
        cards = json.loads(text)
        text_asset = data
        break
    if not cards or text_asset is None:
        print("no TextAsset", file=sys.stderr)
        return 1

    base = copy.deepcopy(cards["10"])
    for comp in base.get("entity", {}).get("components") or []:
        typ = comp.get("$type") or ""
        if ".Card," in typ or typ.endswith(".Card"):
            comp.setdefault("$data", {})["Guid"] = 90001

    cards["90001"] = base
    new_text = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
    text_asset.m_Script = new_text
    text_asset.save()

    data = None
    used = None
    for packer in ("lz4", "original", None):
        try:
            data = env.file.save() if packer is None else env.file.save(packer=packer)
            used = packer
            break
        except Exception as exc:  # noqa: BLE001
            print(f"save {packer}: {exc}", file=sys.stderr)
    if data is None:
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"wrote {out} size={out.stat().st_size} packer={used} cards={len(cards)}")
    print(
        "90001 prefab={0!r} rarity={1!r} ignoreDeckLimit={2!r}".format(
            base.get("prefabName"),
            base.get("rarity"),
            base.get("ignoreDeckLimit"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
