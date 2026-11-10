"""Batch-rebuild indexed Unity 2D prefabs into transparent PNG files."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import re
import traceback
import zlib
from pathlib import Path

import cv2
import numpy as np
import UnityPy
from PIL import Image


INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(value: object) -> str:
    name = INVALID_FILENAME.sub("_", str(value)).strip().rstrip(".")
    return name or "未命名"


def local_matrix(transform, pose=None) -> np.ndarray:
    p, q, s = transform.m_LocalPosition, transform.m_LocalRotation, transform.m_LocalScale
    override = (pose or {}).get(transform.object_reader.path_id, {})
    p = override.get("position", p)
    q = override.get("rotation", q)
    s = override.get("scale", s)
    angle = 2.0 * math.atan2(q.z, q.w)
    c, sn = math.cos(angle), math.sin(angle)
    return np.array(
        [[c * s.x, -sn * s.y, p.x], [sn * s.x, c * s.y, p.y], [0, 0, 1]],
        dtype=np.float64,
    )


def parent_transform(transform):
    return transform.m_Father.read() if transform.m_Father else None


def world_matrix(transform, pose=None) -> np.ndarray:
    chain = []
    current = transform
    while current:
        chain.append(local_matrix(current, pose))
        current = parent_transform(current)
    result = np.eye(3)
    for matrix in reversed(chain):
        result = result @ matrix
    return result


def world_z(transform, pose=None) -> float:
    z = 0.0
    current = transform
    while current:
        override = (pose or {}).get(current.object_reader.path_id, {})
        z += override.get("position", current.m_LocalPosition).z
        current = parent_transform(current)
    return z


def get_transform(game_object):
    for component in game_object.m_Component:
        try:
            obj = component.component.read()
            if obj.object_reader.type.name in ("Transform", "RectTransform"):
                return obj
        except (FileNotFoundError, AttributeError):
            continue
    return None


def is_descendant(transform, root_path_id: int) -> bool:
    current = transform
    while current:
        if current.object_reader.path_id == root_path_id:
            return True
        current = parent_transform(current)
    return False


def find_root(env, uuid: str):
    exact = []
    fallback = []
    needle = uuid.lower()
    for obj in env.objects:
        if obj.type.name != "GameObject":
            continue
        game_object = obj.read()
        name = game_object.m_Name.strip()
        if name.lower() == needle:
            exact.append(game_object)
        elif needle in name.lower():
            fallback.append(game_object)
    candidates = exact or fallback
    if not candidates:
        return None
    # Prefer the highest matching object when a nested object repeats the UUID.
    candidate_ids = {item.object_reader.path_id for item in candidates}
    for item in candidates:
        transform = get_transform(item)
        parent = parent_transform(transform) if transform else None
        if not parent or parent.m_GameObject.read().object_reader.path_id not in candidate_ids:
            return transform
    return get_transform(candidates[0])


def hierarchy_by_hash(root_transform):
    """Map Unity's CRC32 animation path hash to a Transform."""
    result = {0: root_transform}

    def visit(transform, path):
        for child_ptr in transform.m_Children:
            child = child_ptr.read()
            name = child.m_GameObject.read().m_Name
            child_path = f"{path}/{name}" if path else name
            result[zlib.crc32(child_path.encode("utf-8")) & 0xFFFFFFFF] = child
            visit(child, child_path)

    visit(root_transform, "")
    return result


def idle_score(clip):
    name = clip.m_Name.lower()
    return (
        0 if name.endswith("_idle") or name == "idle" else 1,
        sum(word in name for word in ("attack", "special", "enter", "exit", "damage")),
        len(name),
    )


def choose_idle_clip(env, root_transform):
    # First follow this prefab's AnimatorOverrideController. This prevents a
    # generic dependency clip named simply "Idle" from beating Wallnut_idle.
    override_clips = []
    original_clips = []
    for component in root_transform.m_GameObject.read().m_Component:
        try:
            animator = component.component.read()
            if animator.object_reader.type.name != "Animator" or not animator.m_Controller:
                continue
            controller = animator.m_Controller.read()
            if hasattr(controller, "m_Clips"):
                for pair in controller.m_Clips:
                    for pointer, destination in (
                        (pair.m_OverrideClip, override_clips),
                        (pair.m_OriginalClip, original_clips),
                    ):
                        try:
                            clip = pointer.read() if pointer else None
                            if clip and "idle" in clip.m_Name.lower():
                                destination.append(clip)
                        except FileNotFoundError:
                            continue
        except (FileNotFoundError, AttributeError):
            continue
    if override_clips:
        return min(override_clips, key=idle_score)
    if original_clips:
        return min(original_clips, key=idle_score)

    clips = []
    for obj in env.objects:
        if obj.type.name != "AnimationClip":
            continue
        clip = obj.read()
        name = clip.m_Name.lower()
        if "idle" not in name:
            continue
        # Prefer the ordinary idle over attack_idle, special_idle, idle_04, etc.
        clips.append((idle_score(clip), clip))
    return min(clips, key=lambda item: item[0])[1] if clips else None


def first_frame_pose(clip, root_transform):
    """Decode time-zero values using AnimationClip's ValueArrayDelta starts."""
    transforms = hierarchy_by_hash(root_transform)
    values = [item.m_Start for item in clip.m_MuscleClip.m_ValueArrayDelta]
    bindings = clip.m_ClipBindingConstant.genericBindings
    pptr_mapping = clip.m_ClipBindingConstant.pptrCurveMapping
    pose = {}
    sprite_by_transform = {}
    active_by_transform = {}
    enabled_by_transform = {}
    alpha_by_transform = {}
    cursor = 0
    for binding in bindings:
        count = {1: 3, 2: 4, 3: 3, 4: 3}.get(binding.attribute, 1) if binding.typeID == 4 else 1
        current = values[cursor : cursor + count]
        cursor += count
        transform = transforms.get(binding.path)
        if transform is None or len(current) != count:
            continue
        target = pose.setdefault(transform.object_reader.path_id, {})
        if binding.typeID == 4 and binding.attribute == 1:
            target["position"] = type(transform.m_LocalPosition)(*current)
        elif binding.typeID == 4 and binding.attribute == 2:
            target["rotation"] = type(transform.m_LocalRotation)(*current)
        elif binding.typeID == 4 and binding.attribute == 3:
            target["scale"] = type(transform.m_LocalScale)(*current)
        elif binding.typeID == 212 and binding.isPPtrCurve:
            index = int(round(current[0]))
            if 0 <= index < len(pptr_mapping):
                pointer = pptr_mapping[index]
                # A null PPtr is an intentional "no sprite" animation frame.
                sprite_by_transform[transform.object_reader.path_id] = pointer if pointer.path_id else None
        elif binding.typeID == 1 and binding.attribute == 0x7C5A22F6:
            active_by_transform[transform.object_reader.path_id] = current[0] >= 0.5
        elif binding.typeID == 212 and binding.attribute == 0xC50BCE51:
            enabled_by_transform[transform.object_reader.path_id] = current[0] >= 0.5
        elif binding.typeID == 212 and binding.attribute == 0x1222D899:
            alpha_by_transform[transform.object_reader.path_id] = current[0]
    visibility = {
        "active": active_by_transform,
        "enabled": enabled_by_transform,
        "alpha": alpha_by_transform,
    }
    return pose, sprite_by_transform, visibility


def sprite_image(sprite) -> Image.Image:
    # UnityPy handles atlas cropping, packing rotation and compressed Texture2D
    # formats in Sprite.image. Standalone sprites are handled by the same path.
    return sprite.image.convert("RGBA")


def load_with_dependencies(bundle: Path, bundle_dir: Path, cab_index: dict):
    """Load the primary bundle plus its directly referenced CAB bundles."""
    initial = UnityPy.load(str(bundle))
    dependency_paths = []
    seen = {bundle.name}
    for top_file in initial.files.values():
        for asset_file in getattr(top_file, "files", {}).values():
            for external in getattr(asset_file, "externals", []):
                cab_name = Path(external.path).name.lower()
                dependency_name = cab_index.get(cab_name)
                if dependency_name and dependency_name not in seen:
                    candidate = bundle_dir / dependency_name
                    if candidate.is_file():
                        dependency_paths.append(str(candidate))
                        seen.add(dependency_name)
    if not dependency_paths:
        return initial, []
    return UnityPy.load(str(bundle), *dependency_paths), dependency_paths


def animated_active(transform, active_overrides):
    current = transform
    while current:
        path_id = current.object_reader.path_id
        # Animation values override the prefab's serialized active flag. When
        # the idle clip has no curve for a node, preserve its prefab state.
        default_active = bool(current.m_GameObject.read().m_IsActive)
        if active_overrides.get(path_id, default_active) is False:
            return False
        current = parent_transform(current)
    return True


def collect_layers(env, root_transform, pose=None, sprite_overrides=None, visibility=None):
    layers = []
    root_id = root_transform.object_reader.path_id
    for obj in env.objects:
        if obj.type.name != "SpriteRenderer":
            continue
        renderer = obj.read()
        if not renderer.m_Enabled or not renderer.m_Sprite:
            continue
        game_object = renderer.m_GameObject.read()
        transform = get_transform(game_object)
        if transform is None or not is_descendant(transform, root_id):
            continue
        visibility = visibility or {"active": {}, "enabled": {}, "alpha": {}}
        transform_id = transform.object_reader.path_id
        if not animated_active(transform, visibility["active"]):
            continue
        if visibility["enabled"].get(transform_id, True) is False:
            continue
        try:
            transform_id = transform.object_reader.path_id
            if transform_id in (sprite_overrides or {}) and sprite_overrides[transform_id] is None:
                continue
            sprite_ptr = (sprite_overrides or {}).get(transform_id, renderer.m_Sprite)
            sprite = sprite_ptr.read()
            image = sprite_image(sprite)
        except (FileNotFoundError, AttributeError, TypeError):
            # References to generic VFX/shadows often live in a different bundle.
            continue
        if image.width == 0 or image.height == 0:
            continue

        pivot_x = sprite.m_Pivot.x * image.width
        pivot_y = (1.0 - sprite.m_Pivot.y) * image.height
        ppu = float(sprite.m_PixelsToUnits)
        pixel_to_local = np.array(
            [[1 / ppu, 0, -pivot_x / ppu], [0, -1 / ppu, pivot_y / ppu], [0, 0, 1]],
            dtype=np.float64,
        )
        if getattr(renderer, "m_FlipX", False):
            pixel_to_local[0] *= -1
        if getattr(renderer, "m_FlipY", False):
            pixel_to_local[1] *= -1

        color = getattr(renderer, "m_Color", None)
        if color and (color.r, color.g, color.b, color.a) != (1.0, 1.0, 1.0, 1.0):
            rgba = np.asarray(image).astype(np.float32)
            rgba *= np.array([color.r, color.g, color.b, color.a], dtype=np.float32)
            image = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
        animated_alpha = visibility["alpha"].get(transform_id)
        if animated_alpha is not None:
            rgba = np.asarray(image).copy()
            rgba[:, :, 3] = np.clip(rgba[:, :, 3].astype(np.float32) * animated_alpha, 0, 255)
            image = Image.fromarray(rgba.astype(np.uint8), "RGBA")

        matrix = world_matrix(transform, pose) @ pixel_to_local
        sorting_layer = int(getattr(renderer, "m_SortingLayerID", 0))
        sorting_order = int(getattr(renderer, "m_SortingOrder", 0))
        layers.append(
            {
                "z": world_z(transform, pose),
                "sorting_layer": sorting_layer,
                "sorting_order": sorting_order,
                "name": sprite.m_Name,
                "image": image,
                "matrix": matrix,
                "ppu": ppu,
            }
        )
    return layers


def render(layers, output: Path, padding: int = 8) -> tuple[int, int]:
    corners = []
    for layer in layers:
        image, matrix = layer["image"], layer["matrix"]
        points = np.array(
            [[0, 0, 1], [image.width, 0, 1], [0, image.height, 1], [image.width, image.height, 1]],
            dtype=np.float64,
        ).T
        corners.extend((matrix @ points).T[:, :2])
    corners = np.asarray(corners)
    min_x, min_y = corners.min(axis=0)
    max_x, max_y = corners.max(axis=0)
    ppu = max(layer["ppu"] for layer in layers)
    width = math.ceil((max_x - min_x) * ppu) + 2 * padding
    height = math.ceil((max_y - min_y) * ppu) + 2 * padding
    if width <= 0 or height <= 0 or width * height > 100_000_000:
        raise ValueError(f"invalid output dimensions: {width}x{height}")
    world_to_canvas = np.array(
        [[ppu, 0, -min_x * ppu + padding], [0, -ppu, max_y * ppu + padding], [0, 0, 1]],
        dtype=np.float64,
    )
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Farther Z first, then Unity sorting layer/order from low to high.
    ordered = sorted(
        layers,
        key=lambda x: (x["sorting_layer"], x["sorting_order"], -x["z"]),
    )
    for layer in ordered:
        affine = (world_to_canvas @ layer["matrix"])[:2].astype(np.float32)
        warped = cv2.warpAffine(
            np.asarray(layer["image"]),
            affine,
            (width, height),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )
        canvas.alpha_composite(Image.fromarray(warped, "RGBA"))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    return width, height


def process(row, bundle_dir: Path, output_dir: Path, cab_index: dict):
    bundle = bundle_dir / row["TEXTURE_NAME"]
    if not bundle.is_file():
        return "missing_bundle", None, f"找不到 {bundle.name}"
    env, dependencies = load_with_dependencies(bundle, bundle_dir, cab_index)
    root = find_root(env, row["UUID"])
    if root is None:
        return "missing_root", None, f"找不到 UUID 根节点 {row['UUID']}"
    idle = choose_idle_clip(env, root)
    if idle is None:
        return "missing_idle", None, "找不到名称含 idle 的 AnimationClip"
    pose, sprite_overrides, visibility = first_frame_pose(idle, root)
    layers = collect_layers(env, root, pose, sprite_overrides, visibility)
    if not layers:
        return "no_layers", None, "根节点下没有可读取的 SpriteRenderer"
    filename = f"{int(row['GUID']):04d}_{safe_name(row['NAME_CN'])}.png"
    output = output_dir / safe_name(row["FACTION"]) / safe_name(row["TYPE"]) / filename
    size = render(layers, output)
    info = {
        "output": str(output), "size": list(size), "layers": len(layers),
        "idle_clip": idle.m_Name, "animated_transforms": len(pose),
        "animated_sprites": len(sprite_overrides),
        "animated_visibility": sum(len(values) for values in visibility.values()),
        "dependency_bundles": len(dependencies),
    }
    return "ok", info, ""


def process_safe(row, bundle_dir: Path, output_dir: Path, cab_index: dict):
    result = dict(row)
    try:
        status, info, message = process(row, bundle_dir, output_dir, cab_index)
        result.update({"status": status, "message": message})
        if info:
            result.update(info)
    except Exception as exc:
        result.update(
            {
                "status": "error",
                "message": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(limit=4),
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=Path("index_new.json"))
    parser.add_argument("--bundles", type=Path, default=Path("autotagged"))
    parser.add_argument("--output", type=Path, default=Path("拼图输出"))
    parser.add_argument("--cab-index", type=Path, default=Path("cab_index.json"))
    parser.add_argument("--limit", type=int, default=0, help="Only process N eligible rows (for testing)")
    parser.add_argument(
        "--workers", type=int, default=min(8, os.cpu_count() or 4),
        help="Number of concurrent worker threads (default: up to 8)",
    )
    args = parser.parse_args()

    rows = json.loads(args.index.read_text(encoding="utf-8-sig"))
    cab_index = json.loads(args.cab_index.read_text(encoding="utf-8"))["cabs"]
    eligible = [
        row
        for row in rows
        if "！" not in str(row.get("NAME_CN", ""))
        and "!" not in str(row.get("NAME_CN", ""))
        and row.get("TEXTURE_NAME") not in (None, "", "无")
    ]
    if args.limit:
        eligible = eligible[: args.limit]

    report_by_index = {}
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(process_safe, row, args.bundles, args.output, cab_index): index
            for index, row in enumerate(eligible)
        }
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            result = future.result()
            report_by_index[index] = result
            completed += 1
            row = eligible[index]
            print(
                f"[{completed}/{len(eligible)}] {result['status']}: "
                f"{row['GUID']} {row['NAME_CN']} {result.get('message', '')}",
                flush=True,
            )

    report = [report_by_index[index] for index in range(len(eligible))]

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "处理报告.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    counts = {}
    for item in report:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print("SUMMARY", json.dumps(counts, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
