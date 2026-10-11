# 健壮／狡猾追加改版：阶段、墓碑和接收者定时效果

本章记录2026-10-11第三批20项需求。范围仍为用户给出的三份原版Bundle、卡牌JSON和中文CSV，使用现有UnityPy1.25.0。此前两批改动应继续保留，不能从已经修改过的Bundle反复累加组件。

## 本批入口和映射

工程实现位于工作区 `mod2/batch3.py`，由 `build_mod.py` 从核对哈希的原始输入依次构建各批。具体交付表、舍弃理由和验收记录位于 `mod2/第三批制作结果.md`、`mod2/舍弃名单.md`、`mod2/verification/`。这些是案例工程路径，不是本资料库运行依赖。

| 用户简称 | 原包GUID／名称 |
|---|---|
| 掰腕、老师、病毒 | 186掰腕僵尸、506僵尸学讲师、530病毒式传播 |
| 太阳神、咖啡、国王 | 196太阳神僵尸、209咖啡僵尸、199国王僵尸 |
| 剩饭、怪物狂欢、脑残粉、相扑 | 404、15、202英雄脑残粉、187相扑僵尸 |
| 火焰鸡、铲子、高台跳水、狗头 | 550、683铲子僵尸、547高台跳水僵尸、253狗头僵尸 |
| 冰冻雪人、臭臭、冰冻维京、焚面船长 | 545、239、686、328 |
| 掘墓人、陆行器、水兵小鬼 | 252糊涂掘墓人、257机器陆行船、344水兵僵尸 |

数字简写沿用费用／力量／生命。`112`是1费1/2，不是GUID112；狗头`413`是4费1/3，不是玉米狗GUID413。名称必须同时核对卡表的 `prefabName` 和原中文CSV，不能仅凭简称猜GUID。

## 植物打出、负资源与技能替换

- 掰腕186和火焰鸡550只监听植物单位在本路线打出。事件为 `PlayTrigger`，`TriggerTargetFilter`组合Plants、FighterQuery、InLaneQuery和InSameLaneQuery；目标SelfQuery，效果Damage1。不要保留原版的MoveTrigger，否则移动植物也会触发。
- 老师506使用TurnStartTrigger，目标Zombies+Player，GainSun Amount=-1、Duration=EndOfTurn、ActivationTime=Immediate。该字段名虽然是Sun，僵尸玩家上表示脑子。
- 太阳神196同一资源描述器改为SurprisePhaseStartTrigger，目标Plants+Player，Amount=-2。这里是当前回合锦囊阶段，不能照搬上一章的NextTurn延迟组合。
- 病毒530保留三段原版效果中的洗三张自身和抽一，首段Buff改-1/-1并删除GrantAbility Frenzy。剩饭404同样改为全体僵尸-1/-1。
- 改版触发技能使用重写EffectEntitiesDescriptor的方式；基础墓碑、两栖、致命、穿透等未明确移除的关键词保留。维京686原进化技能已不在新需求中，连同EvolutionRestriction和Evolvable一起移除，避免卡面与实际进化门槛不一致。

## 本次增益接收者的阶段自毁

用户明确确认咖啡209应消灭**本次获得增益的所有僵尸**，不能仅在咖啡本体上写Self Destroy，也不能在阶段开始直接重新查询全体僵尸：后者会误杀之后才登场、没有获得这次增益的单位。

采用原版GrantTriggeredAbilityEffectDescriptor，把隐藏的SurprisePhaseStartTrigger → Self Destroy能力授给这次PlayTrigger选中的每个僵尸。每个接收者持有独立的授予记录，咖啡本体离场不应成为这些接收者执行能力的条件。

该授予描述器在 `PvZCards.Engine.Effects` 命名空间，其他常用效果描述器通常在Components。请复制原版399／444的完整 `$type`，不要靠后缀拼错命名空间。

案例新增隐藏技能900000302，克隆原隐藏技能卡562。能力自身筛选采用 `InLaneQuery + IsAliveQuery`，不加WillTriggerEffectsQuery，以表达仍在场的接收者并避开手牌和死亡单位；这也为之后藏入墓碑的接收者保留配置路径。墓碑状态与授予技能的战斗交互没有实战验收，不能把这份配置检查写成战斗实测通过。

隐藏定义不可进普通卡组，设置usable=false、ignoreDeckLimit=true，更新内部Card.Guid。保持原模型资源，避免增加未知prefab。

## 高地互斥与改变位置后的属性

“触手play”15使用两组互斥目标：

1. 僵尸且Not(OnTerrain HighgroundTerrain)：Buff -3/-3。
2. 僵尸且OnTerrain HighgroundTerrain：Buff -6/-6。

按每个接收者所在路线判断。不要先全体-3/-3再高地-6/-6，否则高地叠加成-9/-9。也不要对锦囊自己检查地形，锦囊没有单位所在路线。

高台跳水547沿用原包的高地条件、水路有空位条件和手动水路选择。原版以BuffTrigger监听正增益后移动；直接把原Buff改为-2/-2会使2生命单位可能先死亡，无法保证完成移动。案例改为同一次现身效果先授予两栖，再MoveCardToLanes和Buff -2/-2，保留SecondaryTargetFilter。没有可用水路时沿用原版条件不执行。

## 墓碑现身监听的区分

原版铲子683、跳水547、雪人545等虽然卡面写“现身”，技能使用PlayTrigger；它们有PlaysFaceDown组件，按原版路径现身时执行。重写这些原卡优先沿用已确认的机制。

“登场一次，之后每次自身现身再执行一次”的糊涂掘墓人252需要区别处理：

- 登场沿用原版EnterBoardTrigger；现身另加RevealTrigger。
- 两者TriggerTargetFilter均SelfQuery，不能漏掉自身限制而在其他僵尸现身时洗全场墓碑。
- 沿用原版MixedUpGravediggerEffectDescriptor，它同时完成藏墓碑与随机交换；不要只对僵尸写TurnIntoGravestone而遗漏交换。
- 不把PlayTrigger和RevealTrigger同时作为自身现身效果，避免同一现身重复排队。

native只读核对：MixedUpGravediggerSystem.ProcessEffect在0x21AEB60，执行TurnAllZombiesIntoGravestones与ShuffleAllGravestones；RevealSystem.RevealCard在0x21D06B4，去除FaceDown并记录目标。本章不修改native。

## 弹射、自毁和召唤副本

- 铲子683：PrimaryQuery是本路线Environment或本路线Targetable僵尸，All选择，ReturnToHandFromPlay；包括自身。不是任意选一条有环境的路线，不再弹射植物。
- 臭臭239：PrimaryQuery是Self或相邻路线的植物／僵尸，包括两方；不额外弹射本路线其他单位。用户“相邻身上”按相邻线上处理。
- 相扑187：沿用[05章](05-smarty-card-remix.md)从原版491超新星巨尸、638女巫榛子核对的两条消灭来源路径；此前改版冬窝瓜134已组合这些路径，但原版134自身没有这两条击杀监听。DamageTrigger需来源Self、目标Plants+Fighter且已非存活；DestroyCardTrigger需来源Self、目标Plants+Fighter。两者效果Self Destroy。普通受伤不能误判为击杀。
- 国王199：TurnStart，僵尸Random1 Destroy；需求未说“其他”，范围包含国王自身。
- 陆行船257：8费1/6，保留两栖和穿透。All选择具有僵尸空位的路线，再CreateCard900000301。副本来自水兵344，改0费0/1并保留两栖。344原卡不改。自己的路线已占位，不能硬塞召唤物。

## 生命设值与无法精确覆盖的攻击条件

脑残粉202没有已确认的仅交换双方当前生命快照的原版描述器。CopyStatsEffectDescriptor同时复制力量和生命，不能按名字想当然当作换血。用户已明确授权备选，因此PlayTrigger直接对Zombies+Player应用SetStat Health=1，ModifyOperation=Set、StripNoncontinousModifiers=true。

native只读证据：SetStatSystem.ProcessEffect 0x21B8288调用StatUtils.ModifyStat；Health分支调用SpecialHealthHandling 0x21D3CD8，Set会清零已受伤记录。因此它不是只把最大生命改1并保留旧伤害。这仍属于静态实现证据，未替代实际战斗验收。

狗头253沿用原版DamageTrigger → 植物英雄、来源Self，改为Self Buff -3/-3；卡面如实写“对植物英雄造成伤害后”。原要求“攻击英雄后”包括未造成伤害的攻击，纯JSON没有通用攻击结束监听；该差异列入舍弃名单，身材与已确认伤害触发部分保留。

本批结果为18项实现、1项用户授权备选、1项部分实现。新增未实现内容两条，累计舍弃名单18条，没有整张新增需求放弃。

## 数据与启动验收

必须保留完整的类型值，例如OnTerrainQuery.TerrainType和OpenLaneQuery.PlayerFactionType：它们是带命名空间、EngineLib程序集信息的System.Type值，不是简称枚举。沿用第二批逐类型字段检查，本批针对257和547补充简称拒绝回归，并继续覆盖此前413和313错误。

归档上一版成品、脚本、JSON审查和启动证据，再创建不可覆盖的本次部署前设备备份。本次备份应与第二版成品SHA-256一致。第三批验证还要求：已有第二版卡定义完全一致，只修改新增20张目标卡和两条内部定义；成品重新UnityPy读取后必须等于构建内存数据。

最终三包共656条卡定义、93张原卡改变、5条内部定义、210条中文增量。cards和LocalizedStrings各只改一个TextAsset，其他对象原始字节不变；关卡包仍为原版。

用户的验收标准是进入正常游戏主界面。部署后核对设备哈希，启动、截取新截图并目视确认主界面，再次核对设备三包。保存本版截图及runtime.json、runtime-report.md；不能沿用旧版截图或用PID判成功。启动通过只证明本次加载成功，不证明每个战斗交互都通过实测。

本版已在雷电 `emulator-5554` 进入正常主界面，启动验收PASS。证据为工程中的 `verification/v3-main-menu.png` 与 `verification/runtime.json`；启动后设备三包哈希仍与第三版成品、部署记录一致。2026-10-11完成记录，游戏保持在主界面交由用户测试。
