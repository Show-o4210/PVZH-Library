# 排错手册（实机经验）

> 基于 2026-07 雷电模拟器 / arm64 + Houdini 真机链路验证。  
> 现象描述优先对照 **logcat 栈**，不要只猜 card_data。

## 0. 快速决策树

```text
完全打不开 / 启动闪退
  ├─ logcat 含 .dynamic section has invalid offset
  │     → 旧 v3b（SHT 未同步）→ 换 **v3c**（见错误档案 E2）
  ├─ logcat 含 dlopen / JNI_OnLoad / Unable to load library
  │     → SO 为 v1/v2 或 ABI 不匹配 → 换 **v3c** 或原版 so（E1）
  └─ 能进 Unity 加载画面
        ├─ NullReferenceException @ IsSilverCard
        │     → 库存里有 card_data 不存在的 ID（E5）
        ├─ NullReferenceException @ FixupDecks / IsCardAllowedInAnyDeck
        │     → 套牌脏 ID / 云同步（E5）
        ├─ 主界面正常，组卡无自定义卡
        │     → 路径 / JSON / ID / 未触发 SetLocal
        └─ 能看到卡但数量永远 4
              → ignoreDeckLimit / rarity=basic（E6）
```

完整流程回顾与错误档案 E1–E10：见 [workflow_and_experience.md](./workflow_and_experience.md)。

## 1. 环境核对（先做这一步）

| 检查项 | 期望 |
|--------|------|
| 包名 | `com.ea.gp.pvzheroes` |
| ABI | **arm64-v8a**（当前 Base 仅 64 位） |
| 补丁 so 哈希 | 见 `dist/arm64-v8a/PATCH_INFO.txt` → `patched_sha256` |
| 原版 so 哈希 | 同文件 `orig_sha256`；游戏版本必须匹配 dump |
| extra 路径 | `/sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json` |
| card_data 路径 | `.../files/cache/bundles/files/cards/card_data_*` |
| adb 设备 | 多模拟器时确认 `adb devices` 推到的是正在玩的那台 |

### adb 常用命令

```bash
adb devices
adb shell pidof com.ea.gp.pvzheroes
adb shell wc -c /sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
adb shell cat /sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
adb shell wc -c /sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/bundles/files/cards/card_data_5
adb logcat -c
# 启动游戏后：
adb logcat -d | findstr /i "NullReference Fatal SIGSEGV IsSilverCard FixupDecks dlopen libil2cpp"
```

## 2. 按现象排查

### 2.1 启动闪退：`undefined symbol: JNI_OnLoad` / 无法加载 libil2cpp

**原因**：补丁改了 ELF 布局（新增 PT_LOAD / 搬迁 PHDR），在 Houdini / 部分 linker 下失败。

**处理**：

- **必须使用 v3c**：扩展 RX 段 cave，**不**新增 PT_LOAD、不搬 PHDR，且 **SHT 与 PT_DYNAMIC 同步**。  
- 废弃：v1/v2、未修 SHT 的 v3b。  
- 对照：原版 so 能开 → 是补丁问题；原版也不能开 → 安装/签名/设备问题。

### 2.1b 真机白屏秒退：`.dynamic section has invalid offset`

典型 Abort：

```text
JNI FatalError: Unable to load library: .../libil2cpp.so
dlopen failed: .dynamic section has invalid offset: 0x392b250,
expected to match PT_DYNAMIC offset: 0x392f250
```

差值常为 **0x4000**（= cave 大小）。

**原因**：v3 插入 cave 时只平移了 **Program Header** 的 `p_offset`，未同步 **Section Header** 的 `sh_offset`。  
雷电等 **Houdini** 较松可能仍能加载；**真机 Android bionic** 会严格校验 `PT_DYNAMIC` 与 SHT `.dynamic` 一致并 **SIGABRT**（白屏闪退）。

**处理**：

- 使用 **v3c** 及以后产物（`build_and_patch.py` 会平移 section `sh_offset`，并在校验里比对 PT_DYNAMIC/.dynamic）。  
- 不要再分发未修 SHT 的旧 v3b APK。

### 2.2 能进加载，主界面附近 NRE：`IsSilverCard`

典型栈：

```text
NullReferenceException
  at PvZCards.Inventory.FixupLocalPlayerInventoryCommand.IsSilverCard
  at PvZCards.Inventory.FixupLocalPlayerInventoryCommand.OnExecute
```

**原因**：`PlayerInventory` 里有某个 card id，但 `CardDataProvider` 取不到定义（`card_data` 无此 ID 或 bundle 损坏/残缺）。

常见触发：

1. `inventory_extra.json` 写了不存在的 ID（如只有 extra、无 card_data）。  
2. 设备上的 `card_data_5` **体积不对 / 被截断**（实机曾出现 133697 字节残缺，官方样本约 135220）。  
3. 之前 merge 进库存的自定义 ID 被本地 protobuf 保留，之后又换回不含该 ID 的 card_data。

**处理**：

1. 校验 extra 合法 JSON，且每个 ID 都在当前 `card_data` 中。  
2. 用完整官方 `card_data` 覆盖；需要自定义卡时 **定义与拥有必须成对**。  
3. 临时排障：extra 改为空对象：

```json
{ "schemaVersion": 1, "Cards": {}, "Heroes": {} }
```

### 2.3 主界面 NRE：`FixupDecks` / `IsCardAllowedInAnyDeck`

典型栈：

```text
NullReferenceException
  at DeckEditorUtils.IsCardAllowedInAnyDeck
  at FixupDecksCommand.Execute
```

**原因**：某套牌引用了 **card_data 中不存在的 ID**。  
自定义卡一旦放进套牌，可能 **写入账号并云同步**。只恢复官方 card_data、只清 extra **不够**——登录后服务器会把脏套牌写回本地。

本地路径（root）：

```text
/data/data/com.ea.gp.pvzheroes/files/PlayerData/<personaId>/PlayerDecks
/data/data/com.ea.gp.pvzheroes/files/PlayerData/<personaId>/PlayerInventory
```

**处理（推荐顺序）**：

1. **补定义（最快恢复进游戏）**  
   对套牌里每个自定义 ID，在 `card_data` 中放入 **Guid-only 官方简单卡克隆**（推荐模板官方 #10）。  
   本仓库脚本：`scripts/make_recovery_90001.py`（示例恢复 90001）。  
2. **从套牌中移除自定义卡 → 保存 → 等待同步**，再考虑卸载自定义定义。  
3. 本地删 `PlayerDecks` 中脏条目 **往往会被登录同步覆盖**，不可作为唯一手段。

**重要工作流**：未验证的自定义卡 **先只进库存/收藏，不要进会同步的套牌**。

### 2.4 游戏「冻住」/ 黑屏 / 组卡卡死

**常见原因**：`card_data` 组件/技能结构不合法（错误 Effect、乱改类型、模板混用）。

**处理**：

- 回退到 **整卡克隆官方简单单位**（#10 系），只改 Guid / 展示属性。  
- 不要在第一轮测试里改复杂技能树。  
- 用 logcat 区分：NRE（库存/套牌 ID） vs 无 NRE 的卡死（定义/资源）。

### 2.5 有自定义卡，但数量永远是 4

**原因**：模板卡 `ignoreDeckLimit=true` 或 `rarity` 为 basic 一类规则锁堆叠。

**处理**：

- 需要可计数时，选用官方本身 `ignoreDeckLimit=false` 的模板，或显式设置该字段（可能影响其他规则，需实测）。  
- 确认 `inventory_extra` 里的数量与 UI 规则一致；UI 仍可能 cap 到 4。

### 2.6 有定义仍看不到拥有

检查清单：

1. 是否安装了带 merge 的 Base so / 对应 APK。  
2. 路径是否为 **files/cache/mod/**（不是 Android/data 外其它位置）。  
3. JSON 无尾逗号、UTF-8。  
4. 启动后是否走过登录 / `SetLocalPlayerInventory`（可先联网登录再断网）。  
5. ID 字符串与 Guid 一致（`"90001"` 不是 `90001` 数字键以外的形式均可，但必须十进制字符串）。

### 2.7 上线 / 重登后行为异常

- 自定义拥有 **不应依赖上传**；本 Base 只在本地 merge。  
- 但 **套牌内容会同步**——脏 ID 会回来。  
- 官方 PvP / 排位 **不要使用未收录卡**。

## 3. 文件健康检查

| 文件 | 健康信号 |
|------|----------|
| `libil2cpp.so` | 大小约 63317304；`patched_sha256` 匹配；`PATCH_INFO.strategy = v3_extend_rx_cave` |
| `inventory_extra.json` | `schemaVersion:1`；无尾逗号；Cards 键均存在于 card_data |
| `card_data_5` | 能被 UnityPy 打开；TextAsset 可 `json.loads`；键数量接近官方（约 650+） |
| `PlayerDecks` | 无 `≥90000` 的自定义 ID，或这些 ID 均在 card_data 中 |

### 用 Python 粗查 card_data 是否含 ID

```bash
python scripts/inspect_card_data.py path/to/card_data_5
# 或自写：UnityPy 加载 TextAsset → json.loads → '"90001" in cards'
```

### 粗查 PlayerDecks 是否含 90001

root 下复制出二进制后，查找 varint `91 bf 05`（90001 的 protobuf 编码）或使用工程内分析脚本。

## 4. 推荐干净基线（排障用）

```text
1. inventory_extra.json → Cards/Heroes 均为 {}
2. card_data → 完整官方，或「官方 + 套牌所需全部自定义 ID 的 Guid-only 克隆」
3. 使用 v3b so / 分享包 APK
4. 强制停止游戏后冷启动，看 logcat 是否还有 IsSilverCard / FixupDecks
```

若仍 NRE：拉取 `PlayerDecks`，找出未定义 ID，**补定义优先于删档**。

## 5. 相关文档

| 文档 | 内容 |
|------|------|
| [lessons_learned.md](./lessons_learned.md) | 经验总结 |
| [install.md](./install.md) | 安装步骤 |
| [modder_guide.md](./modder_guide.md) | 创作流程 |
| [inventory_extra_spec.md](./inventory_extra_spec.md) | JSON 合同 |
| [build_patch.md](./build_patch.md) | 重建 so |
| [CHANGELOG.md](./CHANGELOG.md) | 版本与坑位记录 |
