"""Batch-extract all valid indexed PVZH card animations with resume support."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

from batch_rebuild_sprites import safe_name


def is_placeholder_name(value: object) -> bool:
    name = str(value or "").strip()
    return not name or all(unicodedata.category(char)[0] in {"P", "S"} for char in name)


def completed_report(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        clips = report.get("clips", [])
        return bool(clips) and all(Path(clip["mp4"]).is_file() for clip in clips)
    except Exception:
        return False


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("index_new.json"))
    parser.add_argument("--bundles", type=Path, default=Path("autotagged"))
    parser.add_argument("--cab-index", type=Path, default=Path("cab_index.json"))
    parser.add_argument("--output", type=Path, default=Path(r"D:\项目\save"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--min-free-gb", type=float, default=5.0)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    rows = json.loads(args.index.read_text(encoding="utf-8"))
    tasks = [row for row in rows if not is_placeholder_name(row.get("NAME_CN"))]
    if args.limit is not None:
        tasks = tasks[: args.limit]
    master_path = args.output / "批量处理报告.json"
    previous = {}
    if master_path.is_file():
        try:
            previous = {
                str(item["GUID"]): item
                for item in json.loads(master_path.read_text(encoding="utf-8")).get("cards", [])
            }
        except Exception:
            previous = {}
    cards_by_guid = {}
    started_all = time.time()

    def process_card(number, row):
        guid = str(row["GUID"])
        free_bytes = shutil.disk_usage(args.output).free
        if free_bytes < args.min_free_gb * (1024 ** 3):
            return guid, dict(
                row, status="stopped_low_space",
                free_bytes=free_bytes, output=str(args.output),
            )
        card_dir = (
            args.output / safe_name(row.get("FACTION")) / safe_name(row.get("TYPE")) /
            f"{int(guid):04d}_{safe_name(row.get('NAME_CN'))}_{safe_name(row.get('NAME_EN'))}"
        )
        report_path = card_dir / "report.json"
        old = previous.get(guid)
        if completed_report(report_path):
            result = dict(old or row)
            result.update(status="skipped_complete", output=str(card_dir))
            print(f"[{number}/{len(tasks)}] SKIP {guid} {row.get('NAME_EN')}", flush=True)
        elif old and old.get("status") == "error" and not args.retry_errors:
            result = old
            print(f"[{number}/{len(tasks)}] KEEP ERROR {guid} {row.get('NAME_EN')}", flush=True)
        else:
            bundle = args.bundles / str(row.get("TEXTURE_NAME", ""))
            if not bundle.is_file():
                result = dict(row, status="missing_bundle", output=str(card_dir))
            else:
                command = [
                    sys.executable, "extract_animation_mov.py", str(bundle),
                    "--uuid", str(row["UUID"]), "--bundles", str(args.bundles),
                    "--cab-index", str(args.cab_index), "--output", str(card_dir),
                    "--name-cn", str(row.get("NAME_CN", "")),
                ]
                print(f"[{number}/{len(tasks)}] RUN {guid} {row.get('NAME_EN')}", flush=True)
                started = time.time()
                completed = subprocess.run(
                    command, text=True, capture_output=True, encoding="utf-8", errors="replace"
                )
                card_report = None
                if report_path.is_file():
                    card_report = json.loads(report_path.read_text(encoding="utf-8"))
                result = dict(
                    row,
                    status="ok" if completed.returncode == 0 and card_report and card_report.get("clips") else "error",
                    output=str(card_dir), seconds=round(time.time() - started, 3),
                    clip_count=len(card_report.get("clips", [])) if card_report else 0,
                    dependency_count=len(card_report.get("dependency_bundles", [])) if card_report else 0,
                    key_color_hex=card_report.get("key_color_hex") if card_report else None,
                    stdout=completed.stdout.strip(), stderr=completed.stderr.strip(),
                )
            print(f"  -> {result['status']} clips={result.get('clip_count', 0)}", flush=True)
        return guid, result

    def save_master():
        cards = [cards_by_guid[str(row["GUID"])] for row in tasks if str(row["GUID"]) in cards_by_guid]
        counts = {}
        for item in cards:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        write_report(master_path, {
            "index": str(args.index), "output": str(args.output),
            "eligible_cards": len(tasks), "processed_cards": len(cards),
            "excluded_placeholders": len(rows) - len([r for r in rows if not is_placeholder_name(r.get("NAME_CN"))]),
            "statuses": counts, "elapsed_seconds": round(time.time() - started_all, 3),
            "free_bytes": shutil.disk_usage(args.output.parent).free,
            "cards": cards,
        })

    args.output.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        pending = {}
        for number, row in enumerate(tasks, 1):
            free_bytes = shutil.disk_usage(args.output).free
            if free_bytes < args.min_free_gb * (1024 ** 3):
                print(f"STOP SUBMIT: free space {free_bytes / (1024 ** 3):.2f} GB is below safety threshold", flush=True)
                break
            future = executor.submit(process_card, number, row)
            pending[future] = str(row["GUID"])
        for future in concurrent.futures.as_completed(pending):
            guid = pending[future]
            try:
                result_guid, result = future.result()
            except Exception as exc:
                row = next(item for item in tasks if str(item["GUID"]) == guid)
                result_guid, result = guid, dict(row, status="error", error=f"{type(exc).__name__}: {exc}")
            cards_by_guid[result_guid] = result
            save_master()

    print(f"done: {len(cards_by_guid)} cards -> {args.output}")


if __name__ == "__main__":
    main()
