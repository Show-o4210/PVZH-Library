# 静态补丁锚点

> 数据来源：`reference/il2cpp/dump.cs`（本工程快照）  
> 游戏侧缓存 manifest 曾观测：`UnityABVersion_11047`  
> **跟版后必须重 dump 并更新本表**

Il2CppDumper 标注：

- **RVA / VA**：镜像相对虚址（用于 IDA/Ghidra 加载 so 后定位）  
- **Offset**：文件内偏移（部分工具用）  

实际改 `libil2cpp.so` 前，用 `script.json` 或反汇编确认符号与字节，勿盲信未校验的写入。

---

## 1. 推荐挂点（P0）

### `PlayerInventoryHolderImpl.SetLocalPlayerInventory`

| 项 | 值 |
|----|-----|
| Namespace | `PvZCards.Inventory` |
| 签名 | `public virtual void SetLocalPlayerInventory(PlayerInventory inventory)` |
| TypeDefIndex | 6265 |
| Slot | 12 |
| **RVA** | **`0x1FEB478`** |
| Offset | `0x1FE7478` |
| VA | `0x1FEB478` |
| dump 行附近 | ~247558 |

**语义**：把完整 `PlayerInventory` 写入 holder 的 `LocalPlayerInventoryOrDelta`（字段偏移 `0x18`）。

**补丁策略（已实现，2026-07-28）**：

1. 函数先按原逻辑执行到 `str x19, [x20, #0x18]!`（写入 `LocalPlayerInventoryOrDelta`）。  
2. 自 RVA **`0x1FEB4E0`** 起改为 `B` 到新 PT_LOAD payload（`hook_epilogue`）。  
3. Payload：`merge_inventory_extra(inventory)` → 恢复寄存器 → `B 0x180423C`（原 logger tail）。  
4. Payload VA（本构建）：**`0x04000000`**；构建脚本：`scripts/build_and_patch.py`。

### 反汇编确认（arm64-v8a 参考 so）

| 地址 | 指令 | 语义 |
|------|------|------|
| `0x1FEB478` | `stp x30,x21,[sp,#-0x20]!` | 序言 |
| `0x1FEB488` | `mov x19, x1` | inventory |
| `0x1FEB48C` | `mov x20, x0` | this |
| `0x1FEB4DC` | `str x19, [x20, #0x18]!` | 写字段；x20←this+0x18 |
| `0x1FEB4E0` | ~~`mov x0,x20`…~~ → **`B payload`** | **hook 点** |
| `0x1FEB4F0` | 原 `b 0x180423C` | 现由 payload 尾部执行 |

调用约定：AArch64，managed 实例方法 `x0=this`（此处 SetLocal 为虚方法，已是 this/inventory）。

**为何首选**：sync 成功、本地加载等路径最终都 Set，一次补丁覆盖面最大。

---

## 2. 备选挂点

### `SyncPlayerInventoryCommand.LogSuccessAndAcceptServerData`

| 项 | 值 |
|----|-----|
| 签名 | `private void LogSuccessAndAcceptServerData(PlayerInventoryDto fromServer)` |
| **RVA** | **`0x1FECDBC`** |
| Offset | `0x1FE8DBC` |
| 附近 | ~248025 |

仅覆盖「服务器 accept」路径；本地 Persister 直接 Set 时可能漏。

### `SyncPlayerInventoryCommand.HandleSuccess`

| 项 | 值 |
|----|-----|
| 签名 | `private void HandleSuccess(PlayerInventoryDto fromServer)` |
| **RVA** | **`0x1FECC70`** |
| Offset | `0x1FE8C70` |

### `PlayerInventoryDtoTranslator.FromDto`

| 项 | 值 |
|----|-----|
| 签名 | `public virtual PlayerInventory FromDto(PlayerInventoryDto dto)` |
| **RVA** | **`0x222CA10`** |
| Offset | `0x2228A10` |

在 DTO→内存转换后 merge 亦可，但非唯一库存来源。

---

## 3. 数据结构（merge 时要认的字段）

### `PlayerInventory`（运行时）

| 字段 | 偏移 | 类型 |
|------|------|------|
| Cards | 0x10 | `Dictionary<int, int>` |
| Heroes | 0x18 | `Dictionary<string, int>` |
| Currencies | 0x20 | `Dictionary<string, int>` |
| Sparks | 0x40 | int |
| … | | 见 dump ~763042 |

### `PlayerInventoryDto`（网络 JSON）

| JSON 键 | 字段 |
|---------|------|
| Cards | `Dictionary<string, int>` |
| Heroes | `Dictionary<string, int>` |
| … | dump ~669821 |

转换：`BuildIntCardsFromStringCards` RVA `0x222CB40`。

---

## 4. 工具函数（调试 / 备选全解锁）

| 方法 | RVA | 说明 |
|------|-----|------|
| `PlayerInventoryUtility.AddCardToInventory` | `0x1FEB97C` | 向字典加卡 |
| `PlayerInventoryUtility.GetCardInventoryCount` | `0x1FEBB60` | 查询数量 |
| `PlayerInventoryUtility.HasAtLeastOfCard` | `0x1FEBC80` | 是否够用 |

**正式方案不要**只靠改查询函数「恒 true」替代 extra JSON（除非产品改为全解锁沙盒）。

---

## 5. 字符串与路径线索

见 `reference/il2cpp/inventory_stringliterals.txt`，关键包括：

- `{0}v1/inventory/sync`
- `[SyncPlayerInventoryCommand] Offline`
- `PlayerInventory` / `PlayerInventoryDelta`
- `/PlayerData/{0}/`
- `[PlayerInventoryHolder] SetLocalPlayerInventory`

旁路文件（本方案约定，**非官方字符串**）：

```text
cache/mod/inventory_extra.json
```

实现需自行拼接 `Application.persistentDataPath` 或 Android `files` 目录。  
Phase B 应在真机确认：Unity 的 `persistentDataPath` 是否等于  
`/storage/emulated/0/Android/data/com.ea.gp.pvzheroes/files`。

---

## 6. 实现检查清单

- [x] 确认参考 so ABI = **arm64-v8a**（rabin2：ARM aarch64 / Android）  
- [x] r2 打开 so，确认 `0x1FEB478` 为 SetLocal（字段写 0x18、logger 字符串路径）  
- [x] 注入方式：新 PT_LOAD RX + epilogue 跳转（见 `docs/patch_design.md`）  
- [x] merge 只改传入 `PlayerInventory` 的 Cards/Heroes 字典；不触碰 Delta  
- [x] 文件缺失 / JSON 失败静默  
- [x] 产物：`dist/arm64-v8a/libil2cpp.so` + sha256 + `PATCH_INFO.txt`  
- [ ] 真机 Phase C 验收（需设备侧信息，见 `docs/build_patch.md` §7）  

### 本快照补丁元数据

| 项 | 值 |
|----|-----|
| 基底 | `reference/il2cpp/libil2cpp.so` |
| 输出 | `dist/arm64-v8a/libil2cpp.so` |
| Hook RVA | `0x1FEB4E0` |
| Payload VA | `0x04000000` |
| 构建 | `python scripts/build_and_patch.py` |

---

## 7. 跟版流程

1. 新版本重新 Il2CppDumper → 覆盖 `reference/il2cpp/`  
2. 搜索 `SetLocalPlayerInventory` 更新本表 RVA  
3. 重做跳板偏移  
4. 跑 `PLAN.md` Phase C  

---

## 8. 快照信息

| 文件 | 备注 |
|------|------|
| `reference/il2cpp/libil2cpp.so` | ~60 MB，补丁基底 |
| `reference/il2cpp/dump.cs` | 符号与 RVA |
| `reference/il2cpp/script.json` | 方法地址脚本 |
| `reference/il2cpp/global-metadata.dat` | metadata |
| 初始化日期 | 2026-07-28 |
