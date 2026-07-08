import os
import struct
import subprocess
import sys
import json

ALIGNMENT = 16

def require_unitypy():
    try:
        import UnityPy
    except ImportError as exc:
        raise ImportError(
            "当前 Python 环境未安装 UnityPy 库，无法操作 UnityFS 资源包。请先运行 'pip install UnityPy'。"
        ) from exc
    return UnityPy

def is_unityfs(path: str) -> bool:
    with open(path, "rb") as f:
        return f.read(7) == b"UnityFS"

def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def find_vgmstream() -> str | None:
    base = script_dir()
    candidates = [
        os.path.join(base, "vgmstream-cli.exe"),
        os.path.join(base, "vgmstream-win64", "vgmstream-cli.exe"),
        os.path.join(base, "vgmstream", "vgmstream-cli.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None

def prompt(text: str, default: str = "") -> str:
    """
    接收用户输入，并自动去除两端可能存在的 Windows/Mac 路径引号
    """
    if default:
        value = input(f"{text} [{default}]: ").strip()
        value = value or default
    else:
        value = input(f"{text}: ").strip()
    
    # 核心优化：直接剥离两端可能包裹的双引号 " 或单引号 '
    return value.strip('"' + "'")

def parse_bank(data: bytes) -> dict:
    chunks: dict[str, tuple[int, int]] = {}
    offset = 0
    size = len(data)

    while offset + 8 <= size:
        chunk_name = data[offset : offset + 4].decode("ascii", errors="ignore")
        chunk_size = struct.unpack_from("<I", data, offset + 4)[0]
        if chunk_size > size - offset - 8:
            raise ValueError(f"块 {chunk_name!r} 的大小非法")
        chunks[chunk_name] = (offset + 8, chunk_size)
        offset += 8 + chunk_size
        if chunk_size % 2 == 1:
            offset += 1

    for required in ("BKHD", "DIDX", "DATA"):
        if required not in chunks:
            raise ValueError(f"Bank 文件格式不完整，缺少核心块: {required}")
    return chunks

def read_entries(data: bytes, didx_offset: int, didx_size: int) -> list[dict]:
    entries = []
    count = didx_size // 12
    for i in range(count):
        entry_offset = didx_offset + i * 12
        file_id, wem_offset, wem_size = struct.unpack_from("<III", data, entry_offset)
        entries.append(
            {
                "id": file_id,
                "offset": wem_offset,
                "size": wem_size,
            }
        )
    return entries

def find_bkhd_text_assets(env) -> list[tuple]:
    text_assets = []
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        try:
            asset_data = obj.read()
            raw_bytes = asset_data.m_Script.encode("utf-8", "surrogateescape")
            if raw_bytes.startswith(b"BKHD"):
                text_assets.append((obj, asset_data, raw_bytes))
        except Exception:
            pass
    return text_assets

def select_bkhd_text_asset(
    text_assets: list[tuple],
    bundle_info: dict | None = None,
    *,
    interactive: bool = True,
) -> tuple:
    if not text_assets:
        raise ValueError("在 UnityFS 资源包中未找到包含 Wwise Bank (BKHD) 的 TextAsset。")

    if bundle_info and "path_id" in bundle_info:
        target_path_id = int(bundle_info["path_id"])
        for obj, asset_data, raw_bytes in text_assets:
            if obj.path_id == target_path_id:
                return obj, asset_data, raw_bytes

    if len(text_assets) > 1:
        print("[*] 找到多个包含 Wwise Bank 的 TextAsset:")
        for idx, (obj, asset_data, raw_bytes) in enumerate(text_assets):
            print(
                f"  {idx + 1}. 名称: {asset_data.m_Name} "
                f"(PathID: {obj.path_id}, 大小: {len(raw_bytes)} 字节)"
            )
        if interactive:
            choice_str = prompt("请选择要操作的 TextAsset 序号 (默认 1)", "1")
            try:
                choice_idx = int(choice_str) - 1
            except ValueError:
                choice_idx = 0
            if choice_idx < 0 or choice_idx >= len(text_assets):
                choice_idx = 0
        else:
            choice_idx = 0
    else:
        choice_idx = 0

    return text_assets[choice_idx]

def get_original_bank_data(
    bank_path: str,
    bundle_info: dict | None = None,
    *,
    interactive: bool = True,
) -> tuple[bytes, dict | None]:
    if is_unityfs(bank_path):
        print("[*] 检测到输入为 UnityFS 资源包，正在通过 UnityPy 读取内部 Wwise Bank 数据...")
        UnityPy = require_unitypy()
        env = UnityPy.load(bank_path)
        text_assets = find_bkhd_text_assets(env)
        selected_obj, selected_asset, bank_data = select_bkhd_text_asset(
            text_assets, bundle_info, interactive=interactive
        )
        print(f"[*] 已选定 TextAsset: {selected_asset.m_Name} (PathID: {selected_obj.path_id})")
        return bank_data, {
            "type": "UnityFS",
            "path_id": selected_obj.path_id,
            "name": selected_asset.m_Name,
        }

    with open(bank_path, "rb") as f:
        bank_data = f.read()
    return bank_data, None

def iter_bkhd_banks(bank_path: str) -> list[tuple[bytes, dict | None]]:
    if is_unityfs(bank_path):
        UnityPy = require_unitypy()
        env = UnityPy.load(bank_path)
        results = []
        for obj, asset_data, raw_bytes in find_bkhd_text_assets(env):
            results.append(
                (
                    raw_bytes,
                    {
                        "type": "UnityFS",
                        "path_id": obj.path_id,
                        "name": asset_data.m_Name,
                    },
                )
            )
        if not results:
            raise ValueError("在 UnityFS 资源包中未找到包含 Wwise Bank (BKHD) 的 TextAsset。")
        return results

    with open(bank_path, "rb") as f:
        bank_data = f.read()
    if bank_data.startswith(b"BKHD"):
        return [(bank_data, None)]
    raise ValueError("输入文件不是 UnityFS 资源包，也不是有效的 Wwise Bank。")

def load_mapping_data(json_path: str) -> tuple[dict, dict, str | None]:
    with open(json_path, "r", encoding="utf-8") as jf:
        meta_data = json.load(jf)

    source_bundle = meta_data.get("source_bundle")
    if "mapping" in meta_data:
        return meta_data, meta_data["mapping"], source_bundle
    return meta_data, meta_data, source_bundle

def save_mapping_data(json_path: str, full_data: dict, meta_mapping: dict) -> None:
    if "mapping" in full_data:
        full_data["mapping"] = meta_mapping
        payload = full_data
    else:
        payload = meta_mapping

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(payload, jf, indent=4, ensure_ascii=False)

def export_bank_bytes(bundle_path: str, output_path: str) -> dict:
    if not is_unityfs(bundle_path):
        raise ValueError("导出 .bytes 仅支持 UnityFS 资源包，请直接提供 AB 包路径。")

    bank_data, bundle_info = get_original_bank_data(bundle_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "wb") as out_f:
        out_f.write(bank_data)

    print(f"[+] Bank 已导出至: {output_path}")
    print(f"    大小: {len(bank_data)} 字节")
    return bundle_info or {}

def import_bank_bytes(
    bundle_path: str,
    bank_bytes_path: str,
    output_path: str,
    bundle_info: dict | None = None,
) -> None:
    if not is_unityfs(bundle_path):
        raise ValueError("导入 .bytes 仅支持 UnityFS 资源包，请直接提供 AB 包路径。")
    if not os.path.isfile(bank_bytes_path):
        raise FileNotFoundError(f"找不到 Bank 文件: {bank_bytes_path}")

    with open(bank_bytes_path, "rb") as f:
        bank_data = f.read()
    if not bank_data.startswith(b"BKHD"):
        raise ValueError("导入文件不是有效的 Wwise Bank（缺少 BKHD 头）。")

    UnityPy = require_unitypy()
    env = UnityPy.load(bundle_path)
    text_assets = find_bkhd_text_assets(env)
    selected_obj, selected_asset, _ = select_bkhd_text_asset(text_assets, bundle_info)

    target_path_id = selected_obj.path_id
    replaced = False
    for obj in env.objects:
        if obj.path_id != target_path_id:
            continue
        data = obj.read()
        data.m_Script = bank_data.decode("utf-8", "surrogateescape")
        data.save()
        replaced = True
        print(f"  [+] 已更新 TextAsset: {data.m_Name} (PathID: {obj.path_id})")
        break

    if not replaced:
        raise ValueError(f"导入失败：在 UnityFS 资源包中未找到 PathID 为 {target_path_id} 的 TextAsset")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "wb") as out_f:
        out_f.write(env.file.save())

    print(f"\n[+] 导入成功！新 AB 包已输出至: {output_path}")
    print(
        f"    新文件大小: {os.path.getsize(output_path)} 字节 "
        f"(原 AB 大小: {os.path.getsize(bundle_path)} 字节)"
    )
    print(f"    写入 Bank 大小: {len(bank_data)} 字节")

def extract_bank(bank_path: str, out_dir: str) -> list[dict]:
    bank_data, bundle_info = get_original_bank_data(bank_path)

    chunks = parse_bank(bank_data)
    data_offset, _ = chunks["DATA"]
    didx_offset, didx_size = chunks["DIDX"]
    entries = read_entries(bank_data, didx_offset, didx_size)

    wem_dir = os.path.join(out_dir, "wem")
    os.makedirs(wem_dir, exist_ok=True)

    print(f"[*] 找到 {len(entries)} 个音频条目")
    
    meta_mapping = {}

    for entry in entries:
        start = data_offset + entry["offset"]
        end = start + entry["size"]
        blob = bank_data[start:end]
        
        file_id_str = str(entry["id"])
        out_path = os.path.join(wem_dir, f"{file_id_str}.wem")
        
        with open(out_path, "wb") as f:
            f.write(blob)
            
        meta_mapping[file_id_str] = {
            "original_offset": entry["offset"],
            "original_size": entry["size"],
            "wem_path": os.path.relpath(out_path, out_dir)
        }
        print(f"  [+] 已提取: {file_id_str}.wem (大小: {entry['size']} 字节)")

    json_path = os.path.join(out_dir, "mapping.json")
    if bundle_info:
        output_data = {
            "bundle_info": bundle_info,
            "source_bundle": os.path.abspath(bank_path),
            "mapping": meta_mapping,
        }
    else:
        output_data = meta_mapping

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(output_data, jf, indent=4, ensure_ascii=False)
    print(f"[+] 进度及映射关系已备份至本地: {json_path}")

    return entries

def decode_wem_files(entries: list[dict], out_dir: str, vgmstream: str) -> None:
    wem_dir = os.path.join(out_dir, "wem")
    wav_dir = os.path.join(out_dir, "wav")
    os.makedirs(wav_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "mapping.json")
    if os.path.isfile(json_path):
        full_data, meta_mapping, _ = load_mapping_data(json_path)
    else:
        full_data, meta_mapping = {}, {}

    print(f"[*] 开始将 WEM 解码为 WAV...")
    for entry in entries:
        file_id_str = str(entry["id"])
        wem_path = os.path.join(wem_dir, f"{file_id_str}.wem")
        wav_path = os.path.join(wav_dir, f"{file_id_str}.wav")
        
        if not os.path.isfile(wem_path):
            print(f"  [!] 未找到对应的 WEM 文件: {file_id_str}.wem，跳过")
            continue

        print(f"  [->] 正在转换: {file_id_str}.wem -> {file_id_str}.wav")
        result = subprocess.run(
            [vgmstream, "-o", wav_path, wem_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  [!] {file_id_str}.wem 转换失败！")
            continue
        
        if file_id_str in meta_mapping:
            meta_mapping[file_id_str]["wav_path"] = os.path.relpath(wav_path, out_dir)

    save_mapping_data(json_path, full_data, meta_mapping)

def load_manifest(manifest_path: str) -> tuple[dict, list[dict], str | None]:
    with open(manifest_path, "r", encoding="utf-8") as jf:
        manifest = json.load(jf)
    entries = []
    for item in manifest.get("entries", []):
        entries.append(
            {
                "id": int(item["id"]),
                "offset": int(item["original_offset"]),
                "size": int(item["original_size"]),
                "seq": str(item["seq"]),
            }
        )
    return manifest, entries, manifest.get("source_bundle")

def repack_bank(bank_path: str, extract_dir: str, output_path: str) -> None:
    manifest_path = os.path.join(extract_dir, "manifest.json")
    json_path = os.path.join(extract_dir, "mapping.json")
    wem_dir = os.path.join(extract_dir, "wem")

    bundle_info = None
    meta_mapping = {}
    source_bundle = None
    use_seq_names = False
    entries = None

    if os.path.isfile(manifest_path):
        print(f"[*] 检测到 manifest.json，正在加载序列化映射关系...")
        manifest, entries, source_bundle = load_manifest(manifest_path)
        bundle_info = manifest.get("bundle_info")
        use_seq_names = True
    elif os.path.isfile(json_path):
        print(f"[*] 检测到本地备份，正在从 {json_path} 加载音频映射关系...")
        meta_data, meta_mapping, source_bundle = load_mapping_data(json_path)
        bundle_info = meta_data.get("bundle_info")

        entries = []
        for fid, info in meta_mapping.items():
            entries.append({
                "id": int(fid),
                "offset": info["original_offset"],
                "size": info["original_size"]
            })
    else:
        print("[!] 未找到 manifest.json / mapping.json 备份，将从原始 Bank 解析结构。")

    if source_bundle and is_unityfs(source_bundle) and not is_unityfs(bank_path):
        print(f"[*] 检测到解包来源 AB 包，自动切换输入: {source_bundle}")
        bank_path = source_bundle

    original_data, detected_bundle_info = get_original_bank_data(bank_path, bundle_info)
    if bundle_info is None:
        bundle_info = detected_bundle_info

    chunks = parse_bank(original_data)
    bkhd_offset, bkhd_size = chunks["BKHD"]
    didx_offset, didx_size = chunks["DIDX"]
    data_offset, _ = chunks["DATA"]

    bkhd_content = original_data[bkhd_offset - 8 : bkhd_offset + bkhd_size]

    if entries is None:
        entries = read_entries(original_data, didx_offset, didx_size)

    new_data = bytearray()
    new_entries: list[dict] = []

    print(f"[*] 开始重包音频，目标文件夹: {wem_dir}")
    for entry in entries:
        file_id = entry["id"]
        if use_seq_names:
            wem_name = f"{entry['seq']}.wem"
        else:
            wem_name = f"{file_id}.wem"
        wem_path = os.path.join(wem_dir, wem_name)

        if os.path.isfile(wem_path):
            with open(wem_path, "rb") as f:
                wem_data = f.read()
            print(f"  [+] [替换] {wem_name} (id={file_id}, {len(wem_data)} 字节)")
        else:
            start = data_offset + entry["offset"]
            end = start + entry["size"]
            wem_data = original_data[start:end]
            print(f"  [-] [保留原样] {wem_name} (id={file_id}, {len(wem_data)} 字节)")

        align_pad = (ALIGNMENT - (len(new_data) % ALIGNMENT)) % ALIGNMENT
        new_data.extend(b"\x00" * align_pad)

        new_offset = len(new_data)
        new_data.extend(wem_data)
        new_entries.append(
            {
                "id": file_id,
                "offset": new_offset,
                "size": len(wem_data),
            }
        )

    new_didx = bytearray()
    for entry in new_entries:
        new_didx.extend(struct.pack("<III", entry["id"], entry["offset"], entry["size"]))

    new_bank_bytes = bytearray()
    new_bank_bytes.extend(bkhd_content)
    new_bank_bytes.extend(b"DIDX")
    new_bank_bytes.extend(struct.pack("<I", len(new_didx)))
    new_bank_bytes.extend(new_didx)
    new_bank_bytes.extend(b"DATA")
    new_bank_bytes.extend(struct.pack("<I", len(new_data)))
    new_bank_bytes.extend(new_data)

    if bundle_info and bundle_info.get("type") == "UnityFS":
        print("[*] 正在通过 UnityPy 将重包后的 Wwise Bank 回写到 UnityFS 资源包中...")
        temp_bank_path = os.path.join(extract_dir, "_repack_temp.bytes")
        with open(temp_bank_path, "wb") as temp_f:
            temp_f.write(new_bank_bytes)
        import_bank_bytes(bank_path, temp_bank_path, output_path, bundle_info)
        os.remove(temp_bank_path)
        return
    else:
        with open(output_path, "wb") as out_f:
            out_f.write(new_bank_bytes)

    print(f"\n[+] 重包成功！新文件已输出至: {output_path}")
    print(f"    新文件大小: {os.path.getsize(output_path)} 字节 (原大小: {os.path.getsize(bank_path)} 字节)")

def default_extract_dir(bank_path: str) -> str:
    base = os.path.splitext(os.path.basename(bank_path))[0]
    return os.path.join(os.path.dirname(os.path.abspath(bank_path)), f"{base}_extracted")

def default_repack_path(bank_path: str) -> str:
    root, ext = os.path.splitext(bank_path)
    if ext:
        return f"{root}_modified{ext}"
    return f"{bank_path}_modified"

def default_bytes_export_path(bundle_path: str) -> str:
    base = os.path.basename(bundle_path)
    root, ext = os.path.splitext(base)
    name = root or base
    return os.path.join(os.path.dirname(os.path.abspath(bundle_path)), f"{name}.bytes")

def action_export_bytes() -> None:
    bundle_path = prompt("请输入 Unity AB 包路径")
    if not os.path.isfile(bundle_path):
        print("[!] 找不到指定的 AB 包文件")
        return
    if not is_unityfs(bundle_path):
        print("[!] 该文件不是 UnityFS 资源包，无法使用 UnityPy 导出 .bytes")
        return

    output_path = prompt("请输入导出的 .bytes 保存路径", default_bytes_export_path(bundle_path))
    try:
        export_bank_bytes(bundle_path, output_path)
    except Exception as exc:
        print(f"[!] 导出失败: {exc}")

def action_import_bytes() -> None:
    bundle_path = prompt("请输入原始 Unity AB 包路径")
    if not os.path.isfile(bundle_path):
        print("[!] 找不到指定的 AB 包文件")
        return
    if not is_unityfs(bundle_path):
        print("[!] 该文件不是 UnityFS 资源包，无法使用 UnityPy 导入 .bytes")
        return

    bank_bytes_path = prompt("请输入要导入的 .bytes / .bnk 文件路径")
    if not os.path.isfile(bank_bytes_path):
        print("[!] 找不到指定的 Bank 文件")
        return

    output_path = prompt("请输入导入后的新 AB 包保存路径", default_repack_path(bundle_path))
    bundle_info = None
    mapping_path = prompt(
        "可选：输入 mapping.json 路径以自动匹配 TextAsset (直接回车跳过)",
        "",
    )
    if mapping_path and os.path.isfile(mapping_path):
        meta_data, _, source_bundle = load_mapping_data(mapping_path)
        bundle_info = meta_data.get("bundle_info")
        if source_bundle and os.path.isfile(source_bundle):
            bundle_path = source_bundle
            print(f"[*] 已从 mapping.json 读取来源 AB 包: {bundle_path}")

    try:
        import_bank_bytes(bundle_path, bank_bytes_path, output_path, bundle_info)
    except Exception as exc:
        print(f"[!] 导入失败: {exc}")

def action_extract(decode_wav: bool = False) -> None:
    bank_path = prompt("请输入 AB 包 / .bytes / .bnk 文件路径")
    if not os.path.isfile(bank_path):
        print("[!] 找不到指定的文件")
        return

    out_dir = prompt("请输入输出解包目录", default_extract_dir(bank_path))
    try:
        entries = extract_bank(bank_path, out_dir)
    except Exception as exc:
        print(f"[!] 解包失败: {exc}")
        return

    print(f"[+] 原始 WEM 文件成功保存至: {os.path.join(out_dir, 'wem')}")

    if not decode_wav:
        return

    vgmstream = find_vgmstream()
    if not vgmstream:
        print("\n[!] 错误：未在当前目录或子目录下找到 vgmstream-cli.exe")
        print("    请将 vgmstream 工具解压到当前脚本所在的目录下以启用 WAV 解码功能。")
        return

    try:
        decode_wem_files(entries, out_dir, vgmstream)
        print(f"[+] 同名 WAV 文件成功保存至: {os.path.join(out_dir, 'wav')}")
    except Exception as exc:
        print(f"[!] 解码 WAV 失败 (本地备份已保留): {exc}")

def action_repack() -> None:
    bank_path = prompt("请输入原始 AB 包 / .bytes / .bnk 文件路径")
    if not os.path.isfile(bank_path):
        print("[!] 找不到指定的文件")
        return

    default_dir = default_extract_dir(bank_path)
    extract_dir = prompt("请输入解包目录(包含 mapping.json 和 wem 文件夹)", default_dir)
    if not os.path.isdir(extract_dir):
        print("[!] 找不到该解包目录")
        return

    output_path = prompt("请输入重包后的输出路径 (AB 包将自动通过 UnityPy 回写)", default_repack_path(bank_path))
    try:
        repack_bank(bank_path, extract_dir, output_path)
    except Exception as exc:
        print(f"[!] 重包失败: {exc}")

def show_menu() -> None:
    print("\n" + "="*30)
    print("      Wwise/FMOD Bank 工具")
    print("="*30)
    print(" 1. 仅提取原始 WEM 音频")
    print(" 2. 提取并同步解码为【同名 WAV】(推荐听歌)")
    print(" 3. 重新打包 Bank (根据 WEM 目录及 JSON 替换)")
    print(" 4. 从 AB 包导出 Bank 为 .bytes (UnityPy)")
    print(" 5. 将 .bytes 导入回 AB 包 (UnityPy)")
    print(" 0. 退出程序")
    print("="*30)

def main() -> None:
    while True:
        show_menu()
        choice = prompt("请选择操作", "0")

        if choice == "1":
            action_extract(decode_wav=False)
        elif choice == "2":
            action_extract(decode_wav=True)
        elif choice == "3":
            action_repack()
        elif choice == "4":
            action_export_bytes()
        elif choice == "5":
            action_import_bytes()
        elif choice == "0":
            print("已安全退出，再见！")
            break
        else:
            print("[!] 输入无效，请重新选择")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] 操作被用户强行中断。由于有本地 JSON 备份，已提取的数据不会丢失。")
        sys.exit(0)