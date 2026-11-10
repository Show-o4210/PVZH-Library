# 从已有时机连接原版动作

## 四卡修订给出的边界

三头花生的原版SetStat支持将力量设成指定值，因此重力树419缺少的是“任意单位攻击后”的连接，不是设值能力。1015复用攻击结束书签，向真实攻击者发送原版SetStatEffect：Attack、Value=0、Set、StripNoncontinuousModifiers=true。持续光环保留；以后仍能再次获得力量，下次攻击后再设0。

急救萝卜130需要一次选取后回手，再把同一个实体设成0/0。原版ReturnToHandFromPlay保留实体ID，但重置卡牌。故1016按顺序入队Return、SetAttack、SetHealth。不能放两个同类型SetStat描述器进同一实体；改成两个Manual实体又会要求两个独立目标。应由一次原版选取把同一目标交给组合动作。

墓碑之误633的1018先回手，再对该卡造成2伤害。直接并列FaceDown筛选下的Return与Damage，后一个会因目标已经没有FaceDown而失效。连接层继承一次有效墓碑选取的目标，后续用原版Damage执行，不继续套用已经过期的墓碑筛选。抽牌和英雄自伤仍走原有Play实体。

放大草161最终采用“本回合阳光数”的用户确认方案。SunGainedMultiplier能放大AttackInLane，却不意味着也放大GainSun。实测直接组合只扣1。1017读取SunCounter当前总值与AmountUsed，耗尽可用阳光；伤害倍率继续走原版。不能把“本回合总阳光”和“打出后剩余阳光”混称为同一数值。

## 新增五项的契约

| 规则 | 配置位置 | 接入结果 |
|---|---|---|
| 1019 | 137卡体marker | 一次实际攻击结束后，对自己入队DestroyCardEffect |
| 1020 | 490卡体marker | 从原版可成为目标的在场单位选择一个，原版Destroy；包含自身 |
| 1021 | 631卡体marker及CreateCardFromSubset描述器 | 按缓存中的植物池原版召唤，完成后挑其他可用路线移动 |
| 1022 | 194现身PlayTrigger的动作marker | 保存当前实例的本回合禁攻状态，到原版回合边界清除 |
| 1023 | 491原版击杀触发器的动作marker | 保留被击杀卡GUID，先取一次二选一，再执行选中的消灭分支 |

这些数字不是原版Grant枚举。1019～1021只读取卡体标记；1022～1023由已有Grant处理入口截获，不能进入原版未知枚举和图标分派。

## 攻击结束、顺序与所有权

继续沿用R19攻击列表中的前后书签；多线、穿透等攻击的每个伤害包不是一次独立“攻击后”。没有开始或被取消的攻击不产生后续技能。来源须仍为同一实体、GUID和在场实例，不把迟到动作施加给复用编号的新单位。

631的SubsetQuery留在card_data中，运行时深复制给新建CreateCardFromSubsetEffect。原卡的查询树不能直接借给会返池的Effect，否则Effect返池时可能归还仍属于卡牌的查询。新树在交给原生Effect前持有临时GC根，挂入后交由Effect管理。

召唤使用植物玩家身份、攻击结束时的原路线；移动书签排在召唤之后，再复用原版OpenLaneQuery及Effect.ToEntityQueryContext验证空位。MoveCardToLanesSystem由效果路由器持有，没有直接DI绑定；R24试图GetInstance取得该系统时发生可恢复的接口错误，不能仅凭类存在就假定可Resolve。修订参照其LaneIsOpenForCard内部查询流程，真正移动仍交给原版系统执行。不能为了保证成功把随机植物塞进已满路线，也不能先移动再用新路线召唤。无召唤位置仍可尝试移动；无移动位置留在原处。

随机选择使用当前游戏TriggeredEffectTargetChooser持有的MtRandom.Next(Int32)，不引入JavaScript独立随机源。490对单位集合一次选择，不先按阵营各取一半。491先等概率选择两个效果分支；若选随机僵尸，再在僵尸集合中抽取。选中空分支不改选另一个分支。

## 临时状态与击杀上下文

194不能使用永久1001标记冒充本回合。状态按指针／实体ID／GUID身份保存，回手与卡牌Reset清理，效果队列重置、换局也清理；在已有SunCount回合结束边界到期。禁攻检测仍阻止额外攻击，不只是把力量设0。

491复用原版DamageTrigger的KilledBy以及独立DestroyCardTrigger过滤，保留原版防止自己消灭复制后递归触发的条件，并额外限定被击杀者是植物。原版Destroy路径的目标过滤并非天然只含植物，不能盲目照抄。复制指场上同GUID植物，排除原被击杀实例，不包含手牌和牌库。

所有新结果均使用原版Effect、队列、StateCheck和History。并未新增原生hook地址。AI独立预测模型与专属special动画并不因这些逻辑连接自动完成，须分别验证。
