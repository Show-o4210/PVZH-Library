# 墓碑克星动画兼容回退

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/reveal-animation-compatibility.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

`src/mod2-reveal-animation.js` 提供仅针对改版87的窄回退。R16同APK冷启动对照已确认：关闭回退FAIL，开启回退的可见局5项PASS。R17将默认值改为开启，R18最终动作可见局8项全PASS，包含87真实现身、自然队列结束及完整回合。没有修改缓存card_data、引擎技能结果或实际History记录；仍不能把此范围的通过扩展为全部卡牌画面完整验收。

## 实测问题与静态边界

R14 的 `evidence/r14-render-before-static-fixes/result.json` 显示，合法 87 打出后，墓碑目标已移除 FaceDown，生命和路线保留。原版真实记录完整：

`Start(source 27 / effect 28 / group 69) → Reveal(target 25) → End(group 69) → Discard(27) → PhaseResume`。

但是可见模式的 EffectAnimationQueue 超时且一分钟后仍不为空；同一局普通单位出牌动画此前能够结束。R14 记录链本身只能证明逻辑与 History 已完成；R16 随后的只读容器快照已定位实际等待位置。

## R16 关闭回退的冷启动对照

[R16 disabled-cold 报告](../06.R19实现与验收记录/工程资料索引.md#ref-9f607301bb64)再次复现合法87后动画队列15秒超时。其 `final_animation_snapshot` 通过只读字段快照取得：

| 当前动画字段 / 容器 | 实际值 |
| --- | --- |
| 队首类型 | TriggeredAbilityEffectAnimation |
| SourceCardId / AbilityGroupId | 27（GUID87） / 0 |
| IsStarted / IsCancelled | true / false |
| IsCardTimelineComplete | false |
| WaitForLoad | false |
| 两个 EventCommands | 均为 NullEventAction，HasBeenActivated=true |
| ChildAnimations | 0 |
| 内部 AnimationQueue | Animations=0，FrontAnimations=0 |
| TimelinePlayer.Card | 非null，CardViewComponent |

因此本次等待实际在87的原专属 timeline 未结束；没有未完成的子Reveal动画，也不是等待卡牌加载。原有卡视图已经存在，两个空动作也已激活。为什么原素材的结束事件未到达仍未逐层核完整Animator资源，但不影响对当前队列卡点的定位。

快照没有调用 native IsCompleted，没有 hook、修改字段或清空队列；`proves_visual_animation=false` 仍明确表示它不是截屏 / 完整视觉验收。

与当前 B4 对应的 native 静态证据：

| 方法 / RVA | 已确认行为 |
| --- | --- |
| `AnimationEventActionFactory.CreateCommand` / `0x1EDC0AC` | 原版结果分派没有 RevealRecord；其默认路径 `0x1EDC850` 进入 `CreateNullEventAction` / `0x1EDD748`。 |
| `TriggeredAbilityStartRecordProcessor.ProcessRecord` / `0x1FC9B0C` | 取 SourceId、EffectGroupId，以 `HistoryProcessorModel.CurrentPositionInHistory + 1` 查询整组，再处理整组。 |
| `AbilityRecordGroupFinder.FindAbilityRecords` / `0x1ED301C` | 创建新的 List<Record>，读取真实 History.Records，收集组内记录。没有调用 MarkRecordAsProcessed，也没有访问 HistoryProcessorModel。 |
| `TriggeredAbilityStartRecordProcessor.ProcessRecordGroup` / `0x1FC9B90` | 先将相关记录全部标记 processed，再创建 ability animation。Reveal 因而不能再单独进入正常 RevealRecordProcessor。 |
| `HistoryProcessor.ProcessRecord` / `0x1F6D798` | 调用具体执行器后，自行把当前记录标记 processed。 |
| `HistoryProcessorModel.MarkRecordAsProcessed(Record)` / `0x1F6D850` | 正式的原版 processed 集合入口。 |
| `RevealRecordProcessor.ProcessRecord` / `0x1FB7380` | 创建正常 RevealAllCardsAnimation，加入被揭示目标及相关 Reveal 记录。 |

TimelineCommandEffectAnimation 的完成条件为 `IsCardTimelineComplete@0x70 && CommandContainer.IsComplete()`。其 CommandContainer@0x28 内有 EventCommands@0x10、ChildAnimations@0x18、AnimationQueue@0x20。独立只读快照可区分这些等待原因，不需要截屏或强制清空队列。

## 有边界的回退

接口：`install(enhanced) -> {configure({enabled}), status(), dispose()}`。安装验证Start processor、group finder、processed入口三者的metadata首指针与真实RVA，同时验证入口八字节。R16初版默认false，使用显式开关作对照；R17源码默认true。显式关闭时完全调用原处理器，不查询group或当前对局。原版profile即使开关开启也继续原版处理。

启用后，只有同时满足以下条件才走回退：

- 资源模式为 mod2，并已有当前对局缓存；不执行 Unity 全局扫描。
- StartProcessor 注入的 `EntityModel@0x38` 等于当前 `g.entities`。
- 当前 Start 的真实来源卡为 GUID 87、AbilityGroupId=0，当前 History 索引确实指向这个 Start。
- 原版 Finder 返回严格两条记录：RevealRecord、TriggeredAbilityEndRecord；End 的 SourceId、EffectEntityId、EffectGroupId 均与 Start 一致，Reveal 目标仍存在。

随后只通过原版 `MarkRecordAsProcessed(Record)` 标记真实 End，跳过旧 87 ability animation 的创建。外层 HistoryProcessor 仍自动标记当前真实 Start。真实 Reveal 仍未 processed，因此由正常 RevealRecordProcessor 处理；后续 Discard 和 PhaseResume 不变。

不添加、伪造或删除 Start/Reveal/End，不把其他记录划入新 group，不改变普通 Reveal，也不调用 CancelAllRunningAnimations。任一范围条件不符或发生异常，继续调用原版 Start processor。这意味着边界条件之外仍可能表现原卡动画卡住，状态中的 shape_rejected、foreign_models_skipped、errors 会说明原因。

原版 Finder 返回的临时 List<Record> 在后续 native invoke 期间使用局部 pinned GC handle，并在 finally 中释放；processed 集合只通过原版方法修改，不直接写 C# 引用字段。

## 验证范围

初版本地语法检查及10项mock回归通过。适配R17默认值后保留原测试范围、补上显式关闭负对照，共11项：默认开启、显式关闭、严格87组、其他来源、默认开启仍不改变原版模式、不同EntityModel、组内额外记录、End不匹配、native标记异常、缓存缺失、dispose。mock验证只标记End、不标记Reveal、GC根释放。

本地mock只是接口及范围验证。另有R16真实设备对照，证据如下：

| 同一个R16 APK，分别冷启动 | 设备结果 |
| --- | --- |
| [回退关闭](../06.R19实现与验收记录/工程资料索引.md#ref-9f607301bb64) | FAIL，普通单位动画此前结束；合法87后旧special timeline仍未完成，精确快照见上文。 |
| [回退开启](../06.R19实现与验收记录/工程资料索引.md#ref-b13ca6941d6b) | **5项全部PASS，unverified=[]**：可见局启动、普通僵尸出牌、普通植物出牌、合法87揭现并队列自然清空、完整回合推进并队列自然清空。 |

开启组实际采到动画队列busy→empty，末尾原始Animations和FrontAnimations均0；没有强制清空、标记timeline完成或模拟点击。真实History仍保留同source/effect/group的Start→Reveal→End。handler状态为 `applied=1, errors=0, shape_rejected=0, active_gc_roots=0`，且后续回合正常结束。这证明本例确实走了窄回退并完成原版结果消费，而非headless或将队列禁用。

R17据此默认开启。随后 [R18最终真实渲染动作报告](../06.R19实现与验收记录/工程资料索引.md#ref-9523bd8649ae)8checks全PASS、unverified=[]，重新通过普通单位、202、87、106及下回合资源反馈／完整回合。87来源29、effect30、group79的真实Start(sequence42)→Reveal目标25(sequence43)→End(sequence44)保留；handler applied=1/errors=0/shape_rejected=0/active_gc_roots=0，最终原队列两表都0，实际采到busy→empty。因此新APK的默认开启路径已复验，不只引用旧R16开关结果。

测试没有截图，`complete_visible_art_verified=false`与快照`proves_visual_animation=false`仍保留：已验证真实可见模式的正常结束，不声称逐帧美术表现完整。R17延期阳光显示失败报告也保留在 [原始证据](../06.R19实现与验收记录/工程资料索引.md#ref-f943c76eabaa)，R18通过使用独立阳光反馈兼容；它不是87又改变了引擎结果。

R19实际安装Rev4后，[渲染动作复验](../06.R19实现与验收记录/工程资料索引.md#ref-ef2c38fd047f)8checks PASS、unverified=[]，87真实现身及队列自然结束再通过；reveal handler applied=1/errors=0/shape_rejected=0/active_gc_roots=0，最终原两队列0。新增601的两套承伤／交互实际通过，属于独立被动验收，不扩大本页87可见表现范围。

[R19无等待新局中断报告](../06.R19实现与验收记录/工程资料索引.md#ref-58cc13c6ce6d)保留：stats后重开reveal局在start_test发生0x0 AV，尚未执行87出牌，因此不能拿它否定已有局内87可见成功，也不能隐藏生命周期问题。自然2秒、冷恢复后的 [动作逻辑7checks](../06.R19实现与验收记录/工程资料索引.md#ref-968e3f334f71)通过，但随后同样2秒的 [旧静态](../06.R19实现与验收记录/工程资料索引.md#ref-0602f9dd6fe6)banana新局又AV停止。独立新冷进程起点／局间自然5秒的 [最终静态](../06.R19实现与验收记录/工程资料索引.md#ref-c20afe3dbf73)8case/37checks全PASS、全部unverified=[]，含合法87与252交互。等待仅缓解；严格销毁屏障／旧长期根释放尚未实现，详见 [生命周期复核](../05.实测与建局边界/fixture-lifecycle-review.md)。
