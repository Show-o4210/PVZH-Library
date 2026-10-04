# inventory_extra.json 规范（schemaVersion 1）

**文件路径（设备）**

```text
Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
```

相对游戏 `files` 根：`cache/mod/inventory_extra.json`。

本文件是 **modder 与 Base 补丁之间的合同**。变更语义时必须 bump `schemaVersion` 并更新本页。

---

## 1. 完整示例

```json
{
  "schemaVersion": 1,
  "Cards": {
    "90001": 4,
    "90002": 4,
    "90003": 1
  },
  "Heroes": {
    "Penelopea": 1
  }
}
```

## 2. 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `schemaVersion` | number (int) | 是 | 当前为 `1`。未知版本：补丁应拒绝解析并跳过 |
| `Cards` | object | 否 | 键：卡牌 ID **字符串**；值：拥有数量 **非负整数** |
| `Heroes` | object | 否 | 键：英雄 ID 字符串；值：等级/拥有相关整数（与官方库存语义一致，通常 ≥1 表示拥有） |

未列出的字段：实现可忽略（前向兼容），不得报错崩溃。

## 3. Cards 语义

- 键必须是十进制整数字符串，与 `card_data` 中实体 `Guid` / 卡 ID 一致。  
- 建议社区自定义 ID 从 **`90000`** 起，避免与官方约 1–650 冲突。  
- 值：
  - 可组卡对战单位：推荐 **`4`**（常见上限）  
  - Token / 特殊：按同类官方卡，常用 `1`  
- **Merge 规则（Base 补丁必须遵守）**：

```text
for each (id, count) in extra.Cards:
    if count < 0: ignore entry
    existing = inv.Cards[id] if present else 0
    inv.Cards[id] = max(existing, count)
```

- 默认使用 `max`，避免误把官方高数量压低。  
- **不得删除**官方库存中有、extra 中没有的卡。

## 4. Heroes 语义

- 可选。无自定义英雄需求时可 `{}` 或省略。  
- Merge 同样建议 `max`。  
- 英雄 ID 为官方字符串 ID（如样本中的 `Penelopea`），不是数字 Guid。

## 5. 错误处理（补丁）

| 情况 | 行为 |
|------|------|
| 文件不存在 | 跳过，官方库存不变 |
| 不是合法 JSON | 跳过（可打 log） |
| 缺 `schemaVersion` 或版本不支持 | 跳过 |
| 单条 Cards 键无法解析为 int | 跳过该条 |
| 单条值为非数字 / 负数 | 跳过该条 |
| 任意错误 | **不得崩溃**、不得清空库存 |

## 6. 禁止事项

1. 不要把本文件内容写入会上传的 `PlayerInventoryDelta`。  
2. 不要依赖本文件替代 `card_data`：无定义只有数量 → 可能异常。  
3. 不要修改 `/PlayerData/.../PlayerInventory` protobuf 作为社区流程。  
4. 编码必须为 **UTF-8**（可无 BOM，实现应容忍 BOM）。

## 7. 与 card_data 的配合

```text
1. 在 card_data 增加 ID=90001 的完整实体定义
2. 在 inventory_extra.json 写 "90001": 4
3. （可选）loc 增加名称/描述
4. 启动游戏 → 可拥有、可携带
```

校验工具：`scripts/validate_inventory_extra.py`（Phase A 提供）。

### 7.1 启动崩溃与「幽灵 ID」（实机结论）

若库存或**套牌**中出现 card_data 不存在的 ID，可能触发：

- `FixupLocalPlayerInventoryCommand.IsSilverCard` → NullReference  
- `FixupDecksCommand` / `DeckEditorUtils.IsCardAllowedInAnyDeck` → NullReference  

自定义卡进入套牌后可能经 **PlayerDecks 云同步** 写回账号。  
因此：extra 清空或 card_data 回滚后，**仍可能无法进游戏**，必须为脏 ID 补定义或先清套牌。  
详见 `docs/troubleshooting.md` §2.2–2.3。

## 8. 版本历史

| schemaVersion | 日期 | 说明 |
|---------------|------|------|
| 1 | 2026-07-28 | 初版：Cards + Heroes + max merge |
