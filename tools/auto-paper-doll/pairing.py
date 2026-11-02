import os

import UnityPy

from config import ENABLE_PATH_ID_PAIRING, INPUT_DIR, PAIRING_MODE_LABELS, SKINS_DIR
from scanner import find_big_hash_root


def path_id_aliases(path_id):
    return {str(path_id)}


def list_skin_files():
    return sorted(
        f for f in os.listdir(SKINS_DIR) if f.lower().endswith(".png")
    )


def list_bundle_files():
    return sorted(
        f
        for f in os.listdir(INPUT_DIR)
        if os.path.isfile(os.path.join(INPUT_DIR, f))
    )


def try_path_id_match(root_path_id, available_skins):
    """保留功能：仅当 ENABLE_PATH_ID_PAIRING 开启且皮肤文件名匹配大根 PathID 时生效。"""
    aliases = path_id_aliases(root_path_id)
    for skin_file in available_skins:
        stem = os.path.splitext(skin_file)[0]
        if stem in aliases or any(alias in stem for alias in aliases):
            return skin_file, "path_id"
    return None, None


def scan_root_path_id(bundle_name):
    bundle_path = os.path.join(INPUT_DIR, bundle_name)
    env = UnityPy.load(bundle_path)
    root_transform, _ = find_big_hash_root(env)
    if not root_transform:
        return None
    return root_transform.object_reader.path_id


def _collect_reserved_assignments(tasks, skin_files):
    reserved_by_bundle = {}
    used_skins = set()

    for bundle_name, task in tasks.items():
        if task.get("status") != "completed":
            continue
        skin_image = task.get("skin_image")
        if not skin_image or skin_image not in skin_files:
            continue
        reserved_by_bundle[bundle_name] = (skin_image, "completed")
        used_skins.add(skin_image)

    return reserved_by_bundle, used_skins


def build_pairing_plan(bundle_files, skin_files, tasks=None):
    """
    默认盲缝：按 bundle / 皮肤排序顺序 1:1 分配，每张皮肤仅用一次。
    PathID 配对为保留项，需 config.ENABLE_PATH_ID_PAIRING = True 才优先启用。
    已完成任务的绑定不会被重新分配。
    """
    tasks = tasks or {}
    reserved_by_bundle, used_skins = _collect_reserved_assignments(tasks, skin_files)
    available_skins = [skin for skin in skin_files if skin not in used_skins]
    plan = []

    for bundle_name in bundle_files:
        if bundle_name in reserved_by_bundle:
            skin_file, mode = reserved_by_bundle[bundle_name]
            plan.append(
                {
                    "bundle": bundle_name,
                    "skin": skin_file,
                    "mode": mode,
                    "root_path_id": scan_root_path_id(bundle_name),
                }
            )
            continue

        root_path_id = scan_root_path_id(bundle_name)
        if root_path_id is None:
            plan.append(
                {
                    "bundle": bundle_name,
                    "skin": None,
                    "mode": "failed",
                    "root_path_id": None,
                    "error": "未能定位大根 Transform",
                }
            )
            continue

        skin_file = None
        mode = "unmatched"

        if ENABLE_PATH_ID_PAIRING:
            skin_file, mode = try_path_id_match(root_path_id, available_skins)
            if skin_file:
                available_skins.remove(skin_file)

        if skin_file is None and available_skins:
            skin_file = available_skins.pop(0)
            mode = "blind"

        if skin_file:
            used_skins.add(skin_file)

        plan.append(
            {
                "bundle": bundle_name,
                "skin": skin_file,
                "mode": mode,
                "root_path_id": root_path_id,
            }
        )

    return plan


def print_pairing_plan(plan):
    print("\n📋 [配对计划]")
    for entry in plan:
        bundle_name = entry["bundle"]
        if entry["mode"] == "failed":
            print(f"   ❌ {bundle_name}: {entry['error']}")
            continue

        root_id = entry["root_path_id"]
        skin = entry["skin"]
        mode = entry["mode"]

        if skin:
            label = PAIRING_MODE_LABELS.get(mode, mode)
            print(
                f"   ✅ {bundle_name}\n"
                f"      大根 PathID: {root_id}\n"
                f"      → 皮肤: {skin}  [{label}]"
            )
        else:
            print(
                f"   ⚠️  {bundle_name}\n"
                f"      大根 PathID: {root_id}\n"
                f"      → 皮肤不足，将跳过"
            )