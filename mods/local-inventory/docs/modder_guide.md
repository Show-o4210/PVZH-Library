# 卡牌 Modder 指南

你只需改**缓存资源**和一份**明文 JSON**，不必碰 `libil2cpp.so`。

## 你需要的环境

1. 玩家已安装 **PVZH Mod Base**（含库存 merge 补丁）  
2. 能读写：  
   `Android/data/com.ea.gp.pvzheroes/files/cache/`

## 最小工作流

### 1. 定义卡牌

在官方/现有流程下修改：

```text
files/cache/bundles/files/cards/card_data_*
```

- 新增实体 ID（Guid），建议 **≥ 90000**  
- 组件结构可参考本工程 `reference/samples/card_data_5.json`  
- 技能尽量复用已有 `EffectEntitiesDescriptor` 模式  

### 2. 声明拥有

编辑：

```text
files/cache/mod/inventory_extra.json
```

```json
{
  "schemaVersion": 1,
  "Cards": {
    "90001": 4
  },
  "Heroes": {}
}
```

完整协议：`docs/inventory_extra_spec.md`。

本地可用：

```bash
python scripts/validate_inventory_extra.py templates/cache/mod/inventory_extra.json
```

### 3. （可选）名称与贴图

- 本地化：`loc` / csv（样本见 `reference/samples/cn.csv`）  
- 贴图与 manifest：见 `reference/samples/UUID-TEXTURE-AssetPathsManifest.md`  

### 4. 测试

1. 确认 Base 已装  
2. 登录 → 断网  
3. 组卡添加 90001 → 本地对战打出  

## 打包给你的玩家

```text
YourCardMod-v1/
  cache/
    mod/inventory_extra.json      # 只含你的卡 ID
    bundles/files/cards/...       # 你的 card_data 改动
    bundles/files/loc/...         # 可选
  README.txt                      # 写明依赖 Base 版本
```

**不要**在卡包里塞 so（除非你维护 Base）。

## 安全创作清单（强烈建议）

1. **模板**：只从官方简单单位整卡克隆（推荐 id `10` 系），第一轮不改技能组件。  
2. **ID**：自定义 Guid ≥ `90000`，与 `inventory_extra` 一致。  
3. **测试顺序**：只写 extra → 确认收藏/拥有 → **再**放进套牌。  
4. **套牌污染**：自定义卡进套后可能云同步；卸定义前必须先从所有套牌移除并保存。  
5. **恢复**：账号已被脏 ID 污染时，用 Guid-only 克隆补回定义（见 `scripts/make_recovery_90001.py` 与 `docs/troubleshooting.md` §2.3）。  
6. **堆叠数量**：`ignoreDeckLimit=true` 的 basic 类可能 UI 锁 4；要测数量请换可计数模板并实测。

## 常见错误

| 错误 | 结果 |
|------|------|
| 只有 inventory 没有 card_data | `IsSilverCard` NRE 或空白卡 |
| 只有 card_data 没有 inventory | 能加载定义但无法携带 |
| ID 与 card_data 不一致 | 对不上 / Fixup 崩溃 |
| 残缺 card_data 覆盖官方包 | 官方 ID 丢失 → 启动 NRE |
| 套牌含自定义 ID 后卸定义 | `FixupDecks` NRE（云端写回） |
| 复杂技能乱改 | 冻住、卡死、难复现 |
| 使用会上传的外挂改库存 | 同步失败或封号风险；请用 Base 的 extra |

完整排错：[troubleshooting.md](./troubleshooting.md)。经验总结：[lessons_learned.md](./lessons_learned.md)。

## 与原工作区的关系

卡牌美术、索引、AB 实验可在独立逆向工作区继续做；  
**拥有权与分发约定以本工程文档为准**。
