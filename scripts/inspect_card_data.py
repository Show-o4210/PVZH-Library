#!/usr/bin/env python3
"""Inspect card_data UnityFS bundle structure."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import UnityPy


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "reference/samples/card_data_5_device")
    env = UnityPy.load(str(path))
    print("file", path, "size", path.stat().st_size)
    print("objects", len(env.objects))
    for obj in env.objects:
        data = obj.read()
        name = getattr(data, "m_Name", None) or ""
        extra = ""
        if obj.type.name == "TextAsset":
            script = getattr(data, "m_Script", None)
            if script is None:
                script = getattr(data, "script", b"")
            if isinstance(script, bytes):
                text = script
            else:
                text = str(script).encode("utf-8", "replace")
            extra = f" text_len={len(text)} head={text[:80]!r}"
        elif obj.type.name == "MonoBehaviour":
            # try type tree dump keys
            try:
                tree = data.read_typetree()
                keys = list(tree.keys()) if isinstance(tree, dict) else type(tree)
                extra = f" keys={keys}"
            except Exception as exc:  # noqa: BLE001
                extra = f" typetree_err={exc}"
        print(f"  type={obj.type.name:20s} path_id={obj.path_id} name={name!r}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
