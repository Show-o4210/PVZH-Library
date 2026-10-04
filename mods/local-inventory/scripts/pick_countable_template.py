#!/usr/bin/env python3
"""List simple plant fighters that allow non-4 stack (ignoreDeckLimit false)."""
import json
from pathlib import Path

import UnityPy


def main() -> None:
    env = UnityPy.load("reference/samples/card_data_5_device")
    cards = None
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            s = d.m_Script
            text = s if isinstance(s, str) else (
                s.decode("utf-8") if isinstance(s, bytes) else bytes(s).decode("utf-8")
            )
            cards = json.loads(text)
            break
    assert cards
    rows = []
    for cid, c in cards.items():
        if not c.get("isFighter"):
            continue
        if c.get("ignoreDeckLimit"):
            continue
        if c.get("isPower") or c.get("isEnv"):
            continue
        # prefer few components (simpler skill surface)
        ncomp = len(c.get("entity", {}).get("components") or [])
        rows.append(
            (
                ncomp,
                int(cid) if cid.isdigit() else 99999,
                cid,
                c.get("faction"),
                c.get("rarity"),
                c.get("color"),
                c.get("displayAttack"),
                c.get("displayHealth"),
                c.get("displaySunCost"),
                ncomp,
                c.get("prefabName", "")[:36],
            )
        )
    rows.sort()
    print("cid faction rarity color atk/hp/cost ncomp prefab")
    for r in rows[:40]:
        print(
            f"{r[2]:>4} {r[3]:8} rar={r[4]} {r[5]!s:12} "
            f"{r[6]}/{r[7]}/{r[8]} comps={r[9]} {r[10]}"
        )


if __name__ == "__main__":
    main()
