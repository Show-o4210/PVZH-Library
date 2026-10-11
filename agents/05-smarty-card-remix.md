# 05 · 小范围卡牌重写与能力边界

2026-10-10，独立工程 `mod2/` 第一版。基线仍是本目录 README 的三份原包哈希，UnityPy 1.25.0。本章保留七张聪明卡的历史案例；后续累计修改分别见06、07章，当前统计见[09章](09-maintenance-and-evidence.md)。第一版证据归档在交付工程的 `mod2/releases/v1-startup-confirmed/`，不能用当前verification报告替代旧版证据。

## 先确定映射，保存用户纠正

| 需求称呼 | 原版卡／GUID |
|---|---|
| 冰冻生菜 | 140 |
| 冻窝瓜 | 冬窝瓜 134 |
| 冬瓜 | 143 |
| 播种魔法豆 | 333 |
| 豆神 | **小豆丁 326**，用户后续纠正；不能沿用初始魔法豆茎 345 的推测。 |
| 暗物质火龙果 | 464 |
| 原始豌豆 | 原始豌豆射手 658 |

用户确认数字简写 `101 / 816 / 211` 是费用／攻击／生命，含有 0 攻击。不要自行为了让溅射触发改成 1 攻击。“向上的战斗开始前”确认指所在路线。冰冻生菜后续明确为只让**已被冻结**的僵尸额外攻击，不能保留原冻结效果。

卡名以 CN 的 `prefabName + _name` 映射，不依靠昵称猜 GUID。普通字段修改要同步实际组件和 `displaySunCost/displayAttack/displayHealth`；卡框显示更新不等于引擎身材更新。

## 可复用的技能组合

### 已冻结目标额外攻击

沿用 140 的 PlayTrigger、Manual 选取与 Zombies + TargetableInPlayFighterQuery。再给 PrimaryTargetFilter 的 CompositeAllQuery 添加：

```json
{
  "$type": "PvZCards.Engine.Queries.HasComponentQuery, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
  "$data": {
    "ComponentType": "PvZCards.Engine.Components.Slowed, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null"
  }
}
```

把 SlowEffectDescriptor 替换为 ExtraAttackEffectDescriptor。`Slowed` 是冻结状态的 MarkerComponent，不是 SlowedTrigger。本次额外证据为本机 `D:\Codex\PVZH\dump\dump.cs` 的 `PvZCards.Engine.Components.Slowed` 声明；它帮助确认类名，不能证明跨版本 RVA 可用。这里没有使用该 dump 的内存地址，也没有修改 native。

### 冻结消灭、消灭后冻结自己

- 134 原版 SlowedTrigger 的目标查询删去 Zombies 限制，保留 FighterQuery + InLaneQuery，即监听两阵营单位。
- 使用 638 女巫榛子的 DestroyCardTrigger + KilledByQuery(SelfQuery) 表达**由自身消灭**，不能监听任意消灭事件后冻结自己。
- 伤害致死另有 DamageTrigger 路径；491 超新星巨尸同时采用伤害致死和直接消灭两路。本次也给冬窝瓜组合这两路。
- 消灭后冻结自己的 SelfEntityFilter 使用 WillTriggerEffectsQuery + IsAliveQuery，PrimaryTargetFilter 为 SelfQuery，效果为 SlowEffectDescriptor。活体过滤避免死后的自身继续进入冻结／消灭链。
- 需求没有排除自己，因此冬窝瓜自己被冻结也会被自己的 SlowedTrigger 消灭；不要私自加 Not(SelfQuery)。这是该规则的直接后果。

### 本线战斗前／后

562 双重打击隐藏技能的实体包含：LaneCombatEndTrigger、TriggerTargetFilter(SameLaneQuery)、活体 SelfEntityFilter、PrimaryTargetFilter(SelfQuery)、ExtraAttackEffectDescriptor。

以它为壳，冬瓜把效果换成 SlowEffectDescriptor 得到本线结束冻结自己；原始豌豆把触发器换为 LaneCombatStartTrigger 得到本线开始前额外攻击。603 分裂射手也是同线战斗开始前的原版依据。打出冻结自己可用原版冬瓜 PlayTrigger 实体，把主目标改为 SelfQuery。

### 洗牌和关键词

- 333 的 CreateCardInDeckEffectDescriptor：CardGuid 从 345 改为 326，AmountToCreate=5，DeckPosition=Random。目标保留植物 Player 查询。
- 致命取 239、穿透取 139、必中取 78、锦囊免疫取 6 的实际顶层组件；保留 Counters 结构及其不同 Value。
- 溅射直接是 SplashDamage 的 DamageAmount=20。
- 双重打击复用 113 的 GrantedTriggeredAbilities，**真实结构是 `{"a":[{"g":562,"vt":0,"va":0}]}`，不是 `{"a":[562]}`**。卡框特殊能力为 Repeater，不要凭显示文字造 DoubleStrike 组件。
- 关键词引擎组件与 `special_abilities` 卡框表现都要同步；中文使用原包已有的 `[deadly]`、`[doublestrike]` 等 token。

## 能力不等价时的舍弃原则

本次用户明确允许舍弃无法可靠制作的需求。原包与本机引擎类型调查未找到通用每次攻击结束触发器：

| 替代时机 | 为什么不能直接声称是“攻击后” |
|---|---|
| DamageTrigger | 对英雄、穿透、多目标伤害可能分次触发；0 伤害、护甲阻挡等不保证等价。附加伤害还可能递归触发。 |
| LaneCombatEndTrigger | 是路线结算事件，不能覆盖场外或战斗中的每次额外攻击。 |
| ExtraAttackTrigger | 只描述额外攻击事件，不能覆盖普通攻击，且不应凭类名断言在攻击结算后。 |

因此舍弃火龙果“攻击后伤害相邻植物”和原始豌豆“攻击后弹射自己”。不悄悄替换为路线结束或造成伤害后。

“无法获得力量”没有找到全来源增益免疫的现成开关。BuffTrigger 设回 0 不能保证持续光环、手牌增益、变形或设值均被阻止；AttackOverride 依据 CardStat 指定另一个属性作攻击，不是不可加攻。因此此项也舍弃。

以上是**当前纯数据实现的边界**，不是引擎层绝对不可能。舍弃内容必须列明具体效果、理由，并从中文说明中去掉。零攻击的小豆丁仍可能无法按直觉触发部分攻击关键词；本次没有擅自改变用户确认的 0 攻击。

## 独立工程与校验

新工程从干净输入创建，不能直接把上一改版的 out 当原版。即使本次不改关卡，也需部署原样 data_assets_29，避免设备残留 mod1 的新增 BoardAbility 引用。

本次构建检查：651 张卡，仅七个指定 GUID 有变化；14 个中文说明 Key 唯一、非目标 CSV 记录顺序和值不变；输出回读成功；cards 与 LocalizedStrings 各一个序列化对象变化，其余对象原始字节相同；data_assets_29 与原包完全一致。记录每份输入输出 SHA-256 和可审查 before/after JSON。

用户把运行验收限定为能进入游戏，因此报告分开写：静态校验、设备三包哈希、主界面截图。**启动通过不表示卡牌交互经过战斗实测**。不要以 monkey 返回成功、PID 存在或开屏动画冒充进入游戏。

ADB 可列出 device 但 shell 仍可能挂起，调用必须有超时。先核对模拟器实际运行状态，必要时对目标设备重连，再启动用户已有的模拟器。不要据 `emulator-5554` 推断品牌；本次实际是雷电，MuMu 另有关闭的实例。沙箱内模拟器 CLI 可能无法枚举用户桌面的真实窗口／进程，不能仅据此断言模拟器关闭。

本次用户明确要求结束后台 MuMu 并重启雷电，执行后连接恢复。MuMu Remote 三个系统进程需要正常 Windows 管理员授权；仅停止相关进程及对应服务，不改服务启动类型。最后截图确认进入正常对战大厅，**启动验收通过**；保留部署三包哈希与截图作为该构建的证据。不要把 ADB 冲突原因猜测提升为未经对照验证的根因结论。
