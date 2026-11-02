import os

import UnityPy

from animator import inject_animation_clips, summarize_animation_results
from cleaner import (
    prune_all_transform_children,
    remove_broken_sprite_renderers,
    remove_generic_external_renderers,
    remove_old_textures,
    remove_orphan_sprites,
    remove_orphan_transforms,
    sanitize_mono_behaviour_pptrs,
    strip_broken_sprite_renderers_from_gameobject,
)
from config import (
    DEFAULT_PIXELS_TO_UNITS,
    DEFAULT_Y_OFFSET,
    INPUT_DIR,
    OUTPUT_DIR,
    ROOT_POSITION,
    SCRIPT_VERSION,
    SHIP_TEXTURE_SIZE,
    SKINS_DIR,
    TEMPLATE_MAP,
    TEXTURE_ID,
    TRANSFORM_ID,
    init_folders,
)
from injector import (
    finalize_root_transform,
    inject_templates,
    patch_character_gameobject,
    patch_character_renderer,
    patch_character_sprite,
    patch_character_transform,
    patch_ship_texture,
    patch_texture,
    prepare_ship_texture_image,
)
from pairing import build_pairing_plan, list_bundle_files, list_skin_files, print_pairing_plan
from progress import record_run_progress
from tasks import (
    ensure_tasks,
    iter_runnable_tasks,
    mark_task_completed,
    print_skip_completed,
    print_tasks_summary,
)
from scanner import (
    build_type_refs,
    collect_ship_protected_ids,
    describe_ship_protected_assets,
    find_big_hash_root,
    find_ship_inhand_texture,
)
from validator import verify_saved_bundle, write_verification_report


def process_single_bundle(
    bundle_name,
    png_name,
    pairing_mode="manual",
    pixels_to_units=DEFAULT_PIXELS_TO_UNITS,
    y_offset=DEFAULT_Y_OFFSET,
):
    bundle_path = os.path.join(INPUT_DIR, bundle_name)
    png_path = os.path.join(SKINS_DIR, png_name)
    output_path = os.path.join(OUTPUT_DIR, bundle_name)

    print(f"\n🚀 [流水线] 开始对目标源包进行重构手术: {bundle_name}")
    print(f"   🎨 [配对] 皮肤: {png_name}  (模式: {pairing_mode})")
    print(
        f"   📐 [配置] pixels_to_units={pixels_to_units}  |  y_offset={y_offset}"
    )
    env = UnityPy.load(bundle_path)

    root_transform, max_components = find_big_hash_root(env)
    if not root_transform:
        print("❌ 错误: 未能定位核心大哈希 GameObject 或顶级大根 Transform，终止。")
        return {"bundle": bundle_name, "success": False, "error": "未能定位大根 Transform"}

    root_path_id = root_transform.object_reader.path_id
    serialized_file = root_transform.object_reader.assets_file
    refs = build_type_refs(env)
    root_go_name = root_transform.m_GameObject.read().m_Name

    print(f"   🔍 [特征锁定] 成功抓到核心大哈希! 组件数: {max_components}")
    print(
        f"   🔍 [特征锁定] 成功锁定顶级大根 Transform! "
        f"PathID={root_path_id} name={root_go_name!r}"
    )

    protected_ids = collect_ship_protected_ids(env)
    ship_assets = describe_ship_protected_assets(env)
    if ship_assets:
        preserved = ", ".join(
            f"{asset['type']}({asset['name']})" for asset in ship_assets
        )
        print(f"   ├── [保留] ship 加载资源 {len(ship_assets)} 项: {preserved}")

    deleted_count = remove_old_textures(serialized_file, protected_ids)
    print(f"   ├── [清理] 已无损抹除 {deleted_count} 个原厂旧贴图")

    generic_count, generic_names = remove_generic_external_renderers(serialized_file)
    if generic_count:
        print(
            f"   ├── [剔除] 已移除 {generic_count} 个外部通用 Renderer: "
            f"{', '.join(generic_names)}"
        )

    inject_templates(serialized_file, refs, TEMPLATE_MAP)

    patch_texture(serialized_file, png_path)
    print(f"   ├── [覆写] 新 1024x1024 贴图已灌入 Texture2D({TEXTURE_ID})")

    ship_texture = find_ship_inhand_texture(ship_assets)
    if ship_texture:
        ship_image = prepare_ship_texture_image(png_path)
        patch_ship_texture(
            serialized_file,
            ship_texture["path_id"],
            ship_image,
            ship_texture["name"],
        )
        print(
            f"   ├── [卡牌] ship Texture2D 已同步皮肤 "
            f"({SHIP_TEXTURE_SIZE}x{SHIP_TEXTURE_SIZE} 居中裁剪适配，Sprite 保持不变)"
        )

    patch_character_sprite(serialized_file, pixels_to_units, png_path=png_path)
    print(
        f"   ├── [Sprite] 已重建 Tight/FullRect 四顶点网格；"
        f"m_PixelsToUnits={pixels_to_units}"
    )

    patch_character_gameobject(serialized_file)
    patch_character_transform(serialized_file, root_path_id, y_offset=y_offset)
    patch_character_renderer(serialized_file, refs)
    print("   ├── [修正] 已按 ro 参考重绑 GameObject / Transform / SpriteRenderer")
    print(f"   ├── [归零] character({TRANSFORM_ID}) 与大根旋转已强制置为 (0, 0, 0, 1)")

    sprite_removed = remove_orphan_sprites(serialized_file, protected_ids)
    broken_renderer_removed = remove_broken_sprite_renderers(
        serialized_file, protected_ids, keep_ids={root_path_id}
    )
    root_renderer_stripped = strip_broken_sprite_renderers_from_gameobject(
        serialized_file, root_transform.m_GameObject.path_id
    )
    broken_renderer_removed += root_renderer_stripped
    orphan_transform_removed = remove_orphan_transforms(
        serialized_file, keep_ids={root_path_id}
    )
    kept_sprite_count = 1 + sum(
        1 for asset in ship_assets if asset["type"] == "Sprite"
    )
    print(
        f"   ├── [清理] 已删除 {sprite_removed} 个悬空原厂 Sprite，"
        f"保留 {kept_sprite_count} 个（character + ship）"
    )
    if broken_renderer_removed:
        print(
            f"   ├── [清理] 已移除 {broken_renderer_removed} 个断裂 SpriteRenderer 节点"
        )
    if orphan_transform_removed:
        print(
            f"   ├── [清理] 已移除 {orphan_transform_removed} 个悬空 Transform 子树"
        )

    pruned_children = prune_all_transform_children(serialized_file)
    if pruned_children:
        print(f"   ├── [清理] 已修剪 {pruned_children} 个 Transform 的失效子节点引用")

    stitched = finalize_root_transform(serialized_file, root_path_id)
    if stitched:
        print(f"   ├── [缝合] 顶级大根已安全接纳纸片人 Transform({TRANSFORM_ID})")
    print(
        f"   ├── [对齐] 大根位置已设为 ro 标准值 "
        f"({ROOT_POSITION[0]}, {ROOT_POSITION[1]}, {ROOT_POSITION[2]})"
    )

    animation_results = inject_animation_clips(serialized_file)
    print(f"   ├── [动画] {summarize_animation_results(animation_results)}")

    mono_fixed, mono_fix_details = sanitize_mono_behaviour_pptrs(serialized_file)
    if mono_fixed:
        print(
            f"   ├── [修正] 已修复 {mono_fixed} 个 MonoBehaviour 的断裂内部引用"
        )

    bundle_bytes = env.file.save()
    report = verify_saved_bundle(
        bundle_bytes,
        root_path_id,
        pixels_to_units=pixels_to_units,
        y_offset=y_offset,
        ship_assets=ship_assets,
    )
    report_path = write_verification_report(bundle_name, report, pairing_mode, png_name)
    print("   ├── [校验] 纸片人五件套关键引用链全部通畅")
    print(f"   ├── [报告] 校验报告已写入 {os.path.basename(report_path)}")

    with open(output_path, "wb") as output_file:
        output_file.write(bundle_bytes)
    print("✨ 重构完毕！魔改后的包已放入 5_output_bundles/")
    return {
        "bundle": bundle_name,
        "skin": png_name,
        "pairing_mode": pairing_mode,
        "success": True,
        "report_path": report_path,
    }


def main():
    print("==================================================")
    print(f"📦 Unity 独立单位纸片人 Mod 自动化重构流水线 v{SCRIPT_VERSION}")
    print("      (tasks.json 任务驱动 + 断点续传 + 单位级配置外挂)")
    print("==================================================")

    init_folders()

    skin_files = list_skin_files()
    bundle_files = list_bundle_files()

    if not skin_files:
        print("\n📭 提示: [2_new_skins] 中需要至少 1 张 PNG 皮肤。")
        return
    if not bundle_files:
        print("\n📭 提示: [1_input_bundles] 中需要至少 1 个原版包。")
        return

    tasks, created = ensure_tasks(bundle_files, skin_files)
    if created:
        print("\n📝 [初始化] 已自动生成 tasks.json 任务清单")
    print_pairing_plan(build_pairing_plan(bundle_files, skin_files, tasks=tasks))
    print_tasks_summary(tasks)

    pending_tasks = [
        (bundle_name, task)
        for bundle_name, task, state in iter_runnable_tasks(tasks)
        if state == "pending"
    ]
    if not pending_tasks and not any(
        state == "completed"
        for _, _, state in iter_runnable_tasks(tasks)
    ):
        print(
            "\n📭 没有可执行的配对。"
            "请确保 [2_new_skins] 中皮肤数量不少于待处理包数（盲缝按顺序 1:1 分配，不重复使用）。"
        )
        record_run_progress(
            tasks=tasks,
            results=[],
            attempted=0,
            success_count=0,
            skipped=0,
        )
        return

    print("\n--------------------------------------------------")
    results = []
    attempted = 0
    for bundle_name, task, state in iter_runnable_tasks(tasks):
        if state == "completed":
            print_skip_completed(bundle_name)
            continue
        if state == "unmatched":
            print(f"⚠️  [跳过] {bundle_name} 未配对皮肤 (status=unmatched)")
            continue

        attempted += 1
        try:
            result = process_single_bundle(
                bundle_name,
                task["skin_image"],
                task.get("pairing_mode", "manual"),
                pixels_to_units=task.get("pixels_to_units", DEFAULT_PIXELS_TO_UNITS),
                y_offset=task.get("y_offset", DEFAULT_Y_OFFSET),
            )
            if result:
                if result.get("success"):
                    mark_task_completed(tasks, bundle_name)
                results.append(result)
        except Exception as error:
            print(f"❌ 重构翻车 ({bundle_name}): {error}")
            results.append(
                {
                    "bundle": bundle_name,
                    "skin": task["skin_image"],
                    "pairing_mode": task.get("pairing_mode", "manual"),
                    "success": False,
                    "error": str(error),
                }
            )

    success_count = sum(1 for result in results if result.get("success"))
    skipped = sum(
        1 for _, _, state in iter_runnable_tasks(tasks) if state == "completed"
    )
    print("\n==================================================")
    print(
        f"🏁 批量作业结束: 本次处理 {attempted} 个，成功 {success_count} 个，"
        f"累计已完成 {skipped} 个"
    )
    if attempted and success_count < attempted:
        failed = [result["bundle"] for result in results if not result.get("success")]
        print(f"   失败: {', '.join(failed)}")
    print("==================================================")

    record_run_progress(
        tasks=tasks,
        results=results,
        attempted=attempted,
        success_count=success_count,
        skipped=skipped,
    )