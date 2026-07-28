# 重建静态补丁（libil2cpp.so）

目标：从本仓库的参考 so + 脚本，生成可替换的 `dist/arm64-v8a/libil2cpp.so`。

## 0. 前置

| 项 | 要求 |
|----|------|
| OS | Windows / Linux / macOS 均可（脚本为 Python） |
| Python | 3.10+ |
| 依赖 | `pip install keystone-engine` |
| 输入 so | `reference/il2cpp/libil2cpp.so`（arm64-v8a，约 60MB） |
| dump | `reference/il2cpp/dump.cs`（核对 RVA） |

```bash
pip install keystone-engine
```

## 1. 一键构建

在工程根目录：

```bash
python scripts/build_and_patch.py
```

成功输出示例：

```text
payload code: ... bytes
OK: wrote .../dist/arm64-v8a/libil2cpp.so
sha256=...
hook @0x1feb4e0 -> payload @0x4000000
```

产物：

| 文件 | 说明 |
|------|------|
| `dist/arm64-v8a/libil2cpp.so` | 已补丁 so（替换游戏内同 ABI 文件） |
| `dist/arm64-v8a/libil2cpp.so.sha256` | 补丁后哈希 |
| `dist/arm64-v8a/PATCH_INFO.json` 内容见 `PATCH_INFO.txt` | 偏移 / 哈希 / hook 元数据 |
| `dist/arm64-v8a/payload.bin` | 注入用裸 payload（调试） |

## 2. 脚本做了什么

1. 用 Keystone 汇编 `merge_inventory_extra` + `hook_epilogue`（ARM64）  
2. 附带 rodata：三条 JSON 路径 + `schemaVersion`/`Cards`/`Heroes` 键名  
3. 复制参考 so → 追加 **RX PT_LOAD**（VA `0x04000000`）  
4. 在 `SetLocalPlayerInventory` 尾部 RVA **`0x1FEB4E0`** 写入 `B payload`  
5. 写 `PATCH_INFO.txt` 与 sha256  

设计细节：`docs/patch_design.md`。

## 3. 跟版 / 改 RVA

游戏更新后：

1. 重新 Il2CppDumper，覆盖 `reference/il2cpp/`  
2. 在 `dump.cs` 搜 `SetLocalPlayerInventory`，更新：  
   - `docs/static_patch_points.md`  
   - `scripts/build_and_patch.py` 顶部常量：

```python
SET_LOCAL_RVA = 0x1FEB478
HOOK_RVA      = 0x1FEB4E0   # 写完 inventory 字段后的第一条 epilogue
ORIG_TAIL_RVA = 0x180423C   # 原 logger tail
GET_CARD_COUNT = ...
ADD_CARD = ...
# 以及 PLT / il2cpp_string_new / Heroes MethodInfo 槽（需反汇编确认）
```

3. 用 radare2/IDA 打开**新** so，确认：  
   - `HOOK_RVA` 处仍是 `mov x0, x20`（或等价 epilogue）  
   - 文件偏移 = RVA − `0x4000`（本 so 的 RX `p_vaddr - p_offset`）  
4. 再跑 `python scripts/build_and_patch.py`  
5. 跑 Phase C 回归  

## 4. 手工校验（构建后）

```bash
# 哈希
# Windows PowerShell:
Get-FileHash dist\arm64-v8a\libil2cpp.so -Algorithm SHA256

# 反汇编 hook（需 radare2）
r2 -q -c "e asm.arch=arm; e asm.bits=64; s 0x1FEB4E0; pd 6; s 0x4000000; pd 20" dist/arm64-v8a/libil2cpp.so
```

期望：

- `0x1FEB4E0`: `b 0x4000000`  
- `0x4000000`: `sub sp, sp, #0x30` … `bl merge` … `b 0x180423c`  

## 5. 安装到设备（验收用）

> 仅替换你自己的客户端；官方 PvP / 上传不在支持范围。

1. 确认设备 ABI 为 **arm64-v8a**（见下方 Phase C 信息清单）  
2. 备份原 `libil2cpp.so`  
3. 将 `dist/arm64-v8a/libil2cpp.so` 放进 APK/`lib/arm64-v8a/` 或已提取的 lib 目录后重打包/挂载（按你现有改包流程）  
4. 推送 JSON：

```text
Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
```

模板：`templates/cache/mod/inventory_extra.json`  
示例：`examples/demo_card/inventory_extra.json`

5. 校验 JSON（PC 上）：

```bash
python scripts/validate_inventory_extra.py path/to/inventory_extra.json
```

## 6. 无 NDK 说明

本流水线**不需要** Android NDK：payload 由 Keystone 在构建机直接汇编。  
语义参考源码：`native/merge_inventory_extra.c`（文档级，非当前链接产物）。

若改为 C/NDK 实现：编译为 PIC 机器码后，仍用同一 `patch_elf` 逻辑注入即可。

## 7. Phase C 需要你提供的设备信息

真机未在本环境验收时，请补充：

| 项 | 示例 | 用途 |
|----|------|------|
| 设备型号 / Android 版本 | Pixel 6 / 14 | 兼容性 |
| CPU ABI 列表 | `arm64-v8a` 优先？是否仅 32 位 | **必须与 so 一致** |
| 游戏版本 / 包版本名 | 如商店版本号 | 与 dump 对齐 |
| 包内 so 路径与 **原 so SHA256** | `lib/arm64-v8a/libil2cpp.so` | 确认基底一致 |
| `files` 实际根路径 | `…/Android/data/com.ea.gp.pvzheroes/files` | 确认 JSON 路径 |
| 是否有完整性校验 / 加固 | 启动即闪退？ | 决定是否还需过校验 |
| 安装方式 | 重打包 APK / Magisk 模块 / 模拟器替换 | 写 install 终稿 |

最低验收（见 `PLAN.md` Phase C）：

1. 无 extra 文件：能进游戏，官方库存正常  
2. 有合法 extra：对应 `cardId` 在客户端视为拥有（组卡/数量）  

## 8. 故障排查

| 现象 | 排查 |
|------|------|
| 构建 Keystone 报错 | `pip install -U keystone-engine`；看 `dist/arm64-v8a/payload_debug.S` |
| hook 站点字节不符 | 跟版后 epilogue 变了 → 更新 `HOOK_RVA` 与 expected 校验 |
| **启动即闪退** | 确认使用 **v3**（`PATCH_INFO.txt` 含 `v3_extend_rx_cave` / `crash_fix: v3`）。v1/v2 已废弃。用 `dist/apk_test/pvzh_v3_so.apk` 或自行换 so 后重签 |
| 旧 v1/v2 补丁 | 新增 PT_LOAD / 搬 PHDR → Houdini 上报 `undefined symbol: JNI_OnLoad`；勿使用 |
| 进游戏后崩溃 | 可能是 merge 路径运行时问题；先无 `inventory_extra.json` 测；抓 `logcat` |
| JSON 不生效 | 路径、schemaVersion、validate 脚本；确认已走到 SetLocal（登录/同步后） |
| 仅 32 位设备 | 当前**只交付 arm64-v8a**；armeabi-v7a 需另 dump/另编 |

## 9. 安全边界

- 只合并本地 JSON 到**内存**库存视图  
- 不写 `PlayerInventoryDelta`、不做官方服刷卡  
- 自定义卡仅用于本地/单机研究场景  
