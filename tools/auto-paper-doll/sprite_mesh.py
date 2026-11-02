import struct

from PIL import Image

CHARACTER_SPRITE_SIZE = 1024
# bit 6 set => SpriteMeshType.Tight, Unity uses custom vertex buffer on device
SPRITE_SETTINGS_TIGHT_MESH = 64


def detect_content_bbox(
    image_path,
    tex_width=CHARACTER_SPRITE_SIZE,
    tex_height=CHARACTER_SPRITE_SIZE,
    alpha_threshold=10,
    pad=2,
):
    image = Image.open(image_path).convert("RGBA")
    if image.size != (tex_width, tex_height):
        image = image.resize((tex_width, tex_height), Image.Resampling.LANCZOS)

    alpha = image.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > alpha_threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return 0, 0, tex_width, tex_height

    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(tex_width, right + pad)
    bottom = min(tex_height, bottom + pad)
    return left, top, right - left, bottom - top


def build_full_rect_positions(
    width,
    height,
    pixels_to_units,
    pivot_x=0.5,
    pivot_y=0.5,
):
    width_units = width / pixels_to_units
    height_units = height / pixels_to_units
    pivot_x_units = pivot_x * width_units
    pivot_y_units = pivot_y * height_units
    return [
        (-pivot_x_units, -pivot_y_units, 0.0),
        (width_units - pivot_x_units, -pivot_y_units, 0.0),
        (-pivot_x_units, height_units - pivot_y_units, 0.0),
        (width_units - pivot_x_units, height_units - pivot_y_units, 0.0),
    ]


def build_full_rect_vertex_bytes(positions, uvs):
    stream0 = b"".join(struct.pack("<fff", *position) for position in positions)
    stream0 = stream0.ljust((len(stream0) + 15) & ~15, b"\x00")
    stream1 = b"".join(struct.pack("<ff", *uv) for uv in uvs)
    return stream0 + stream1


def build_full_rect_index_buffer():
    return bytes(struct.pack("<6H", 0, 1, 2, 2, 1, 3))


def build_sprite_uv_transform(pixels_to_units, tex_width, tex_height):
    # Matches factory sprites: (ptu, tex_h/2, ptu, tex_w/2)
    return (
        float(pixels_to_units),
        float(tex_height) * 0.5,
        float(pixels_to_units),
        float(tex_width) * 0.5,
    )


def _apply_sprite_render_data(
    sprite,
    pixels_to_units,
    mesh_width,
    mesh_height,
    texture_rect,
    uvs,
    tex_width=CHARACTER_SPRITE_SIZE,
    tex_height=CHARACTER_SPRITE_SIZE,
):
    pivot_x = 0.5
    pivot_y = 0.5

    sprite.m_Rect.x = 0.0
    sprite.m_Rect.y = 0.0
    sprite.m_Rect.width = float(tex_width)
    sprite.m_Rect.height = float(tex_height)
    sprite.m_Offset.x = 0.0
    sprite.m_Offset.y = 0.0
    sprite.m_Pivot.x = pivot_x
    sprite.m_Pivot.y = pivot_y
    sprite.m_IsPolygon = False
    sprite.m_Extrude = 1

    render_data = sprite.m_RD
    rect_x, rect_y, rect_width, rect_height = texture_rect
    render_data.textureRect.x = float(rect_x)
    render_data.textureRect.y = float(rect_y)
    render_data.textureRect.width = float(rect_width)
    render_data.textureRect.height = float(rect_height)
    render_data.textureRectOffset.x = float(rect_x)
    render_data.textureRectOffset.y = float(rect_y)
    uv_x, uv_y, uv_z, uv_w = build_sprite_uv_transform(
        pixels_to_units, tex_width, tex_height
    )
    render_data.uvTransform.x = uv_x
    render_data.uvTransform.y = uv_y
    render_data.uvTransform.z = uv_z
    render_data.uvTransform.w = uv_w
    render_data.downscaleMultiplier = 1.0
    render_data.settingsRaw = SPRITE_SETTINGS_TIGHT_MESH

    half_w = (mesh_width / pixels_to_units) * 0.5
    half_h = (mesh_height / pixels_to_units) * 0.5

    submesh = render_data.m_SubMeshes[0]
    submesh.firstByte = 0
    submesh.indexCount = 6
    submesh.topology = 0
    submesh.baseVertex = 0
    submesh.firstVertex = 0
    submesh.vertexCount = 4
    submesh.localAABB.m_Center.x = 0.0
    submesh.localAABB.m_Center.y = 0.0
    submesh.localAABB.m_Center.z = 0.0
    submesh.localAABB.m_Extent.x = half_w
    submesh.localAABB.m_Extent.y = half_h
    submesh.localAABB.m_Extent.z = 0.0

    positions = build_full_rect_positions(
        mesh_width, mesh_height, pixels_to_units, pivot_x, pivot_y
    )
    vertex_data = render_data.m_VertexData
    vertex_data.m_VertexCount = 4
    vertex_data.m_DataSize = build_full_rect_vertex_bytes(positions, uvs)
    render_data.m_IndexBuffer = build_full_rect_index_buffer()


def apply_full_rect_sprite_wrapped(
    sprite,
    pixels_to_units,
    width=CHARACTER_SPRITE_SIZE,
    height=CHARACTER_SPRITE_SIZE,
):
    uvs = [
        (0.0, 0.0),
        (1.0, 0.0),
        (0.0, 1.0),
        (1.0, 1.0),
    ]
    _apply_sprite_render_data(
        sprite,
        pixels_to_units,
        width,
        height,
        (0.0, 0.0, float(width), float(height)),
        uvs,
        tex_width=width,
        tex_height=height,
    )


def apply_content_rect_sprite_wrapped(
    sprite,
    pixels_to_units,
    bbox,
    tex_width=CHARACTER_SPRITE_SIZE,
    tex_height=CHARACTER_SPRITE_SIZE,
):
    x, y_top, width, height = bbox
    y_bottom = tex_height - y_top - height
    u0 = x / tex_width
    u1 = (x + width) / tex_width
    v0 = y_bottom / tex_height
    v1 = (y_bottom + height) / tex_height
    uvs = [
        (u0, v0),
        (u1, v0),
        (u0, v1),
        (u1, v1),
    ]
    _apply_sprite_render_data(
        sprite,
        pixels_to_units,
        width,
        height,
        (float(x), float(y_bottom), float(width), float(height)),
        uvs,
        tex_width=tex_width,
        tex_height=tex_height,
    )