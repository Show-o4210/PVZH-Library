# 一次性扩展动作

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/action-rules.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

实现为 `src/mod2-skills.js`，只在 gate 的已校验 receipt 为 mod2 时启用。原版0–18 Grant 值原样调用原系统；100x 不进入原版枚举或图标映射。动作失败写入 `mod2-action-error`，`mod2_status` 返回错误计数，不能把“接口返回成功”误认为技能成功。

## 87 墓碑现身

使用卡表原版墓碑目标选择，将对应描述器替换为1013。运行时排入 pooled RevealEffect，保留原版现身记录、现身技能和触发流程。目标已非墓碑时跳过并记录原因。

## 202 交换当前生命

1014捕获来源卡与所选僵尸英雄的当前生命，再分别使用原版 SetStatEffect(Health,Set)。原版 SpecialHealthHandling 在Set时清零CurrentDamage，因此Value不能加旧伤害。Value取“对方当前生命－本方当前生命修饰总量”，StripNoncontinuousModifiers=false保留修饰器。两个Set完成后统一StateCheck，不在中间判定死亡。后续连续光环变化仍按原版计算。

## 106 下回合阳光减少3

每次1012施放登记一笔独立债务，来源死亡不撤回债务。同一个原生游戏模型的下一次SunCountSystem.ProcessEffect(TurnEnd)完成时，原版资源已刷新，债务转为原版GainSunEffect(-3,Immediate,EndOfTurn)。ResponseEffects先于已有TurnStart处理，下一次刷新清除临时负修饰。独立施放可叠加，资源不足按原版floor0截断。

切换游戏模型/调试generation时清空未结算债务，避免新局继承。原版模式不登记或消费改版债务。原生路径证据详见 `actions-native-semantics.md`，实际结果以 `evidence/` 为准。

Modifier GroupId 使用数字来源实体 ID，以兼容原版 Int32.Parse 的 strip 路径。不同债务以独立序号记录，原版 IntModifier.AddModifier 无按GroupId去重，所以相同来源仍逐笔叠加。

实机发现重用PlayTrigger实体包装手动换血会让原版效果验证拒绝结果：它要求原触发Target和目标筛选，而交换需要两个不同目标。因此初版不额外生成Special bookends。合法出牌动作仍处于原版PlayTrigger的真实Start/End之间；其它结果使用原版通用记录。可选History观察器初始化失败只关闭观察，不阻止调试和技能。

## 真机逻辑、触发链与可见模式验收

[R14动作套件](../06.R19实现与验收记录/工程资料索引.md#ref-99f2c9deb5d7)7项通过，覆盖合法87、106双债叠加／次轮恢复／资源0下限、合法202手牌增益与受伤双方交换。它们证明相应状态和结算，不单独证明画面。

[R15合法87揭252](../06.R19实现与验收记录/工程资料索引.md#ref-e7cb45147bbe)为3checks PASS，实际路径不是r16-grave-legal87。进入场上重藏一次、87揭其他僵尸不触发252、87揭252自身后重藏恰一次均验证。后续 [R16同响应组快照](../06.R19实现与验收记录/工程资料索引.md#ref-638768656c7f)记录直接fixture现身的时机修正：揭别人时MixedUp calls/completed仍3，揭自己后立即变4且三株均FaceDown，推进下一原生阶段仍4，没有重复。

[R16继承静态完整套件](../06.R19实现与验收记录/工程资料索引.md#ref-cafe9d491e00)8case/37checks全PASS，包含上述合法grave分支、咖啡墓碑接收者、97转伤和547移动／减益／自然Discard等；不代表全部99张卡已测。

87原special曾卡在未结束的timeline，详见 [R16关闭冷对照](../06.R19实现与验收记录/工程资料索引.md#ref-9f607301bb64)和 [开启冷对照5项PASS](../06.R19实现与验收记录/工程资料索引.md#ref-b13ca6941d6b)。窄 [87兼容模块](../04.History与原版动画/reveal-animation-compatibility.md)保留真实Start/Reveal/End，让独立原Reveal消费者完成结果；默认额外bookends仍禁用。

最终 [R18真实渲染动作](../06.R19实现与验收记录/工程资料索引.md#ref-9523bd8649ae) **8checks全PASS，unverified=[]**：普通双方单位合法出牌、202交换、87现身、106当场伤害／登记债务、下回合阳光反馈及完整回合推进。实际队列采到busy→empty，最终原Animations、FrontAnimations都0；无模拟点击、截图或强制清队列。

同一报告实际History包含：202 source26 / effect27 / group60的Start→SetStat(26,80)→SetStat(5,1)→End；87 source29 / effect30 / group79的Start→Reveal(25)→End；106 source31的group0伤害Start→Damage5→End及group1登记债务Start→End。下回合阳光是独立GainSunRecord，不在上回合已结束的bookends中：原SunCountIncrementedRecord将植物总资源递增到51，随后Source31、Target0的GainSun attempted=-3、actual=-3、available=48；来源卡仍为106且已Discard。

R17曾因已退场来源的CardView粒子查找异常导致报告整体FAIL；R18使用 [窄原生PlayerView.LoseSun反馈](../04.History与原版动画/sun-animation-compatibility.md)，保持原效果与记录，handler applied=1/errors=0/active_gc_roots=0。动作errors=0、pending_sun=0、临时effect roots=0。此可见模式测试关闭opponent_ai，`complete_visible_art_verified=false`仍保留：证明真实队列自然完成，不声称逐帧美术或所有AI／复杂组合通过。

## R19安装Rev4后的复验

[R19真实渲染动作](../06.R19实现与验收记录/工程资料索引.md#ref-ef2c38fd047f)8checks PASS、unverified=[]，202／87／106及延期阳光／完整回合再通过，真实busy→empty、原两队列0，87与sun handler各applied1/errors0/roots0。它证明Rev4安装后的可见例，不替代受伤／叠加／0下限等独立逻辑断言。

stats后立即无等待重开reveal发生0x0 AV，主代理停止子进程并强停游戏，原 [中断报告](../06.R19实现与验收记录/工程资料索引.md#ref-58cc13c6ce6d)及 [日志](../06.R19实现与验收记录/工程资料索引.md#ref-be0f894a25d8)保留。测试仅添加自然2秒过渡等待、遇native AV立即停止且不做新的诊断游戏调用，运行时／APK未因此更改。冷恢复后的 [R19动作逻辑](../06.R19实现与验收记录/工程资料索引.md#ref-968e3f334f71)7checks全PASS：87合法现身、106双债／下回合-6／次轮恢复／0下限、202合法受伤英雄与手牌增益、1014双方受伤保留生命buff均复验。

这次动作复测并非每局冷起，报告fixture_reset_uses_cold_start=false。随后相同自然2秒的 [R19旧静态](../06.R19实现与验收记录/工程资料索引.md#ref-0602f9dd6fe6)又在banana第三branch新局AV停止。独立新冷进程起点、fixture_delay_seconds=5的 [R19最终静态](../06.R19实现与验收记录/工程资料索引.md#ref-c20afe3dbf73)8case/37checks全部PASS、全部unverified=[]；严格销毁屏障及held旧代释放仍未实现，不能宣称两秒或五秒根治了温重开。具体边界见 [生命周期复核](../05.实测与建局边界/fixture-lifecycle-review.md)。

Rev4新增601由 [承伤9case/17checks](../06.R19实现与验收记录/工程资料索引.md#ref-f4dc6c721c73)与 [交互2case/6checks](../06.R19实现与验收记录/工程资料索引.md#ref-ab90c34fdc90)实际通过，共321笔Damage请求；此被动不额外制造Special bookends。沉默／目标依赖倍率及全部AI组合未全面验证，与一次性动作证明范围分别记录。
