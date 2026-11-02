import copy
import os

from PIL import Image
from UnityPy.classes.PPtr import PPtr
from UnityPy.helpers import TypeTreeHelper
from UnityPy.streams import EndianBinaryReader

from config import (
    CHARACTER_POSITION,
    CHARACTER_SCALE,
    GAMEOBJECT_ID,
    RENDERER_ID,
    ROOT_POSITION,
    SHIP_TEXTURE_SIZE,
    SPRITE_ID,
    TEMPLATE_MAP,
    TEMPLATES_DIR,
    TEXTURE_ID,
    TRANSFORM_ID,
)
from scanner import get_path_id
from sprite_mesh import apply_full_rect_sprite_wrapped

INJECTED_PATH_IDS = frozenset(TEMPLATE_MAP.keys())


def read_injected_typetree(obj, wrap=False):
    if obj.data is None:
        return obj.read_typetree(wrap=wrap)

    reader = EndianBinaryReader(obj.data, endian=obj.reader.endian)
    node = obj._get_typetree_node()
    result = TypeTreeHelper.read_typetree(
        node,
        reader,
        as_dict=not wrap,
        assetsfile=obj.assets_file,
        byte_size=len(obj.data),
    )
    if wrap:
        result.set_object_reader(obj)
    return result


def safe_read_object(obj, wrap=False):
    if obj.path_id in INJECTED_PATH_IDS and obj.data is not None:
        return read_injected_typetree(obj, wrap=wrap)
    if wrap:
        return obj.read_typetree(wrap=True)
    return obj.read()


def inject_object(serialized_file, refs, path_id, type_name, raw_bytes):
    source = refs[type_name]
    new_obj = copy.copy(source)
    new_obj.path_id = path_id
    new_obj.byte_size = len(raw_bytes)
    new_obj.set_raw_data(raw_bytes)
    serialized_file.objects[path_id] = new_obj


def inject_templates(serialized_file, refs, template_map):
    for path_id, type_name in template_map.items():
        template_path = os.path.join(TEMPLATES_DIR, f"{path_id}.dat")
        with open(template_path, "rb") as template_file:
            raw_bytes = template_file.read()
        inject_object(serialized_file, refs, path_id, type_name, raw_bytes)


def prepare_ship_texture_image(png_path, target_size=SHIP_TEXTURE_SIZE):
    image = Image.open(png_path).convert("RGBA")
    width, height = image.size

    if width != height:
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        image = image.crop((left, top, left + side, top + side))

    if image.size != (target_size, target_size):
        image = image.resize(
            (target_size, target_size),
            Image.Resampling.LANCZOS,
        )
    return image


def patch_ship_texture(serialized_file, texture_path_id, image, texture_name):
    tex_obj = serialized_file.objects[texture_path_id]
    tex_data = tex_obj.read()
    tex_data.m_Name = texture_name
    tex_data.image = image
    tex_data.save()


def patch_texture(serialized_file, png_path):
    tex_obj = serialized_file.objects[TEXTURE_ID]
    tex_data = read_injected_typetree(tex_obj, wrap=True)
    tex_data.image = png_path
    tex_data.m_Name = "character"
    tex_data.save()


def patch_character_sprite(serialized_file, pixels_to_units, png_path=None):
    sprite_obj = serialized_file.objects[SPRITE_ID]
    sprite_data = read_injected_typetree(sprite_obj, wrap=True)
    apply_full_rect_sprite_wrapped(sprite_data, pixels_to_units)
    sprite_data.m_PixelsToUnits = pixels_to_units
    sprite_data.m_Name = "character"
    sprite_data.save()
    if sprite_obj.data is not None:
        sprite_obj.byte_size = len(sprite_obj.data)
    serialized_file.mark_changed()
    return pixels_to_units


def patch_character_gameobject(serialized_file):
    go_obj = serialized_file.objects[GAMEOBJECT_ID]
    go_data = read_injected_typetree(go_obj, wrap=True)
    component_pair = go_data.m_Component[0]
    go_data.m_Name = "character"
    go_data.m_Component = [
        type(component_pair)(
            component=PPtr(m_FileID=0, m_PathID=TRANSFORM_ID, assetsfile=serialized_file)
        ),
        type(component_pair)(
            component=PPtr(m_FileID=0, m_PathID=RENDERER_ID, assetsfile=serialized_file)
        ),
    ]
    go_data.save()


def reset_transform_rotation(transform):
    transform.m_LocalRotation.x = 0
    transform.m_LocalRotation.y = 0
    transform.m_LocalRotation.z = 0
    transform.m_LocalRotation.w = 1


def patch_character_transform(serialized_file, root_path_id, y_offset=None):
    transform_obj = serialized_file.objects[TRANSFORM_ID]
    char_transform = read_injected_typetree(transform_obj, wrap=True)
    char_transform.m_GameObject = PPtr(
        m_FileID=0, m_PathID=GAMEOBJECT_ID, assetsfile=serialized_file
    )
    char_transform.m_Father = PPtr(
        m_FileID=0, m_PathID=root_path_id, assetsfile=serialized_file
    )
    char_transform.m_LocalPosition.x = CHARACTER_POSITION[0]
    char_transform.m_LocalPosition.y = (
        CHARACTER_POSITION[1] if y_offset is None else y_offset
    )
    char_transform.m_LocalPosition.z = CHARACTER_POSITION[2]
    char_transform.m_LocalScale.x = CHARACTER_SCALE[0]
    char_transform.m_LocalScale.y = CHARACTER_SCALE[1]
    char_transform.m_LocalScale.z = CHARACTER_SCALE[2]
    reset_transform_rotation(char_transform)
    char_transform.m_Children = []
    char_transform.save()


def prune_transform_children(transform, valid_ids):
    transform.m_Children = [
        child
        for child in transform.m_Children
        if get_path_id(child) in valid_ids
    ]


def finalize_root_transform(serialized_file, root_path_id):
    valid_ids = set(serialized_file.objects.keys())
    root_transform = serialized_file.objects[root_path_id].read()
    prune_transform_children(root_transform, valid_ids)
    root_transform.m_LocalPosition.x = ROOT_POSITION[0]
    root_transform.m_LocalPosition.y = ROOT_POSITION[1]
    root_transform.m_LocalPosition.z = ROOT_POSITION[2]
    reset_transform_rotation(root_transform)

    if not any(get_path_id(child) == TRANSFORM_ID for child in root_transform.m_Children):
        root_transform.m_Children.append(
            PPtr(m_FileID=0, m_PathID=TRANSFORM_ID, assetsfile=serialized_file)
        )
        stitched = True
    else:
        stitched = False

    root_transform.save()
    return stitched


def patch_character_renderer(serialized_file, refs):
    ref_renderer = refs["SpriteRenderer"].read()
    renderer_obj = serialized_file.objects[RENDERER_ID]
    renderer = read_injected_typetree(renderer_obj, wrap=True)
    renderer.m_GameObject = PPtr(
        m_FileID=0, m_PathID=GAMEOBJECT_ID, assetsfile=serialized_file
    )
    renderer.m_Sprite = PPtr(
        m_FileID=0, m_PathID=SPRITE_ID, assetsfile=serialized_file
    )
    renderer.m_Materials = [ref_renderer.m_Materials[0]]
    renderer.save()