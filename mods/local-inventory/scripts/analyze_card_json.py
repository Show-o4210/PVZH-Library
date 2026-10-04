#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

import UnityPy


def load_cards(path: Path) -> dict:
    env = UnityPy.load(str(path))
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        data = obj.read()
        script = data.m_Script
        if isinstance(script, str):
            text = script
        elif isinstance(script, bytes):
            text = script.decode("utf-8")
        else:
            # array.array or memoryview
            text = bytes(script).decode("utf-8")
        return json.loads(text)
    raise RuntimeError("no TextAsset cards")


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "reference/samples/card_data_5_device")
    cards = load_cards(path)
    print("num cards", len(cards))
    print("sample keys", list(cards.keys())[:15])

    # Pick a simple plant fighter if possible
    for cid in ("1", "2", "3", "5", "10", "20"):
        if cid not in cards:
            continue
        s = json.dumps(cards[cid], ensure_ascii=False)
        print(f"\n=== card {cid} len={len(s)} ===")
        for m in re.finditer(
            r'"(?:[^"]*(?:[Pp]refab|[Aa]sset|[Uu]uid|Guid|Art|Icon|Texture)[^"]*)"\s*:\s*("[^"]*"|[0-9]+|true|false|null|\{)',
            s,
        ):
            print(" ", m.group(0)[:160])
        # top-level structure
        ent = cards[cid].get("entity", {})
        comps = ent.get("components", [])
        print(" components:", len(comps))
        for c in comps[:12]:
            t = c.get("$type", "")
            short = t.split(",")[0].split(".")[-1]
            data = c.get("$data", {})
            print(f"  - {short}: keys={list(data.keys())[:8]}")


if __name__ == "__main__":
    main()
