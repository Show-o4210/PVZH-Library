import json
import os

from config import (
    DEFAULT_PIXELS_TO_UNITS,
    DEFAULT_Y_OFFSET,
    SKINS_DIR,
    TASKS_FILE,
)
from pairing import build_pairing_plan

GREEN = "\033[32m"
RESET = "\033[0m"


def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, "r", encoding="utf-8") as tasks_file:
        try:
            return json.load(tasks_file)
        except json.JSONDecodeError as error:
            backup_path = f"{TASKS_FILE}.corrupt"
            os.replace(TASKS_FILE, backup_path)
            raise ValueError(
                f"tasks.json 格式损坏（{error}），已备份为 {os.path.basename(backup_path)}，"
                "将按当前 input/skins 重新生成。"
            ) from error


def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as tasks_file:
        json.dump(tasks, tasks_file, ensure_ascii=False, indent=2)
        tasks_file.write("\n")


def _skin_file_exists(skin_image):
    return bool(
        skin_image
        and os.path.isfile(os.path.join(SKINS_DIR, skin_image))
    )


def _default_task_entry(skin_image, pairing_mode):
    return {
        "skin_image": skin_image,
        "status": "pending" if skin_image else "unmatched",
        "pixels_to_units": DEFAULT_PIXELS_TO_UNITS,
        "y_offset": DEFAULT_Y_OFFSET,
        "pairing_mode": pairing_mode,
    }


def _should_refresh_pairing(task):
    if task.get("status") == "completed":
        return False
    if task.get("pairing_locked"):
        return False
    return True


def _apply_pairing_plan(task, skin_image, pairing_mode):
    changed = False
    resolved_mode = pairing_mode or "manual"

    if task.get("skin_image") != skin_image:
        task["skin_image"] = skin_image
        changed = True
    if task.get("pairing_mode") != resolved_mode:
        task["pairing_mode"] = resolved_mode
        changed = True

    if skin_image:
        if task.get("status") in ("unmatched", None):
            task["status"] = "pending"
            changed = True
    elif task.get("status") != "unmatched":
        task["status"] = "unmatched"
        changed = True

    return changed


def ensure_tasks(bundle_files, skin_files):
    created = not os.path.exists(TASKS_FILE)
    try:
        tasks = load_tasks()
    except ValueError as error:
        print(f"⚠️  {error}")
        tasks = {}
        created = True
    plan = build_pairing_plan(bundle_files, skin_files, tasks=tasks)
    plan_by_bundle = {entry["bundle"]: entry for entry in plan}
    bundle_set = set(bundle_files)
    changed = created

    stale_bundles = [name for name in tasks if name not in bundle_set]
    for bundle_name in stale_bundles:
        del tasks[bundle_name]
        changed = True

    for entry in plan:
        bundle_name = entry["bundle"]
        skin_image = entry["skin"]
        pairing_mode = entry["mode"]

        if bundle_name not in tasks:
            tasks[bundle_name] = _default_task_entry(skin_image, pairing_mode)
            changed = True
            continue

        task = tasks[bundle_name]
        if not _skin_file_exists(task.get("skin_image")):
            if task.get("skin_image"):
                task["skin_image"] = None
                if task.get("status") != "completed":
                    task["status"] = "unmatched"
                changed = True

        if _should_refresh_pairing(task):
            if _apply_pairing_plan(task, skin_image, pairing_mode):
                changed = True
        elif skin_image and not task.get("skin_image"):
            task["skin_image"] = skin_image
            if task.get("status") == "unmatched":
                task["status"] = "pending"
            changed = True

        task.setdefault("pixels_to_units", DEFAULT_PIXELS_TO_UNITS)
        task.setdefault("y_offset", DEFAULT_Y_OFFSET)
        task.setdefault("pairing_mode", pairing_mode or "manual")
        task.setdefault("status", "pending" if task.get("skin_image") else "unmatched")

    for bundle_name, task in tasks.items():
        if task.get("status") == "completed":
            continue
        if not _skin_file_exists(task.get("skin_image")):
            entry = plan_by_bundle.get(bundle_name, {})
            if _should_refresh_pairing(task):
                if _apply_pairing_plan(
                    task,
                    entry.get("skin"),
                    entry.get("mode"),
                ):
                    changed = True

    if changed:
        save_tasks(tasks)

    return tasks, created


def print_tasks_summary(tasks):
    pending = sum(1 for task in tasks.values() if task.get("status") == "pending")
    completed = sum(1 for task in tasks.values() if task.get("status") == "completed")
    unmatched = sum(1 for task in tasks.values() if task.get("status") == "unmatched")

    print("\n📋 [任务清单] tasks.json")
    print(f"   待处理: {pending}  |  已完成: {completed}  |  未配对: {unmatched}")
    for bundle_name in sorted(tasks):
        task = tasks[bundle_name]
        status = task.get("status", "pending")
        skin = task.get("skin_image") or "(无皮肤)"
        scale = task.get("pixels_to_units", DEFAULT_PIXELS_TO_UNITS)
        y_offset = task.get("y_offset", DEFAULT_Y_OFFSET)
        print(
            f"   • {bundle_name}\n"
            f"     皮肤: {skin}  |  状态: {status}  |  "
            f"pixels_to_units={scale}  |  y_offset={y_offset}"
        )


def print_skip_completed(bundle_name):
    print(
        f"{GREEN}⏭️  [跳过] {bundle_name} 已完成 (status=completed){RESET}"
    )


def mark_task_completed(tasks, bundle_name):
    tasks[bundle_name]["status"] = "completed"
    save_tasks(tasks)


def iter_runnable_tasks(tasks):
    for bundle_name in sorted(tasks):
        task = tasks[bundle_name]
        if task.get("status") == "completed":
            yield bundle_name, task, "completed"
        elif task.get("status") == "unmatched" or not task.get("skin_image"):
            yield bundle_name, task, "unmatched"
        else:
            yield bundle_name, task, "pending"