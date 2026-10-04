# Changelog

## 2026-07-28 — 社区封面 v3c.1 + 分发树整理

### 社区包 v3c.1

- 启动 `sharedassets0.assets` 换为**社区/非官方**封面提示后重打 APK  
- 包标识：`VERSION.txt`；更新 `README.md` / `NOTICE.txt` / `SHA256SUMS.txt`  
- 同步：`dist/apk/`、`share/PVZH_LocalInventory_CommunityPack/`、同名 zip  
- 真机安装验证：进程可进 Unity，无 `.dynamic` / sharedassets 加载失败

### 仓库布局

| 路径 | 用途 |
|------|------|
| `share/PVZH_LocalInventory_CommunityPack/` | 玩家向精简包（含 APK） |
| `github_ready/` | **可公开 GitHub** 的源码+文档（无 APK/so/dump） |

- 根 `README.md`、`share/README.md` 标明双通道分发  
- `github_ready/GITHUB_SCOPE.md` 写清可上传 / 勿上传清单

## 2026-07-28 — 全流程与错误档案文档

- 新增 `docs/workflow_and_experience.md`：端到端工作流、演进时间线、**错误档案 E1–E10**（v1/v2 加载失败、真机 `.dynamic`、幽灵 ID、多设备等）
- `troubleshooting.md` 决策树指向 v3c 与 E 编号
- `lessons_learned.md` / 根 README 交叉链接

## 2026-07-28 — 工作区整理 + 精简社区包

### 删除（临时 / 过时）

- `dist/apk_test`（旧 v1–v3b 测试 APK，~1.8GB）
- `dist/apk_rebuild`、`apk_extracted_so`、设备 dump
- `apk/1` apktool 全量反编译（~1GB，可再解）
- 实验性 `card_mods` 变体目录；保留 recovery + empty extra
- 旧分享包内重复 v3b APK、idsig、native so、冗长多文档

### 精简分享包

```text
share/PVZH_LocalInventory_CommunityPack/
  README.md + NOTICE.txt + SHA256SUMS.txt
  apk/pvzh_mod_base_v3c.apk
  templates/cache/mod/
  examples/  (demo/empty extra + recovery card_data)
```

zip 约 186MB（原先 ~400MB+ 含重复 so/apk）。

## 2026-07-28 — v3c：真机 bionic `.dynamic` 偏移修复

### 现象

- 社区包 v3b 在**真机**白屏秒退；模拟器 Houdini 可能仍可进。  
- logcat：

```text
.dynamic section has invalid offset: 0x392b250,
expected to match PT_DYNAMIC offset: 0x392f250
```

### 原因

插入 RX cave 后只更新了 PHDR `p_offset`，未更新 SHT `sh_offset`（差 0x4000）。

### 修复

- `scripts/build_and_patch.py`：对 `insert_at` 之后的 section `sh_offset` 统一 `+CAVE_SIZE`  
- `_validate_patched_v3`：强制 `PT_DYNAMIC.p_offset == .dynamic.sh_offset`  
- 产物：`dist/apk_test/pvzh_v3c_so.apk`、分享包 `apk/pvzh_mod_base_v3c.apk`  
- 华为 STK-TL00 (Android 10) 已验证：Unity 正常启动，无 dlopen abort

## 2026-07-28 — 社区分享包 + 排错/经验文档

### 文档

- 新增 `docs/troubleshooting.md`：IsSilverCard / FixupDecks / v1v2 加载失败 / 套牌云同步污染等实机排错
- 新增 `docs/lessons_learned.md`：SO、extra、card_data、持久化全链路经验
- 更新 `docs/install.md`、`docs/modder_guide.md`、根 `README.md`
- 新增可分发目录 `share/PVZH_LocalInventory_CommunityPack/`（手册 + v3b APK + 模板 + native so）

### 运行时结论（验证）

- 脏套牌 ID（如 90001）会经 **PlayerDecks 云同步** 写回；仅恢复官方 card_data / 空 extra **不能**保证能进游戏
- 恢复优先：**为套牌中每个自定义 ID 补 Guid-only 定义**（`scripts/make_recovery_90001.py`）
- 推荐 Base：`v3b`（RX cave + 简单 JSON 扫描 + AddCard）

## 2026-07-28 — 真机/模拟器验证闪退并修复到 v3 / v3b

### 复现环境（adb）

- 设备：雷电等 x86_64 + Houdini arm64 翻译
- 对照：原版 so 可启动；v1/v2 补丁 so 启动闪退

### logcat 根因（v2）

```text
Unable to load library: .../lib/arm64/libil2cpp.so
[dlopen failed: undefined symbol: JNI_OnLoad]
```

v1/v2 采用「新增 PT_LOAD + 搬迁 PHDR」：在 Houdini/native bridge 下动态加载失败。

### 修复（v3）

- **不再新增 PHDR / PT_LOAD**
- 利用 RX 与 RW 之间 VA 空隙扩展原 RX `PT_LOAD`，写入 payload
- Hook：`0x1FEB4E0` → cave
- 产物：`dist/arm64-v8a/libil2cpp.so`

### v3b

- 去掉复杂 GetCount 路径；简单扫 `"digits":digits` + `AddCardToInventory`
- 测试包：`dist/apk_test/pvzh_v3b_so.apk`

### 废弃

- v1 / v2 请勿再使用

## 2026-07-28 — Phase B：静态 so 补丁可构建

### Phase A 扫尾

- `scripts/validate_inventory_extra.py`、examples/templates
- RVA：`SetLocalPlayerInventory` = `0x1FEB478`

### Phase B

- 挂点确认、payload、`scripts/build_and_patch.py`
- 文档：`patch_design.md`、`build_patch.md`、`static_patch_points.md`

## 2026-07-28 — 工程初始化

- 方案：静态 so + `cache/mod/inventory_extra.json`
- PLAN / 架构 / JSON 规范 / 安装与 modder 文档
