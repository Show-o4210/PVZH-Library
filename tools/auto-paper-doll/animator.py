import copy
import os

from config import ANIMS_DIR, CHARACTER_NODE_NAME
from dump_parser import parse_uabea_dump

ANIM_KEYWORDS = (
    "attack",
    "idle",
    "damage",
    "die",
    "enter",
    "inhand",
    "special",
)

LEGACY_CURVE_FIELDS = (
    "m_RotationCurves",
    "m_CompressedRotationCurves",
    "m_EulerCurves",
    "m_PositionCurves",
    "m_ScaleCurves",
    "m_FloatCurves",
    "m_PPtrCurves",
)

# 手动对齐的 UABEA Dump 使用的 character 绑定路径哈希
CHARACTER_PATH_HASH = 2474291252


def unity_string_hash(name):
    hash_value = 0
    for char in name:
        hash_value = (hash_value * 31 + ord(char)) & 0xFFFFFFFF
    return hash_value


def classify_clip_name(clip_name):
    lower_name = clip_name.lower()
    for keyword in ANIM_KEYWORDS:
        if keyword in lower_name:
            return keyword
    return None


def load_animation_dumps():
    dumps = {}
    if not os.path.isdir(ANIMS_DIR):
        return dumps

    for file_name in os.listdir(ANIMS_DIR):
        if not file_name.lower().endswith(".txt"):
            continue
        stem = os.path.splitext(file_name)[0].lower()
        dump_path = os.path.join(ANIMS_DIR, file_name)
        with open(dump_path, "r", encoding="utf-8") as dump_file:
            dumps[stem] = parse_uabea_dump(dump_file.read())
    return dumps


def collect_allowed_binding_paths(animation_dumps):
    allowed = {0, CHARACTER_PATH_HASH, unity_string_hash(CHARACTER_NODE_NAME)}
    for typetree in animation_dumps.values():
        bindings = typetree.get("m_ClipBindingConstant", {}).get("genericBindings", [])
        for binding in bindings:
            allowed.add(binding["path"])
    return allowed


def _redirect_legacy_curve_paths(clip, character_node_name):
    redirected = 0
    for field_name in LEGACY_CURVE_FIELDS:
        curves = getattr(clip, field_name, None)
        if not curves:
            continue
        for curve in curves:
            path = getattr(curve, "path", None)
            if path in (None, "", character_node_name):
                continue
            curve.path = character_node_name
            redirected += 1
    return redirected


def _redirect_generic_bindings(clip, character_path_hash, preserve_root_motion):
    bindings = clip.m_ClipBindingConstant.genericBindings
    redirected = 0
    preserved_root = 0

    for binding in bindings:
        if preserve_root_motion and binding.path == 0:
            preserved_root += 1
            continue
        if binding.path == character_path_hash:
            continue
        binding.path = character_path_hash
        redirected += 1

    return redirected, preserved_root


def patch_animation_clip_fallback(
    clip,
    character_path_hash=CHARACTER_PATH_HASH,
    preserve_root_motion=True,
):
    binding_redirected, root_preserved = _redirect_generic_bindings(
        clip, character_path_hash, preserve_root_motion
    )
    legacy_redirected = _redirect_legacy_curve_paths(clip, CHARACTER_NODE_NAME)
    changed = binding_redirected > 0 or legacy_redirected > 0
    if changed:
        clip.save()
    return {
        "mode": "path_redirect",
        "binding_redirected": binding_redirected,
        "legacy_redirected": legacy_redirected,
        "root_preserved": root_preserved,
        "character_path_hash": character_path_hash,
        "changed": changed,
    }


def inject_animation_clips(serialized_file, animation_dumps=None):
    if animation_dumps is None:
        animation_dumps = load_animation_dumps()

    results = []
    for path_id, obj in list(serialized_file.objects.items()):
        if obj.type.name != "AnimationClip":
            continue

        clip_name = obj.read().m_Name
        keyword = classify_clip_name(clip_name)
        if keyword and keyword in animation_dumps:
            original_typetree = obj.read_typetree()
            typetree = copy.deepcopy(animation_dumps[keyword])
            typetree["m_Name"] = clip_name
            if "m_Events" in original_typetree:
                typetree["m_Events"] = copy.deepcopy(original_typetree["m_Events"])
            obj.save_typetree(typetree)
            serialized_file.mark_changed()
            bindings = typetree["m_ClipBindingConstant"]["genericBindings"]
            binding_paths = sorted({binding["path"] for binding in bindings})
            results.append(
                {
                    "path_id": path_id,
                    "clip_name": clip_name,
                    "keyword": keyword,
                    "mode": "dump_import",
                    "dump_file": f"{keyword}.txt",
                    "binding_count": len(bindings),
                    "binding_paths": binding_paths,
                    "muscle_clip_size": typetree.get("m_MuscleClipSize"),
                    "changed": True,
                }
            )
            continue

        clip = obj.read()
        patch_result = patch_animation_clip_fallback(clip)
        if patch_result["changed"] or keyword:
            serialized_file.mark_changed()
            results.append(
                {
                    "path_id": path_id,
                    "clip_name": clip_name,
                    "keyword": keyword,
                    **patch_result,
                }
            )

    return results


def summarize_animation_results(results):
    if not results:
        return "未发现 AnimationClip"

    dump_imported = [entry for entry in results if entry.get("mode") == "dump_import"]
    redirected = [entry for entry in results if entry.get("mode") == "path_redirect"]
    keywords = sorted({entry["keyword"] for entry in results if entry.get("keyword")})

    parts = [f"处理 {len(results)} 个 AnimationClip"]
    if dump_imported:
        parts.append(f"Dump 注入 {len(dump_imported)} 个")
    if redirected:
        parts.append(f"路径重定向 {len(redirected)} 个")
    if keywords:
        parts.append(f"关键词: {', '.join(keywords)}")
    return "；".join(parts)


# 兼容旧调用名
redirect_animation_clips = inject_animation_clips