# 静态补丁设计（Phase B）

## 1. 选型

| 方案 | 结论 |
|------|------|
| Inline trampoline（函数头跳板） | 可用，但需复制整段序言 |
| **函数尾 epilogue 跳转 + 新 PT_LOAD** | **采用**：在 `SetLocalPlayerInventory` 写完字段后 `B` 到 payload |
| 扩展已有 RX 段 / code cave | 本 so 无 ≥1KB 连续 0 cave |
| 预留 hook 表 | 无官方表可复用 |

交付仍为**纯静态改 so**，不依赖 Frida / LSPosed。

## 2. 挂点行为（反汇编摘要）

`PlayerInventoryHolderImpl.SetLocalPlayerInventory` @ RVA **`0x1FEB478`**（arm64-v8a）

| 寄存器 | 含义 |
|--------|------|
| 入口 `x0` | `this`（HolderImpl） |
| 入口 `x1` | `PlayerInventory* inventory` |
| 序言后 `x19` | inventory |
| 序言后 `x20` | this；`str x19,[x20,#0x18]!` 后变为 **this+0x18** |

关键指令：

```text
0x1FEB4DC  str  x19, [x20, #0x18]!   ; LocalPlayerInventoryOrDelta = inventory
0x1FEB4E0  mov  x0, x20               ; ← 从此处起被覆盖
0x1FEB4E4  mov  x1, x19
0x1FEB4E8  ldp  x20, x19, [sp, #0x10]
0x1FEB4EC  ldp  x30, x21, [sp], #0x20
0x1FEB4F0  b    0x180423C             ; logger tail
```

**补丁**：`0x1FEB4E0` 起 5 条指令 → `B payload` + 4×NOP。  
Payload 入口 `hook_epilogue`：

1. 保存 `x19`/`x20`  
2. `merge_inventory_extra(x19)`  
3. 恢复 logger 所需 `x0=this+0x18`、`x1=inventory`  
4. 弹出原函数栈帧  
5. `B 0x180423C`（原 tail）

无 extra / 解析失败时 merge 直接返回 → 行为与原版一致。

## 3. Payload 布局（v3，adb 已验证可加载）

| 项 | 值 |
|----|-----|
| 策略 | **扩展既有 RX `PT_LOAD`**，填满其与下一 RW 段之间的 **0x4000 VA gap** |
| 插入点（文件） | RX 段 `p_offset + p_filesz`（原 `0x377E4F0`） |
| code VA | **`0x37824F0`**（原 RX 结束 VA） |
| 体积 | ~1.8 KiB payload + 零填充至 0x4000 |
| PHDR | **不改动** `e_phoff` / `e_phnum` / 表位置 |

ELF 修改：

1. 在 RX 文件末尾插入 `0x4000` 字节 cave，写入 payload  
2. RX 的 `p_filesz`/`p_memsz` 各 +`0x4000`（结束 VA 正好贴上 RW 起始 `0x37864F0`）  
3. 所有 `p_offset >= 插入点` 的 program header **仅平移 p_offset**（vaddr 不变）  
4. Hook 处 `B 0x37824F0`

### 废弃方案

| 版本 | 做法 | 结果 |
|------|------|------|
| v1 | 文件末尾新 LOAD + PHDR 在 LOAD 外 | 秒闪（linker 拒载） |
| v2 | 新 LOAD 内含 PHDR | 本机 Houdini：`dlopen undefined symbol: JNI_OnLoad` |
| **v3** | **扩展 RX cave** | **可启动** |

## 4. Merge 逻辑

见 `native/merge_inventory_extra.c` 与 `docs/inventory_extra_spec.md`。

| 步骤 | 实现 |
|------|------|
| 路径 | 依次 `open(O_RDONLY)` 三个候选 files 路径（见下） |
| 读入 | `malloc` 256KiB，`read`，NUL 结尾；容忍 UTF-8 BOM |
| schema | 找 `"schemaVersion"`，`strtol` 必须为 **1** |
| Cards | 找 `"Cards"` 对象；键十进制 ID；`max` 通过 `GetCardInventoryCount` + `AddCardToInventory(delta)` |
| Heroes | 找 `"Heroes"`；`il2cpp_string_new` + `GetHeroInventoryCount` + `Dictionary.set_Item`（MethodInfo 与 `AddHeroToInventory` 同槽） |
| Delta | **不调用** 任何 Delta / sync 上传路径 |
| 失败 | 全路径静默 return |

候选路径：

```text
/storage/emulated/0/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
/sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
/data/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
```

（Phase C 若路径不符，可再加 `Application.persistentDataPath` 拼接，需处理 IL2CPP String。）

## 5. 调用的游戏 / libc 符号

| 符号 | VA（本快照） |
|------|----------------|
| `PlayerInventoryUtility.GetCardInventoryCount` | `0x1FEBB60` |
| `PlayerInventoryUtility.AddCardToInventory` | `0x1FEB97C` |
| `PlayerInventoryUtility.GetHeroInventoryCount` | `0x1FEBBF0` |
| `Dictionary<string,int>.set_Item` trampoline | `0x265B1FC` |
| `il2cpp_string_new` | `0x0178CC3C` |
| libc：`open`/`read`/`close`/`malloc`/`free`/`strlen`/`strtol`/`strncmp`/`memcpy` | PLT |

全部为 **同 so 内 PC 相对 BL**，ASLR 下仍有效。

## 6. 风险与降级

| 风险 | 处理 |
|------|------|
| 游戏完整性校验 so | Phase C 验证；若失败需另解签名/校验（本阶段不改） |
| Heroes MethodInfo 未 init | payload 内按 `AddHero` 同款 flag + `0x1804290` 初始化 |
| 路径与 `files` 不一致 | 多候选；C 阶段按设备补路径 |
| 跟版 RVA 变化 | 重 dump 后改 `scripts/build_and_patch.py` 常量并重建 |

**不采用**「`GetCardInventoryCount` 恒 return 4」作为主方案；仅在 so 注入完全不可行时再议。

## 7. 构建入口

```text
python scripts/build_and_patch.py
→ dist/arm64-v8a/libil2cpp.so
```

详见 `docs/build_patch.md`。
