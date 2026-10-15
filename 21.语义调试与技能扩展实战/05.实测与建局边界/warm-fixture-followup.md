# R19 连续温建局的只读补核

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/warm-fixture-followup.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

本轮只读 runtime.startTest / appReady / resolve / live 缓存和匹配 1.67.8 ARM64 ELF，不改源码、APK、ADB，也不改另一个代理维护的 fixture-lifecycle-review.md。结论是**现有证据不能确定访问 0x0 的具体根因**；能确定的范围是建局入口及其原版子调用，而非某一张牌的技能实现。

## 实际失败与通过范围

R19 的攻击 14 case、属性 8 case、伞叶 321 笔（含五笔零伤）已经由主代理实机通过。紧接属性套件、无等待启动动作 fixture 时，在 EnterCheatGame 阶段出现 access violation 0x0；冷恢复并增加自然两秒等待后，七条动作断言通过。

[R19 static 命令尾部](../06.R19实现与验收记录/工程资料索引.md#ref-35c1bd65f430) 又记录另一份独立失败：前五个静态 case 和香蕉前两个分支已完成；香蕉第三次 fresh 之前仍为 generation15、temporary_effect_roots=0，实际自然等待 2.0001395 秒。start 请求约 0.0982 秒后报 access violation 0x0，测试停止。[中断结果](../06.R19实现与验收记录/工程资料索引.md#ref-0602f9dd6fe6) 必须保留为失败，不能被冷起后单项通过覆盖。

因此，两秒延迟没有证明温建局生命周期已经修复。主代理正在冷起后单跑 static、自然延迟五秒，当前仅报告前五个 case 和香蕉首分支通过，其余结果尚待；本文件不提前给该整套写 PASS。

## 能确定的 Context 选择

startTest 的入口是 `appContext()`，调用原版 `AutomationGameObjectUtils.GetAppContext`（RVA 0x1E21ADC）。实际机器码路径为：

1. `GameObject.Find("ApplicationRoot")`，字符串 RVA 0x3AFECA8。
2. `GetComponent<AppRoot>()`，按 Unity Object 非空语义检查。
3. 读取 AppRoot 的 context 字段 +0x20，并检查其类型为 AppContext。

这不是 runtime.live() 的 PvE GameContext 选择，也没有直接读取 extensionGame 缓存。startTest 后续 `resolve(context,name)` 使用这个 AppContext 的 injectionBinder.GetInstance。因而现有 EnterCheatGame 失败不能直接归因为“extensionLive 选了旧局”；旧局缓存与长期根仍有生命周期问题，但不是这条入口所读的 context。

runtime.live() 只在缓存 generation 与捕获 GameModel 一致时返回缓存，否则经唯一 LocalPveGameContext 查找及绑定解析；extensionLive() 本身仅返回已有缓存，缺失时抛错。新的 initializer onEnter 才使 generation 递增、旧缓存失效并捕获新模型。这个身份隔离保护局内技能访问，不提供 startTest 的旧屏幕/Context 完整移除屏障。

## appReady 的缺口与进入链

appReady 保证启动已满 120 秒、AppContext 非空、列出的 binding 存在且 binding.value 非空。它没有检查每个 value 是已经注入完成的实例还是 RuntimeType，也没有检查 ScreenTransitionQueue.IsTransitionActive、旧 GameRoot/Context 已移除、是否已有一次 start 正在进行。非空 binding 不能证明过渡完成。

startTest 会在旧局真正移除之前改 headless/manualBoth，重写两个固定 agent_test 牌组、节点与共享 GameConfig，并新建/手工设置进入所需对象。gate 的许多依赖直接 resolve AppContext singleton，没有逐字段实际类型/实例状态日志。新 gate 的节点服务、playerSetter、opponentInitializer 则由本次函数新建，不是直接拿旧 GameContext。

EnterCheatGame 是一个短原生跳转，不能把报错阶段当作唯一故障函数：

| 位置 | 原版实际调用 |
|---|---|
| 0x1F56DA4 | 设置 PveMode=Cheat(5)，跳入 EnterGameForPvENode |
| 0x1F56D64 | MatchType.SetToPveMatch → SetupGameConfigForNode → EnterGame |
| 0x1F56DE0 | 写 GameConfig.ProgressionNode；从 IdentityProvider 取身份；转换 AI 策略；NodeDataService.GetNode；调用本次 playerSetter |
| 0x1F56F74 | 调 OpponentSelectionDataInitializer.InitializeOpponentData（0x1F9A218）；调用 QuestProvider 接口 slot2 HaltScheduledResync；派发 ShowGameSignal |
| 0x30731F4 | Signal.Dispatch，后续进入原版显示、加载、替换屏幕流程 |

setup/enter 中有多个原生虚调用和接口派发。因此字符串“EnterCheatGame: access violation 0x0”没有给出究竟是设置对手、QuestProvider、ShowGameSignal 的处理器还是后续 Unity 屏幕加载访问了失效对象/空指针。当前日志没有具体 PC/backtrace 或上述子阶段进入/返回对照，不能定因。

## 最小下一轮方向

优先加入独立只读阶段观察，而不改卡牌技能：记录本次 gate、AppContext/binder，以及 gate+0x10/+0x18/+0x20/+0x28/+0x38/+0x40/+0x48/+0x50 的指针和真实类型；逐个标记 SetupGameConfigForNode、InitializeOpponentData、HaltScheduledResync、ShowGameSignal/ShowGameCommand 的进入与返回。使用当前现成对象的原生 className/raw 字段，不在 listener 中全局 Resources 扫描或重新实例化依赖。若能获得实际故障 PC，再与这条原生链匹配。

与此同时观察 ScreenTransitionQueue 活跃状态、旧 GameRemoved/Context.OnRemove、新 initializer 完成和新模型可用，以证明是否发生重叠过渡。后续实施应采用跨帧 start 状态机，拒绝并发启动或在已观测的过渡期间继续改局内配置；自然等待可作对照，不能充当销毁屏障。

held 未分代释放是已确认的强根累积，旧 Unity 对象异步移除无屏障也是已确认的框架缺口；二者都值得后续按代管理/补屏障，但本轮没有新证据能将其中一项单独判为此 AV 的根因。不能直接清空所有 held 或手动 RemoveContext/Destroy 来“试修”，以免留下当前/共享对象或屏幕队列的不一致。

静态测试没有使用 601；伞叶 packet/context Maps 为空。已有 321 笔及原版复制/倍率交互通过，既没有可指向伞叶复制 hook 的具体故障栈，也不应仅因候选新增了它便推断为根因。若后续要做排除对照，必须保留同一建局/过渡条件并单独记证据。
