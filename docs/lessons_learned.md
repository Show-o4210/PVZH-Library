# 经验总结（Lessons Learned）

面向维护者与社区贡献者。最终用户请优先看分享包内《社区手册》与 [troubleshooting.md](./troubleshooting.md)。

> **全流程回顾 + 错误档案 E1–E10（含失败路径）**请读：  
> **[workflow_and_experience.md](./workflow_and_experience.md)**（主文档）。  
> 本文为精简条目索引。

## 1. 问题本质

| 层 | 结论 |
|----|------|
| 卡牌**定义** | 改 `card_data` 等缓存即可加载新实体（已验证） |
| 卡牌**拥有** | 客户端看 `PlayerInventory.Cards`；服务器不会给社区 ID |
| 本工程解法 | 静态补丁 `libil2cpp.so`：在 `SetLocalPlayerInventory` 后合并本地 `inventory_extra.json` |
| 非目标 | Frida 常驻、商店破解、PvP 作弊、私服 |

一句话：**定义走缓存，拥有走本地 JSON，Base 只做 merge。**

## 2. SO 补丁

### 2.1 锚点

- 函数：`SetLocalPlayerInventory`（RVA 见 `PATCH_INFO` / `static_patch_points.md`）  
- 注入点：写完本地库存指针后的 epilogue（约 `0x1FEB4E0`）  
- 行为：读 `files/cache/mod/inventory_extra.json` → 对 Cards 调用 `AddCardToInventory`

### 2.2 ELF 布局（关键教训）

| 方案 | 结果 |
|------|------|
| v1 新 PHDR 到文件尾 | 加载失败 |
| v2 额外 PT_LOAD | Houdini 仍 `JNI_OnLoad` 失败 |
| **v3 扩展 RX 段 cave** | Houdini 可加载 |
| v3 + 复杂 GetCount/完整 JSON | 曾 SIGSEGV |
| **v3b 简单扫描 + 仅 AddCard** | 模拟器稳定；**真机白屏**（SHT 未同步） |
| **v3c = v3b + 平移 section sh_offset** | 真机 bionic 通过（华为 Android 10 验证） |

**原则**：在 Houdini / 模拟器环境，**不要动 PHDR 表、不要新增 LOAD**；payload 越简单越好。

### 2.3 Merge 语义（实现现状）

- 规格写的是 `max(existing, extra)`。  
- v3b 简化实现以 **AddCard** 为主：首次插入可设数量；重复 Set 可能累加——本地测试可接受。  
- 文件缺失 / 解析失败应静默跳过，不得崩。

## 3. inventory_extra.json

- 路径固定：`Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json`  
- `schemaVersion: 1`；Cards 键为十进制字符串 ID  
- **每个 ID 必须在当前 card_data 中有定义**  
- 合法 JSON（无尾逗号）；UTF-8  
- 校验：`python scripts/validate_inventory_extra.py <file>`

## 4. card_data

### 4.1 安全改法

1. 用 UnityPy 打开官方 bundle。  
2. **深拷贝一张官方简单卡**（推荐 #10 一类基础单位）。  
3. 只改：`Guid`、（可选）展示攻防费、稀有度、阵营等表面字段。  
4. 第一轮测试 **不要**改复杂技能 / Effect 图。  
5. 自定义 ID 建议 **≥ 90000**。

### 4.2 已踩坑

| 做法 | 结果 |
|------|------|
| 乱拼技能组件 | 冻住 / 异常 |
| 多模板乱扩 | 难定位 |
| 只改 ignoreDeckLimit 测数量 | 可能有效，但规则面未完全摸清 |
| 残缺 / 错误体积的 card_data | 官方 ID 丢失 → Fixup NRE |
| 套牌用了自定义 ID 后卸载定义 | **云端套牌仍引用** → FixupDecks NRE |

### 4.3 污染账号恢复

若套牌含 `90001` 等而 card_data 没有：

1. **补 Guid-only 克隆** 进 card_data（最快恢复进游戏）。  
2. 再从套牌移除 → 同步 → 才考虑删定义。  
3. 脚本示例：`scripts/make_recovery_90001.py`。

## 5. 库存与套牌持久化

| 位置 | 说明 |
|------|------|
| `PlayerData/<id>/PlayerInventory` | 本地库存 protobuf；可含已 merge 的卡 |
| `PlayerData/<id>/PlayerDecks` | 套牌；**会云同步** |
| `inventory_extra.json` | 每次 Set 时 merge 源；不替代云端套牌清理 |

**教训**：本地删套牌脏数据 ≠ 永久干净；登录会写回。  
**流程**：未验证卡只加库存 → 确认稳定 → 再进套牌。

## 6. 环境与测试

- 多模拟器 / 多 adb 端口易推错设备。  
- 雷电等 x86_64 + Houdini 必须用 v3 系 so。  
- 排障优先 logcat：`IsSilverCard`、`FixupDecks`、`dlopen`、`libil2cpp`。  
- 对照实验：空 extra + 完整官方 card_data + v3b so = 基线。

## 7. 分发形态

| 产物 | 受众 |
|------|------|
| 重签 APK（内嵌 v3b so） | 普通玩家 |
| 单独 `libil2cpp.so` | 会自己换包 / Magisk 模块者 |
| `cache/mod` + card_data 卡包 | 卡师；**不要**重复塞 Base so |
| 工程 `docs/*` | 维护者 |

社区打包目录见仓库根下 `share/PVZH_LocalInventory_CommunityPack/`（若已生成）。

## 8. 安全与合规

- 仅本地 / 单机研究与社区卡收集。  
- 勿在官方 PvP 使用未收录卡。  
- 勿引导修改会上传的作弊库存协议。  
- 版本绑定：so 与游戏 build 必须匹配 `orig_sha256`。

## 9. 未完成 / 已知限制

- Heroes merge 在 v3b 简化路径中未作为重点验证。  
- 严格 `max` 语义与重复 Add 的差异。  
- armeabi-v7a 未交付补丁。  
- 换游戏版本需重新 dump + 重打补丁。  
- 可计数堆叠与 `ignoreDeckLimit` 的完整规则表未定稿。

## 10. 推荐阅读顺序

1. 本文件（全貌）  
2. [troubleshooting.md](./troubleshooting.md)（排错）  
3. [inventory_extra_spec.md](./inventory_extra_spec.md)（合同）  
4. [modder_guide.md](./modder_guide.md)（创作）  
5. [build_patch.md](./build_patch.md)（重建 Base）  
