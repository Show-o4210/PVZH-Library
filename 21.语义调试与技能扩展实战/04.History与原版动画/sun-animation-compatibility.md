# 106延期扣阳光的可见反馈

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/sun-animation-compatibility.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

R17 [带渲染动作报告](../06.R19实现与验收记录/工程资料索引.md#ref-f943c76eabaa)在前6项检查后FAIL：202交换当前生命、87正常现身、106当场伤害和登记债务均完成动画；下回合扣阳光时，`GainSunRecordProcessor → VisualEffectEventAction.RetrieveFactoryAndCreateParticle` 抛出 `ViewMapException: CardView entity31`。31是已经Discard的106卡，模型中的来源卡仍存在，但其卡牌视图已正常删除。

[异常后的原生History及模型快照](../06.R19实现与验收记录/工程资料索引.md#ref-5072b7e91851)进一步区分了结算与显示：sequence78是植物玩家0的`SunCountIncrementedRecord`，原生回合递增1后总资源51；sequence80是`GainSunRecord`，SourceId=31、SourceGuid=106、TargetId=0、AttemptedAmountIncremented=-3、AmountIncremented=-3、AvailableSun=48。植物玩家模型同时为total=48、used=0、available=48。引擎已经正确扣除3，失败发生在消费该记录的粒子显示。

这一渲染fixture的StartingSun=50，正确期望是`50 + 原轮递增1 - 延期扣3 = 48`。此前测试中的0期望已修正；0下限应由另外的低资源场景验证，不能用本场景的错误期望否定真实结算。

## 原版分派与不能采用的替代

匹配B4实际dump与ARM64机器码确认：

| 方法 / RVA | 行为 |
| --- | --- |
| GainSunRecordProcessor.ProcessRecord / `0x1F41AB8` | 创建GainSunEventAction，然后创建所需事件动画，无来源负值分支。 |
| EventActionSequencedEffectAnimation.AddAnimationFromData / `0x1F18B40` | 首先无条件调用AddParticleEffectAnimation / `0x1F18C30`。 |
| VisualEffectEventAction.RetrieveFactoryAndCreateParticle / `0x1ED9570` | 在`0x1ED965C`读SourceId@0x30，直接请求GetViewObject<CardView>。 |
| EntityViewMapper.GetViewObject<T> / `0x2359C24` | 未映射到要求的视图类型就抛ViewMapException，没有SourceId=-1的特殊成功路径。 |
| GainSunEventAction.CreateCommonTargetReactionAnimation / `0x1EDA9CC` | 从TargetIds[0]取PlayerView；AmountIncremented<=0时调用正式LoseSun反应。 |
| SunCountSystem.IncrementSunCount / `0x21D10AC` | 原回合刷新创建独立SunCountIncrementedRecord，以玩家实体为Target，并非同一GainSunRecord粒子路径。 |

因此不能仅把延期效果Source改为-1，也不能拿英雄0充当CardView来源；这两者都不满足原版粒子检索要求。引擎效果、SourceId、modifier.GroupId和债务ledger继续保留原106来源。

## 窄显示兼容模块

[mod2-sun-animation.js](../06.R19实现与验收记录/工程资料索引.md#ref-d93510e94206)导出 `install(enhanced) -> {status(), dispose()}`。不修改主运行时、卡表或引擎结果。四个入口均校验metadata实际方法首指针及机器码：GainSunRecordProcessor、AnimationEventActionFactory.CreateCommand、GainSunEventAction.CreateCommonTargetReactionAnimation、EffectAnimationQueue.AddAnimation。

只对当前mod2真实记录中这类反馈生效：Source卡GUID106；目标有Player、Plants、SunCounter；AttemptedAmountIncremented=-3，实际AmountIncremented在[-3,0]，包括原生0下限情况。

当前视图归属由原生action.LocalCardChecker@0x28确定：其GameModel@0x10和EntityModel@0x18必须分别等于当前g.model/g.entities。随后再次确认记录实际在当前History.Records中。History优先通过现有binder.GetBinding/get_value读取已存实例；若singleton binding仍存Type，则在以上归属通过、且原生系统已经生成GainSunRecord之后正式解析一次，每generation缓存。安装/status不取对局或DI，native回调仅用cache-only live，不进行Unity全局对象扫描。

通过范围检查后，用原factory创建正式GainSunEventAction，直接调用其原版CreateCommonTargetReactionAnimation，并将正式玩家资源反应加入原动画队列。仅略过需要已删除来源CardView的粒子步骤。没有增加或伪造History记录，没有清空队列、强制标记完成或改变资源结算。

action与reaction分别以短期pinned GC handle保活；reaction成功入队后由原生队列拥有，finally逐个释放临时根。创建、归属检查或入队失败均释放已有根并继续原处理器；非目标来源、原版模式、AI模型、非当前History记录都继续原路径。

## 当前验证范围

语法与13项本地mock通过，包括实际扣3、0下限反馈、其他来源/金额、原版模式、不同视图模型、非当前History、binding及singleton按代复用、创建反应失败、入队失败和dispose。它们证明范围及临时所有权逻辑，不是native动画成功证据。

R17失败保留。此模块接入R18的`animation.sun_compatibility`后，[R18最终真实渲染动作报告](../06.R19实现与验收记录/工程资料索引.md#ref-9523bd8649ae) **8checks全PASS，unverified=[]**：202、87、106当场效果及下回合阳光反馈均自然结束，并完成一个完整回合。实际采到busy→empty；最终原Animations、FrontAnimations都0，没有强制清空或模拟点击。

R18仍保留同样的真实原生资源链：sequence78，植物玩家0的SunCountIncrementedRecord从基础50递增到51；sequence80，SourceId31 / SourceGuid106 / TargetId0的GainSunRecord attempted=-3、actual=-3、available=48。来源31确已在Discard，效果及来源没有改成-1或英雄。最终模型total=48、used=0、available=48，僵尸玩家资源51，动作pending_sun=0/errors=0。sun handler applied=1/errors=0/active_gc_roots=0，history_bindings=1/binding_value_hits=1，证明实际复用原有History实例且走了窄原生玩家反馈。

R18可见例验证实际扣3及自然显示结束；同回合叠加-6、下一轮恢复与0下限的逻辑证据仍来自 [R14动作套件](../06.R19实现与验收记录/工程资料索引.md#ref-99f2c9deb5d7)，本地mock另覆盖actual=0反馈。没有把R18这一个扣3可见例扩大成0下限、多债务可见表现或所有普通原版GainSun的完整回归。报告的`complete_visible_art_verified=false`仍保留，测试未截图，不能宣称逐帧美术验收。

实际安装Rev4后，[R19渲染复验](../06.R19实现与验收记录/工程资料索引.md#ref-ef2c38fd047f)8checks PASS、unverified=[]，同样真实busy→empty、原两队列0。延期GainSun仍Source31／GUID106／Target0、attempted=-3／actual=-3／available48，sun handler applied=1/errors=0/active_gc_roots=0，History binding实际复用1次。独立冷恢复后的 [R19动作逻辑7checks](../06.R19实现与验收记录/工程资料索引.md#ref-968e3f334f71)再次验证双债-6／次轮恢复／0下限；这些逻辑通过不是所有对应显示分支的完整美术矩阵。

Rev4的601承伤主套件与交互已独立真机通过，不能据此扩大本模块阳光反馈范围。R19无等待新局及自然2秒静态重开均有0x0 AV失败历史；仅测试增加自然等待／遇AV停止，运行时与本模块未因此更改。独立新冷进程起点／局间自然5秒的 [R19最终静态](../06.R19实现与验收记录/工程资料索引.md#ref-c20afe3dbf73)8case/37checks全PASS、全部unverified=[]。不把局内阳光显示成功或此次等待后通过当成温重开生命周期根治，详见 [生命周期复核](../05.实测与建局边界/fixture-lifecycle-review.md)。
