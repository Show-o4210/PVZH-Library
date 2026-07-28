#!/usr/bin/env python3
import re
import sys
from pathlib import Path

text = Path("reference/il2cpp/script.json").read_text(encoding="utf-8", errors="replace")
for name in sys.argv[1:] or [
    "AddCardToInventory",
    "GetCardInventoryCount",
    "HasAtLeastOfCard",
    "SetLocalPlayerInventory",
]:
    for m in re.finditer(rf'"Name":\s*"[^"]*{re.escape(name)}"[^\n]*\n[^\n]*"Signature":\s*"([^"]+)"', text):
        print(name, "=>", m.group(1)[:240])
        break
    else:
        print(name, "=> NOT FOUND")
