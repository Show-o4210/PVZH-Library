from config import RENDERER_ID, SPRITE_ID, TEXTURE_ID, TRANSFORM_ID
from injector import safe_read_object
from scanner import get_path_id

# 删除 Transform 后，部分 MonoBehaviour 仍可能引用旧节点（如 Shoot Origin）
MONO_BEHAVIOUR_TRANSFORM_REMAP = {
    "MuzzleOrigin": TRANSFORM_ID,
}


def find_transform_for_gameobject(serialized_file, gameobject_path_id):
    for path_id, obj in serialized_file.objects.items():
        if obj.type.name != "Transform":
            continue
        transform = safe_read_object(obj, wrap=True)
        if transform.m_GameObject.path_id == gameobject_path_id:
            return path_id
    return None


def collect_component_ids_for_gameobject(serialized_file, gameobject_path_id):
    go_obj = serialized_file.objects.get(gameobject_path_id)
    if go_obj is None or go_obj.type.name != "GameObject":
        return set()
    ids = {gameobject_path_id}
    transform_path_id = find_transform_for_gameobject(serialized_file, gameobject_path_id)
    if transform_path_id is not None:
        ids.add(transform_path_id)
    for component in go_obj.read().m_Component:
        ids.add(component.component.path_id)
    return ids


def collect_transform_subtree_ids(serialized_file, root_transform_ids):
    subtree_ids = set()
    pending = list(root_transform_ids)

    while pending:
        transform_path_id = pending.pop()
        if transform_path_id in subtree_ids:
            continue
        transform_obj = serialized_file.objects.get(transform_path_id)
        if transform_obj is None or transform_obj.type.name != "Transform":
            continue
        subtree_ids.add(transform_path_id)
        transform = safe_read_object(transform_obj, wrap=True)
        for child in transform.m_Children:
            pending.append(get_path_id(child))
    return subtree_ids


def expand_removal_closure(serialized_file, seed_ids):
    removed_ids = set(seed_ids)

    transform_seeds = []
    for path_id in seed_ids:
        obj = serialized_file.objects.get(path_id)
        if obj is None:
            continue
        if obj.type.name == "Transform":
            transform_seeds.append(path_id)
        elif obj.type.name == "GameObject":
            transform_path_id = find_transform_for_gameobject(serialized_file, path_id)
            if transform_path_id is not None:
                transform_seeds.append(transform_path_id)

    removed_ids.update(collect_transform_subtree_ids(serialized_file, transform_seeds))

    for path_id in list(removed_ids):
        obj = serialized_file.objects.get(path_id)
        if obj is None:
            continue
        if obj.type.name == "Transform":
            gameobject_path_id = safe_read_object(obj, wrap=True).m_GameObject.path_id
            removed_ids.update(
                collect_component_ids_for_gameobject(serialized_file, gameobject_path_id)
            )
        elif obj.type.name == "GameObject":
            removed_ids.update(
                collect_component_ids_for_gameobject(serialized_file, path_id)
            )

    return removed_ids


def detach_transform_children(serialized_file, removed_ids):
    changed = 0
    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name != "Transform":
            continue
        transform = safe_read_object(obj, wrap=True)
        filtered_children = [
            child
            for child in transform.m_Children
            if get_path_id(child) not in removed_ids
        ]
        if len(filtered_children) == len(transform.m_Children):
            continue
        transform.m_Children = filtered_children
        transform.save()
        changed += 1
    return changed


def delete_objects(serialized_file, removed_ids):
    if not removed_ids:
        return 0
    detach_transform_children(serialized_file, removed_ids)
    deleted_count = 0
    for path_id in removed_ids:
        if path_id in serialized_file.objects:
            del serialized_file.objects[path_id]
            deleted_count += 1
    if deleted_count:
        serialized_file.mark_changed()
    return deleted_count


def prune_all_transform_children(serialized_file):
    valid_ids = set(serialized_file.objects.keys())
    changed = 0
    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name != "Transform":
            continue
        transform = safe_read_object(obj, wrap=True)
        before = len(transform.m_Children)
        transform.m_Children = [
            child
            for child in transform.m_Children
            if get_path_id(child) in valid_ids
        ]
        if len(transform.m_Children) == before:
            continue
        transform.save()
        changed += 1
    if changed:
        serialized_file.mark_changed()
    return changed


def _is_internal_pptr(node):
    return (
        isinstance(node, dict)
        and "m_FileID" in node
        and "m_PathID" in node
        and node.get("m_FileID", 0) == 0
    )


def _sanitize_typetree_pptrs(node, valid_ids, field_name=None, fixes=None):
    if fixes is None:
        fixes = []

    if isinstance(node, dict):
        if _is_internal_pptr(node):
            path_id = node.get("m_PathID", 0)
            if path_id != 0 and path_id not in valid_ids:
                remap_target = MONO_BEHAVIOUR_TRANSFORM_REMAP.get(field_name)
                if remap_target is not None and remap_target in valid_ids:
                    node["m_PathID"] = remap_target
                    fixes.append((field_name, path_id, remap_target))
                else:
                    node["m_PathID"] = 0
                    fixes.append((field_name, path_id, 0))
            return fixes

        for key, value in node.items():
            _sanitize_typetree_pptrs(value, valid_ids, field_name=key, fixes=fixes)
    elif isinstance(node, list):
        for item in node:
            _sanitize_typetree_pptrs(item, valid_ids, field_name=field_name, fixes=fixes)

    return fixes


def sanitize_mono_behaviour_pptrs(serialized_file):
    valid_ids = set(serialized_file.objects.keys())
    fixed_count = 0
    details = []

    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name != "MonoBehaviour":
            continue
        typetree = obj.read_typetree()
        fixes = _sanitize_typetree_pptrs(typetree, valid_ids)
        if not fixes:
            continue
        obj.save_typetree(typetree)
        fixed_count += 1
        details.extend((path_id, field, old, new) for field, old, new in fixes)

    if fixed_count:
        serialized_file.mark_changed()
    return fixed_count, details


def remove_old_textures(serialized_file, protected_ids=None):
    protected_ids = protected_ids or set()
    removed_ids = set()
    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name == "Texture2D" and path_id != TEXTURE_ID and path_id not in protected_ids:
            removed_ids.add(path_id)
    return delete_objects(serialized_file, removed_ids)


def remove_generic_external_renderers(serialized_file):
    seed_ids = set()
    removed_names = []

    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name != "SpriteRenderer":
            continue

        renderer = obj.read()
        if renderer.m_Sprite.m_FileID == 0:
            continue

        seed_ids.update(
            collect_component_ids_for_gameobject(
                serialized_file, renderer.m_GameObject.path_id
            )
        )
        seed_ids.add(path_id)

        try:
            removed_names.append(renderer.m_GameObject.read().m_Name)
        except Exception:
            removed_names.append(str(renderer.m_GameObject.path_id))

    removed_ids = expand_removal_closure(serialized_file, seed_ids)
    delete_objects(serialized_file, removed_ids)
    return len(removed_names), removed_names


def remove_orphan_sprites(serialized_file, protected_ids=None):
    protected_ids = protected_ids or set()
    removed_ids = set()
    for path_id, obj in list(serialized_file.objects.items()):
        if (
            obj.type.name == "Sprite"
            and path_id != SPRITE_ID
            and path_id not in protected_ids
        ):
            removed_ids.add(path_id)
    return delete_objects(serialized_file, removed_ids)


def strip_broken_sprite_renderers_from_gameobject(serialized_file, gameobject_path_id):
    go_obj = serialized_file.objects.get(gameobject_path_id)
    if go_obj is None or go_obj.type.name != "GameObject":
        return 0

    valid_ids = set(serialized_file.objects.keys())
    go_data = safe_read_object(go_obj, wrap=True)
    kept_components = []
    removed_renderer_ids = []

    for component in go_data.m_Component:
        component_id = component.component.path_id
        component_obj = serialized_file.objects.get(component_id)
        if component_obj is None or component_obj.type.name != "SpriteRenderer":
            kept_components.append(component)
            continue

        renderer = safe_read_object(component_obj, wrap=True)
        if renderer.m_Sprite.m_FileID != 0:
            kept_components.append(component)
            continue

        sprite_path_id = renderer.m_Sprite.path_id
        if sprite_path_id in valid_ids and sprite_path_id != 0:
            kept_components.append(component)
            continue

        removed_renderer_ids.append(component_id)

    if not removed_renderer_ids:
        return 0

    go_data.m_Component = kept_components
    go_data.save()
    delete_objects(serialized_file, set(removed_renderer_ids))
    return len(removed_renderer_ids)


def remove_broken_sprite_renderers(serialized_file, protected_ids=None, keep_ids=None):
    protected_ids = protected_ids or set()
    protected_ids.update({RENDERER_ID})
    keep_ids = keep_ids or set()
    if keep_ids:
        for keep_id in keep_ids:
            obj = serialized_file.objects.get(keep_id)
            if obj is None:
                continue
            if obj.type.name == "Transform":
                protected_ids.add(keep_id)
                protected_ids.add(safe_read_object(obj, wrap=True).m_GameObject.path_id)
                protected_ids.update(
                    collect_component_ids_for_gameobject(
                        serialized_file,
                        safe_read_object(obj, wrap=True).m_GameObject.path_id,
                    )
                )
            elif obj.type.name == "GameObject":
                protected_ids.add(keep_id)
                protected_ids.update(
                    collect_component_ids_for_gameobject(serialized_file, keep_id)
                )
            else:
                protected_ids.add(keep_id)
    valid_ids = set(serialized_file.objects.keys())
    seed_ids = set()

    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name != "SpriteRenderer":
            continue
        if path_id in protected_ids:
            continue

        renderer = obj.read()
        if renderer.m_Sprite.m_FileID != 0:
            continue

        sprite_path_id = renderer.m_Sprite.path_id
        if sprite_path_id in valid_ids and sprite_path_id != 0:
            continue

        gameobject_path_id = renderer.m_GameObject.path_id
        if gameobject_path_id in protected_ids:
            continue

        seed_ids.update(
            collect_component_ids_for_gameobject(serialized_file, gameobject_path_id)
        )
        seed_ids.add(path_id)

    removed_ids = expand_removal_closure(serialized_file, seed_ids)
    removed_ids -= protected_ids
    return delete_objects(serialized_file, removed_ids)


def remove_orphan_transforms(serialized_file, keep_ids=None):
    keep_ids = keep_ids or set()
    keep_ids.update({TRANSFORM_ID})
    valid_ids = set(serialized_file.objects.keys())
    seed_ids = set()

    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name != "Transform":
            continue
        if path_id in keep_ids:
            continue

        transform = safe_read_object(obj, wrap=True)
        father_path_id = get_path_id(transform.m_Father)
        if father_path_id in (0, -1):
            continue
        if father_path_id in valid_ids:
            continue

        seed_ids.add(path_id)

    removed_ids = expand_removal_closure(serialized_file, seed_ids)
    return delete_objects(serialized_file, removed_ids)