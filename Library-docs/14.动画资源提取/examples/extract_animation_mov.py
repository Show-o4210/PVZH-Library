"""Render every 2D AnimationClip in a Unity AssetBundle to transparent MOV.

This extractor targets PVZH's generic (non-humanoid) 2D clips.  It decodes
StreamedClip polynomial coefficients and ConstantClip values, applies them to
the prefab hierarchy, renders a fixed canvas, and encodes ProRes 4444 files.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import UnityPy
from PIL import Image

from batch_rebuild_sprites import (
    collect_layers,
    find_root,
    get_transform,
    hierarchy_by_hash,
    is_descendant,
    load_with_dependencies,
    safe_name,
)


MAX_OUTPUT_PPU = 100.0
MAX_OUTPUT_DIMENSION = 2048


@dataclass
class StreamKey:
    time: float
    coeff: tuple[float, float, float, float]


def parse_streamed_clip(streamed) -> dict[int, list[StreamKey]]:
    """Decode Unity's uint32 StreamedClip buffer into scalar curve keys."""
    raw = struct.pack(f"<{len(streamed.data)}I", *streamed.data)
    curves: dict[int, list[StreamKey]] = {}
    offset = 0
    while offset < len(raw):
        time, count = struct.unpack_from("<fI", raw, offset)
        offset += 8
        for _ in range(count):
            index, c0, c1, c2, c3 = struct.unpack_from("<I4f", raw, offset)
            offset += 20
            # Sentinel frames carry tangent setup, not playable values.
            if math.isfinite(time) and time >= 0:
                curves.setdefault(index, []).append(StreamKey(time, (c0, c1, c2, c3)))
    return curves


def evaluate_polynomial_curve(keys: list[StreamKey], time: float, discrete: bool = False) -> float:
    """Evaluate Unity's cubic coefficient segment at time."""
    key = keys[0]
    for candidate in keys[1:]:
        if candidate.time > time + 1e-7:
            break
        key = candidate
    if discrete:
        return key.coeff[3]
    dt = max(0.0, time - key.time)
    c0, c1, c2, c3 = key.coeff
    return ((c0 * dt + c1) * dt + c2) * dt + c3


def scalar_values(clip, time: float) -> list[float]:
    """Return all scalar animation values in ClipBindingConstant order."""
    muscle = clip.m_MuscleClip
    packed = muscle.m_Clip.data
    values = [float(item.m_Start) for item in muscle.m_ValueArrayDelta]
    streamed = packed.m_StreamedClip
    dense = packed.m_DenseClip

    discrete_count = int(getattr(streamed, "discreteCurveCount", 0) or 0)
    streamed_count = streamed.curveCount + discrete_count
    for index, keys in parse_streamed_clip(streamed).items():
        if index < len(values) and keys:
            values[index] = evaluate_polynomial_curve(
                keys, time, discrete=index >= streamed.curveCount
            )

    dense_offset = streamed_count
    if dense.m_CurveCount:
        frame = min(
            max(int(round(time * dense.m_SampleRate)), 0),
            max(dense.m_FrameCount - 1, 0),
        )
        start = frame * dense.m_CurveCount
        for index in range(dense.m_CurveCount):
            values[dense_offset + index] = float(dense.m_SampleArray[start + index])

    constant_offset = streamed_count + dense.m_CurveCount
    for index, value in enumerate(packed.m_ConstantClip.data):
        if constant_offset + index < len(values):
            values[constant_offset + index] = float(value)
    return values


def evaluate_pose(clip, root_transform, time: float):
    """Map scalar clip values to Transform/SpriteRenderer/GameObject state."""
    transforms = hierarchy_by_hash(root_transform)
    values = scalar_values(clip, time)
    bindings = clip.m_ClipBindingConstant.genericBindings
    pptr_mapping = clip.m_ClipBindingConstant.pptrCurveMapping
    pose: dict[int, dict] = {}
    sprite_by_transform = {}
    active_by_transform = {}
    enabled_by_transform = {}
    alpha_by_transform = {}
    color_by_transform = {}
    cursor = 0
    unmatched = set()

    for binding in bindings:
        count = {1: 3, 2: 4, 3: 3, 4: 3}.get(binding.attribute, 1) if binding.typeID == 4 else 1
        current = values[cursor : cursor + count]
        cursor += count
        transform = transforms.get(binding.path)
        if transform is None:
            unmatched.add(int(binding.path))
            continue
        if len(current) != count:
            continue
        transform_id = transform.object_reader.path_id
        target = pose.setdefault(transform_id, {})
        if binding.typeID == 4 and binding.attribute == 1:
            target["position"] = type(transform.m_LocalPosition)(*current)
        elif binding.typeID == 4 and binding.attribute == 2:
            target["rotation"] = type(transform.m_LocalRotation)(*current)
        elif binding.typeID == 4 and binding.attribute == 3:
            target["scale"] = type(transform.m_LocalScale)(*current)
        elif binding.typeID == 4 and binding.attribute == 4:
            half_z = math.radians(current[2]) * 0.5
            target["rotation"] = type(transform.m_LocalRotation)(
                0.0, 0.0, math.sin(half_z), math.cos(half_z)
            )
        elif binding.typeID == 212 and binding.isPPtrCurve:
            index = int(round(current[0]))
            pointer = pptr_mapping[index] if 0 <= index < len(pptr_mapping) else None
            sprite_by_transform[transform_id] = pointer if pointer and pointer.path_id else None
        elif binding.typeID == 1 and binding.attribute == 0x7C5A22F6:
            active_by_transform[transform_id] = current[0] >= 0.5
        elif binding.typeID == 212 and binding.attribute == 0xC50BCE51:
            enabled_by_transform[transform_id] = current[0] >= 0.5
        elif binding.typeID == 212 and binding.attribute == 0x1222D899:
            alpha_by_transform[transform_id] = current[0]
        elif binding.typeID == 212 and binding.attribute in (0x969C9947, 0xFB417DAC, 0x8B2B8923):
            channel = {0x969C9947: "r", 0xFB417DAC: "g", 0x8B2B8923: "b"}[binding.attribute]
            color_by_transform.setdefault(transform_id, {})[channel] = current[0]

    return pose, sprite_by_transform, {
        "active": active_by_transform,
        "enabled": enabled_by_transform,
        "alpha": alpha_by_transform,
        "color": color_by_transform,
    }, unmatched


def animator_root_and_clips(env):
    """Follow the sample prefab Animator and its override controller."""
    for obj in env.objects:
        if obj.type.name != "Animator":
            continue
        animator = obj.read()
        root = get_transform(animator.m_GameObject.read())
        controller = animator.m_Controller.read() if animator.m_Controller else None
        clips = []
        if controller and hasattr(controller, "m_Clips"):
            for pair in controller.m_Clips:
                pointer = pair.m_OverrideClip or pair.m_OriginalClip
                try:
                    clip = pointer.read() if pointer else None
                except FileNotFoundError:
                    clip = None
                if clip and all(clip.object_reader.path_id != x.object_reader.path_id for x in clips):
                    clips.append(clip)
        if not clips:
            clips = [o.read() for o in env.objects if o.type.name == "AnimationClip"]
        return root, sorted(clips, key=lambda x: x.m_Name.lower())
    raise RuntimeError("Bundle contains no Animator")


def clips_for_root(env, root):
    """Resolve clips only through an Animator belonging to this prefab."""
    root_assets_file = root.object_reader.assets_file
    for obj in env.objects:
        if obj.type.name != "Animator":
            continue
        if obj.assets_file is not root_assets_file:
            continue
        animator = obj.read()
        transform = get_transform(animator.m_GameObject.read())
        if transform is None or not is_descendant(transform, root):
            continue
        controller = animator.m_Controller.read() if animator.m_Controller else None
        clips = []
        if controller and hasattr(controller, "m_Clips"):
            for pair in controller.m_Clips:
                for pointer in (pair.m_OverrideClip, pair.m_OriginalClip):
                    try:
                        clip = pointer.read() if pointer else None
                    except FileNotFoundError:
                        clip = None
                    if clip and all(clip.object_reader.path_id != x.object_reader.path_id for x in clips):
                        clips.append(clip)
                # An override wins for this state; remove its original slot.
                try:
                    override = pair.m_OverrideClip.read() if pair.m_OverrideClip else None
                    original = pair.m_OriginalClip.read() if pair.m_OriginalClip else None
                    if override and original:
                        clips = [x for x in clips if x.object_reader.path_id != original.object_reader.path_id]
                except FileNotFoundError:
                    pass
        if clips:
            return sorted(clips, key=lambda x: x.m_Name.lower())
    # Primary bundles normally contain only this prefab's clips. This fallback
    # is useful for simple effects without an override controller.
    return sorted(
        [obj.read() for obj in env.objects if obj.type.name == "AnimationClip"],
        key=lambda x: x.m_Name.lower(),
    )


def load_targeted_dependencies(bundle: Path, bundle_dir: Path, cab_index: dict, uuid: str):
    """Load only CABs referenced by this indexed prefab and its local clips."""
    initial = UnityPy.load(str(bundle))
    root = find_root(initial, uuid)
    if root is None:
        raise RuntimeError(f"Prefab root not found: {uuid}")
    required_file_ids = set()
    for obj in initial.objects:
        if obj.type.name == "SpriteRenderer":
            renderer = obj.read()
            transform = get_transform(renderer.m_GameObject.read())
            if transform is not None and is_descendant(transform, root) and renderer.m_Sprite:
                if renderer.m_Sprite.file_id > 0:
                    required_file_ids.add(int(renderer.m_Sprite.file_id))
        elif obj.type.name == "Animator":
            animator = obj.read()
            transform = get_transform(animator.m_GameObject.read())
            if transform is not None and is_descendant(transform, root) and animator.m_Controller:
                if animator.m_Controller.file_id > 0:
                    required_file_ids.add(int(animator.m_Controller.file_id))
        elif obj.type.name == "AnimationClip":
            clip = obj.read()
            for pointer in clip.m_ClipBindingConstant.pptrCurveMapping:
                if pointer.file_id > 0:
                    required_file_ids.add(int(pointer.file_id))

    dependency_paths = []
    seen = set()
    for top_file in initial.files.values():
        for asset_file in getattr(top_file, "files", {}).values():
            externals = list(getattr(asset_file, "externals", []))
            for file_id in sorted(required_file_ids):
                if not 1 <= file_id <= len(externals):
                    continue
                cab_name = Path(externals[file_id - 1].path).name.lower()
                dependency_name = cab_index.get(cab_name)
                if not dependency_name or dependency_name in seen:
                    continue
                candidate = bundle_dir / dependency_name
                if candidate.is_file():
                    dependency_paths.append(str(candidate))
                    seen.add(dependency_name)
    if not dependency_paths:
        return initial, [], sorted(required_file_ids)
    return UnityPy.load(str(bundle), *dependency_paths), dependency_paths, sorted(required_file_ids)


def layer_corners(layers):
    points = np.array(
        [[0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]], dtype=np.float64
    ).T
    corners = []
    for layer in layers:
        scaled = points.copy()
        scaled[0] *= layer["image"].width
        scaled[1] *= layer["image"].height
        corners.extend((layer["matrix"] @ scaled).T[:, :2])
    return corners


def render_fixed(layers, bounds, ppu: float, padding: int, supersample: int = 1) -> Image.Image:
    min_x, min_y, max_x, max_y = bounds
    width = math.ceil((max_x - min_x) * ppu) + 2 * padding
    height = math.ceil((max_y - min_y) * ppu) + 2 * padding
    # ProRes works most reliably with even dimensions.
    width += width % 2
    height += height % 2
    if width <= 0 or height <= 0 or width * height > 100_000_000:
        raise ValueError(f"invalid output dimensions: {width}x{height}")
    high_width, high_height = width * supersample, height * supersample
    high_ppu = ppu * supersample
    high_padding = padding * supersample
    world_to_canvas = np.array(
        [[high_ppu, 0, -min_x * high_ppu + high_padding], [0, -high_ppu, max_y * high_ppu + high_padding], [0, 0, 1]],
        dtype=np.float64,
    )
    canvas = Image.new("RGBA", (high_width, high_height), (0, 0, 0, 0))
    for layer in sorted(layers, key=lambda x: (x["sorting_layer"], x["sorting_order"], -x["z"])):
        affine = (world_to_canvas @ layer["matrix"])[:2].astype(np.float32)
        source_corners = np.array(
            [[0, 0, 1], [layer["image"].width, 0, 1],
             [0, layer["image"].height, 1],
             [layer["image"].width, layer["image"].height, 1]],
            dtype=np.float32,
        ).T
        transformed = (affine @ source_corners).T
        x0 = max(0, int(math.floor(float(transformed[:, 0].min()))) - 2)
        y0 = max(0, int(math.floor(float(transformed[:, 1].min()))) - 2)
        x1 = min(high_width, int(math.ceil(float(transformed[:, 0].max()))) + 2)
        y1 = min(high_height, int(math.ceil(float(transformed[:, 1].max()))) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        local_affine = affine.copy()
        local_affine[0, 2] -= x0
        local_affine[1, 2] -= y0
        rgba = np.asarray(layer["image"], dtype=np.float32) / 255.0
        rgba[:, :, :3] *= rgba[:, :, 3:4]
        warped = cv2.warpAffine(
            rgba, local_affine, (x1 - x0, y1 - y0),
            flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )
        alpha = np.clip(warped[:, :, 3:4], 0.0, 1.0)
        straight = np.zeros_like(warped)
        straight[:, :, 3:4] = alpha
        np.divide(warped[:, :, :3], alpha, out=straight[:, :, :3], where=alpha > 1e-6)
        straight = np.clip(straight * 255.0, 0, 255).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(straight, "RGBA"), dest=(x0, y0))
    return canvas.resize((width, height), Image.Resampling.LANCZOS)


def encode_mov(frame_dir: Path, fps: float, output: Path) -> None:
    """Encode lossless RGBA with the PNG video codec inside MOV."""
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", f"{fps:g}", "-i", str(frame_dir / "%04d.png"),
        "-c:v", "png", "-pred", "mixed", "-pix_fmt", "rgba", str(output),
    ]
    subprocess.run(command, check=True)


def choose_key_color(samples) -> tuple[int, int, int]:
    """Choose a saturated background farthest from this character's pixels."""
    candidates = np.array([
        (255, 0, 255), (0, 255, 0), (0, 255, 255),
        (0, 0, 255), (255, 0, 0), (255, 255, 0),
    ], dtype=np.float32)
    pixels = []
    seen = set()
    for layers in samples:
        for layer in layers:
            key = (layer["name"], layer["image"].size)
            if key in seen:
                continue
            seen.add(key)
            image = layer["image"].copy()
            image.thumbnail((128, 128), Image.Resampling.BILINEAR)
            rgba = np.asarray(image, dtype=np.uint8)
            pixels.append(rgba[:, :, :3][rgba[:, :, 3] >= 32])
    if not pixels:
        return 255, 0, 255
    colors = np.concatenate(pixels).astype(np.float32)
    # A low percentile is robust to isolated antialias pixels while still
    # avoiding colors used by a meaningful part of the artwork.
    distances = np.sqrt(((colors[:, None, :] - candidates[None, :, :]) ** 2).sum(axis=2))
    scores = np.percentile(distances, 2.0, axis=0)
    return tuple(int(x) for x in candidates[int(np.argmax(scores))])


def encode_mp4(frame_dir: Path, fps: float, size, key_color, output: Path) -> None:
    width, height = size
    color = "0x" + "".join(f"{channel:02X}" for channel in key_color)
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", f"{fps:g}", "-i", str(frame_dir / "%04d.png"),
        "-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}:r={fps:g}",
        "-filter_complex", "[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-movflags", "+faststart",
        str(output),
    ]
    subprocess.run(command, check=True)


def open_raw_mp4_encoder(fps: float, size, key_color, output: Path):
    """Accept raw RGBA frames on stdin and encode the keyed MP4 directly."""
    width, height = size
    color = "0x" + "".join(f"{channel:02X}" for channel in key_color)
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{width}x{height}",
        "-r", f"{fps:g}", "-i", "pipe:0",
        "-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}:r={fps:g}",
        "-filter_complex", "[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-movflags", "+faststart",
        str(output),
    ]
    return subprocess.Popen(command, stdin=subprocess.PIPE)


def render_clip(
    env, root, clip, output_root: Path, keep_frames: bool,
    card_key_color=None, output_name=None, include_mov: bool = False,
) -> dict:
    name = safe_name(output_name or clip.m_Name)
    clip_dir = output_root / name
    frame_dir = clip_dir / "frames"
    clip_dir.mkdir(parents=True, exist_ok=True)
    if include_mov or keep_frames:
        frame_dir.mkdir(parents=True, exist_ok=True)
    fps = float(clip.m_SampleRate or 30.0)
    duration = max(float(clip.m_MuscleClip.m_StopTime), 0.0)
    frame_count = max(1, int(round(duration * fps)) + 1)
    samples = []
    all_corners = []
    ppu = 1.0
    unmatched = set()
    empty_frames = []

    for frame in range(frame_count):
        time = min(frame / fps, duration)
        pose, sprites, visibility, missing = evaluate_pose(clip, root, time)
        layers = collect_layers(env, root, pose, sprites, visibility)
        if not layers:
            # Death/exit clips may intentionally end with every node inactive.
            empty_frames.append(frame)
        samples.append(layers)
        all_corners.extend(layer_corners(layers))
        if layers:
            ppu = max(ppu, *(float(layer["ppu"]) for layer in layers))
        unmatched.update(missing)

    if not all_corners:
        raise RuntimeError(f"{clip.m_Name} has no visible frame")
    corners = np.asarray(all_corners)
    min_x, min_y = corners.min(axis=0)
    max_x, max_y = corners.max(axis=0)
    bounds = (float(min_x), float(min_y), float(max_x), float(max_y))
    # External A packages often contain 400-PPU source art. Using the maximum
    # source PPU for the entire canvas inflates videos to 4x width/height and
    # 16x pixel work. Sprite PPU has already established correct world size;
    # cap only the final raster density at Unity's conventional 100 PPU.
    ppu = min(ppu, MAX_OUTPUT_PPU)
    world_width = max_x - min_x
    world_height = max_y - min_y
    usable_dimension = MAX_OUTPUT_DIMENSION - 24
    if world_width > 0 and world_height > 0:
        ppu = min(ppu, usable_dimension / max(world_width, world_height))
    size = None
    key_color = card_key_color or choose_key_color(samples)
    mp4 = clip_dir / f"{name}.mp4"
    encoder = None
    for frame, layers in enumerate(samples):
        image = render_fixed(layers, bounds, ppu, padding=12)
        size = image.size
        if encoder is None and not include_mov:
            encoder = open_raw_mp4_encoder(fps, size, key_color, mp4)
        if encoder is not None:
            encoder.stdin.write(image.tobytes())
        if include_mov or keep_frames:
            image.save(frame_dir / f"{frame:04d}.png")

    mov = None
    if encoder is not None:
        encoder.stdin.close()
        return_code = encoder.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, encoder.args)
    if include_mov:
        mov = clip_dir / f"{name}.mov"
        encode_mov(frame_dir, fps, mov)
        encode_mp4(frame_dir, fps, size, key_color, mp4)
    info = {
        "clip": clip.m_Name,
        "output_name": name,
        "fps": fps,
        "duration": duration,
        "frames": frame_count,
        "size": list(size),
        "output_ppu": ppu,
        "max_output_dimension": MAX_OUTPUT_DIMENSION,
        "mp4": str(mp4),
        "key_color_rgb": list(key_color),
        "key_color_hex": "#" + "".join(f"{channel:02X}" for channel in key_color),
        "empty_frames": empty_frames,
        "unmatched_path_hashes": sorted(unmatched),
    }
    if mov is not None:
        info["mov"] = str(mov)
    (clip_dir / "clip.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    if (include_mov or keep_frames) and not keep_frames:
        shutil.rmtree(frame_dir)
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", nargs="?", type=Path, default=Path("2ceeb890a69397041ba1fd559056c358_1"))
    parser.add_argument("--output", type=Path, default=Path("动画输出") / "Guacodile")
    parser.add_argument("--clip", help="Only render clips containing this text")
    parser.add_argument("--uuid", help="Select the indexed prefab root by UUID")
    parser.add_argument("--name-cn", help="Chinese card name used for shared output filenames")
    parser.add_argument("--bundles", type=Path, help="Bundle directory used to resolve CAB dependencies")
    parser.add_argument("--cab-index", type=Path, default=Path("cab_index.json"))
    parser.add_argument("--keep-frames", action="store_true", help="Keep intermediate PNG sequences")
    parser.add_argument("--include-mov", action="store_true", help="Also create a lossless transparent MOV")
    args = parser.parse_args()

    dependencies = []
    if args.bundles:
        cab_payload = json.loads(args.cab_index.read_text(encoding="utf-8"))
        cab_index = cab_payload.get("cabs", cab_payload)
        if args.uuid:
            env, dependencies, required_file_ids = load_targeted_dependencies(
                args.bundle, args.bundles, cab_index, args.uuid
            )
        else:
            env, dependencies = load_with_dependencies(args.bundle, args.bundles, cab_index)
            required_file_ids = []
    else:
        env = UnityPy.load(str(args.bundle))
    if args.uuid:
        root = find_root(env, args.uuid)
        if root is None:
            raise RuntimeError(f"Prefab root not found: {args.uuid}")
        clips = clips_for_root(env, root)
    else:
        root, clips = animator_root_and_clips(env)
    if args.clip:
        clips = [clip for clip in clips if args.clip.lower() in clip.m_Name.lower()]
    args.output.mkdir(parents=True, exist_ok=True)
    # Pick one chroma-key color for the whole card, sampling the beginning and
    # midpoint of every selected action.
    key_samples = []
    for clip in clips:
        duration = max(float(clip.m_MuscleClip.m_StopTime), 0.0)
        for time in {0.0, duration * 0.5}:
            pose, sprites, visibility, _missing = evaluate_pose(clip, root, time)
            layers = collect_layers(env, root, pose, sprites, visibility)
            if layers:
                key_samples.append(layers)
    card_key_color = choose_key_color(key_samples)
    def action_name_cn(clip_name: str) -> str:
        lower = clip_name.lower().replace(" ", "_")
        rules = [
            (("special_down", "power_down"), "向下特殊技能"),
            (("special_up", "power_up"), "向上特殊技能"),
            (("attack_down",), "向下攻击"),
            (("attack_up",), "向上攻击"),
            (("power_activated",), "能力激活"),
            (("special", "ability", "power"), "特殊技能"),
            (("damage", "hurt"), "受伤"),
            (("inhand", "in_hand"), "手牌"),
            (("enter", "spawn"), "登场"),
            (("ko_idle",), "击倒待机"),
            (("idle",), "待机"),
            (("attack",), "攻击"),
            (("die", "death", "lose"), "死亡"),
            (("win",), "胜利"),
            (("celebrate",), "庆祝"),
            (("block",), "格挡"),
            (("take",), "获得增益"),
            (("think",), "思考"),
            (("tense",), "警戒"),
            (("nod",), "点头"),
        ]
        for needles, label in rules:
            if any(needle in lower for needle in needles):
                suffix = ""
                match = re.search(r"(?:_|\s)(\d+)$", clip_name)
                if match:
                    suffix = match.group(1)
                return label + suffix
        return "动作_" + safe_name(clip_name)

    output_names = []
    used_names = set()
    for clip in clips:
        base = action_name_cn(clip.m_Name)
        if args.name_cn:
            base = f"{safe_name(args.name_cn)}_{base}"
        candidate = base
        serial = 2
        while candidate in used_names:
            candidate = f"{base}_{serial}"
            serial += 1
        used_names.add(candidate)
        output_names.append(candidate)
    results = []
    for clip, output_name in zip(clips, output_names):
        print(f"rendering {clip.m_Name} ...", flush=True)
        results.append(render_clip(
            env, root, clip, args.output, args.keep_frames, card_key_color, output_name
            , args.include_mov
        ))
    report = {
        "bundle": str(args.bundle),
        "root": root.m_GameObject.read().m_Name,
        "dependency_bundles": [Path(path).name for path in dependencies],
        "required_external_file_ids": required_file_ids if args.bundles else [],
        "key_color_rgb": list(card_key_color),
        "key_color_hex": "#" + "".join(f"{channel:02X}" for channel in card_key_color),
        "clips": results,
    }
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done: {len(results)} clips -> {args.output}")


if __name__ == "__main__":
    main()
