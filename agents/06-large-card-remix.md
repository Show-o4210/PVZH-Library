# 06 · 多职业卡牌改写、能力复用与启动验收

2026-10-11，`mod2` 第二版；继续第一批七张卡，追加74项需求。原包哈希沿用入口README，UnityPy 1.25.0。此章保留第二版的历史统计；最新第三版见[07章](07-hearty-sneaky-remix.md)，总体状态见[09章](09-maintenance-and-evidence.md)。

## 先把需求落到 GUID

从CN的 `prefabName + _name` 建立卡表索引，再保存用户确认，避免昵称撞名。本轮重要映射：

| 需求称呼 | 确认或依据 | GUID |
|---|---|---|
| 冬青大帝 | 用户确认快乐的冬青 | 409 |
| 纸箱之神 | 用户确认纸板机器人僵尸 | 350 |
| 第二条“香蕉分身212” | 用户确认半支香蕉；第一条仍是香蕉分身 | 473；第一条472 |
| 叶绿素 | 用户描述“+1/+1，然后额外攻击一次”，CN完全对应植物养料 | 118 |
| 莓果轰击（传送） | 用户确认改莓果轰击 | 36 |
| 小吞 | 需求语义与墓碑克星相符；现身效果无法实现，本轮整卡保留 | 87 |
| 锤子 | 打僵尸／Smack-a-Zombie的卡面与功能 | 346 |
| 舞王、切片器、投巨小 | 迪斯科僵尸、奶酪切片器、投巨尸小鬼 | 224、546、521 |

本包职业内部值包括 `MegaGro`、`Hungry`、`Madcap`，不能按通用英文称呼猜枚举。数字为费用／力量／生命；生命0、攻击0都是用户需求，不擅自修成1。未指定身材和基础关键词沿用原版；清单给出的触发效果替换原触发效果。整项无实现路径时保留原卡，部分实现时说明去掉的效果和旧技能。

## 类型字段不能缩写成显示名称

本轮首个启动候选卡在开屏，日志为 `TypeNotFoundException: Plants`。原因是调查工具为了阅读方便，把所有 `PvZCards.Engine...` 字符串显示成了简称；这些简称不能写回原包。

不仅 `$type` 和HasComponentQuery.ComponentType要求完整串，**OpenLaneQuery.PlayerFactionType也是System.Type，不是阵营枚举**；OnTerrainQuery.TerrainType同样是类型字段。例如：

```json
{
  "$type": "PvZCards.Engine.Queries.OpenLaneQuery, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
  "$data": {
    "PlayerFactionType": "PvZCards.Engine.Components.Plants, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
    "IsForTeamupCard": false
  }
}
```

OnTerrainQuery的TerrainType使用 `PvZCards.Engine.Components.HighgroundTerrain, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null`。不能仅因为字段名带Type就认定是枚举。OriginEntityType="Self"、SelectionType="All"和GrantableAbilityType="Unhurtable"则是原版已有的枚举写法。

修复后按原包中每种描述器／字段的实际值识别类型字段，新增静态检查：这些字段必须保留引擎全名和程序集串。仅验证字段名和`$type`集合不足以发现该错误。失败截图和日志保存在工程 `verification/failed-short-type-strings/`，它们是失败证据，不能作启动通过证据。

## 组合原版描述器

- 409 PlayTrigger：目标是自身或相邻植物，不能只把原 Zombies 改 Plants 而忘记加 SelfQuery。
- 131 SlowedTrigger：两阵营 FighterQuery + InLaneQuery；效果目标Self、DestroyCard。活体SelfEntityFilter避免死亡后重复链。
- 黑眼豌豆／大嘴花：QueryEntityCondition的Finder=SameLaneQuery，ConditionEvaluationType=Any，Query=LaneWithMatchingFighterQuery(僵尸查询)。这是存在条件，不是把僵尸当最终伤害对象。
- 本线战斗前／后：沿用562的LaneCombatStart/EndTrigger和TriggerTargetFilter(SameLaneQuery)。回合开始是TurnStartTrigger；僵尸锦囊阶段开始是SurprisePhaseStartTrigger，三者不能混用。
- 伤害来源判定：切片器用DamageTrigger + TriggerSourceFilter(SelfQuery) + TriggerTargetFilter(植物Player)，再消灭Self；不能监听任意人打英雄。
- 计数：QueryMultiplier来自98、639，Divider=1；把倍率查询改为目标阵营。蘑菇头目本轮计数包含自身，番茄技工数僵尸。
- 进化：沿用605／600的EnterBoardTrigger + HasComponent(Evolved) + EvolutionRestriction；保留门槛，替换效果。不要把进化变为每次普通登场都会发动。
- 藏墓碑：复用258的TurnIntoGravestoneEffectDescriptor及僵尸Manual目标。保留目标阵营；这个效果不等于让墓碑现身。
- 固定变形：586的TransformIntoCardFromSubsetEffectDescriptor，SubsetQuery改为CardGuidQuery(350)。这里没有名为TransformIntoCardEffectDescriptor的原包类型。
- 红针花设值：复用411两个SetStatEffectDescriptor，分别Attack=7、Health=0，ModifyOperation=Set、StripNoncontinousModifiers=true。BehindSameLaneQuery用于“在后方打出”。
- 随机移动：原640的MoveCardToLanesEffectDescriptor搭配SecondaryTargetFilter(SelectionType=Random,NumTargets=1,OpenLaneQuery)。主目标选谁移动，次目标选目的地，不能倒置。
- 空位：召唤和移动遵守原版位置约束。普通植物与组队植物的OpenLaneQuery参数不同；相邻召唤在边缘、已有单位和水线条件下可能少于两张，不硬塞单位。

### 选择路线后作用于附近单位

沿用原包661的AdditionalTargetType=Query和OnlyApplyEffectsOnAdditionalTargets=true。主目标为Lane、SelectionType=Manual；AdditionalTargetQuery用InLaneSameAsLaneQuery或InLaneAdjacentToLaneQuery(Either)连接植物查询。太阳风暴只伤害附加单位目标，不能给Lane对象扣生命。

三倍体同样先Manual选择植物，附加目标用TargetCardGuidQuery + 植物单位 + Not(TargetQuery)，只对附加目标DestroyCard。这样被选中的原植物保留，消灭的是场上其他同GUID复制体；手牌、牌库复制不在该范围。

### 将定时自毁授予被施肥单位

复制562的隐藏能力卡骨架：prefabName=null、usable=false、非fighter、Card.Guid唯一；它的EffectEntitiesDescriptor改为SurprisePhaseStartTrigger → SelfQuery → DestroyCard，使用活体过滤。肥料对所选植物Buff(+4,+4)并授予这个能力。隐藏技能的名字与图标沿用615的Unique和ShowTriggeredIcon(13)，避免把新效果显示成双重打击。

**GrantTriggeredAbilityEffectDescriptor的命名空间是 `PvZCards.Engine.Effects`，不是Components。** 原包399、444已有完整串。字段是AbilityGuid、AbilityValueType="None"、AbilityValueAmount=0。肥料同一目标反复施放时，授予的定时自毁是同一能力，下一锦囊阶段消灭这个单位。

### 召唤专用副本

当“本牌召唤的单位”身材或技能区别于全局原卡，可以克隆原卡定义，分配唯一GUID、同步Card.Guid，复用prefabName美术，usable=false、ignoreDeckLimit=true，避免新增收藏卡或污染普通原卡。原GUID保持原来的用途。

本轮双人菇召唤1费0/1小喷菇，原小喷菇是0费0/1；召唤直升机使用同模型同身材、EnterBoardTrigger自毁的副本，原直升机176保持不变。新增隐藏技能／副本应记录来源和引用关系，并校验GUID没有冲突。

### 伤害重定向

原94美须藤、529行星护卫的能力实体含DamageEffectRedirector、DamageEffectRedirectorDescriptor、活体SelfEntityFilter、TriggerTargetFilter和PrimaryTargetFilter，没有普通DamageEffectDescriptor。

TriggerTargetFilter过滤原伤害承受者；可追加TriggerSourceFilter限定伤害来源；PrimaryTargetFilter选择替代承受者。双人菇过滤原伤害来源Self，承受者为本线召唤专用小喷菇GUID；原目标还必须不是该小喷菇GUID。重定向后再次成为伤害的同一笔数据已指向小喷菇，排除条件让它停止再次转移。实际战斗中的护甲、致命、多个重定向并存等交互未实测，不由启动验收推断。

伞叶原文字面让原目标和替代目标都包含Self，而原版重定向会重新生成伤害。本轮没有确认能安全排除相同自指伤害反复转移的条件；只转给相邻其他植物又不符合原文。因此最终没有写入伞叶改动，保留原卡并记录舍弃；不要把此前调查阶段的候选方案当成已交付效果。

反射坚果是DamageTrigger(Self)再Damage(Self,1)。后续自身伤害也满足监听条件，会继续触发直到死亡；活体过滤停止死后循环。不要擅自排除自身伤害来源以改变用户字面需求。

## 不能把存在的字段当成可靠路径

- 原版没有已确认的可配置普通攻击禁止开关。“力量为0”可以再加攻，也会受到攻击属性覆盖，不等于无法攻击。忧郁菇、山胡桃石、大喷菇、读报等只实现其余部分；无脑坚果、绿叶贤者、迪斯科舞池整卡保留原版。
- RevealTrigger是监听器。native有RevealEffect并不意味着JSON能配置RevealEffectDescriptor；原包没有后者。本轮墓碑立即现身略过，不引入引擎补丁。
- MultiplyDamage=1是倍率1，不会将所有伤害固定成1。本轮双子星整项略过。
- 火炬树桩的“前方植物攻击时反伤该植物”需要通用攻击开始时机及本次攻击量，不能用普通DamageTrigger冒充。
- 指定外部音效需要提供素材及可替换入口。缺少耄耋哈气片段时记录略过，不把其他猫声冒充要求的素材。

### 延迟一回合的资源修正陷阱

GainSunEffectDescriptor有Amount、Duration、ActivationTime。原175是EndOfTurn + Immediate，原496是Permanent + NextTurn。冰脑本轮沿用“从下回合开始+1”的原版持续增费。

太阳风暴要求的下回合单次减3无法直接用EndOfTurn + NextTurn：本机对应版本只读反汇编确认ExpiredIntModifierMatcher.Matches仅按Duration==EndOfTurn判断清除，不检查ActivationTime，因此在本回合末就可能清掉未激活修正。Permanent + NextTurn则会持续扣费。

给玩家授予TurnStart + OncePerGame隐藏能力也不能可靠实现可反复施放：GrantTriggeredAbilitySystem只有AbilityCounter.IsFirstTimeGranted为真时创建能力实体；重复同GUID不会为下一次施放创建独立单次实例。因此此项在最终成品中省去并进入舍弃名单。

上述native读取来自本机 `D:\Codex\PVZH\dump` 的v1.67.8 dump/script/libil2cpp，仅用于核对字段、类型和失败方案；没有修改native，也不把RVA当跨版本接口。以后换输入须重新验证，不能照抄地址。

## 构建、文档与验收

先将上一版的输出、构建脚本、报告、备份、截图归档到版本目录，再编辑当前工程。当前构建从干净输入先应用第一批、校验，再应用第二批，防止漏掉已完成需求。

静态验证：仅指定原卡改变；新增GUID唯一；Card.Guid与字典键一致；身材组件和显示字段一致；所有描述器类型来自原包；按每种类型的$data校验字段集合、类型字段保持完整类型串；CreateCard和GrantTriggeredAbility引用可解析。CN按CSV逻辑记录增量修改，保留未触及的原始物理行；覆盖长短说明、改名和flavorText，检查Key唯一且其他记录不变。

UnityPy写出后重新加载TextAsset，按序列化文件名与path_id比较所有原始对象字节；只允许cards、LocalizedStrings各一个对象变化。关卡包原样复制，记录三份输入／输出SHA-256。交付状态表和舍弃名单从构建报告生成，避免统计或卡面描述与结果漂移。

部署前再创建**版本化设备备份**，原有设备备份不能覆盖。指定ADB serial，三包pull后本地和设备哈希一致；force-stop游戏后push三包，再核对设备哈希。`restore`明确选择要恢复的备份版本，不清理存档或重装APK。

用户的验收仍是顺利进入游戏。必须看到大厅／主界面截图；开屏、黑屏、PID、启动命令成功都不算通过。文档分别记录静态通过、部署哈希、启动截图，不能把它们写成战斗技能实测。

2026-10-11第二版最终构建已进入正常游戏主界面，**启动验收通过**。该版本卡表654条，73张原卡发生数据变化、3条内部新增定义，167条中文记录更新；第二批状态为59项实现、7项部分实现、2项原版已符合、6项整卡保留原版。启动后设备三包哈希再次与第二版成品一致。完整历史证据归档在交付工程 `mod2/releases/v2-startup-confirmed/verification/`，包含v2-main-menu.png、runtime.json及runtime-report.md；战斗技能未逐项实测。
