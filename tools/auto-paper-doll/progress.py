import os
import re
from datetime import datetime, timezone

from config import PROGRESS_FILE, SCRIPT_VERSION


def _format_task_row(bundle_name, task):
    skin = task.get("skin_image") or "(无)"
    status = task.get("status", "pending")
    mode = task.get("pairing_mode", "manual")
    scale = task.get("pixels_to_units", "-")
    y_offset = task.get("y_offset", "-")
    return (
        f"| `{bundle_name}` | {skin} | {status} | {mode} | "
        f"{scale} | {y_offset} |"
    )


def _build_run_entry(tasks, results, attempted, success_count, skipped):
    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %z")

    lines = [
        f"### {timestamp} — v{SCRIPT_VERSION}",
        "",
        f"- 本次处理: **{attempted}**  |  成功: **{success_count}**  |  "
        f"累计已完成: **{skipped}**",
    ]

    if results:
        lines.append("")
        lines.append("**本次结果:**")
        lines.append("")
        lines.append("| Bundle | 皮肤 | 结果 | 备注 |")
        lines.append("| ------ | ---- | ---- | ---- |")
        for result in results:
            bundle = result.get("bundle", "?")
            skin = result.get("skin") or "-"
            if result.get("success"):
                outcome = "✅ 成功"
                note = result.get("pairing_mode", "")
            else:
                outcome = "❌ 失败"
                note = result.get("error", "")
            lines.append(f"| `{bundle}` | {skin} | {outcome} | {note} |")

    pending = sum(1 for t in tasks.values() if t.get("status") == "pending")
    completed = sum(1 for t in tasks.values() if t.get("status") == "completed")
    unmatched = sum(1 for t in tasks.values() if t.get("status") == "unmatched")

    lines.extend(
        [
            "",
            f"- 任务总览: 待处理 **{pending}**  |  已完成 **{completed}**  |  "
            f"未配对 **{unmatched}**",
            "",
            "| Bundle | 皮肤 | 状态 | 配对模式 | scale | y_offset |",
            "| ------ | ---- | ---- | -------- | ----- | -------- |",
        ]
    )
    for bundle_name in sorted(tasks):
        lines.append(_format_task_row(bundle_name, tasks[bundle_name]))

    lines.append("")
    return "\n".join(lines)


def _update_header(content, today):
    content = re.sub(
        r"> 最后更新：.*",
        f"> 最后更新：{today}  ",
        content,
        count=1,
    )
    content = re.sub(
        r"> 当前脚本版本：\*\*v[\d.]+\*\*",
        f"> 当前脚本版本：**v{SCRIPT_VERSION}**",
        content,
        count=1,
    )
    return content


def record_run_progress(tasks, results, attempted, success_count, skipped):
    run_entry = _build_run_entry(
        tasks, results, attempted, success_count, skipped
    )
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    section_marker = "## 十二、运行记录"

    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as progress_file:
            content = progress_file.read()
        content = _update_header(content, today)

        if section_marker in content:
            content = content.rstrip() + "\n\n" + run_entry
        else:
            content = (
                content.rstrip()
                + f"\n\n---\n\n{section_marker}\n\n"
                + run_entry
            )
    else:
        content = (
            f"# Unity 纸片人 Mod 自动化重构 — 项目进度文档\n\n"
            f"> 最后更新：{today}  \n"
            f"> 当前脚本版本：**v{SCRIPT_VERSION}**\n\n"
            f"---\n\n{section_marker}\n\n"
            f"{run_entry}"
        )

    with open(PROGRESS_FILE, "w", encoding="utf-8") as progress_file:
        progress_file.write(content)
        if not content.endswith("\n"):
            progress_file.write("\n")

    print(f"\n📝 [进度] 运行记录已写入 {os.path.basename(PROGRESS_FILE)}")