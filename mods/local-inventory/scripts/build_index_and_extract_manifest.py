# -*- coding: utf-8 -*-
"""
1) Extract AssetPathsManifest (JSON + bin) to workspace
2) Rebuild / improve index_new.json from card_data + cn.csv + manifest + old index
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\15731\Desktop\PVZH")
CACHE_MANIFEST_DIR = (
    ROOT
    / "com.ea.gp.pvzheroes"
    / "files"
    / "cache"
    / "manifest"
    / "UnityABVersion_11047"
)
BUNDLE_FILES = (
    ROOT
    / "com.ea.gp.pvzheroes"
    / "files"
    / "cache"
    / "bundles"
    / "files"
)
EXAMPLE = ROOT / "示例"
OUT_DIR = ROOT / "extracted"
INDEX_OUT = EXAMPLE / "index_new.json"
INDEX_BACKUP = EXAMPLE / "index_new.backup.json"

FACTION_CN = {"Plants": "植物", "Zombies": "僵尸", "plants": "植物", "zombies": "僵尸"}
RARITY_NAME = {
    0: "Common",
    1: "Uncommon",
    2: "Rare",
    3: "Super-Rare",
    4: "Legendary",
    5: "Event",
}


def load_manifest_json(path: Path) -> dict:
    # Accept pretty or compact JSON
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_manifest() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_json = CACHE_MANIFEST_DIR / "AssetPathsManifest"
    src_bin = CACHE_MANIFEST_DIR / "AssetPathsManifest.bin"
    ver_file = CACHE_MANIFEST_DIR.parent / "manifest_version"
    version = ver_file.read_text(encoding="utf-8").strip() if ver_file.exists() else "unknown"

    data = load_manifest_json(src_json)

    # Compact JSON (canonical for tooling)
    compact_path = OUT_DIR / "AssetPathsManifest.json"
    with compact_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    # Pretty JSON (readable)
    pretty_path = OUT_DIR / "AssetPathsManifest.pretty.json"
    with pretty_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Binary as used by the game (primary load path)
    bin_out = OUT_DIR / "AssetPathsManifest.bin"
    shutil.copy2(src_bin, bin_out)

    # Meta note
    meta = {
        "source_version": version,
        "source_dir": str(CACHE_MANIFEST_DIR),
        "path_count": len(data.get("BundleNamesByAssetPath", {})),
        "bundle_count": len(data.get("BundleNameToDetails", {})),
        "files": {
            "json_compact": str(compact_path.relative_to(ROOT)),
            "json_pretty": str(pretty_path.relative_to(ROOT)),
            "bin": str(bin_out.relative_to(ROOT)),
        },
        "runtime_load_order": [
            "1. Prefer AssetPathsManifest.bin (BinaryDataService / IBinarySerializable)",
            "2. If binary missing or deserialize fails -> fallback to JSON AssetPathsManifest",
            "Class: AssetPathsManifestLoader : BinaryJsonFallBackDataService<AssetPathsManifest>",
        ],
        "notes": [
            "Both formats are present in cache and represent the same logical data.",
            "Editing only the JSON will NOT affect the game while .bin still loads successfully.",
            "TEXTURE_NAME = basename(Bn) + '_' + Version, e.g. autotagged/abc... + Version 1 -> abc..._1",
        ],
    }
    with (OUT_DIR / "AssetPathsManifest.README.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[manifest] version={version}")
    print(f"[manifest] paths={meta['path_count']} bundles={meta['bundle_count']}")
    print(f"[manifest] wrote {compact_path}")
    print(f"[manifest] wrote {pretty_path}")
    print(f"[manifest] wrote {bin_out} ({bin_out.stat().st_size} bytes)")
    return data


def parse_cn_csv(path: Path) -> dict[str, dict[str, str]]:
    """Return {uuid: {name, shortDesc, longDesc, flavorText}}"""
    by_uuid: dict[str, dict[str, str]] = {}
    # key pattern: optional junk prefix, uuid-or-name, _field
    field_re = re.compile(
        r"^\s*`?\s*(.+?)_(name|shortDesc|longDesc|flavorText)\s*$",
        re.IGNORECASE,
    )
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for line in f:
            line = line.strip()
            if not line or line == ",":
                continue
            # CSV is simple key,value — value may contain commas rarely; split once
            if "," not in line:
                continue
            key, val = line.split(",", 1)
            key = key.strip().lstrip("`").strip()
            m = field_re.match(key)
            if not m:
                continue
            uid, field = m.group(1), m.group(2)
            by_uuid.setdefault(uid, {})[field] = val
    return by_uuid


def card_type_cn(card: dict) -> str:
    if card.get("isEnv"):
        return "环境"
    if card.get("isPower"):
        return "魔法"
    if card.get("isFighter"):
        return "单位"
    # tokens / unknown
    return "其他"


def texture_from_manifest(manifest: dict, uuid: str) -> dict:
    """Resolve TEXTURE_NAME for a card prefabName/UUID.

    Priority for the individual card AB (TEXTURE_NAME source):
      1. Prefabs/Cards/{uuid}
      2. GeneratedSprites/InHand/{uuid}
      3. GeneratedSprites/InCollection/{uuid} only if Bn is autotagged/* (not color atlas)
    """
    bnap = manifest["BundleNamesByAssetPath"]
    bnd = manifest["BundleNameToDetails"]

    if not uuid:
        return {
            "TEXTURE_NAME": "无",
            "BUNDLE": None,
            "INHAND_BUNDLE": None,
            "INCOLLECTION_BUNDLE": None,
            "CACHE_PATH": None,
            "TEXTURE_EXISTS": False,
        }

    prefab = f"Assets/Ship/Prefabs/Cards/{uuid}"
    inhand = f"Assets/Ship/Cards/GeneratedSprites/InHand/{uuid}"
    incol = f"Assets/Ship/Cards/GeneratedSprites/InCollection/{uuid}"

    inhand_info = bnap.get(inhand)
    incol_info = bnap.get(incol)
    prefab_info = bnap.get(prefab)

    chosen = prefab_info or inhand_info
    if not chosen and incol_info:
        bn_try = incol_info.get("Bn") or ""
        # power cards may only have InCollection on an autotagged individual pack
        if bn_try.startswith("autotagged/"):
            chosen = incol_info

    if not chosen:
        return {
            "TEXTURE_NAME": "无",
            "BUNDLE": None,
            "INHAND_BUNDLE": (inhand_info or {}).get("Bn"),
            "INCOLLECTION_BUNDLE": (incol_info or {}).get("Bn"),
            "CACHE_PATH": None,
            "TEXTURE_EXISTS": False,
        }

    bn = chosen["Bn"]
    base = bn.split("/")[-1]
    det = bnd.get(bn, {})
    ver = det.get("Version", 1)
    tex = f"{base}_{ver}"
    cache_rel = bn.replace("/", os.sep) + f"_{ver}"
    cache_abs = BUNDLE_FILES / cache_rel
    exists = cache_abs.is_file()

    return {
        "TEXTURE_NAME": tex,
        "BUNDLE": bn,
        "INHAND_BUNDLE": (inhand_info or {}).get("Bn"),
        "INCOLLECTION_BUNDLE": (incol_info or {}).get("Bn"),
        "CACHE_PATH": str(cache_abs.relative_to(ROOT)).replace("\\", "/")
        if exists
        else cache_rel.replace("\\", "/"),
        "TEXTURE_EXISTS": exists,
        "BUNDLE_SIZE": det.get("Size"),
        "BUNDLE_VERSION": ver,
    }


def build_index(manifest: dict) -> list[dict]:
    card_path = EXAMPLE / "card_data_5.json"
    cn_path = EXAMPLE / "cn.csv"
    old_index_path = EXAMPLE / "index_new.json"

    cards = json.loads(card_path.read_text(encoding="utf-8"))
    cn = parse_cn_csv(cn_path)

    old_by_guid: dict[str, dict] = {}
    old_by_uuid: dict[str, dict] = {}
    if old_index_path.exists():
        old = json.loads(old_index_path.read_text(encoding="utf-8"))
        for row in old:
            old_by_guid[str(row.get("GUID"))] = row
            if row.get("UUID"):
                old_by_uuid[row["UUID"]] = row

    # Sort guids numerically when possible
    def guid_key(g: str):
        try:
            return (0, int(g))
        except ValueError:
            return (1, g)

    rows: list[dict] = []
    for guid in sorted(cards.keys(), key=guid_key):
        card = cards[guid]
        uuid = card.get("prefabName") or ""
        tex_info = texture_from_manifest(manifest, uuid) if uuid else {
            "TEXTURE_NAME": "无",
            "BUNDLE": None,
            "INHAND_BUNDLE": None,
            "INCOLLECTION_BUNDLE": None,
            "CACHE_PATH": None,
            "TEXTURE_EXISTS": False,
        }

        loc = cn.get(uuid, {})
        old = old_by_guid.get(str(guid)) or old_by_uuid.get(uuid) or {}

        name_cn = loc.get("name") or old.get("NAME_CN") or ""
        name_en = old.get("NAME_EN") or ""

        faction = card.get("faction") or ""
        faction_cn = FACTION_CN.get(faction, old.get("FACTION") or faction)

        rarity = card.get("rarity")
        row = {
            "GUID": str(guid),
            "UUID": uuid,
            "NAME_CN": name_cn,
            "NAME_EN": name_en,
            "TYPE": card_type_cn(card) if any(
                card.get(k) for k in ("isFighter", "isEnv", "isPower")
            ) else (old.get("TYPE") or card_type_cn(card)),
            "FACTION": faction_cn,
            "COLOR": card.get("color") or "",
            "RARITY": rarity,
            "RARITY_NAME": RARITY_NAME.get(rarity, str(rarity) if rarity is not None else ""),
            "SET": card.get("set") or "",
            "COST": card.get("displaySunCost"),
            "ATTACK": card.get("displayAttack"),
            "HEALTH": card.get("displayHealth"),
            "TEXTURE_NAME": tex_info["TEXTURE_NAME"],
            "BUNDLE": tex_info.get("BUNDLE"),
            "INCOLLECTION_BUNDLE": tex_info.get("INCOLLECTION_BUNDLE"),
            "CACHE_PATH": tex_info.get("CACHE_PATH"),
            "TEXTURE_EXISTS": tex_info.get("TEXTURE_EXISTS", False),
            "IS_FIGHTER": bool(card.get("isFighter")),
            "IS_ENV": bool(card.get("isEnv")),
            "IS_POWER": bool(card.get("isPower")),
            "IS_AQUATIC": bool(card.get("isAquatic")),
            "IS_TEAMUP": bool(card.get("isTeamup")),
        }
        rows.append(row)

    # Keep any old-index-only entries (cheat/blank cards not in card_data)?
    # Optional: append old entries whose GUID not in card_data
    seen = {r["GUID"] for r in rows}
    if old_index_path.exists():
        old = json.loads(old_index_path.read_text(encoding="utf-8"))
        for o in old:
            g = str(o.get("GUID"))
            if g in seen:
                continue
            uuid = o.get("UUID") or ""
            tex_info = texture_from_manifest(manifest, uuid) if uuid else {
                "TEXTURE_NAME": o.get("TEXTURE_NAME") or "无",
                "BUNDLE": None,
                "INCOLLECTION_BUNDLE": None,
                "CACHE_PATH": None,
                "TEXTURE_EXISTS": False,
            }
            # if old said 无 and we still have none, keep 无
            tex_name = tex_info["TEXTURE_NAME"]
            if tex_name == "无" and o.get("TEXTURE_NAME") and o["TEXTURE_NAME"] != "无":
                # prefer old if manifest misses (e.g. nonstandard prefab)
                tex_name = o["TEXTURE_NAME"]
            rows.append(
                {
                    "GUID": g,
                    "UUID": uuid,
                    "NAME_CN": o.get("NAME_CN") or cn.get(uuid, {}).get("name") or "",
                    "NAME_EN": o.get("NAME_EN") or "",
                    "TYPE": o.get("TYPE") or "",
                    "FACTION": o.get("FACTION") or "",
                    "COLOR": "",
                    "RARITY": None,
                    "RARITY_NAME": "",
                    "SET": "",
                    "COST": None,
                    "ATTACK": None,
                    "HEALTH": None,
                    "TEXTURE_NAME": tex_name,
                    "BUNDLE": tex_info.get("BUNDLE"),
                    "INCOLLECTION_BUNDLE": tex_info.get("INCOLLECTION_BUNDLE"),
                    "CACHE_PATH": tex_info.get("CACHE_PATH"),
                    "TEXTURE_EXISTS": tex_info.get("TEXTURE_EXISTS", False),
                    "IS_FIGHTER": False,
                    "IS_ENV": False,
                    "IS_POWER": False,
                    "IS_AQUATIC": False,
                    "IS_TEAMUP": False,
                    "NOTE": "not_in_card_data_5",
                }
            )

    rows.sort(key=lambda r: guid_key(r["GUID"]))
    return rows


def main():
    manifest = extract_manifest()

    # backup old index
    if INDEX_OUT.exists() and not INDEX_BACKUP.exists():
        shutil.copy2(INDEX_OUT, INDEX_BACKUP)
        print(f"[index] backup -> {INDEX_BACKUP}")
    elif INDEX_OUT.exists():
        # refresh backup each run
        shutil.copy2(INDEX_OUT, INDEX_BACKUP)
        print(f"[index] backup refreshed -> {INDEX_BACKUP}")

    rows = build_index(manifest)
    with INDEX_OUT.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    # also root-level copy for convenience
    root_index = ROOT / "index_new.json"
    with root_index.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    with_tex = sum(1 for r in rows if r["TEXTURE_NAME"] not in (None, "", "无"))
    exists = sum(1 for r in rows if r.get("TEXTURE_EXISTS"))
    no_en = sum(1 for r in rows if not r.get("NAME_EN"))
    no_cn = sum(1 for r in rows if not r.get("NAME_CN"))
    print(f"[index] total={len(rows)} with_texture={with_tex} texture_on_disk={exists}")
    print(f"[index] missing NAME_EN={no_en} missing NAME_CN={no_cn}")
    print(f"[index] wrote {INDEX_OUT}")
    print(f"[index] wrote {root_index}")

    # sample Guacodile
    g = next((r for r in rows if r["GUID"] == "1"), None)
    print("[sample]", json.dumps(g, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
