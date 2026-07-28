# 全流程回顾与经验总结（含错误档案）

> **读者**：后续维护者、接手 Agent、需要复现/排错的社区开发者。  
> **配套**：现象导向排错见 [troubleshooting.md](./troubleshooting.md)；JSON 合同见 [inventory_extra_spec.md](./inventory_extra_spec.md)。  
> **日期跨度**：2026-07 立项 → 模拟器验收 → 真机 v3c → 社区精简包。  
> **原则**：本文**保留失败路径**，方便对照 logcat 与版本号，避免重踩坑。

---

## 0. 一句话结论

| 问题 | 答案 |
|------|------|
| 社区卡为什么组不进套？ | 客户端 `PlayerInventory.Cards` 没有该 ID（服务器不会发） |
| 定义从哪来？ | 改缓存 `card_data_*`（UnityFS TextAsset JSON） |
| 拥有从哪来？ | 静态补丁 so 在 `SetLocalPlayerInventory` 后 merge 本地 JSON |
| 交付形态？ | 替换/重签 APK 内 `libil2cpp.so` + `cache/mod/inventory_extra.json`（无 Frida） |
| 当前可用版本？ | **v3c**（RX cave + 简单 AddCard + **SHT sh_offset 同步**） |

---

## 1. 目标与非目标（未偏离）

### 1.1 目标

1. 本地/单机模式下，玩家可**拥有**社区自定义卡并组卡、对战。  
2. 全静态、可社区传播：玩家只装 APK / 换 so + 放文件。  
3. 卡师只改 `card_data` + `inventory_extra.json`，不碰 so。  

### 1.2 非目标

- Frida / Xposed / 常驻 Hook 作为交付  
- 官方 PvP / 匹配用未收录卡  
- 私服、商店经济、刷资源  

### 1.3 已验证前提（立项前）

1. 官方登录后断网，本地模式可玩。  
2. 改 `card_data` 能加载新卡**定义**。  
3. 瓶颈是**拥有权**，不是贴图/名称 alone。  

---

## 2. 架构（最终形态）

```text
                  ┌─────────────────────────┐
                  │  官方登录 / 本地读档     │
                  │  SetLocalPlayerInventory │
                  └───────────┬─────────────┘
                              │ hook @ 0x1FEB4E0（epilogue）
                              ▼
                  ┌─────────────────────────┐
                  │  payload (cave)         │
                  │  open/read extra JSON   │
                  │  AddCardToInventory     │
                  └───────────┬─────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
  inventory_extra.json   PlayerInventory      card_data_*
  (拥有数量声明)          .Cards 字典           (实体定义 Guid)
         │                    │                    │
         └──────── must match IDs ─────────────────┘
```

### 2.1 关键路径（设备）

```text
# 拥有声明
Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json

# 卡定义（常见）
.../files/cache/bundles/files/cards/card_data_5

# 本地持久化（root 可见，会与云同步纠缠）
/data/data/com.ea.gp.pvzheroes/files/PlayerData/<personaId>/PlayerInventory
/data/data/com.ea.gp.pvzheroes/files/PlayerData/<personaId>/PlayerDecks
```

### 2.2 补丁技术参数（本快照）

见 `dist/arm64-v8a/PATCH_INFO.txt`（以文件为准）：

| 项 | 值（示例） |
|----|------------|
| 策略 | `v3_extend_rx_cave` |
| SetLocal RVA | `0x1FEB478` |
| Hook RVA | `0x1FEB4E0` |
| Cave VA | `0x37824F0`，file off `0x377E4F0`，size `0x4000` |
| Payload | `build_payload_simple`，~650B，扫 `"id":count` + `AddCard` |
| 原版 so sha256 | `ccade235…` |
| v3c so sha256 | `c717afb9…` |

换游戏版本必须重新 dump + 重算 RVA + 重打补丁。

---

## 3. 推荐工作流（正确顺序）

以后做同类工作或跟版，按此顺序，可少踩坑。

### Phase A — 规格与样本

1. 从官方包提取 `libil2cpp.so`、`global-metadata.dat`，Il2CppDumper → `dump.cs`。  
2. 在 dump 中定位 `SetLocalPlayerInventory` / `AddCardToInventory` / 库存字段偏移。  
3. 约定 `inventory_extra` schema（`docs/inventory_extra_spec.md`）。  
4. 抽出官方 `card_data` 样本，确认 TextAsset JSON 结构。  

### Phase B — 静态补丁

1. **禁止**一上来就新 PT_LOAD / 搬 PHDR（见错误档案 E1）。  
2. 在 RX 与 RW 的 VA 空隙插入 cave，扩展 RX `filesz/memsz`。  
3. **必须**同步：  
   - 所有 `p_offset >= insert` 的 PHDR  
   - 所有 `sh_offset >= insert` 的 SHT（含 `.dynamic`）← **真机必过**  
4. Hook 只跳到简单 payload：读文件 → 解析 → `AddCard`；失败静默。  
5. `build_and_patch.py` 校验：`PT_DYNAMIC.p_offset == .dynamic.sh_offset`。  

### Phase C — 模拟器验收

1. 重签 APK 或换 so；确认 ABI arm64。  
2. 空 extra 能进游戏。  
3. 官方简单卡 ID 写入 extra，确认数量/组卡。  
4. 再测自定义 Guid-only 克隆。  

### Phase D — 真机验收

1. **不要**假设「模拟器过了 = 真机过」（见 E2）。  
2. 抓 logcat：`Unable to load` / `dynamic section` / `Fatal signal`。  
3. 通过后再做卡内容测试。  

### Phase E — 卡内容创作

1. UnityPy 克隆官方**简单**单位（推荐 #10），只改 Guid（≥90000）。  
2. `inventory_extra` 只写**已有定义**的 ID。  
3. **先库存/收藏，确认稳定，再进套牌**（见 E5）。  
4. 发给玩家：Base APK + 你的 cache 卡包（不要重复塞 so）。  

### Phase F — 分发

1. 社区包只留：v3c APK + 模板 + 短手册 + 少量 example。  
2. so / dump / 完整 docs 留在工程，不塞进玩家 zip。  

---

## 4. 实际演进时间线（含失败）

### 4.1 立项与规格

- 确立静态 so + `inventory_extra` 方案。  
- 写 PLAN、architecture、JSON 规范、templates。  
- 校验脚本：`scripts/validate_inventory_extra.py`。  

### 4.2 SO 补丁迭代（核心痛苦）

| 版本 | 做法 | 结果 | 教训编号 |
|------|------|------|----------|
| v1 | 新 PHDR 到文件尾 | 加载失败 | E1 |
| v2 | 额外 PT_LOAD | Houdini：`undefined symbol: JNI_OnLoad` | E1 |
| v3 | RX cave，不改 PHDR 表 | 模拟器可加载 | — |
| v3 + 复杂 JSON/GetCount | 完整 max 语义 | **SIGSEGV** | E3 |
| **v3b** | 简单扫描 + 仅 AddCard | 模拟器稳定 | — |
| v3b 上真机 | 同包 | **白屏秒退** | E2 |
| **v3c** | v3b + 平移 SHT sh_offset | 真机 Unity 正常 | — |

### 4.3 卡数据与库存测试

| 尝试 | 结果 | 教训 |
|------|------|------|
| 扩展技能/多属性大改 card_data | 冻住、难定位 | E4 |
| 整卡克隆 #10 + 表面字段 | 可加载 | 推荐 |
| `ignoreDeckLimit=true`（basic） | 数量显示锁 4 | E6 |
| 改 `ignoreDeckLimit=false` 测计数 | 部分有效，规则未完全摸清 | E6 |
| 换「非 basic」模板 | 曾冻/不稳定 | 慎选 |
| 只有 extra / 残缺 card_data | `IsSilverCard` NRE | E5 |
| 套牌含 90001 后卸定义 | `FixupDecks` NRE；清本地会被云写回 | E5 |

### 4.4 环境与流程坑

| 现象 | 原因 | 教训 |
|------|------|------|
| 「改了没效果」 | adb 推到错误模拟器实例 | E7 |
| 「官方文件也进不去」 | 云端套牌仍引用自定义 ID | E5 |
| 日志被华为系统噪音淹没 | 要用 `pidof` / 过滤 `ea.gp.pvzheroes` | E8 |

### 4.5 工程与分发

- 曾堆积 GB 级中间 APK、apktool 全量反编译、设备 dump。  
- 清理后：`share/` 精简包 ~186MB zip；完整 docs 留仓库。  

---

## 5. 错误档案（保留对照）

下列每条：**症状 → 根因 → 错误做法 → 正确做法 → 如何验证**。

---

### E1 — ELF 乱改导致无法 dlopen（v1/v2）

**症状**

```text
Unable to load library: .../libil2cpp.so
dlopen failed: undefined symbol: JNI_OnLoad
```

或启动即闪退，原版 so 可进。

**根因**

新增 PT_LOAD、搬迁 `e_phoff`/PHDR，在 **Houdini / 部分 linker** 下符号/布局校验失败。

**错误做法**

- 为了塞代码随便加 LOAD 段。  
- 把 PHDR 挪到文件尾且不在任何 LOAD 内。  

**正确做法**

- 用 RX 与 RW 之间已有 **VA 空隙** 扩展原 RX LOAD（cave）。  
- **不**增加 `e_phnum`、**不**搬 PHDR 表。  

**验证**

- 原版 so 对照；补丁后 logcat 无 `Unable to load`。  
- 当前策略：`PATCH_INFO.strategy = v3_extend_rx_cave`。  

---

### E2 — 真机白屏：`.dynamic` 与 `PT_DYNAMIC` 偏移不一致（旧 v3b）

**症状**

真机白屏秒退；模拟器可能正常。

```text
Abort message: '... Unable to load library: .../libil2cpp.so
[dlopen failed: ".dynamic section has invalid offset: 0x392b250,
expected to match PT_DYNAMIC offset: 0x392f250"]'
```

差值常为 **`0x4000`（= CAVE_SIZE）**。

**根因**

插入 cave 后只改了 Program Header 的 `p_offset`，**未改 Section Header 的 `sh_offset`**。  
真机 **bionic** 严格比对；Houdini 较松。

**错误做法**

- 仅在模拟器验收就发社区包。  
- 校验只查 hook 跳转、不查 DYNAMIC。  

**正确做法（v3c）**

- 对所有 `sh_offset >= insert_at` 的节 `+CAVE_SIZE`。  
- 构建时 assert：`PT_DYNAMIC.p_offset == .dynamic.sh_offset`。  
- 代码：`scripts/build_and_patch.py` → `patch_elf_extend_rx` / `_validate_patched_v3`。  

**验证**

```bash
# 启动后应有 Unity 日志且无 Fatal signal 6 / dynamic section
adb logcat -d | findstr /i "Unable to load dynamic section Fatal signal Unity"
```

**版本**

- 废弃：未修 SHT 的 v3b。  
- 使用：v3c APK / `patched_sha256` 见 `PATCH_INFO`。  

---

### E3 — 复杂 payload SIGSEGV

**症状**

so 能加载，进游戏后或 Set 库存时 native 崩。

**根因**

复杂 JSON 解析 + `GetCardInventoryCount` 路径寄存器/调用约定在 IL2CPP 下不稳（曾在 Houdini 复现）。

**错误做法**

- 一次实现完整 schema、max 语义、Heroes、严格 JSON。  

**正确做法**

- v3b/v3c payload：扫 `"digits":digits`，`AddCardToInventory(id, dict, count, MethodInfo=NULL)`。  
- 文件不存在/解析失败：静默返回。  
- 规格上的 `max` 语义可后续再加，先保证不崩。  

**验证**

- 空 extra、简单 extra 反复冷启动无 tombstone。  

---

### E4 — card_data 改得太「花」导致冻住

**症状**

能进游戏，打开组卡/战斗白屏、卡死，未必有清晰 NRE。

**根因**

技能组件、Effect 图、类型混用与官方运行时假设不符。

**错误做法**

- 第一轮就改复杂技能、多模板乱扩、拼组件。  

**正确做法**

1. 整卡 `deepcopy` 官方简单单位（#10 系）。  
2. **只改** `Guid`（及可选展示攻防费/稀有度）。  
3. 稳定后再考虑技能。  
4. 脚本：`clone_card_into_card_data.py`、`make_safe_variant_cards.py`、`make_recovery_90001.py`。  

**验证**

- 新旧 card_data 体积接近官方；UnityPy 可 `json.loads`；键数量合理（约 650+）。  

---

### E5 — 库存/套牌幽灵 ID（IsSilverCard / FixupDecks）

**症状 A**

```text
NullReferenceException
  at FixupLocalPlayerInventoryCommand.IsSilverCard
```

**症状 B**

```text
NullReferenceException
  at DeckEditorUtils.IsCardAllowedInAnyDeck
  at FixupDecksCommand.Execute
```

**根因**

`PlayerInventory` 或 **PlayerDecks** 中有 card id，但当前 `card_data` **没有**对应定义。  
自定义卡进套后可能 **云同步**；只恢复官方 card_data / 清空 extra **不够**——登录会写回脏套牌。

**错误做法**

- 只推官方 card_data，以为「干净了」。  
- 本地删 `PlayerDecks` 当唯一修复（会被服务器覆盖）。  
- 测试阶段把未验证卡放进会同步的套牌。  

**正确做法**

1. **补定义优先**：为每个脏 ID 做 Guid-only 克隆写回 card_data（最快恢复进游戏）。  
2. 进游戏 → 从套牌移除自定义卡 → 保存/同步。  
3. 再考虑删除自定义定义。  
4. 工作流：**先库存，后套牌**。  

**验证**

```bash
# extra 必须与 card_data 键一致
adb shell cat .../cache/mod/inventory_extra.json
# 恢复包示例
# examples/card_data_5_recovery_90001 或 dist/card_mods/card_data_5_recovery_90001
```

**典型脏 ID**

- `90001` 及 ≥90000 社区段。  

---

### E6 — 数量永远是 4

**症状**

extra 写 1/2/3，UI 仍显示 4。

**根因（部分确认）**

模板卡 `ignoreDeckLimit=true` 或 basic 稀有度等规则锁堆叠；UI 也可能 cap。

**错误做法**

- 只改 extra 数量，不看卡定义字段。  

**正确做法**

- 查模板 `ignoreDeckLimit` / `rarity`。  
- 需可计数时换官方本身可堆叠的模板，并实测。  
- 规则表未完全定稿，**以实机 UI 为准**。  

---

### E7 — 多设备 / 多模拟器推错目标

**症状**

「文件改了游戏没变」或「另一台好了这台没有」。

**根因**

`adb devices` 多设备；`127.0.0.1:5555` 与 `emulator-5554` 等混用。

**正确做法**

```bash
adb devices -l
adb -s <serial> push ...
adb -s <serial> shell cat .../inventory_extra.json
```

---

### E8 — logcat 被系统噪音淹没

**症状**

真机（尤其华为）大量 `systemmanager` 崩溃，掩盖游戏 abort。

**正确做法**

```bash
adb logcat -c
adb shell am start -n com.ea.gp.pvzheroes/com.ea.nimble.plugin.NimbleActivity
# 等数秒
adb shell pidof com.ea.gp.pvzheroes
adb logcat -d | findstr /i "ea.gp.pvzheroes libil2cpp Unable to load dynamic Fatal signal IsSilverCard FixupDecks Unity"
```

关键字符串：

| 关键字 | 指向 |
|--------|------|
| `JNI_OnLoad` / `Unable to load library` | E1 / E2 |
| `dynamic section has invalid offset` | E2 |
| `IsSilverCard` | E5-A |
| `FixupDecks` / `IsCardAllowedInAnyDeck` | E5-B |
| `Fatal signal 11` / SIGSEGV | E3 或其它 native |

---

### E9 — 残缺 card_data 体积不对

**症状**

官方 ID（如 1001）丢失；IsSilverCard；「我明明恢复了官方文件」。

**根因**

设备上 `card_data_5` 字节数小于完整样本（曾见 ~133697 vs 官方样本 ~135220），键不全。

**正确做法**

- 用 `reference/samples/card_data_5_device` 或可信完整包覆盖。  
- `wc -c` + UnityPy 计键数。  

---

### E10 — JSON 尾逗号 / 非法 extra

**症状**

merge 不生效或严格解析失败；简单扫描可能仍半生效。

**正确做法**

- 合法 JSON，无尾逗号。  
- `python scripts/validate_inventory_extra.py path`。  

---

## 6. 标准测试清单（回归）

跟版或改 payload 后最少跑这些：

| # | 步骤 | 期望 |
|---|------|------|
| 1 | 装 v3c + 空 extra + 完整官方 card_data | 能进主界面 |
| 2 | extra 写已有官方 ID 与数量 | 登录后组卡可见 |
| 3 | Guid-only 克隆 90001 + extra | 可见；**先不进套** |
| 4 | 冷启动 3 次 | 无 dlopen abort、无 IsSilverCard |
| 5 | 真机再跑 1–4 | 与模拟器一致 |
| 6 | （可选）进套 → 再卸定义 | 应复现 E5；用 recovery 验证修复路径 |

---

## 7. 文件与脚本地图

### 7.1 维护者日常

| 路径 | 用途 |
|------|------|
| `scripts/build_and_patch.py` | 打 v3c so |
| `scripts/build_payload_simple.py` | 简单 payload 汇编 |
| `scripts/clone_card_into_card_data.py` | 克隆卡进 bundle |
| `scripts/make_recovery_90001.py` | 污染恢复示例 |
| `scripts/validate_inventory_extra.py` | 校验 extra |
| `dist/arm64-v8a/` | so + PATCH_INFO |
| `dist/apk/pvzh_mod_base_v3c.apk` | 最终 APK |
| `share/PVZH_LocalInventory_CommunityPack/` | 对外精简包 |

### 7.2 文档分工

| 文档 | 内容 |
|------|------|
| **本文** `workflow_and_experience.md` | 全流程 + 错误档案 + 正确工作流 |
| `troubleshooting.md` | 按现象查 |
| `lessons_learned.md` | 精简条目（可与本文对照） |
| `inventory_extra_spec.md` | JSON 合同 |
| `modder_guide.md` | 卡师流程 |
| `static_patch_points.md` / `patch_design.md` / `build_patch.md` | 补丁细节 |
| `CHANGELOG.md` | 按日变更 |
| 分享包 `README.md` | 玩家三步 |

---

## 8. 已知限制（诚实列表）

1. Heroes merge 未作为重点验收。  
2. 严格 `max(existing, extra)` 与重复 `AddCard` 累加行为不一致。  
3. 仅 arm64-v8a。  
4. 换客户端版本必须重打补丁。  
5. 堆叠 / `ignoreDeckLimit` 完整规则未定稿。  
6. 脏套牌依赖补定义或清套，无自动「扫描并剥离云端脏 ID」工具（可后续做）。  

---

## 9. 给后来者的最短路径

```text
1. 读本文 §0–§3
2. 读 PATCH_INFO + build_and_patch.py 头部注释
3. 模拟器：空 extra → 官方 ID → 自定义 Guid-only
4. 真机：同样步骤 + 盯 E2 关键字
5. 创作卡：只克隆简单模板；先库存后套牌
6. 出问题：logcat 关键字 → 本文 §5 错误档案 → troubleshooting.md
```

**永远记住：**

1. 模拟器 ≠ 真机（DYNAMIC/SHT）。  
2. card_data 与 inventory 与 **套牌** 三者 ID 必须一致。  
3. 云同步会把你的「本地清理」弄脏回来。  

---

*文档随 CHANGELOG 演进；新错误请新增 E11… 并改 troubleshooting 决策树。*
