# 03 · 僵尸任务 200 与中文对话

## 真实入口

TextAsset 的 m_Name 和 JSON Id 都是 `PVE_Soft_Node_Zombie_200`。

原关卡玩家为僵尸（Faction=1），AI 为植物（Faction=0）、英雄 Citron，AI 卡组为 `Soft_PVE_Deck_Plant_Citron_020`。玩家 `HeroSelection=1`、`DeckId=""` 允许自行选择英雄和卡组。双方初始生命为 `Parameters.InitialHealth=20`。

原场景能力 `[362,363,394,376]` 提供随机额外卡和资源。第一版改版以 `[900000101]` 替换，避免原始规则及旧说明干扰新玩法；第一版保留其余英雄、牌组、地形和难度配置。

## 第二版：场景、对手、生命和路线

用户确认第一版“完美运行”后，第二版进一步调整目标关卡：

| 字段 | 第二版值 | 核对来源 |
|---|---|---|
| BoardConfig.PlantsBoardName / ZombiesBoardName | GrassKnuckles | 原关卡 botd_week12_day1 等使用该场景；编辑器场景表映射为拳王菜海滩 |
| OpponentConfig.HeroId | Rose | 原包 Rose 英雄定义，Faction=0，Colors=24（聪明+光能） |
| OpponentConfig.DeckId | Deck_Rose_R2 | 原包同名 TextAsset，Patrol_Node_Rose_02 已引用该卡组 |
| RepresentationConfig.Id | Rose | 与原关卡 Type=5 的英雄头像表示方式保持一致 |
| OpponentConfig.Parameters.InitialHealth | 30 | 英雄初始生命值字段 |
| PlayerConfig.Parameters.InitialHealth | 30 | 同上，不是改 Fighter 的 Health |
| BoardConfig.LaneEntries[*].LaneType | 0,1,1,1,2 | 高地、平地、平地、平地、水路 |

角色 ID `Grass_Knuckles` 与场景 ID `GrassKnuckles` 不同，不可混用。若要双方都呈现同一场景，必须同时设置 PlantsBoardName 和 ZombiesBoardName。

“冷酷牌组”由中文键 `DECK_RECIPE_ROSE_R2_TITLE`、`DECK_RECIPE_ROSE_R2_DESCRIPTION` 核对。40 张卡包括小雪花 131×4、冬窝瓜 134×4、快乐的冬青 409×4、酷酷豆 461×4，其余沿用原牌组。直接引用已有 DeckId，无需修改该共享卡组资产，避免影响其他关卡。构建时验证总数 40、全部植物阵营、职业在 Smarty/Solar、每个 GUID 不超过 4 张。

此次“卡套”按配套卡组处理；原关卡没有独立的卡背皮肤字段，不杜撰字段。保留玩家选英雄与选卡组、原难度、原超能力配置和已验证的场景技能。

不要根据章节教学示例构造不存在的 StartingSun、MaxHealth 等字段；此包实际使用 InitialSunCount、InitialHealth 等名称。

## 已核对的开场对话格式

```json
{
  "TriggerConfig": {"Type":1,"CardId":280,"TurnNumber":0,"RecordType":7},
  "DismissConfig": {"Type":0,"TimeToWait":0.0},
  "ViewType":2,
  "X":0.0,
  "Y":1.5,
  "TextKey":"Node_PVE_Soft_Node_Zombie_200:Mod1_Title",
  "Delay":0.0,
  "MustTapThrough":true,
  "TelemetryEvent":0,
  "Narrator":2,
  "$type":"PvZCards.Core.Data.MessageEventConfig"
}
```

优先深拷贝原关卡已有开场事件，改 TextKey，保留触发结构。原关卡已有两个开场消息，本次替换为标题、规则两段。

说话者枚举由原关卡和 `tools/level-editor/ui/tab_events.py`、`i18n.py` 交叉核对：0 无、1 戴夫、2 僵王博士。**人类章节中 `Speaker=1` / `MessageLocKey` 的教学示例不适用于这批文件。**

## 中文资源

Bundle 是 `cn_8`，内部 TextAsset 为 `LocalizedStrings`，不是 `cn`。本次关键 Key：

```text
Node_PVE_Soft_Node_Zombie_200:Name
Node_PVE_Soft_Node_Zombie_200:Description
Node_PVE_Soft_Node_Zombie_200:Mod1_Title
Node_PVE_Soft_Node_Zombie_200:Mod1_Rules
```

卡牌说明 Key 使用 `prefabName + "_shortDesc" / "_longDesc"`，不使用数字 GUID。`prefabName` 本身可能呈 GUID 字符串外观，两者不可混淆。本次为 414 张新增技能的单位追加说明；冬青已有说明保留。场景生命规则仅属于目标关卡，不要把它写成所有卡牌永久自带的技能。

## CSV 编辑要求

- 保持 UTF-8，无新增 BOM。保留原有特殊开头、空行和 `,` 占位记录，不重排整份语言表。
- 使用 CSV 解析器识别记录，不能以逗号 split 整行代替 CSV。
- 可利用 `csv.reader.line_num` 记录每条记录对应的原始物理行区间，只重写目标记录，其他区间直接复制。
- 说明中的换行常是两个字面字符 `\\n`；不要误改为物理换行。
- 原文件可能无末尾换行，追加新 Key 前先补记录分隔，防止新键粘到末条记录。
- 检查所有改动 Key 恰好出现一次，每个 GameEvent.TextKey 均能解析。
- 终端中文字形或编码异常不能代表资源损坏。用 UTF-8 回读和游戏截图确认。

## 2026-10-16补充：全量翻译、共享标记与名称同步

上述是历史增量案例。批量翻译另见[复用引用工作流](../03.本地化说明/04.复用引用与批量翻译工作流.md)、[文言中文包实战](../03.本地化说明/05.文言中文包实战与验收.md)及其[证据摘要](../03.本地化说明/文言中文包证据摘要.json)。该例从不同指纹的B4中文包提取，不能沿用本目录2026-10-08输入哈希。

- 读同版 `fonts/inline_text_tag` 的 `HeroesInlineTextTagMapping.Mappings`，区分图标、文字链接与 `|key|` 依赖；只在cn新增键不足以证明新 `[temp]` 标记可用。
- 原BOM、首键前缀、额外列、空键填充、引号内物理换行及字面反斜杠序列分别保留；“无新增BOM”不等于去掉已有BOM。
- `_name` 不等于卡名，需结合 `prefabName`、英雄与UI上下文。任务、商店、牌阵标题、来源提示和旧别称也要同步，普通词及同名人物用按键策略处理，禁止递归全局替换。
- 确认源文与完整覆盖，检查标记／参数／带符号数值／百分号／换行，再回读新Bundle并核对只有目标对象改变。语义审核、部署哈希、实机字形与排版分别记录，用户总体好评不代替全量通过。
