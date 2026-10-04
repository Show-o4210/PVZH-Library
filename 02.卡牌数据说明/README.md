# 02. 卡牌数据说明 (card_data)

本章节深入解析《植物大战僵尸：英雄》（PVZH）核心数据包 `cards/card_data_X` 中保存的卡牌 JSON 数据结构、属性组件、技能逻辑树机制以及相关的开发维护指南。

---

## 目录导航

| 序号 | 专题文档 | 核心涵盖内容 |
| :---: | :--- | :--- |
| **01** | [01. 基础属性与元数据](01.基础属性与元数据.md) | 包含 GUID、baseId、阵营/职业 (faction/color)、稀有度 (rarity)、费用与基础攻防、Subtypes（类别标签）、Tags（UI标签）及 Affinities（关联权重）等。 |
| **02** | [02. 底层 JSON 组件结构](02.底层JSON组件结构.md) | 详解 `entity.components` 数组机制、核心属性组件（Card, SunCost, Attack, Health, Rarity）、常见独立能力组件（Teamup, Armor, Untrickable, Strikethrough 等）及 Counters 计数器结构。 |
| **03** | [03. 技能逻辑树与 EffectEntities](03.技能逻辑树与EffectEntities.md) | 详解 `EffectEntitiesDescriptor` 节点树、Triggers（触发器）、Filters（过滤器）、Targets（目标选择器）、Effects（效果节点）以及双轨/赋予型能力（GrantedTriggeredAbility）。 |
| **04** | [04. Card-Editor 与 JSON 映射指南](04.Card-Editor与JSON映射指南.md) | 结合社区工具 `PVZH-Card-Editor` 的架构设计，讲解图形化编辑器 `.phantom` 工程格式与游戏原生 JSON 数据之间的转换规范与校验注意要点。 |
| **05** | [05. 手动修改最佳实践与新建卡牌指南](05.手动修改最佳实践与新建卡牌指南.md) | **黄金法则**：手动修改 JSON 强烈推荐直接复制原版代码块粘贴修改；讲解如何通过在 JSON 底部接续全新 GUID + 复用 `prefabName` 快速创建全新独立卡牌。 |
| **06** | [06. 技能效果 JSON 复制模板 (Effects)](06.技能效果JSON复制模板.md) | **纯代码模板库 (一)**：整理 Buff 增益/减益、关键字特质赋予、伤害/消灭/弹回/治疗及抽卡/费用/召唤纯净 JSON 复制模板。 |
| **07** | [07. 检测与判定逻辑 JSON 复制模板 (Queries & Filters)](07.检测与判定逻辑JSON复制模板.md) | **纯代码模板库 (二)**：整理 `CompositeAllQuery` (与门)、`CompositeAnyQuery` (或门)、`NotQuery` (非门)、过滤器与状态断言纯净 JSON 复制模板。 |
| **08** | [08. 触发条件与时机 JSON 复制模板 (Triggers)](08.触发条件与时机JSON复制模板.md) | **纯代码模板库 (三)**：整理登场打出、回合开始/结束、受伤害、本线战斗结束、亡语死亡及抽卡等触发时机纯净 JSON 复制模板。 |
| **09** | [09. 目标选择器 JSON 复制模板 (Targets)](09.目标选择器JSON复制模板.md) | **纯代码模板库 (四)**：整理自身实体、全场随从、随机随从、双方英雄及所在线路目标选择器纯净 JSON 复制模板。 |

---

## 核心要点概览

1. **结构分层**：
   PVZH 的卡牌数据分为**外层元数据**（用于 UI 渲染、卡组构筑限制、合成消耗、筛选过滤）与**内层实体组件 (`entity.components`)**（游戏引擎底层逻辑运行所需的实际数据与 C# 组件对象）。
2. **能力实现双轨制**：
   - **基础能力组件**：如 `TeamupComponent`（团队协作）、`ArmorComponent`（护甲）、`UntrickableComponent`（无法成为法术目标）等，直接挂载在 `entity.components` 中。
   - **逻辑树能力 (`EffectEntitiesDescriptor`)**：复杂技能（如战吼、登场、死亡触发、连击、加Buff、抽卡等）通过嵌套的触发器（Trigger）、过滤器（Filter）、目标（Target）和效果（Effect）节点组装而成。
3. **新建卡牌与修改黄金法则**：
   - **手工修改 JSON 首选“复制粘贴原版代码”**，能最大程度避免程序集拼错或 JSON 括号语法缺失。
   - 新建卡牌只需在 JSON 底部全套复制某张卡牌框架，**赋予全局唯一的 GUID**；`prefabName` 复用完全没有问题（复用只代表共享原版 2D 贴图与动画，引擎仍视其为全新的独立卡牌）。

---

> [!TIP]
> 推荐结合 [PVZH-Card-Editor](https://github.com/Show-o4210/PVZH-Library/tree/main/tools/card-editor) 一同阅读本章节。编辑器源码中的 [card_model.py](https://github.com/Show-o4210/PVZH-Library/blob/main/tools/card-editor/card_model.py) 和 [logic_library.py](https://github.com/Show-o4210/PVZH-Library/blob/main/tools/card-editor/logic_library.py) 是对底层 JSON 最直观的代码化整理。

