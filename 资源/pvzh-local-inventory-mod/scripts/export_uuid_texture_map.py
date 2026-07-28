import json
import os
from collections import Counter

AP = r"com.ea.gp.pvzheroes\files\cache\manifest\UnityABVersion_11047\AssetPathsManifest"
BUNDLE_ROOT = r"com.ea.gp.pvzheroes\files\cache\bundles\files"

with open(AP, "r", encoding="utf-8") as f:
    data = json.load(f)

bnap = data["BundleNamesByAssetPath"]
bnd = data["BundleNameToDetails"]

mapping = []
for p, info in sorted(bnap.items()):
    if "/Prefabs/Cards/" not in p:
        continue
    uuid = p.rsplit("/", 1)[-1]
    bn = info["Bn"]  # e.g. autotagged/HASH
    base = bn.split("/")[-1]
    det = bnd.get(bn, {})
    ver = det.get("Version", 1)
    tex = f"{base}_{ver}"
    ic = bnap.get(f"Assets/Ship/Cards/GeneratedSprites/InCollection/{uuid}")
    ih = bnap.get(f"Assets/Ship/Cards/GeneratedSprites/InHand/{uuid}")
    mapping.append(
        {
            "UUID": uuid,
            "TEXTURE_NAME": tex,
            "BUNDLE": bn,
            "PREFAB_PATH": p,
            "INHAND_BUNDLE": ih.get("Bn") if ih else None,
            "INCOLLECTION_BUNDLE": ic.get("Bn") if ic else None,
            "SIZE": det.get("Size"),
            "VERSION": ver,
        }
    )

out = "uuid_texture_map_from_manifest.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)
print("wrote", out, "count", len(mapping))

g = next(m for m in mapping if m["UUID"] == "2f9fa005-8b50-4d1a-89be-38e4a82036c4")
print("Guacodile:", json.dumps(g, indent=2, ensure_ascii=False))

cf = os.path.join(BUNDLE_ROOT, *g["BUNDLE"].split("/")) + f"_{g['VERSION']}"
print("cache exists", os.path.exists(cf), cf)
if os.path.exists(cf):
    print("cache size", os.path.getsize(cf))

print(
    "inhand same as prefab",
    sum(1 for m in mapping if m["INHAND_BUNDLE"] == m["BUNDLE"]),
)
print(
    "incollection atlas types",
    Counter(m["INCOLLECTION_BUNDLE"] for m in mapping if m["INCOLLECTION_BUNDLE"]).most_common(20),
)

# cross-check index_new
with open(os.path.join("示例", "index_new.json"), "r", encoding="utf-8") as f:
    idx = json.load(f)
by_uuid = {m["UUID"]: m for m in mapping}
ok = miss = mismatch = 0
for card in idx:
    uuid = card["UUID"]
    expected = card["TEXTURE_NAME"]
    if expected in (None, "无", ""):
        continue
    m = by_uuid.get(uuid)
    if not m:
        miss += 1
        continue
    if m["TEXTURE_NAME"] == expected:
        ok += 1
    else:
        mismatch += 1
        print("MISMATCH", card.get("NAME_EN"), expected, "vs", m["TEXTURE_NAME"])
print(f"index_new crosscheck ok={ok} miss={miss} mismatch={mismatch}")
