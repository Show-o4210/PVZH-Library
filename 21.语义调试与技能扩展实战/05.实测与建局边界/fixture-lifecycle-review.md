# Fixture 生命周期只读复核

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/fixture-lifecycle-review.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

复核日期：2026-10-14，文档补核至R19。范围是 `scripts/verify.py`、`scripts/session.py`、`src/runtime.js`、本机原版IL2CPP退出／销毁路径及已有设备报告；文档作者未运行ADB、未修改源码或测试。原静态调查保留，以下另明确已获得的冷回归与有限温重开证据；核心技能通过不代表严格销毁屏障已经实现。

## 已确认的结论

`start_test` 有原版界面替换路径，旧对局并非必然永久叠加。原版 `ShowGameCommand.ShowScreen` 会安排异步 `ScreenDestroyer` 清理旧 `GameScreen`，后续存在 `GameRemovedSignal` 和上下文 `OnRemove` 的清理路径。但是，当前 `start_test` 返回的是“已发起进入”，测试框架没有等待旧局移除完成的独立屏障；不能把一次新 `GameModel` 初始化直接当作旧局完整清理的证明。

`session.start_fixture(reset=True)` 先 `am force-stop`，再通过资源选择界面冷启动。它隔离旧进程内的对局、hook 缓存和 GC handle，保留磁盘账户及缓存；没有 `pm clear`。`reset=False` 连接活进程并直接再次 `start_test`，依赖原版的异步界面替换。当前攻击与静态抽样脚本使用后者，因此温重开生命周期是一个需要单独验收的框架前提。

## Python 与运行时的具体保证

| 位置 | 实际行为 | 能证明什么 / 尚缺什么 |
| --- | --- | --- |
| `session.launch(reset=True)` | 强停应用，通过 Gate Intent 显式选择 profile，等待 `installed` 与 `app_ready` | 冷进程隔离；不等同于某项技能通过 |
| `session.launch(reset=False)` | 若已有 `pvzh-test-mode` 响应，直接复用；不重新打开 Gate | `profile` 参数只影响需要冷启动的分支，活进程不会由此改 profile |
| `session.start_fixture` | 发 `start_test`，等 `state.fixture && state.headless && active_player >= 0` | 等新测试模型可用；没有旧 Context 移除计数或屏幕过渡队列完成断言；此 helper 不适用于 `render=true` |
| `runtime.startTest` | 重写 `agent_test` 节点与两副测试牌组，设置测试模式，组装 Gate，调用 `EnterCheatGame` | 没有直接调用退出/销毁服务；通过原版 ShowGame 的间接路径进行界面替换 |
| `expectedGeneration` / `ownFixture` / `mutableLive` | 要求新初始化代数、`agent_test` 节点、捕获模型身份匹配，结束后拒绝修改 | 能拒绝对旧模型的命令写入；不能证明旧模型、上下文、托管根或动画队列已经释放 |

`headless` 与 `manualBoth` 在进入新局之前改变；测试节点、牌组固定 ID 和共享 `GameConfig` 也在旧界面真正移除之前更新。是否影响过渡期间仍在执行的旧局，需以代数/模型身份和退出日志验证。仅看到新开局手牌清空不够。

`held`仍是进程级数组。`pin`当前调用 `il2cpp_gchandle_new(pointer,0)`，创建强GC handle，未请求地址固定。初始化hook为每局initializer、GameModel、GameConfig创建handle；`newObject`和测试节点也加入held。当前仍未实现held旧代释放或清理，所以这部分托管根会随温重开累积；它不能单独证明Unity GameObject未销毁，但会保留旧托管对象图。

不要再把“所有handle均不释放”当作当前事实：pool效果另由effectRoots管理，`releaseEffect`实际调用api.unpin；咖啡及动画兼容模块也在finally释放局部pinned根。R19渲染报告的temporary_effect_roots及兼容模块active_gc_roots均0。需要分代回收的是仍在held中的旧长期根，不能直接清空整个数组，当前局与进程级共享对象仍可能依赖它。

## 原版退出与销毁入口的静态证据

本机二进制为 `D:\Codex\PVZH\dump\libil2cpp.so`，SHA-256：

`18178b2f35959bc3954378a9778cddd67aab8a7ef22579ea59d736521eec8c91`

以下 RVA 仅适用于这份 1.67.8 arm64 二进制。使用既有本机 Capstone 和 pyelftools 只读反汇编，并结合 `dump.cs` 的字段/接口 slot 核对；不是仅凭空方法体推测。

| 方法 / RVA | 核对到的行为 |
| --- | --- |
| `GameEntryGateKeeper.EnterCheatGame` / `0x1F56DA4` | 当前 `start_test` 的进入入口，后续通过原版 `ShowGameSignal` 进入显示流程 |
| `ShowGameCommand.ShowScreen` / `0x1FBC95C` | 创建新屏幕；按 ProgressionUtility 的条件调用 ScreenLoader 接口 slot 14 `PopAllAndShow` 或 slot 8 `ReplaceScreenAndMaintainAsync`；不是普通 slot 7 `ReplaceScreenAsync` |
| `ScreenLoaderImpl.ReplaceScreenAndMaintainAsync(ScreenRequest)` / `0x1E7CA9C` | 保存 `GetTopScreen()` 为 current，调用 `CreateScreenDestroyer(current)`，并把它传入 `EnqueueScreenPush`。名称中的 Maintain 不能解释为保留当前旧局 GameObject |
| `ScreenLoaderImpl.CreateScreenDestroyer` / `0x1E7CB58` | current 非空时创建 `ScreenDestroyer(current)`；current 为空时使用 NullDestroyer |
| `ScreenDestroyer.DestroyOldScreens` / `0x1B7C014` | 枚举旧 ScreenRequest，对尚未销毁者调用 `ScreenRequest.Destroy` |
| `ScreenRequest.Destroy` / `0x1B7C15C` | 先调用 LoadableScreen 的 `OnDestroy`（接口 slot 12），再将旧根 SetActive(false)，调用 Unity `Object.Destroy`，清空根引用并设置已销毁标志 |
| `GameScreen.OnDestroy` / `0x1FBC710` | `0x1FBC750` 调基类 `PrefabListLoadableScreen.OnDestroy`；`0x1FBC760` 调 `BaseGameRoot.SendGameRemovedSignal`；随后还涉及 LevelLoader 与 ResourceCache 清理 |
| `BaseGameRoot.SendGameRemovedSignal` / `0x1F5BBE8` | 原版对局移除通知入口，可按旧 GameRoot/Context 身份记录 |
| `ContextView.OnDestroy` / `0x307B7CC` | 取自身 child context，调用 `Context.firstContext.RemoveContext(child)`（IContext slot 3） |
| `CrossContext.RemoveContext` / `0x307C874` | 先拆 CrossContext，再调用基类 `Context.RemoveContext` |
| `Context.RemoveContext` / `0x307B5DC` | child 非 firstContext 时调用其 `OnRemove`（IBinder slot 15）；上下文销毁存在原版解绑链 |
| `BaseContext.OnRemove` / `0x1B7AB44` | 调 `MVCSContext.OnRemove`，并通过 binder 获取/派发移除相关 signal |

`ScreenTransition` 有 `UnloadResourcesAndLoadNextScene`、`OnComplete`；`ScreenTransitionQueue.IsTransitionActive()` 也是现存的过渡状态入口。界面请求进入队列、旧 ScreenRequest 的显式 `OnDestroy`、Unity 原生对象真正销毁及 child Context `OnRemove` 不一定发生在同一个同步调用栈里。建议分别观察这些边界，而不是在 `start_test` 调用内等待或递归驱动 Unity 更新。

dump 中没有 `ExitGameService` / `IExitGameService`，它们是讨论时的假定名称。实际有 `ExitMatchSignal` / `ExitMatchCommand`（Execute `0x1F19824`），但后者依赖认输信号、确认对话框与 Android 最小化服务。它不是已确认的“无 UI、无结算、立即销毁测试对局” API，不应按名称直接接入自动测试。

也不建议直接调用 `Context.OnRemove`、`RemoveContext` 或 `Object.Destroy` 作为首选重开实现。单独触发低层销毁可能留下 ScreenGrid、过渡请求、资源引用或原版对局状态不一致。优先继续使用已确认存在的原版屏幕替换/移除流程，加显式观测屏障。

## 原版回归目前覆盖的范围

`scripts/verify.py`默认 `--profile original`，普通运行通过默认reset=True冷启动一次，验证原版模仿演员、抽牌、合法出牌、原版召唤、完整战斗胜利和错误请求不改状态。脚本本身只运行一局，不把它当连续温重开套件。

此前“没有profile断言／报告”的描述已过时：当前脚本在取状态后明确断言 `runtime_status.resource_profile == args.profile`，成功报告包含resource_profile与runtime_status。`--existing`跳过冷启动和固定seed断言，但仍执行profile断言；不会把已运行mod2无声当成original。session温连接传profile参数本身仍不切模式。独立交付验证还可核Gate receipt及资源hash；APK/script hash只证明载荷，不能代替实际资源模式。

[R18原版回归](../06.R19实现与验收记录/工程资料索引.md#ref-8848769e6b44)已由主代理实际执行并PASS：resource_profile=original、cold_started=true、固定seed1337，17checks通过；完整战斗21次play与15次end_phase，共36步，植物玩家0胜利，未模拟点击或截图。因此不再说“原版回归从未执行”。此证据是原版冷起单局，不能替代R19或无限次温重开。

最终同候选 [R19原版回归](../06.R19实现与验收记录/工程资料索引.md#ref-a23302579545)也已PASS：original／cold_started=true／固定seed1337，17checks与36步原版完整胜利，APK SHA-256 `c7e48e0ae694d9fbf1b9c0e59d7fd73311fb880a4b56dc13ac1656c4cc6652cf`，安装script `3cc23604419967c87e89186a260dfa039ad9286389ba468a71c3f9c410efe32b`。[原版隔离](../06.R19实现与验收记录/工程资料索引.md#ref-a062986f539c)PASS，改版active=false、attack.generated=0、umbrella.selections=0、temporary_effect_roots=0。它证明该候选原版模式完整战斗与规则隔离；仍没有证明所有旧root／Context均已释放。

[R12 original温重开](../06.R19实现与验收记录/工程资料索引.md#ref-e8e292040245)和 [R12 mod2温重开](../06.R19实现与验收记录/工程资料索引.md#ref-a450f607f561)各连续3fixture PASS，original代数2→3→4、mod2代数1→2→3；两个报告均明确old_context_teardown_proven=false。它们证明当时有限用例能重开，没有证明旧root／Context已释放。

R19核心新配置下，承伤、攻击、属性及可见动作分别已有通过报告；但stats后立即无等待重开reveal发生 `access violation accessing 0x0`。主代理停止该测试子进程并强停游戏，原 [中断报告](../06.R19实现与验收记录/工程资料索引.md#ref-58cc13c6ce6d)及 [命令日志](../06.R19实现与验收记录/工程资料索引.md#ref-be0f894a25d8)保留，checks为空。仅测试脚本添加自然2秒过渡等待和遇native AV立即停止，不再做可能重入的诊断调用；运行时未因此修改。之后独立冷恢复、局间自然2秒等待的 [R19动作复测](../06.R19实现与验收记录/工程资料索引.md#ref-968e3f334f71)7checks PASS；fixture_reset_uses_cold_start=false，不能误写成每个fixture均冷起。

紧接的 [R19旧静态](../06.R19实现与验收记录/工程资料索引.md#ref-0602f9dd6fe6)同样fixture_delay_seconds=2，却在banana472第三branch／previous_generation15重开时再次0x0 AV并停止。前五case共18checks及banana前2checks通过，完整报告仍FAIL，copter／diver当时未执行。随后独立新冷进程起点、fixture_delay_seconds=5的 [R19最终静态](../06.R19实现与验收记录/工程资料索引.md#ref-c20afe3dbf73)8case/37checks全部PASS、全部unverified=[]，也覆盖后续banana、copter及diver。这证明这次有等待的有限完整流程通过；两秒已明确不足，五秒也不是严格销毁屏障，不能替代旧root／Context移除事件及按代释放，更不能宣称任意长期批量重开已彻底修复。

后续 [含601／202初始牌组的建局](../06.R19实现与验收记录/工程资料索引.md#ref-64fbbefb4214)在cold_started=true时仍0x0 AV、报告FAIL；没有成功终态，不能计作该自定义初始牌组初始化通过。因此未定位的start_test异常不能只写成warm重开问题，也没有证据把原因归结为601承伤或202技能逻辑。

普通347／350初始牌组冷建局、之后give601／202的实际对局完成14次play和9次end_phase，共23步，原版game_over=true、僵尸5胜／植物0败，见 [R19战斗审计](../06.R19实现与验收记录/工程资料索引.md#ref-8fe05f7e69d0)。601在真实combat选择2次，技能errors=0、temporary_effect_roots=0；审计PASS明确只证明实际完整战斗。

原 [整局测试报告](../06.R19实现与验收记录/工程资料索引.md#ref-898a6b792046)仍为FAIL：原版效果队列停在终局LoseEffect，最后after-marker没有被继续处理，attack.generated/started/completed=19/19/18，pending_attacks=1、pending_markers=1，metadata保留至重置。审计没有排空队列或伪造completed，也不把原报告改成全PASS。终局停止、模块元数据仍在与严格销毁／旧根释放是不同问题；目前都不能作为已完成清理的证明。

## 安全替代方案与最小验收

短期保留 `reset=False` 以检查重开稳定性；若第二局出现上下文数量不唯一、stale cache、过渡超时或进程崩溃，单项改用冷起隔离。隔离结果必须标明 cold-start，不能把隔离后的通过反写为温重开修复通过。冷起只需要强停再选模式，保持账户及资源缓存，无需重装或清数据。

后续温重开可以采用跨帧状态机：

1. 确认当前修改对象属于 `agent_test`，保存旧 root/context/model 和代数；阻止同一时刻另一次 start 请求。
2. 标记 transition 中，暂时拒绝局内修改；从原版入口发起屏幕替换。缓存失效、释放旧代根与回调注销按对象身份处理，不能用“当前全局代数”误删已经初始化的新局缓存。
3. 在原版回调中只记录旧 `GameRemoved` / `Context.OnRemove` 边界，避免调用 `Resources.FindObjectsOfTypeAll` 或重新解析 live Context。必要的只读查找移到 UnityMain 的普通命令/帧刷新阶段。
4. 等过渡不再 active、旧 Context 移除、新的 initializer 完成、模型身份/新代数一致，以及新队列可用，才返回 ready。超时进入明示错误状态；不强行继续对可能失效的旧指针调用方法。
5. 按代管理本模块创建的 GC handle，在原版移除完成后释放旧代 handle；对全局共享 GameConfig 等重复对象去重或按引用计数保留。当前局和进程级对象的根单独管理。

实机温重开用例建议使用一进程三局：第一局创建可识别单位并触发效果，第二局换种子/牌组与渲染模式，第三局正常完成战斗。每次都证明旧 root/context 的移除事件、generation 严格递增、新开局实体集合与手牌符合新配置、旧单位不再出现、旧回调不再修改新模型；再跑同样的冷起版本作对照。实体 ID 可在新模型重用，因此不能只用 entity ID 集合作为旧对象身份依据。单独的窗口状态/动画队列消退与逻辑结果分别记录，缺少旧局销毁观察时应标为生命周期证据不足。

以上跨帧退出屏障与held旧代回收仍是建议，未实现新的退出API或严格销毁完成屏障。当前cache-only／临时根及引用字段ABI改进已有核心回归证据，但R19冷建局和温重开均有失败，终局还保留一笔after-marker元数据；不承诺所有开局、批量重开或终局清理已修复。本页只读取既有源码与报告，没有执行新ADB验证。
