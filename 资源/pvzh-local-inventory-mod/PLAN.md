# Agent 执行计划：PVZH 本地库存扩展（静态方案）

> **项目根目录**：`C:\Users\15731\Desktop\PVZH_LocalInventoryMod`  
> **原工作区（只读参考，勿与本工程混写）**：`C:\Users\15731\Desktop\PVZH`  
> **方案名**：静态客户端补丁 + `files/cache/mod/inventory_extra.json` 合并  
> **约束**：可社区传播、全静态、**禁止** Frida/LSPosed/运行时 Hook 作为交付方案

本文是后续 Agent 的**主计划**。实施时按 Phase 顺序推进；完成一项勾一项，并在 `docs/CHANGELOG.md` 记录。

---

## 0. 背景与目标（不可偏离）

### 已验证事实

1. 官方登录后断网，本地模式可玩。
2. 修改官方缓存 `card_data` 等资源即可加载**新卡定义**。
3. **瓶颈是拥有权**：`PlayerInventory.Cards` 中没有该 cardId → 无法携带。
4. 服务器权威不会收录社区新卡；本地断网场景只需改**客户端内存库存**。
5. 网络库存为明文 JSON，对应 `PlayerInventoryDto`（字段 `Cards` / `Heroes` 等）。

### 目标

| 优先级 | 目标 | 验收 |
|--------|------|------|
| P0 | 玩家安装 Base 后，本地 JSON 中的卡 ID 视为拥有 | 新 ID 可进入组卡并本地对战 |
| P0 | 无运行时 Hook；交付物为替换文件 + 缓存 JSON | 安装说明无需 Frida |
| P0 | modder 只编辑缓存旁 JSON + card_data | README 可独立完成创作 |
| P1 | 不写 InventoryDelta、不向官方回传自定义卡 | 断网/在线切换不炸号、不刷非法 sync |
| P2 | 跟版文档与回归清单 | 游戏更新后有复测步骤 |

### 非目标

- 官方 PvP / 匹配使用自定义卡  
- 完整私服、任务/商店经济闭环  
- 运行时动态注入框架作为正式方案  

---

## 1. 目录与职责

```text
PVZH_LocalInventoryMod/
├── PLAN.md                          ← 本文件（Agent 主计划）
├── README.md                        ← 项目总览
├── docs/
│   ├── architecture.md              ← 架构与数据流
│   ├── inventory_extra_spec.md      ← JSON 规范（modder 合同）
│   ├── static_patch_points.md       ← 静态补丁锚点 / RVA / 语义
│   ├── install.md                   ← 最终用户安装
│   ├── modder_guide.md              ← modder 创作指南
│   └── CHANGELOG.md                 ← 实施过程记录（Agent 维护）
├── templates/cache/mod/             ← 分发用模板
│   ├── inventory_extra.json
│   └── README.txt
├── examples/demo_card/              ← 最小可演示示例
├── reference/                       ← 逆向与样本（已从原工作区复制）
│   ├── il2cpp/                      ← dump / so / metadata / script.json
│   ├── samples/                     ← card_data / loc / index 样本
│   └── game_cache_layout/
├── scripts/                         ← 辅助脚本（校验 JSON、生成补丁说明等）
└── dist/                            ← 对外发布物输出目录
```

**规则**：

- 新代码、补丁产物、文档写在本工程。  
- `reference/` 视为只读快照；重新 dump 时覆盖并更新 `static_patch_points.md` 中的 RVA。  
- 原工作区 `PVZH` 可继续做卡牌美术/索引实验，**库存方案实现以本工程为准**。

---

## 2. 技术规格摘要

### 2.1 旁路文件路径（设备）

```text
Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
```

实现时用游戏 `persistentDataPath` / `files` 根拼接：

```text
{files}/cache/mod/inventory_extra.json
```

### 2.2 JSON 最小 schema

见 `docs/inventory_extra_spec.md`。核心：

```json
{
  "schemaVersion": 1,
  "Cards": { "90001": 4 },
  "Heroes": {}
}
```

Merge 语义（默认）：

- 对每个 extra 中的 cardId：`inv.Cards[id] = max(existing, extraCount)`  
- 文件缺失或解析失败：**静默跳过**，不影响官方库存  
- **禁止**将 extra 卡写入 `PlayerInventoryDelta`  

### 2.3 静态补丁挂点（优先级）

| 优先级 | 符号 | 说明 |
|--------|------|------|
| **1** | `PlayerInventoryHolderImpl.SetLocalPlayerInventory` | 所有库存写入入口，推荐 |
| 2 | `SyncPlayerInventoryCommand.LogSuccessAndAcceptServerData` | 仅覆盖 sync 成功路径 |
| 3 | `PlayerInventoryDtoTranslator.FromDto` | 仅 DTO 转换路径 |

辅助只读参考：

- `PlayerInventoryDto` / `PlayerInventory` / `PlayerInventoryUtility.GetCardInventoryCount`  
- API：`{PersistenceBaseUrl}v1/inventory/sync`  
- 本地落盘名：`PlayerInventory` / `PlayerInventoryDelta`（protobuf 系，**勿让 modder 改**）

RVA / 偏移以 `reference/il2cpp/dump.cs` + `script.json` 为准，维护在 `docs/static_patch_points.md`。

---

## 3. 分阶段任务（Agent 按序执行）

### Phase A — 规格冻结与工具（无改 so）

**状态目标**：文档与校验脚本齐备，可交给 modder 试写 JSON。

| ID | 任务 | 产出 | 完成标准 |
|----|------|------|----------|
| A1 | 确认/完善 `inventory_extra` schema | `docs/inventory_extra_spec.md` | schemaVersion、字段、错误处理写清 |
| A2 | 写 JSON 校验脚本 | `scripts/validate_inventory_extra.py` | 能检查类型、空文件、非法 key |
| A3 | 完善示例 | `examples/demo_card/` | 含假想 90001 + 说明 |
| A4 | 从 dump 提取精确 RVA 表 | 更新 `docs/static_patch_points.md` | SetLocalPlayerInventory 等方法地址齐全 |
| A5 | CHANGELOG 初始化 | `docs/CHANGELOG.md` | 有日期与 Phase A 记录 |

**本阶段不要**：修改 `libil2cpp.so` 真机分发。

---

### Phase B — 静态补丁设计与实现

**状态目标**：得到可替换的 `libil2cpp.so`（或经评估的等价静态方案），启动后 merge extra JSON。

| ID | 任务 | 产出 | 完成标准 |
|----|------|------|----------|
| B1 | 反汇编确认 `SetLocalPlayerInventory` 实现 | 笔记写入 `static_patch_points.md` | 明确寄存器/调用约定、插入点 |
| B2 | 设计注入方式 | `docs/patch_design.md` | 选一种：inline trampoline / 扩展段 / 预留 hook 表（仍属静态改 so） |
| B3 | 实现文件读取 + 轻量 JSON 解析 | 源码或补丁工程目录 `native/` | 仅依赖 libc；失败静默 |
| B4 | 实现 Cards（及可选 Heroes）merge | 同上 | 与 spec 一致；不触碰 Delta |
| B5 | 打补丁生成 `dist/libil2cpp.so` | `dist/` | 与参考 so 同架构（通常 arm64-v8a） |
| B6 | 记录复现步骤 | `docs/build_patch.md` | 另一 Agent 可按文档重建补丁 |

**约束复查**：交付路径中不得出现「请安装 Frida」。

---

### Phase C — 真机验收

| ID | 任务 | 完成标准 |
|----|------|----------|
| C1 | 干净安装：无 extra 文件 | 游戏正常登录、官方库存不变 |
| C2 | 放置模板 extra（空 Cards） | 行为与 C1 相同 |
| C3 | extra 写入已有官方卡 ID 提高数量 | 收藏/组卡数量体现（若 UI 绑定库存） |
| C4 | extra 写入**仅存在于 mod card_data 的新 ID** | 可添加进套，本地 vs AI 可打出 |
| C5 | 登录 → sync → 再读 extra | 自定义卡仍在（merge 在 Set 路径） |
| C6 | 断网本地模式完整一局 | 无崩溃、无强制联网 |
| C7 | 确认未产生非法 Delta 回传 | 抓包或日志：无自定义 ID 上传；或保持断网 |

失败时：回滚 so，记录 `docs/CHANGELOG.md`，回到 Phase B。

---

### Phase D — 社区分发包

| ID | 任务 | 产出 |
|----|------|------|
| D1 | 组装 Base 包 | `dist/PVZH-ModBase-vX.Y.Z.zip` |
| D2 | 用户安装文档终稿 | `docs/install.md` + zip 内 INSTALL |
| D3 | modder 文档终稿 | `docs/modder_guide.md` |
| D4 | 版本对齐表 | 游戏版本 / manifest / so 哈希 |

Base 包建议内容：

```text
PVZH-ModBase-vX.Y.Z/
  lib/<abi>/libil2cpp.so
  cache/mod/inventory_extra.json
  cache/mod/README.txt
  INSTALL.txt
  VERSION.txt
```

---

### Phase E — 跟版与维护（持续）

| ID | 任务 |
|----|------|
| E1 | 游戏更新后重新 dump，对比 `SetLocalPlayerInventory` 符号/RVA |
| E2 | 重打补丁，更新 `reference/il2cpp` 快照 |
| E3 | 跑 Phase C 回归清单 |
| E4 | bump 版本，发布新 Base（card mods 的 JSON 协议尽量保持 schemaVersion 兼容） |

---

## 4. Agent 工作守则

1. **先读** `PLAN.md` → `docs/architecture.md` → `docs/inventory_extra_spec.md` → `docs/static_patch_points.md`。  
2. **只写本工程**；原 `PVZH` 工作区除非用户明确要求，否则只读。  
3. **全静态交付**：研究阶段可用反汇编/调试，但发布物不得依赖 Hook 框架。  
4. **安全**：仅单机/本地库存扩展；不实现向官方服务器注入未收录卡。  
5. **大文件**：`reference/il2cpp/script.json`、`dump.cs`、`libil2cpp.so` 已就位，勿无故重复全量复制。  
6. 每完成一个 Phase，更新 `docs/CHANGELOG.md` 与本文件中的状态（可在文首加 `Status:` 行）。  
7. 不确定 merge 语义或路径时，以 `inventory_extra_spec.md` 为准，改 spec 需用户确认。

---

## 5. 建议的立即下一步（给下一个 Agent / 用户）

Phase B 产物已就绪。优先 **Phase C 真机**：

```text
1. 确认设备为 arm64-v8a，且游戏 libil2cpp.so 与 reference 哈希同源（或同版本可重 dump）
2. 备份原 so → 替换为 dist/arm64-v8a/libil2cpp.so（按现有改包流程）
3. 推送 templates 或 examples 的 inventory_extra.json 到 files/cache/mod/
4. 跑 PLAN Phase C1–C7；失败则回滚 so 并记 CHANGELOG
5. 若 JSON 不生效：核对路径、抓日志、必要时补 persistentDataPath 候选
```

---

## 6. 风险登记

| 风险 | 影响 | 缓解 |
|------|------|------|
| 游戏更新改动 SetLocal 逻辑 | 补丁失效 | Phase E 跟版；符号级定位优先于写死字节 |
| 路径与 `files/cache` 不一致 | 读不到 JSON | 多候选路径；日志（若可静态加） |
| JSON 解析在 native 过重 | so 膨胀/不稳 | 仅支持子集解析器或极简手写解析 |
| 误写 Delta | 同步异常 | 补丁只改传入的 Inventory，不调用 Delta Persister |
| 完整性校验 | so 无法加载 | 若存在校验需一并静态处理（评估后再做） |

---

## 7. 状态看板（Agent 更新）

| Phase | 状态 | 备注 |
|-------|------|------|
| A 规格与工具 | **done** | A1–A5 齐备（schema/校验/示例/RVA/CHANGELOG） |
| B 静态补丁 | **done（PC 可测产物）** | `dist/arm64-v8a/libil2cpp.so`；见 `docs/build_patch.md` |
| C 真机验收 | pending | 需设备 ABI / 原 so 哈希 / files 路径；清单见 build_patch §7 |
| D 分发包 | pending | |
| E 跟版 | pending | |

最后更新：2026-07-28（Phase B：全静态 patch 构建管线 + arm64 so）
