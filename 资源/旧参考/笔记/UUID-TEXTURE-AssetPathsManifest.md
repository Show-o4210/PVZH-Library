# PVZH：UUID ↔ TEXTURE_NAME 与 AssetPathsManifest 探索总结

> 基于工作区内 `libil2cpp.so` / `dump.cs`、客户端缓存 `com.ea.gp.pvzheroes`、以及 `示例/` 数据的逆向与对照结果。  
> 日期参考：2026-07。版本以缓存中 `manifest_version = 11047` 为准。

---

## 1. 问题是什么

希望搞清楚卡牌逻辑 ID（**UUID**）如何对应资源文件名（**TEXTURE_NAME**），例如：

| 字段 | 示例（鳄梨 / Guacodile） |
|------|--------------------------|
| GUID | `1` |
| UUID | `2f9fa005-8b50-4d1a-89be-38e4a82036c4` |
| TEXTURE_NAME | `2ceeb890a69397041ba1fd559056c358_1` |
| 磁盘文件 | UnityFS AssetBundle |

**结论：客户端不会用算法把 UUID 哈希成 TEXTURE_NAME。**  
对应关系来自运行时加载的 **`AssetPathsManifest`** 查表。

---

## 2. 关键数据源

### 2.1 卡牌数据

| 文件 | 作用 |
|------|------|
| `示例/card_data_5.json` | 卡牌权威数据；`prefabName` **就是 UUID**（或少数特殊名如 `Goat`） |
| `示例/cn.csv` | 本地化：`{uuid}_name` / `_shortDesc` / `_longDesc` / `_flavorText` |
| `示例/index_new.json` | 整理后的索引（已用 manifest 重建过，见第 7 节） |

`CardData`（dump）关键字段：

- `PrefabName`（JSON 键 `prefabName`）→ UUID / 资源 ID  
- `IsFighter` / `IsEnv` / `IsPower` 等 → 类型判断  

### 2.2 客户端缓存布局

```text
com.ea.gp.pvzheroes/
  files/cache/
    manifest/
      manifest_version                    → 当前如 11047
      UnityABVersion_11047/
        AssetPathsManifest                → JSON（可被编辑器美化）
        AssetPathsManifest.bin            → 二进制（运行时优先）
    bundles/
      files/
        autotagged/<32hex>_<version>      → 单卡 AB（Texture/Prefab 等）
        atlastagged/cardfaces_<color>_n → 图鉴合图
        versions
    abg/
      all_bundles.abg / bootstrap.abg / ...
```

示例包：

```text
.../bundles/files/autotagged/2ceeb890a69397041ba1fd559056c358_1
```

包内可扫到 UUID 字符串与 `cards/generated` 等路径痕迹。

---

## 3. 完整映射链

```text
card_data.prefabName  (= UUID，少数为特殊名)
        │
        ▼
逻辑资源路径（运行时再拼/规范化，manifest 中为完整路径）:
  Assets/Ship/Prefabs/Cards/{UUID}                         ← Avatar Prefab
  Assets/Ship/Cards/GeneratedSprites/InHand/{UUID}         ← 手牌图
  Assets/Ship/Cards/GeneratedSprites/InCollection/{UUID}   ← 图鉴图
        │
        ▼
AssetPathsManifest.BundleNamesByAssetPath[path]
  → { "Ex": ".prefab"|".png", "Bn": "autotagged/<32hex>" }
        │
        ▼
AssetPathsManifest.BundleNameToDetails[Bn]
  → { "Version": 1, "Size": ..., "Dependencies": [...] }
        │
        ▼
TEXTURE_NAME = basename(Bn) + "_" + Version
             = "2ceeb890a69397041ba1fd559056c358" + "_" + "1"
        │
        ▼
磁盘: bundles/files/autotagged/<32hex>_<version>
      （UnityFS，Unity 2022.3.x）
```

### 3.1 代码侧路径常量（`CardViewConstants`）

```text
CARD_PREFAB_ROOT_PATH          = "Prefabs/Cards/"
CARD_IN_HAND_SPRITE_PATH       = "Cards/GeneratedSprites/InHand/"
CARD_IN_COLLECTION_SPRITE_PATH = "Cards/GeneratedSprites/InCollection/"
```

加载任务（`CardAssetsTask`）用 `CardData.PrefabName` 拼路径；  
`AssetBundlePathProvider.AssetPathToBundleName` 再查 manifest 得到 `Bn`；  
`AssetBundleUtilities.GetPathForBundle(bundleName, version)` 得到缓存路径（格式串含 `{0}{1}_{2}` 一类拼接）。

### 3.2 Prefab / InHand / InCollection 差异

| 用途 | 典型 Bn | 是否等于 index 里的 TEXTURE_NAME |
|------|---------|----------------------------------|
| Prefab + InHand | `autotagged/<32hex>`（通常同一 Bn） | **是**（单卡包） |
| InCollection | 多为 `atlastagged/cardfaces_<颜色>` 合图 | **否**（多卡共用 atlas） |
| 少数 Power 等 | 可能只有 InCollection 落在 `autotagged/*` | 可作为 TEXTURE 回退源 |

**Bn 带目录前缀**（`autotagged/`、`atlastagged/`）；  
**TEXTURE_NAME 只用最后一段 hash + 版本号**。

### 3.3 哈希含义

- `Bn` 中 32 位 hex 是 **打包时的内容哈希**（Unity AssetBundle 命名），不是客户端对 UUID 做 MD5/SHA1。  
- 无 manifest 时 **无法** 仅凭 UUID 算出 TEXTURE_NAME。

---

## 4. AssetPathsManifest 结构

### 4.1 JSON 顶层

```json
{
  "BundleNamesByAssetPath": {
    "Assets/Ship/Prefabs/Cards/<uuid>": {
      "Ex": ".prefab",
      "Bn": "autotagged/<32hex>"
    }
  },
  "BundleNameToDetails": {
    "autotagged/<32hex>": {
      "Dependencies": [ "autotagged/...", "materials", "shaders" ],
      "Version": 1,
      "Size": 225466
    }
  }
}
```

约（11047）：**8015** 条路径映射，**2880** 个 bundle 详情。

### 4.2 类型（dump）

- `BundleInfo`：`Ex`（扩展名）、`Bn`（bundle 名）  
- `BundleDetails`：`Dependencies`、`Version`、`Size`  
- `AssetPathsManifest`：`FILENAME = "AssetPathsManifest"`  
  实现 `IBinarySerializable` + FastJson 序列化  

TypeCode：

| Code | 类型 |
|------|------|
| 1000 | `BundleInfo` |
| 1001 | `BundleDetails` |
| 1002 | `AssetPathsManifest` |

---

## 5. 运行时加载：bin 优先，JSON 兜底

### 5.1 类关系

```text
AssetPathsManifestLoader
  : BinaryJsonFallBackDataService<AssetPathsManifest>
  : BinaryDataService<AssetPathsManifest>
  : FileReaderDataServiceBase
```

### 5.2 顺序

1. 尝试加载 **`AssetPathsManifest.bin`**（二进制 `IBinarySerializable`）  
2. 若 bin 缺失或反序列化失败 → **`ConverFromJson`** 读 **`AssetPathsManifest`**（无后缀 JSON）  

因此：

| 文件 | 正常游戏下 |
|------|------------|
| **`.bin`** | **主路径，真正生效** |
| **JSON** | Fallback；与 bin 是同一逻辑数据的两种序列化 |

**只改 JSON、不处理 bin → 游戏行为通常不变。**  
用 JSON 插件美化缓存中的 JSON，一般也不影响已能成功加载的 bin。

### 5.3 bin 格式要点（非定长表）

- 带 **count + 变长字符串** 的自定义序列化，不是固定槽位表。  
- **可以新增条目**（增大文件、count+1），但不能简单 append 几个字节；需按 `Write/Read` **整包重写**。  
- 文件头可观察到 TypeCode `1002`、路径数字典 count 与 JSON 一致（如 8015）。

---

## 6. 修改 / 扩展思路（待后续细化）

### 6.1 方案对比

| 方案 | 做法 | 优点 | 注意 |
|------|------|------|------|
| **A. 强制 JSON** | 改 JSON，删/改名 `.bin` | 实现快，无需编解码 | 热更可能重新下 bin |
| **B. 重生成 bin** | JSON 编辑 → 按规则编码写回 bin | 长期稳定 | 需实现 round-trip 编解码 |
| **C. 仅改指向** | 已有 Bn 之间重映射 | 不必新资源 | 变长字符串不宜手 patch |
| **D. 复用资源** | 改 `card_data.prefabName` 指向已有 UUID | 常无需动 manifest | 适合换皮/占位 |

### 6.2 “新增内容”完整条件

即使 manifest 写对，仍需：

1. 磁盘上存在对应 UnityFS：`bundles/files/...`  
2. `BundleNamesByAssetPath` + `BundleNameToDetails` 齐全  
3. `Dependencies` 满足（materials/shaders/其它 autotagged）  
4. 防止 `manifest_version` / CDN 覆盖本地修改  

### 6.3 建议优先级

1. 试验：方案 A  
2. 长期 mod：方案 B（bin ↔ json 工具 + round-trip）  
3. 只换已有图：优先改 `prefabName` 复用 Bn  

---

## 7. 本仓库已产出物

### 7.1 提取的 Manifest

目录：`extracted/`

| 文件 | 说明 |
|------|------|
| `AssetPathsManifest.json` | 紧凑 JSON（与未美化缓存一致量级） |
| `AssetPathsManifest.pretty.json` | 缩进版，便于阅读 |
| `AssetPathsManifest.bin` | 运行时主用二进制副本 |
| `README.md` | 提取说明 |
| `AssetPathsManifest.README.json` | 元数据 |

源路径：

```text
com.ea.gp.pvzheroes/files/cache/manifest/UnityABVersion_11047/
```

### 7.2 完善后的 Index

| 文件 | 说明 |
|------|------|
| `示例/index_new.json` | 重建后的索引 |
| `示例/index_new.backup.json` | 重建前备份 |
| `index_new.json` | 根目录副本 |

在原有 `GUID / UUID / NAME_CN / NAME_EN / TYPE / FACTION / TEXTURE_NAME` 上补充例如：

- `COLOR`, `RARITY`, `RARITY_NAME`, `SET`  
- `COST`, `ATTACK`, `HEALTH`  
- `BUNDLE`, `INCOLLECTION_BUNDLE`, `CACHE_PATH`, `TEXTURE_EXISTS`  
- `IS_FIGHTER`, `IS_ENV`, `IS_POWER`, `IS_AQUATIC`, `IS_TEAMUP`  

生成逻辑脚本：`build_index_and_extract_manifest.py`  

TEXTURE 解析优先级：

1. `Prefabs/Cards/{id}`  
2. `InHand/{id}`  
3. `InCollection/{id}` 且 Bn 为 `autotagged/*`（如部分法术只有图鉴单包）  

### 7.3 其它

- `uuid_texture_map_from_manifest.json`：较早导出的 UUID↔纹理表  
- `export_uuid_texture_map.py`：早期导出脚本  

---

## 8. 关键 so / dump 符号（便于续挖）

| 符号 / 类型 | 作用 |
|-------------|------|
| `PvZCards.Common.AssetPathsManifest` | 路径→包、包→详情 |
| `PvZCards.Common.BundleInfo` / `BundleDetails` | Ex/Bn；Version/Size/Deps |
| `AssetBundlePathProvider.AssetPathToBundleName` | 查 Bn |
| `AssetBundlePathProvider.AssetPathToUsableAssetName` | 路径 + Ex |
| `AssetBundleUtilities.GetPathForBundle` | 缓存文件名 |
| `AssetPathsManifestLoader.LoadManifest` | 按版本加载 |
| `BinaryJsonFallBackDataService.Deserialize` / `ConverFromJson` | bin→json 回退 |
| `CardAssetsTask` / `CardViewConstants` | 卡资源路径与加载 |
| `CardData.PrefabName` | UUID 入口 |

---

## 9. 鳄梨对照样例（端到端）

```text
UUID:   2f9fa005-8b50-4d1a-89be-38e4a82036c4
路径:   Assets/Ship/Prefabs/Cards/2f9fa005-8b50-4d1a-89be-38e4a82036c4
        Assets/Ship/Cards/GeneratedSprites/InHand/2f9fa005-...
Bn:     autotagged/2ceeb890a69397041ba1fd559056c358
Version:1
TEXTURE_NAME: 2ceeb890a69397041ba1fd559056c358_1
InCollection Bn: atlastagged/cardfaces_guardian
缓存:   .../bundles/files/autotagged/2ceeb890a69397041ba1fd559056c358_1
```

---

## 10. 后续可做清单（未完成）

- [ ] 实现 `AssetPathsManifest.bin` ↔ JSON 的完整编解码（round-trip）  
- [ ] 「强制 JSON 模式」一键备份/删除/恢复 bin 脚本  
- [ ] 新增映射模板：uuid + 已有 texture → 改 JSON（可选写 bin）  
- [ ] 热更覆盖防护策略（本地 version 钉死 / 拦截下载）  
- [ ] 解析 AB 内部资源清单（Prefab/Sprite 名与依赖）  
- [ ] 英文名独立数据源（当前 index 的 `NAME_EN` 主要继承旧表）  

---

## 11. 一句话总结

> **UUID = 卡资源 ID（prefabName）；TEXTURE_NAME = manifest 查表得到的 AssetBundle 文件名（内容哈希_版本）；运行时优先读 `.bin`，JSON 仅 fallback；改映射可改 JSON 并去掉 bin，或正确重写 bin；新增资源还需磁盘 AB 与依赖齐全。**

---

*文档由工作区逆向探索整理，便于后续独立处理 bin/JSON 修改与资源替换。*
