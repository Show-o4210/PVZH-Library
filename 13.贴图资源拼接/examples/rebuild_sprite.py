"""Rebuild a Unity 2D prefab from its SpriteRenderer and Texture2D objects."""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
import UnityPy
from PIL import Image


BUNDLE = Path("2ceeb890a69397041ba1fd559056c358_1")
OUTPUT = Path("guacodile_composite.png")
PADDING = 8


def local_matrix(transform) -> np.ndarray:
    p = transform.m_LocalPosition
    q = transform.m_LocalRotation
    s = transform.m_LocalScale
    # All visible artwork is in the XY plane. Convert the quaternion's Z
    # rotation to a conventional 2D affine matrix.
    angle = 2.0 * math.atan2(q.z, q.w)
    c, sn = math.cos(angle), math.sin(angle)
    return np.array(
        [[c * s.x, -sn * s.y, p.x], [sn * s.x, c * s.y, p.y], [0, 0, 1]],
        dtype=np.float64,
    )


def world_matrix(transform) -> np.ndarray:
    chain = []
    current = transform
    while current:
        chain.append(local_matrix(current))
        current = current.m_Father.read() if current.m_Father else None
    result = np.eye(3)
    for matrix in reversed(chain):
        result = result @ matrix
    return result


def world_z(transform) -> float:
    z = 0.0
    current = transform
    while current:
        z += current.m_LocalPosition.z
        current = current.m_Father.read() if current.m_Father else None
    return z


def main() -> None:
    env = UnityPy.load(str(BUNDLE))
    layers = []

    for obj in env.objects:
        if obj.type.name != "SpriteRenderer":
            continue
        renderer = obj.read()
        if not renderer.m_Enabled or not renderer.m_Sprite:
            continue
        try:
            sprite = renderer.m_Sprite.read()
            texture = sprite.m_RD.texture.read()
        except FileNotFoundError:
            # The bundle also references generic effects and a shadow stored in
            # another bundle. They are not part of this character's artwork.
            continue

        transform = renderer.m_GameObject.read().m_Component[0].component.read()
        image = texture.image.convert("RGBA")
        pivot_x = sprite.m_Pivot.x * image.width
        pivot_y = (1.0 - sprite.m_Pivot.y) * image.height
        ppu = sprite.m_PixelsToUnits

        # Source image pixels (Y down) -> Unity world coordinates (Y up).
        pixel_to_local = np.array(
            [[1 / ppu, 0, -pivot_x / ppu], [0, -1 / ppu, pivot_y / ppu], [0, 0, 1]],
            dtype=np.float64,
        )
        matrix = world_matrix(transform) @ pixel_to_local
        layers.append((world_z(transform), sprite.m_Name, image, matrix, ppu))

    if not layers:
        raise RuntimeError("No self-contained SpriteRenderer layers found")

    corners = []
    for _, _, image, matrix, _ in layers:
        points = np.array(
            [[0, 0, 1], [image.width, 0, 1], [0, image.height, 1], [image.width, image.height, 1]],
            dtype=np.float64,
        ).T
        corners.extend((matrix @ points).T[:, :2])
    corners = np.asarray(corners)

    # Keep the source artwork at its native pixels-per-unit resolution.
    common_ppu = max(layer[4] for layer in layers)
    min_x, min_y = corners.min(axis=0)
    max_x, max_y = corners.max(axis=0)
    width = math.ceil((max_x - min_x) * common_ppu) + 2 * PADDING
    height = math.ceil((max_y - min_y) * common_ppu) + 2 * PADDING
    world_to_canvas = np.array(
        [[common_ppu, 0, -min_x * common_ppu + PADDING], [0, -common_ppu, max_y * common_ppu + PADDING], [0, 0, 1]],
        dtype=np.float64,
    )

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    # Unity camera is on the negative-Z side: larger Z is farther away.
    for _, name, image, matrix, _ in sorted(layers, key=lambda item: item[0], reverse=True):
        affine = (world_to_canvas @ matrix)[:2].astype(np.float32)
        rgba = np.asarray(image)
        warped = cv2.warpAffine(
            rgba,
            affine,
            (width, height),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )
        canvas.alpha_composite(Image.fromarray(warped, "RGBA"))
        print(f"placed {name}")

    canvas.save(OUTPUT)
    print(f"saved {OUTPUT} ({width}x{height})")


if __name__ == "__main__":
    main()
