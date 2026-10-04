import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave

import repack_bnk

ROOT = repack_bnk.script_dir()
INPUT_AB = os.path.join(ROOT, "input", "ab")
INPUT_REPLACE = os.path.join(ROOT, "input", "replace")
OUTPUT_EXTRACTED = os.path.join(ROOT, "output", "extracted")
OUTPUT_MODIFIED = os.path.join(ROOT, "output", "modified")
CONFIG_PATH = os.path.join(ROOT, "config.json")
ZSOUND2WEM = os.path.join(ROOT, "zSound2wem.cmd")

AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".wma"}


def load_config() -> dict:
    defaults = {
        "samplerate": "",
        "channels": "",
        "volume": "",
        "conversion": "Vorbis Quality High",
    }
    if not os.path.isfile(CONFIG_PATH):
        return defaults
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    defaults.update(data)
    return defaults


def ensure_dirs() -> None:
    for path in (INPUT_AB, INPUT_REPLACE, OUTPUT_EXTRACTED, OUTPUT_MODIFIED):
        os.makedirs(path, exist_ok=True)


def seq_width(count: int) -> int:
    return max(3, len(str(count)))


def format_seq(index: int, width: int) -> str:
    return str(index).zfill(width)


def ab_stem(path: str) -> str:
    base = os.path.basename(path)
    stem, _ = os.path.splitext(base)
    return stem or base


def project_name(ab_path: str, bundle_info: dict | None) -> str:
    if bundle_info and bundle_info.get("name"):
        return str(bundle_info["name"])
    return ab_stem(ab_path)


def project_dir_name(ab_path: str, bundle_info: dict | None, bank_count: int) -> str:
    name = project_name(ab_path, bundle_info)
    if bank_count > 1:
        return os.path.join(ab_stem(ab_path), name)
    return name


def list_ab_files() -> list[str]:
    if not os.path.isdir(INPUT_AB):
        return []
    files = []
    for entry in os.listdir(INPUT_AB):
        path = os.path.join(INPUT_AB, entry)
        if not os.path.isfile(path):
            continue
        if entry.lower().endswith((".txt", ".md", ".json", ".bat", ".cmd")):
            continue
        if repack_bnk.is_unityfs(path):
            files.append(path)
    return sorted(files)


def list_extracted_projects() -> list[str]:
    projects = []
    if not os.path.isdir(OUTPUT_EXTRACTED):
        return projects
    for root, _, files in os.walk(OUTPUT_EXTRACTED):
        if "manifest.json" in files:
            projects.append(root)
    return sorted(projects)


def relative_project_key(project_dir: str) -> str:
    return os.path.relpath(project_dir, OUTPUT_EXTRACTED)


def resolve_replace_dir(project_dir: str) -> str | None:
    key = relative_project_key(project_dir)
    candidates = [
        os.path.join(INPUT_REPLACE, key),
        os.path.join(INPUT_REPLACE, os.path.basename(project_dir)),
    ]
    projects = list_extracted_projects()
    if len(projects) == 1:
        candidates.append(INPUT_REPLACE)

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if os.path.isdir(candidate) and any(
            os.path.isfile(os.path.join(candidate, name))
            for name in os.listdir(candidate)
            if os.path.splitext(name)[1].lower() in AUDIO_EXTENSIONS
        ):
            return candidate
    return None


def find_ffmpeg(config: dict) -> str | None:
    custom = str(config.get("ffmpeg", "")).strip()
    if custom and os.path.isfile(custom):
        return custom

    for entry in sorted(os.listdir(ROOT)):
        if "ffmpeg" not in entry.lower():
            continue
        candidate = os.path.join(ROOT, entry, "bin", "ffmpeg.exe")
        if os.path.isfile(candidate):
            return candidate

    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path
    return None


def find_wwise_console() -> str | None:
    wwise_root = os.environ.get("WWISEROOT", "").strip()
    if wwise_root:
        candidate = os.path.join(
            wwise_root, "Authoring", "x64", "Release", "bin", "WwiseConsole.exe"
        )
        if os.path.isfile(candidate):
            return candidate

    for env_key in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(env_key, "")
        if not base:
            continue
        ak_root = os.path.join(base, "Audiokinetic")
        if not os.path.isdir(ak_root):
            continue
        for entry in sorted(os.listdir(ak_root), reverse=True):
            candidate = os.path.join(
                ak_root,
                entry,
                "Authoring",
                "x64",
                "Release",
                "bin",
                "WwiseConsole.exe",
            )
            if os.path.isfile(candidate):
                return candidate
    return None


def wav_duration(path: str) -> float | None:
    try:
        with wave.open(path, "rb") as wf:
            rate = wf.getframerate()
            if rate <= 0:
                return None
            return wf.getnframes() / rate
    except Exception:
        return None


def run_ffmpeg(ffmpeg: str, args: list[str]) -> None:
    result = subprocess.run(
        [ffmpeg, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or "FFmpeg 执行失败")


def normalize_audio(ffmpeg: str, source_path: str, target_wav: str, config: dict) -> None:
    args = ["-hide_banner", "-loglevel", "warning", "-y", "-i", source_path]
    samplerate = str(config.get("samplerate", "")).strip()
    channels = str(config.get("channels", "")).strip()
    volume = str(config.get("volume", "")).strip()
    if samplerate:
        args.extend(["-ar", samplerate])
    if channels:
        args.extend(["-ac", channels])
    if volume:
        if volume.lower().endswith("db"):
            args.extend(["-af", f"volume={volume}"])
        else:
            args.extend(["-af", f"volume={volume}"])
    args.extend(["-c:a", "pcm_s16le", target_wav])
    run_ffmpeg(ffmpeg, args)


def decode_wem_dir(wem_dir: str, wav_dir: str, vgmstream: str, entries: list[dict]) -> None:
    os.makedirs(wav_dir, exist_ok=True)
    for entry in entries:
        wem_path = os.path.join(wem_dir, entry["wem_file"])
        wav_path = os.path.join(wav_dir, entry["wav_file"])
        if not os.path.isfile(wem_path):
            print(f"  [!] 未找到 WEM: {entry['wem_file']}，跳过")
            continue
        print(f"  [->] {entry['wem_file']} -> {entry['wav_file']}")
        result = subprocess.run(
            [vgmstream, "-o", wav_path, wem_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            print(f"  [!] 解码失败: {entry['wem_file']}")
            continue
        entry["duration_sec"] = wav_duration(wav_path)


def write_manifest(project_dir: str, manifest: dict) -> None:
    path = os.path.join(project_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)


def write_index(project_dir: str, manifest: dict) -> None:
    lines = [
        "# 音频清单：使用左侧序号在 input/replace/ 中放置替换文件",
        "# 例如：001.mp3  003.wav",
        "",
    ]
    for entry in manifest["entries"]:
        duration = entry.get("duration_sec")
        duration_text = f"  duration={duration:.2f}s" if duration else ""
        lines.append(
            f"{entry['seq']}  id={entry['id']}  size={entry['original_size']}"
            f"{duration_text}  wav={entry['wav_file']}"
        )
    with open(os.path.join(project_dir, "index.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def extract_bank_to_project(
    bank_data: bytes,
    bundle_info: dict | None,
    source_path: str,
    project_dir: str,
    vgmstream: str,
) -> None:
    if os.path.isdir(project_dir):
        shutil.rmtree(project_dir)

    chunks = repack_bnk.parse_bank(bank_data)
    data_offset, _ = chunks["DATA"]
    didx_offset, didx_size = chunks["DIDX"]
    raw_entries = repack_bnk.read_entries(bank_data, didx_offset, didx_size)

    wem_dir = os.path.join(project_dir, "wem")
    wav_dir = os.path.join(project_dir, "wav")
    os.makedirs(wem_dir, exist_ok=True)

    width = seq_width(len(raw_entries))
    manifest_entries = []

    print(f"[*] 找到 {len(raw_entries)} 个音频条目")
    for index, entry in enumerate(raw_entries, start=1):
        seq = format_seq(index, width)
        start = data_offset + entry["offset"]
        end = start + entry["size"]
        blob = bank_data[start:end]

        wem_name = f"{seq}.wem"
        wav_name = f"{seq}.wav"
        wem_path = os.path.join(wem_dir, wem_name)
        with open(wem_path, "wb") as f:
            f.write(blob)

        manifest_entries.append(
            {
                "seq": seq,
                "id": entry["id"],
                "original_offset": entry["offset"],
                "original_size": entry["size"],
                "wem_file": wem_name,
                "wav_file": wav_name,
                "replaced": False,
            }
        )
        print(f"  [+] {wem_name} (id={entry['id']}, {entry['size']} 字节)")

    manifest = {
        "bundle_info": bundle_info,
        "source_bundle": os.path.abspath(source_path),
        "project_name": os.path.basename(project_dir),
        "entries": manifest_entries,
    }
    write_manifest(project_dir, manifest)
    decode_wem_dir(wem_dir, wav_dir, vgmstream, manifest_entries)
    write_index(project_dir, manifest)
    print(f"[+] manifest: {os.path.join(project_dir, 'manifest.json')}")
    print(f"[+] 试听目录: {wav_dir}")


def scan_replace_files(replace_dir: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for name in os.listdir(replace_dir):
        path = os.path.join(replace_dir, name)
        if not os.path.isfile(path):
            continue
        stem, ext = os.path.splitext(name)
        if ext.lower() not in AUDIO_EXTENSIONS:
            continue
        if not re.fullmatch(r"\d+", stem):
            print(f"  [!] 忽略未按序号命名的文件: {name}")
            continue
        seq = stem.zfill(max(3, len(stem)))
        files[seq] = path
    return files


def run_zsound2wem(
    wav_files: list[str],
    output_dir: str,
    config: dict,
    ffmpeg: str,
    wwise_console: str,
) -> None:
    if not os.path.isfile(ZSOUND2WEM):
        raise FileNotFoundError(f"找不到 zSound2wem.cmd: {ZSOUND2WEM}")

    args = [
        ZSOUND2WEM,
        f"--out:{output_dir}",
        f"--ffmpeg:{ffmpeg}",
        f"--wwise:{wwise_console}",
        f"--conversion:{config.get('conversion', 'Vorbis Quality High')}",
    ]
    samplerate = str(config.get("samplerate", "")).strip()
    channels = str(config.get("channels", "")).strip()
    volume = str(config.get("volume", "")).strip()
    if samplerate:
        args.append(f"--samplerate:{samplerate}")
    if channels:
        args.append(f"--channels:{channels}")
    if volume:
        args.append(f"--volume:{volume}")
    args.extend(wav_files)

    result = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or "zSound2wem 执行失败")


def preflight_extract() -> str:
    repack_bnk.require_unitypy()
    vgmstream = repack_bnk.find_vgmstream()
    if not vgmstream:
        raise RuntimeError("未找到 vgmstream-cli.exe，请将 vgmstream-win64 放在项目目录下。")
    return vgmstream


def preflight_build(config: dict) -> tuple[str, str]:
    repack_bnk.require_unitypy()
    ffmpeg = find_ffmpeg(config)
    if not ffmpeg:
        raise RuntimeError(
            "未找到 FFmpeg。请将包含 bin/ffmpeg.exe 的 ffmpeg 目录放在项目根目录，"
            "或在 config.json 中指定 ffmpeg 路径。"
        )
    wwise = find_wwise_console()
    if not wwise:
        raise RuntimeError("未找到 Wwise，请先安装 Wwise 并确保 WWISEROOT 环境变量可用。")
    if not os.path.isfile(ZSOUND2WEM):
        raise RuntimeError(f"找不到 zSound2wem.cmd: {ZSOUND2WEM}")
    return ffmpeg, wwise


def cmd_extract() -> int:
    ensure_dirs()
    vgmstream = preflight_extract()
    ab_files = list_ab_files()
    if not ab_files:
        print("[!] 请先将 AB 包放入 input/ab/ 目录")
        return 1

    print("=" * 60)
    print("解包阶段")
    print("=" * 60)

    for ab_path in ab_files:
        print(f"\n[*] 处理 AB 包: {ab_path}")
        if not repack_bnk.is_unityfs(ab_path):
            print("  [!] 跳过：不是 UnityFS 资源包")
            continue

        banks = repack_bnk.iter_bkhd_banks(ab_path)
        for bank_data, bundle_info in banks:
            project_key = project_dir_name(ab_path, bundle_info, len(banks))
            project_dir = os.path.join(OUTPUT_EXTRACTED, project_key)
            print(f"[*] 项目目录: {project_dir}")
            extract_bank_to_project(bank_data, bundle_info, ab_path, project_dir, vgmstream)

    print("\n[+] 解包完成")
    print(f"    试听：{OUTPUT_EXTRACTED}")
    print(f"    替换：将音频放入 {INPUT_REPLACE}/<项目名>/ ，按序号命名，例如 001.mp3")
    print("    然后运行 2-打包输出.bat")
    return 0


def cmd_build() -> int:
    ensure_dirs()
    config = load_config()
    ffmpeg, wwise = preflight_build(config)

    projects = list_extracted_projects()
    if not projects:
        print("[!] 未找到解包产物，请先运行 1-解包试听.bat")
        return 1

    print("=" * 60)
    print("打包阶段")
    print("=" * 60)

    built_any = False
    for project_dir in projects:
        replace_dir = resolve_replace_dir(project_dir)
        if not replace_dir:
            print(f"\n[-] 跳过 {relative_project_key(project_dir)}：input/replace/ 中没有替换文件")
            continue

        manifest_path = os.path.join(project_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        replace_files = scan_replace_files(replace_dir)
        if not replace_files:
            print(f"\n[-] 跳过 {relative_project_key(project_dir)}：没有有效的替换音频")
            continue

        seq_map = {entry["seq"]: entry for entry in manifest["entries"]}
        matched = []
        for seq, source_path in sorted(replace_files.items()):
            if seq not in seq_map:
                print(f"  [!] 序号 {seq} 在 manifest 中不存在，忽略: {os.path.basename(source_path)}")
                continue
            matched.append((seq, source_path, seq_map[seq]))

        if not matched:
            print(f"\n[-] 跳过 {relative_project_key(project_dir)}：没有匹配到有效序号")
            continue

        print(f"\n[*] 打包项目: {relative_project_key(project_dir)}")
        print(f"[*] 替换目录: {replace_dir}")
        print(f"[*] 将替换 {len(matched)} 个音频")

        with tempfile.TemporaryDirectory(prefix="pipeline_wav_") as temp_wav_dir:
            wav_for_zsound = []
            for seq, source_path, entry in matched:
                target_wav = os.path.join(temp_wav_dir, f"{seq}.wav")
                print(f"  [->] 规范化: {os.path.basename(source_path)} -> {seq}.wav")
                normalize_audio(ffmpeg, source_path, target_wav, config)
                wav_for_zsound.append(target_wav)

            with tempfile.TemporaryDirectory(prefix="pipeline_wem_") as temp_wem_dir:
                print("[*] 调用 zSound2wem 转换为 WEM...")
                run_zsound2wem(wav_for_zsound, temp_wem_dir, config, ffmpeg, wwise)

                wem_dir = os.path.join(project_dir, "wem")
                for seq, source_path, entry in matched:
                    produced = os.path.join(temp_wem_dir, f"{seq}.wem")
                    if not os.path.isfile(produced):
                        raise RuntimeError(f"zSound2wem 未生成预期文件: {seq}.wem")
                    shutil.copy2(produced, os.path.join(wem_dir, entry["wem_file"]))
                    entry["replaced"] = True
                    entry["replace_source"] = os.path.relpath(source_path, ROOT).replace("\\", "/")
                    print(f"  [+] 已替换: {entry['wem_file']} (id={entry['id']})")

        write_manifest(project_dir, manifest)

        source_bundle = manifest.get("source_bundle")
        if not source_bundle or not os.path.isfile(source_bundle):
            print("  [!] manifest 中缺少有效的 source_bundle，无法回写 AB 包")
            continue

        project_key = relative_project_key(project_dir).replace("\\", "_")
        output_path = os.path.join(OUTPUT_MODIFIED, f"{project_key}_modified")
        print(f"[*] 回写 AB 包 -> {output_path}")
        repack_bnk.repack_bank(source_bundle, project_dir, output_path)
        built_any = True

    if not built_any:
        print("\n[!] 没有项目被打包。请确认已将替换音频放入 input/replace/")
        return 1

    print(f"\n[+] 打包完成，成品 AB 包位于: {OUTPUT_MODIFIED}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Wwise AB 音频流水线")
    parser.add_argument("mode", choices=["extract", "build"], help="extract=解包试听, build=打包输出")
    args = parser.parse_args()

    try:
        if args.mode == "extract":
            return cmd_extract()
        return cmd_build()
    except Exception as exc:
        print(f"\n[!] 失败: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())