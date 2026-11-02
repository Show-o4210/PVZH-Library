import io
import json
import os
from datetime import datetime, timezone

import UnityPy

from animator import CHARACTER_PATH_HASH, collect_allowed_binding_paths, load_animation_dumps
from config import (
    GAMEOBJECT_ID,
    OUTPUT_DIR,
    RENDERER_ID,
    ROOT_POSITION,
    SCRIPT_VERSION,
    SHIP_INHAND_MARKER,
    SHIP_TEXTURE_SIZE,
    SPRITE_ID,
    TEXTURE_ID,
    TRANSFORM_ID,
)
from sprite_mesh import CHARACTER_SPRITE_SIZE
from scanner import get_path_id


def _rotation_is_identity(rotation, tolerance=0.001):
    return (
        abs(rotation.x) <= tolerance
        and abs(rotation.y) <= tolerance
        and abs(rotation.z) <= tolerance
        and abs(rotation.w - 1.0) <= tolerance
    )


def verify_saved_bundle(
    bundle_bytes,
    root_path_id,
    pixels_to_units=None,
    y_offset=None,
    ship_assets=None,
):
    env = UnityPy.load(io.BytesIO(bundle_bytes))
    serialized_file = env.assets[0]
    issues = []

    go_data = serialized_file.objects[GAMEOBJECT_ID].read()
    component_ids = [component.component.path_id for component in go_data.m_Component]
    if component_ids != [TRANSFORM_ID, RENDERER_ID]:
        issues.append(f"GameObject({GAMEOBJECT_ID}) 组件链异常: {component_ids}")

    char_transform = serialized_file.objects[TRANSFORM_ID].read()
    if char_transform.m_Father.path_id != root_path_id:
        issues.append(f"Transform({TRANSFORM_ID}) 父指针未绑定到大根")

    char_pos = char_transform.m_LocalPosition
    if y_offset is not None and abs(char_pos.y - y_offset) > 0.001:
        issues.append(
            f"character({TRANSFORM_ID}) Y 偏移未对齐配置值: {char_pos.y} (期望 {y_offset})"
        )

    char_rotation = char_transform.m_LocalRotation
    if not _rotation_is_identity(char_rotation):
        issues.append(
            f"character({TRANSFORM_ID}) 旋转未归零: "
            f"({char_rotation.x}, {char_rotation.y}, {char_rotation.z}, {char_rotation.w})"
        )

    root_transform = serialized_file.objects[root_path_id].read()
    root_rotation = root_transform.m_LocalRotation
    if not _rotation_is_identity(root_rotation):
        issues.append(
            "大根旋转未归零: "
            f"({root_rotation.x}, {root_rotation.y}, {root_rotation.z}, {root_rotation.w})"
        )
    if not any(get_path_id(child) == TRANSFORM_ID for child in root_transform.m_Children):
        issues.append(f"大根 Transform 未挂载 character({TRANSFORM_ID})")

    root_pos = root_transform.m_LocalPosition
    if (
        abs(root_pos.x - ROOT_POSITION[0]) > 0.001
        or abs(root_pos.y - ROOT_POSITION[1]) > 0.001
        or abs(root_pos.z - ROOT_POSITION[2]) > 0.001
    ):
        issues.append(
            "大根 Transform 位置未对齐 ro 标准值: "
            f"({root_pos.x}, {root_pos.y}, {root_pos.z})"
        )

    ship_assets = ship_assets or []
    expected_ship_sprite_ids = {
        asset["path_id"]
        for asset in ship_assets
        if asset.get("type") == "Sprite"
    }
    expected_sprite_count = 1 + len(expected_ship_sprite_ids)

    sprite_count = sum(
        1 for obj in serialized_file.objects.values() if obj.type.name == "Sprite"
    )
    if sprite_count != expected_sprite_count:
        issues.append(
            f"Sprite 清理异常，当前数量: {sprite_count} "
            f"(期望 {expected_sprite_count} = character + ship)"
        )

    for asset in ship_assets:
        path_id = asset["path_id"]
        if path_id not in serialized_file.objects:
            issues.append(
                f"ship 加载资源缺失: {asset['type']}({asset.get('name', '')}) "
                f"path_id={path_id}"
            )
            continue
        obj = serialized_file.objects[path_id]
        if obj.type.name != asset["type"]:
            issues.append(
                f"ship 加载资源类型异常 path_id={path_id}: "
                f"期望 {asset['type']}，实际 {obj.type.name}"
            )

    external_renderers = []
    for obj in serialized_file.objects.values():
        if obj.type.name != "SpriteRenderer":
            continue
        renderer = obj.read()
        if renderer.m_Sprite.m_FileID != 0:
            external_renderers.append(renderer.m_GameObject.read().m_Name)
    if external_renderers:
        issues.append(
            "仍存在外部通用 SpriteRenderer: " + ", ".join(external_renderers)
        )

    sprite_data = serialized_file.objects[SPRITE_ID].read()
    if sprite_data.m_Name != "character":
        issues.append(f"Sprite({SPRITE_ID}) 名称异常: {sprite_data.m_Name!r} (期望 'character')")
    if sprite_data.m_RD.texture.path_id != TEXTURE_ID:
        issues.append(
            f"Sprite({SPRITE_ID}) 纹理指针异常: "
            f"{sprite_data.m_RD.texture.path_id} (期望 {TEXTURE_ID})"
        )
    sprite_rect = sprite_data.m_Rect
    if abs(sprite_rect.width - 1024) > 0.5 or abs(sprite_rect.height - 1024) > 0.5:
        issues.append(
            f"Sprite({SPRITE_ID}) 尺寸异常: "
            f"{sprite_rect.width}x{sprite_rect.height} (期望 1024x1024)"
        )
    if pixels_to_units is not None and abs(sprite_data.m_PixelsToUnits - pixels_to_units) > 0.001:
        issues.append(
            f"Sprite({SPRITE_ID}) m_PixelsToUnits 未对齐配置值: "
            f"{sprite_data.m_PixelsToUnits} (期望 {pixels_to_units})"
        )

    sprite_rd = sprite_data.m_RD
    vertex_count = sprite_rd.m_VertexData.m_VertexCount
    if vertex_count != 4:
        issues.append(
            f"Sprite({SPRITE_ID}) 网格顶点数异常: {vertex_count} (期望 4，FullRect)"
        )
    texture_rect = sprite_rd.textureRect
    if (
        abs(texture_rect.width - 1024) > 0.5
        or abs(texture_rect.height - 1024) > 0.5
        or abs(texture_rect.x) > 0.001
        or abs(texture_rect.y) > 0.001
    ):
        issues.append(
            f"Sprite({SPRITE_ID}) textureRect 未对齐全图 1024x1024: "
            f"({texture_rect.x}, {texture_rect.y}, {texture_rect.width}, {texture_rect.height})"
        )
    rect_offset = sprite_rd.textureRectOffset
    if abs(rect_offset.x) > 0.001 or abs(rect_offset.y) > 0.001:
        issues.append(
            f"Sprite({SPRITE_ID}) textureRectOffset 应为 0: "
            f"({rect_offset.x}, {rect_offset.y})"
        )
    if sprite_rd.settingsRaw != 64:
        issues.append(
            f"Sprite({SPRITE_ID}) settingsRaw 异常: {sprite_rd.settingsRaw} (期望 64，Tight 自定义网格)"
        )
    uv = sprite_rd.uvTransform
    expected_uv = (
        sprite_data.m_PixelsToUnits,
        CHARACTER_SPRITE_SIZE * 0.5,
        sprite_data.m_PixelsToUnits,
        CHARACTER_SPRITE_SIZE * 0.5,
    )
    if any(abs(getattr(uv, axis) - value) > 0.5 for axis, value in zip("xyzw", expected_uv)):
        issues.append(
            f"Sprite({SPRITE_ID}) uvTransform 未对齐原厂格式: "
            f"({uv.x}, {uv.y}, {uv.z}, {uv.w}) (期望 {expected_uv})"
        )
    if sprite_rd.downscaleMultiplier == 0:
        issues.append(f"Sprite({SPRITE_ID}) downscaleMultiplier 为 0，真机可能不渲染")

    ship_texture_asset = next(
        (
            asset
            for asset in ship_assets
            if asset.get("type") == "Texture2D"
            and SHIP_INHAND_MARKER in asset.get("container", "").lower()
        ),
        None,
    )
    ship_texture_size = None
    if ship_texture_asset:
        ship_tex = serialized_file.objects[ship_texture_asset["path_id"]].read()
        ship_texture_size = [ship_tex.m_Width, ship_tex.m_Height]
        if (
            ship_tex.m_Width != SHIP_TEXTURE_SIZE
            or ship_tex.m_Height != SHIP_TEXTURE_SIZE
        ):
            issues.append(
                "ship inhand Texture2D 尺寸异常: "
                f"{ship_tex.m_Width}x{ship_tex.m_Height} "
                f"(期望 {SHIP_TEXTURE_SIZE}x{SHIP_TEXTURE_SIZE})"
            )
        if ship_tex.m_Name != ship_texture_asset.get("name"):
            issues.append(
                "ship inhand Texture2D 名称被改写: "
                f"{ship_tex.m_Name!r} (期望保留 {ship_texture_asset.get('name')!r})"
            )

    serialized_file.objects[RENDERER_ID].read().m_Sprite.deref()
    texture = serialized_file.objects[TEXTURE_ID].read()

    valid_ids = set(serialized_file.objects.keys())
    def walk_typetree_pptrs(node, prefix=""):
        if isinstance(node, dict):
            if (
                "m_FileID" in node
                and "m_PathID" in node
                and node.get("m_FileID", 0) == 0
            ):
                path_id = node.get("m_PathID", 0)
                if path_id not in (0,) and path_id not in valid_ids:
                    issues.append(
                        f"{prefix} 指向缺失对象: {path_id}"
                    )
                return
            for key, value in node.items():
                walk_typetree_pptrs(value, f"{prefix}.{key}" if prefix else key)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk_typetree_pptrs(value, f"{prefix}[{index}]")

    for obj in serialized_file.objects.values():
        if obj.type.name == "MonoBehaviour":
            walk_typetree_pptrs(obj.read_typetree(), f"MonoBehaviour({obj.path_id})")

    for obj in serialized_file.objects.values():
        if obj.type.name == "Transform":
            transform = obj.read()
            father_path_id = transform.m_Father.path_id
            if father_path_id not in (0,) and father_path_id not in valid_ids:
                issues.append(
                    f"Transform({obj.path_id}) 父节点缺失: {father_path_id}"
                )
            for child in transform.m_Children:
                child_path_id = child.path_id
                if child_path_id not in valid_ids:
                    issues.append(
                        f"Transform({obj.path_id}) 子节点缺失: {child_path_id}"
                    )
        elif obj.type.name == "SpriteRenderer":
            renderer = obj.read()
            if renderer.m_Sprite.m_FileID == 0:
                sprite_path_id = renderer.m_Sprite.path_id
                if sprite_path_id == 0 or sprite_path_id not in valid_ids:
                    issues.append(
                        f"SpriteRenderer({obj.path_id}) 指向缺失 Sprite: {sprite_path_id}"
                    )

    allowed_animation_paths = collect_allowed_binding_paths(load_animation_dumps())
    animation_clips = []
    for obj in serialized_file.objects.values():
        if obj.type.name != "AnimationClip":
            continue
        clip = obj.read()
        bindings = clip.m_ClipBindingConstant.genericBindings
        binding_paths = sorted({binding.path for binding in bindings})
        invalid_paths = [
            path
            for path in binding_paths
            if path not in allowed_animation_paths
        ]
        if invalid_paths:
            issues.append(
                f"AnimationClip({clip.m_Name}) 仍存在未重定向路径: {invalid_paths}"
            )
        animation_clips.append(
            {
                "name": clip.m_Name,
                "binding_count": len(bindings),
                "binding_paths": binding_paths,
                "root_bindings": sum(1 for binding in bindings if binding.path == 0),
            }
        )

    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "script_version": SCRIPT_VERSION,
        "root_path_id": root_path_id,
        "checks": {
            "gameobject_components": component_ids,
            "character_father": char_transform.m_Father.path_id,
            "character_position": [char_pos.x, char_pos.y, char_pos.z],
            "pixels_to_units": sprite_data.m_PixelsToUnits,
            "character_rotation": [
                char_rotation.x,
                char_rotation.y,
                char_rotation.z,
                char_rotation.w,
            ],
            "root_position": [root_pos.x, root_pos.y, root_pos.z],
            "root_rotation": [
                root_rotation.x,
                root_rotation.y,
                root_rotation.z,
                root_rotation.w,
            ],
            "sprite_count": sprite_count,
            "expected_sprite_count": expected_sprite_count,
            "ship_assets": ship_assets,
            "external_renderer_count": len(external_renderers),
            "texture_size": [texture.m_Width, texture.m_Height],
            "ship_texture_size": ship_texture_size,
            "animation_clip_count": len(animation_clips),
            "character_path_hash": CHARACTER_PATH_HASH,
            "allowed_animation_paths": sorted(allowed_animation_paths),
            "animation_clips": animation_clips,
        },
        "passed": not issues,
        "issues": issues,
    }

    if issues:
        raise RuntimeError("; ".join(issues))

    return report


def write_verification_report(bundle_name, report, pairing_mode, skin_name):
    report_path = os.path.join(OUTPUT_DIR, f"{bundle_name}.report.json")
    payload = {
        "bundle": bundle_name,
        "skin": skin_name,
        "pairing_mode": pairing_mode,
        **report,
    }
    with open(report_path, "w", encoding="utf-8") as report_file:
        json.dump(payload, report_file, ensure_ascii=False, indent=2)
    return report_path