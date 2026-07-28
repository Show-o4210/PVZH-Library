#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

import UnityPy


def main() -> None:
    env = UnityPy.load("reference/samples/card_data_5_device")
    cards = None
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            s = d.m_Script
            text = s if isinstance(s, str) else (s.decode("utf-8") if isinstance(s, bytes) else bytes(s).decode("utf-8"))
            cards = json.loads(text)
            break
    assert cards
    for field in ("rarity", "color", "faction", "set", "isTeamup", "isAquatic", "isFighter", "isEnv"):
        vals = Counter()
        for c in cards.values():
            if field in c:
                vals[str(c[field])] += 1
        print(field, vals.most_common(12))

    # dump one plant and one zombie fully top-level
    for cid in ("10", "2", "1"):
        c = cards[cid]
        top = {k: v for k, v in c.items() if k != "entity"}
        print("\n==", cid, "==")
        print(json.dumps(top, ensure_ascii=False, indent=2)[:800])


if __name__ == "__main__":
    main()
