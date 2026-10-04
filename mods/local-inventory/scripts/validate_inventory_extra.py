#!/usr/bin/env python3
"""Validate inventory_extra.json against schemaVersion 1 (PVZH Local Inventory Mod)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SUPPORTED_SCHEMA = {1}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def validate(data: Any, path: Path) -> int:
    errors = 0
    if not isinstance(data, dict):
        fail(f"{path}: root must be a JSON object")
        return 1

    if "schemaVersion" not in data:
        fail(f"{path}: missing schemaVersion")
        errors += 1
    else:
        ver = data["schemaVersion"]
        if not isinstance(ver, int) or isinstance(ver, bool):
            fail(f"{path}: schemaVersion must be int")
            errors += 1
        elif ver not in SUPPORTED_SCHEMA:
            fail(f"{path}: unsupported schemaVersion {ver} (supported: {sorted(SUPPORTED_SCHEMA)})")
            errors += 1

    for field in ("Cards", "Heroes"):
        if field not in data:
            continue
        obj = data[field]
        if not isinstance(obj, dict):
            fail(f"{path}: {field} must be an object")
            errors += 1
            continue
        for k, v in obj.items():
            if not isinstance(k, str):
                fail(f"{path}: {field} key must be string, got {type(k).__name__}")
                errors += 1
                continue
            if field == "Cards":
                if not k.isdigit():
                    fail(f"{path}: Cards key '{k}' must be decimal digits (card id)")
                    errors += 1
                else:
                    cid = int(k)
                    if cid < 90000:
                        warn(f"{path}: Cards id {cid} < 90000 (may collide with official ids)")
            if isinstance(v, bool) or not isinstance(v, int):
                fail(f"{path}: {field}['{k}'] must be int, got {type(v).__name__}")
                errors += 1
            elif v < 0:
                fail(f"{path}: {field}['{k}'] must be >= 0")
                errors += 1

    # Unknown keys are allowed (forward compatible) — only note them.
    known = {"schemaVersion", "Cards", "Heroes"}
    extra = set(data.keys()) - known
    if extra:
        warn(f"{path}: unknown keys ignored by current base: {sorted(extra)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="inventory_extra.json path(s)")
    args = parser.parse_args()

    total_errors = 0
    for path in args.files:
        if not path.is_file():
            fail(f"file not found: {path}")
            total_errors += 1
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
            data = json.loads(text)
        except Exception as exc:  # noqa: BLE001 — report any parse failure
            fail(f"{path}: {exc}")
            total_errors += 1
            continue
        errs = validate(data, path)
        if errs == 0:
            print(f"OK: {path}")
        total_errors += errs

    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
