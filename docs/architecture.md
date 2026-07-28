# 架构说明

## 1. 问题切分

```text
┌─────────────────────┐     ┌──────────────────────┐
│  card_data 缓存      │     │  PlayerInventory     │
│  （卡是什么）         │     │  （你有没有这张卡）    │
│  ✅ 已可用缓存 mod    │     │  ❌ 原仅服务器下发     │
└─────────────────────┘     └──────────────────────┘
         │                            │
         └──────────┬─────────────────┘
                    ▼
              组卡 / 本地对战
```

本工程**只解决右侧拥有权**；卡牌定义仍走现有缓存 mod 管线。

## 2. 官方库存流（简化）

```text
登录
  → SyncPlayerInventoryCommand
  → HTTP {PersistenceBaseUrl}v1/inventory/sync
  → PlayerInventoryDto  (JSON: Cards, Heroes, …)
  → PlayerInventoryDtoTranslator.FromDto
  → PlayerInventoryHolder.SetLocalPlayerInventory
  → 内存 Dictionary<int,int> Cards
  → LocalPlayerInventoryPersister 落盘（protobuf 系，非 modder 界面）
```

断网后：`[SyncPlayerInventoryCommand] Offline`，继续用内存/本地缓存库存。

组卡查询核心：

- `PlayerInventoryUtility.GetCardInventoryCount`
- `PlayerInventoryUtility.HasAtLeastOfCard`

## 3. 本方案插入点

```text
SetLocalPlayerInventory(inv)
    │
    ├─ 1. （原逻辑）保存 inv
    │
    └─ 2. 【静态补丁新增】
          path = {files}/cache/mod/inventory_extra.json
          if file ok:
              parse Cards / Heroes
              merge into inv.Cards / inv.Heroes
          （不写 PlayerInventoryDelta）
```

选择 `SetLocalPlayerInventory` 的原因：

- 覆盖「服务器 sync」「本地加载」等所有写入路径  
- 每次以服务端数据覆盖后再 merge，自定义卡不会丢  

## 4. 设备文件布局

```text
Android/data/com.ea.gp.pvzheroes/files/
  cache/
    bundles/files/cards/card_data_*    ← 卡牌定义（现有 mod）
    bundles/files/loc/…               ← 文本（可选）
    mod/                              ← 本方案约定
      inventory_extra.json            ← 拥有权旁路
      README.txt
  … 其它官方文件 …
```

## 5. 分发拓扑

```text
维护者：逆向 → 静态 patch libil2cpp.so → 发布 Base 包
玩家：  替换 so + 放入 cache/mod/
modder：只改 inventory_extra.json + card_data（及贴图/文本）
```

## 6. 与「全解锁」方案的区别

| | inventory_extra merge（本方案） | 恒返回 4 全解锁 |
|--|-------------------------------|----------------|
| 粒度 | 只声明的卡 | 全部卡 |
| modder JSON | 需要 | 不需要 |
| 社区创作面 | 有 | 无 |
| 实现复杂度 | 中 | 低 |

本工程采用 **merge**，以支持自由创作。

## 7. 安全边界

- 不实现向 `v1/inventory/sync` **上传**自定义卡。  
- 补丁禁止调用会标记 Delta 的加卡路径写入 extra。  
- 官方 PvP 不在支持范围。
