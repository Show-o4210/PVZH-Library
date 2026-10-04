# Demo：扩展属性自定义卡 90001–90005

在官方 `card_data` 上克隆多张模板，改 **Guid / prefab / 三维属性 / 稀有度 / 职业色 / 阵营 / 系列 / 水生·并肩** 等字段，验证扩展属性能否加载。

重建脚本：`python scripts/make_extended_demo_cards.py`

> **公开 Git 树**：仅含 JSON / 本说明；UnityFS `card_data_5` 与完整 dump 在作者本地工作区，需自备官方缓存后用脚本生成。

## 文件

| 文件 | 说明 |
|------|------|
| `inventory_extra.json` | 拥有示例 ID 的 extra |
| `card_data_snippet.json` | 字段摘录（非完整 bundle） |
| `card_data_5`（仅完整工作区） | 注入扩展卡的 UnityFS |

## 五张扩展卡一览

| ID | 模板 | 攻/血/费 | 稀有 | 色 | 阵营 | 系列 | 特殊 |
|----|------|----------|------|----|------|------|------|
| 90001 | 10 | **9/9/1** | 4 | MegaGro | Plants | Silver | 基础克隆 |
| 90002 | 1 | **5/5/3** | 2 | Guardian | Plants | Gold | **isAquatic** |
| 90003 | 2 | **2/12/4** | 0 | Hearty | **Zombies** | Gold | 坦克僵尸 |
| 90004 | 10 | **8/1/2** | 1 | Kabloom | Plants | Set2 | 玻璃炮 |
| 90005 | 10 | **6/6/7** | 5 | Solar | Plants | Event | **isTeamup** + 高费 |

每张 `prefabName` 均唯一（`mod-ext-9000x-…`），tag 含 `modcard9000x` / `mod_extended`。
## 设备路径

```text
.../files/cache/bundles/files/cards/card_data_5
.../files/cache/mod/inventory_extra.json
```

## 重建 card_data

```bash
python scripts/clone_card_into_card_data.py ^
  --src reference/samples/card_data_5_device ^
  --out dist/card_mods/card_data_5 ^
  --from-id 10 --to-id 90001 ^
  --prefab mod-custom-90001-localtest ^
  --dump-json dist/card_mods/card_90001.json
```

## 校验 / 推送示例

```bash
python scripts/validate_inventory_extra.py examples/demo_card/inventory_extra.json

adb push dist/card_mods/card_data_5 ^
  /sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/bundles/files/cards/card_data_5
adb push dist/card_mods/inventory_extra.json ^
  /sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json
```

## 依赖

- Mod Base：`dist/libil2cpp.so`（**v3b 简化 merge**：读 JSON + `AddCardToInventory`）
- 游戏需能加载该版本 `card_data_5` 缓存

## 游戏内如何认

1. 登录后进**收藏/组卡**  
2. 找 **费用 1、攻击 9、生命 9** 的植物单位（贴图可能仍像豌豆，因 prefab 无独立美术）  
3. 或靠 debug/过滤：tag `modcard90001` / id 90001  

> 名称本地化未改时可能显示缺失文案；不影响拥有权与战斗数值。
