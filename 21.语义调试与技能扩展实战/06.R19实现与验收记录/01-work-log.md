# mod2 技能整合工作记录

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/01-work-log.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](工程资料索引.md)，所收检查摘要不替代完整原始证据。

用户授权在独立版中实现 mod2 技能，启动资源界面必须选择原版或改版；可以使用 Gadget 扩展原引擎。音频暂不处理。原版动画与 History 链同时核对，复杂显示问题单独记录。

## 基线与分工

- 独立目录：D:\Codex2\pvzh-mod\mod2-runtime。
- B4 与 mod2 第三版保留不改。新工程复制调试接口与教程导航，未加载 Android Java 工作台。
- 原版资源从 B4 内置11056提取；mod2内容从已核对输出构建。
- 原生资源选择器编译为独立 dex，避免 Gadget Java 桥；每次启动明确选择，切换只操作三份登记缓存。
- 原版描述器扩展编号1001–1014，字段与真实类型保持合法；正式生效由原引擎规则模块处理。
- 伞叶的单次随机承伤语义正在等待用户可选回复，其他技能独立推进。

## 当前进度

已完成必选资源界面 dex 与 11 项离线事务测试。原版资源来自 B4 的原始包；改版为 mod2 v3 的完整 656 定义，新增 16 张扩展配置，相对原版共 98 张改卡。标签配置、中文说明和隐藏定义均通过静态核对。

攻击模块已接入共用攻击列表、实际效果队列书签和伤害记录，覆盖禁攻、受伤解锁和攻击前后动作。书签不执行额外死亡检查，保留原版双方同时还击时序。力量限制与僵尸伤害固定模块接入中。

一次性动作通过原版 GrantAbilitySystem 截获 reserved 值，排入原版 Reveal、SetStat、GainSun 效果。生命交换先快照双方当前生命和生命修饰量，保留修饰器，最后统一状态检查。阳光债务在原版 SunCount 的 TurnEnd 资源刷新完成后消费，再使用 Immediate/EndOfTurn 负 GainSun：原版 NextTurn/EndOfTurn 组合会在激活同轮直接过期，因此不使用。

动画核对确认：通用结果由原版 History 消费；Special 需要真实触发实体和原版动画组0或1。初版只复用本轮已完成的安全原版触发实体，其他新增被动技能保留通用结果动画并记录 special-unavailable，不创建自动参与触发扫描的假实体。动画是否被实际画面采用仍须区别于逻辑测试。

设备验证和所有集成构建由主代理统一操作。此处为集成前进度，不代表真机技能验收已通过。

## 首轮实机与接口修正

r1安装成功，原版→mod2→原版→mod2四次冷选择的receipt/三份缓存SHA/运行模式一致；正常界面必选、返回键不可绕过、未选择前Unity未加载，共8项通过，证据 `evidence/r1-gate-b/result.json`。测试脚本原先exec-out不能识别cat失败，已改shell-v2；失败证据保留为r1-gate。

r1攻击测试证明原版1/1双方仍互杀，但新增禁攻的实际额外攻击失败；模块回调计数为0。r2合法墓碑克星落入原版Grant1013字典异常。独立核对库SHA、dump/script RVA、effect字段均一致。除了修正过早缓存旧对局模型，还定位到主要原因：所有同步JSON命令在Unity帧的Interceptor.onEnter中调用原引擎，Gum listener TLS递归保护让嵌套原生调用绕过其它监听/替换。异步GameInitializer仍能被捕获，故原底座API仍表面可用。

r5把UnitySynchronizationContext.ExecuteTasks静态入口改为replacement wrapper（void(MethodInfo*)），保留原帧任务调用、UnityMain线程归属和一次一条pending命令；native invoke显式开启traps all。此变化须实测新的技能拦截与原版底座完整游戏回归，不把源码推断当通过。r1–r5候选/构建指纹各自保留，未覆盖原B4或mod2。

参考[Frida官方Gum实现](https://raw.githubusercontent.com/frida/frida-gum/main/gum/guminterceptor.c)的begin_invocation/回调guard路径。r3/r4仅构建留存；没有将构建通过记成设备通过。

## r5 后的真机结果与边界修正

r5攻击完整组先通过10case：同步互杀、四张单位正攻禁攻且普通伤害仍结算、两种路线限制与异线对照、读报真实伤害解锁、火龙果邻线6点、原始豌豆回手。火炬致死场景失败：其原版StateCheck实际死亡移除晚于预生成攻击包。后续修正只对已承受火炬前置伤害的frame额外检查HP≤0，保留普通同步战斗0HP还击。

r5动作通过合法87现身、两次合法106债务独立登记/下轮-6/再轮恢复/0下限、合法202增益手牌与受伤英雄换血。进一步受伤双方手动触发换血失败；原因是额外Special包装重写EffectEntityId和Context，原版触发筛选要求SelfQuery、结果目标又要求僵尸玩家，双SetStat被原版取消。初版关闭额外bookends，保留真实PlayTrigger自带的外层记录与通用结果。

r5力量测试前三项通过，健康Strip发生abort。原版StripNonContinuousModifiers会Int32.Parse(modifier.GroupId)，setup Buff池默认空串不能兼容。后续setup Buff、狗头Buff改用数字来源实体ID；Sun modifier也使用数字来源ID，独立债务序号仍由ledger保留，原版List.Add不按组去重。

r6可选History模块fullname写错导致bootError，r7仅构建；r8fullname修正后首次建局发生0地址异常。先将History观察改为显式查询时读取原版快照，不在建局期挂钩；但r9没有History hook仍崩溃，不能把原生崩溃归因于History观察器。观察不足按缺失报告，不阻止核心技能。候选与每轮失败证据均保留；后续最终验收将重跑完整组。

## 连续建局稳定性调查

r9延后冷启动及重复建局仍失败，设备栈显示AssetGarbageCol线程在IL2CPP Unity liveness对象遍历中访问无效class。原来新增native hook在cache miss时调用live→Resources.FindObjectsOfTypeAll，可能重入对象扫描。r11改为native hook只读已缓存的当前generation上下文；cache miss跳过并报告，明确不发起全局扫描。显式命令以及最外层Unity帧才允许刷新缓存。此处记录修正方向，尚须完整连续测试验证，不能称为已确认根因。

r10同时补充启动binding元数据检查、managed field空值防护和debug boot warmup。暖机只限制调试命令，不阻止普通游戏启动；延长暖机本身不能修复r9已发生的重复建局崩溃。新候选r11的GainSun GroupId用il2cpp_field_set_value赋托管字符串，保留写屏障。

r11再次通过同步互杀与600禁攻后，在第三次建局出现同一AssetGarbageCol liveness栈，证据`evidence/r11-attacks/native-crash.txt`。因此cache-only是必要隔离，尚不足以解释或修复该崩溃。

r12修正两个具体GC root缺口：原版Pool.Acquire不保存InUse对象集合，新建效果只被JS数组持有期间可能失去托管根；禁攻Clear之后批量Return原效果同样失去列表根。新效果立即建立临时strong GCHandle，进入原版列表/队列成功后释放；攻击构造器返回的List在onLeave回调期间也临时保活，Clear前保活旧效果，Return后释放。错误路径仅返还尚未入队的对象。新增status临时root计数便于查漏。

r12还从当前InitializeGameStateCommand已注入binder中查询named IContext(ContextKeys.CONTEXT=0)、GameModel和GameStateUtils的已有实例value，校验类型及当前模型后缓存，不通过GetInstance提前创建单例。此路径可在初始效果之前供给技能上下文；外层frame回退刷新保留。以上仍须设备验证。

## 对照实验与攻击效果所有权

r12真机原版17项底座检查、36条语义动作完成对局胜利通过，随后同进程温重开3局（generation2/3/4）通过。改版不进行攻击的温重开3局同样通过。扩展GC临时root每case回到0，但simultaneous→ban600→新局仍崩溃；进一步单独ban422通过后，下一新局再次崩溃。证据分开保存在r12-original-regression、r12-original-warm、r12-mod2-warm、r12-attacks、r12-ban-only。

r13禁攻路径改为取消原列表内效果，由原版queue按自身生命周期处理并返池；不再由Gadget清空列表后手动返还原效果。原列表保留全部托管所有权，禁攻不插入新书签，也不执行扩展after动作。此处仅是最小路径修正，尚须复测确定是否解决崩溃。History显式查询新增原版CardIdData(key36)的EntityId/CardGuid解析，为瞬态召唤顺序提供可核对证据。

## 引用字段ABI错误已确认

r13禁攻改用Cancel仍在同样路径复现，不能归因于Clear/Return。进一步对照发现：失败的首个禁攻case都会使用fixture Buff设置数字GroupId；r5已过的前10case未新增该字段写入，原版完整回归与两种profile纯建局对照均无此赋值。

对实际libil2cpp机器码核对确认：il2cpp_field_set_value(RVA0x17CFD1C→0x179FE34)对String/Class/Object引用字段直接写传入value对象地址；标量字段才解引用缓冲区。旧setField(pointer)传入Memory.alloc(8)指针缓冲区，实际把非托管临时内存写成C# String引用，构成明确对象损坏。先前“使用field_set_value因此已正确执行写屏障”的判断不成立：写屏障不能修正参数本身错误。

r14专门对引用字段调用il2cpp_field_set_value_object(RVA0x17CFD20)，直接传原对象；标量仍传正确大小缓冲区。涉及setup Buff、狗头Buff、GainSun GroupId三处引用赋值。临时GC roots、cache-only与保留原效果所有权仍保留为独立生命周期改进，但不再称它们为此次崩溃根因。r14设备整套验收尚待执行。

r14首个完整攻击套件已经通过全部14case：同进程连续建局达到generation14、全部新攻击语义断言通过、模块错误计数未增加、临时effect roots逐case为0。证据`evidence/r14-attacks/result.json`。这与ABI二进制证据共同证明之前可复现的坏引用路径已修正；属性、动作、继承静态技能及有渲染对局继续分别验证。

r14一次性动作7项全部通过，证据`evidence/r14-actions-result.json`。属性／伤害最终8case全部通过，证据`evidence/r14-stats-final/result.json`：326手牌、合法打出、SetStat、持续光环及替换、回手；518真实手牌墓碑、现身前后、各来源、0伤害、乘算、装甲、免疫、最低生命与合法锦囊伤害、实际离场后恢复原伤害。初期失败来自测试假设，未改核心技能来迁就断言：原版召唤不等于墓碑打出；Destroy只标记后须正常StateCheck阶段；type1真实组件为DamageImmunity；最低生命Source必须Fighter+InLane。失败报告保留，修正测试后的断言保持原强度。

继承静态抽测中冬瓜自冻通过，但紧接立即温重开出现EnterCheatGame原生访问异常。冷恢复后测试每次自然等待2秒，冬瓜／冻窝瓜联动完整通过，证据`r14-static-freeze-delay2`；这是测试节奏缓解，不声称正式UI生命周期全部解决。反射坚果实测11HP因1点外伤有限连锁到0HP，后续正常end_phase才触发死亡生成77；独立追验证据`r14-reflection-phase-probe.json`。因此其测试以及类似Destroy分支正补真实死亡处理等待，不把HP0误当已完成所有死亡触发。

## 继承静态技能的额外修复与 R15

R14 的反射坚果、香蕉分身、直升机瞬态召唤／自毁均有原版路径实测；双人菇97和潜水员547仍发现真实缓存问题。97 的 SameLaneQuery 只选路线实体，改成 InSameLaneQuery(OriginEntityType=Self)才可选到真实副本单位。547的合并描述器在执行GrantAquatic前先检查次目标水路，导致整组没有合法目标；拆为原版三实体风格，先授予两栖再移动，移动后自身MoveTrigger在水路扣-2/-2，避免高地条件在移走后取消扣属性。原PlaysFaceDown和PlayTrigger保留，原版Reveal会重放PlayTrigger。

profile_revision=3仅增加97、547这两项静态修复；与v3相比共18张定义调整，16张扩展标记，原版650、改版656定义和5个内部定义均保持。改版card_data SHA为c0bf2d71f7b2ad37a52ee81c1ee4e46d69aaf42cf2c07bc9ff6c7842483a7ce5。R15真实额外攻击的97转伤、无副本回退全部5项通过；547现身后两栖／移动／扣属性、满水路反例全部行为断言通过。2HP自然死亡History实为CardMoveRecord→BuffRecord→DiscardFromPlayRecord，测试曾错误要求DestroyCardRecord，故旧报告PARTIAL保留；正在改验收为真实自然死亡链。

R15引入默认关闭的窄触发诊断，仅只读选定ID的原版条件和MixedUp调用。252手动fixture Grant现身的两条件均通过，但Triggered集合直到下一原版阶段才解析；下一阶段真实MixedUp恰一次且重藏所有僵尸。因此不把该直接fixture的中间状态当作正式卡牌失败，改为两次合法87出牌路径复验。

咖啡209变墓碑丢失900000302源于原版清临时counter及技能实体。窄补丁仅在GravestoneMaker调用期间临时保护该counter，返回恢复，以保留弹回手牌时原版清除规则。R15首次保护未执行，事件明确为Frida FFI bool参数“expected an integer”；root(pointer,true)已改为整数1，mock同步检查真实ABI输入限制，等待下一候选真机复验。未把本地mock通过当作设备通过。

R14带渲染测试中普通350／347出牌能自然结束，但合法87现身后原动画队列持续非空。原History有完整Start→Reveal→End→Discard→PhaseResume，技能和模型阶段已正常完成，不能称画面通过。正在读取真实动画容器并核原版专属special是否消费了不支持的RevealRecord，后续以窄原版Reveal处理路径对照验证；此问题不会通过清空队列或伪造完成标志掩盖。

## R16—R18 真机结算与原版动画链

R16 的继承静态抽测全部通过：8 case、37 项检查，覆盖冬瓜／冻窝瓜、反射坚果有限连锁和死亡、咖啡墓碑保留与回手清除、墓碑重藏、双人菇真实额外攻击转伤、香蕉分身边界、直升机瞬态召唤自毁，以及潜水员现身后两栖／移动／扣属性／自然死亡。证据为 `evidence/r16-static-full/result.json`。咖啡保护 FFI 修正后真实执行，临时 roots、受保护 counter 和活动调用均回到 0。

87 的合法出牌与直接 fixture 分别验证。直接 fixture 的 InterruptQueue 先获得新组，而 CurrentGroupId 尚未推进；扩展响应改继承源 Grant 的 EffectGroupId，避免被旧 Blocking 组延后到下一阶段。`evidence/r16-grave-response-group/result.json` 记录同次指令即时原版 MixedUp，后续正常阶段不重复。

87 的专属 special 不支持新增 Reveal 结果，冷启动对照关闭兼容时队列真实停滞，启用窄兼容后 5 项渲染检查通过。兼容仅针对当前模型中 87、group0、真实 Start 后严格 [Reveal,匹配 End] 的结构：原版 End 标记已处理，保留 Reveal 给原版独立 RevealRecordProcessor；不伪造 History、不清队列。R17 起默认启用。失败与成功分别保留于 `r16-render-87-disabled-cold`、`r16-render-87-fallback-on`。

106 次轮扣阳光在引擎正确结算，但原 GainSun 粒子工厂试图查已经弃牌的来源 CardView，产生 ViewMapException。R18 仅针对 106、植物 SunCounter、实际 -3..0 的延迟 GainSun 记录，使用原版 GainSunEventAction 的公共目标反应动画进入原动画队列，保留真实来源、记录及阳光账本。`evidence/r18-render-actions-final/result.json` 全部 8 项通过：202 换血、87 现身、106 延迟扣阳光，以及带渲染完整回合中 busy→empty 的自然动画完成。原版 SunCountIncremented=51，随后真实来源的 GainSun=-3，最终 total/available=48。首次 R18 测试错误地将含 modifier 的 total 预期写为 51，失败记录保留；修正测试后无需改变 APK 即通过。

R18 原版模式再次完成 17 项底座检查及 36 步语义操作的整局胜利，证据 `evidence/r18-original-regression-result.json`。全程不需要坐标触屏或截图。上述渲染验证证明所测原版结果动画队列能够自然完成，未对新美术或所有技能逐帧验收。

## 用户确认伞叶规则与 Rev4

用户确认 601 每笔伤害在自身及左右相邻路线的各株植物中随机选一株承受，选择自身则正常结算，每笔只转移一次。保留原版 Teamup 与 CreateInFront 站位，移除旧 Untrickable 光环，新增保留标记 1011 和对应中文说明。Rev4 仅改变 601 与两项中文键；其他 655 定义、原版包、关卡数据和 5 个内部副本保持 Rev3。范围更新为相对原版 99 张改卡、17 张扩展配置、相对旧 mod2 v3 的 19 张修复／扩展。

正在接入当前对局的原版 RNG 与伤害前置流水线。单次标记必须跟随原版伤害复制、转向上下文及返池清理；不能使用未定义的 EffectData enum，因为原版序列化会拒绝 0..11 以外的键。最终设备结果另行追加，尚不把配置或本地检查算作伞叶真机通过。

R19 已安装，并完成伞叶真机完整组：`evidence/r19-umbrella/result.json`，9 case、17 检查全 PASS；225 笔 DamageEffect，其中 5 笔零伤害。逐笔核对原版 RNG 选择事件、全部实体生命差、来源及双方英雄保持，以及处理后 packet/context Map 归零。覆盖无邻株自承伤、自己／单邻株、双伞叶只选择一次、同线及僵尸排除、左右邻线各两株按个体参与、真正接收者 Armor／DamageImmunity、零伤害，以及 518 配合来源 MultiplyDamage 后仍最终 1、装甲可减到 0。相对原目标的特殊倍率、沉默与原生额外重定向交互不混入这份报告；后者另做严格实测。

R19 额外交互组 `evidence/r19-umbrella-interactions/result.json` 2 case、6 检查、96 笔全 PASS。合法双人菇97自身作为来源，伞叶随机选择后继续走原版97转副本链，真机证明复制包继承单次标记、只抽选一次、原来源倍率2只计算一次；左右边路与远线反例也通过。总321笔中220+96笔正伤害各选择一次，5笔零伤害不选择。目标依赖的 EffectEntityMultiplier 与沉默控制者缺少可严格构造的现有 API 场景，明确保留未测。

同一 R19 的攻击14 case / 21检查、属性伤害8 case / 39检查，以及带渲染8检查全 PASS，分别见 `r19-attacks`、`r19-stats`、`r19-render-actions`。带渲染报告有真实 busy→empty、完整原版回合与 History，未作逐帧美术验收。

## R19 连续建局失败与严格记录

属性套件后立即无等待进入动作测试的新局时出现 `access violation accessing 0x0`。旧动作测试没有在 native AV 后停止，而准备进入下一 case；主代理停止其特定子进程，再强停游戏，保留 `evidence/r19-actions.jsonl` 与独立失败记录 `r19-actions-interrupted-result.json`。仅修改测试：每次建局前自然等待2秒，出现 native AV 立即停止、不再查询可能损坏的对局。运行时与 APK 没有改变。

冷启动恢复后动作完整组 `r19-actions-final-result.json` 7检查全 PASS。其后静态完整组 `r19-static/result.json` 前5 case / 18检查与香蕉前2项通过，但第15代模型后的香蕉第三分支再次在温建局入口遇到 native AV，即使等2秒仍不能保证稳定。此报告保持 FAIL，不能把已通过的技能断言反写成全套通过，也不能宣称2秒等待修好了生命周期。后续冷进程静态独立复验另存 `r19-static-cold-final`；旧局销毁屏障与按代 GC handle 回收尚未实现。

`evidence/r19-static-cold-final/result.json` 最终8 case / 37检查全 PASS、unverified为空。此轮先启动新冷进程，再各场景自然等待5秒；严格保留所有技能断言，没有更换 APK、清队列或伪造完成状态。这个结果证明此轮技能矩阵能够完成，不证明5秒等待可保证任意长时间连续建局。只读后续方向见 `docs/warm-fixture-followup.md`：建局入口实际使用 ApplicationRoot 的 AppContext，并非旧 extensionLive；缺少子阶段 PC/返回证据，当前不能确定哪项原生依赖造成0x0，不能把原因直接归到伞叶或 GC handles。

含601／202的初始牌组第一次冷建局仍出现入口0x0，`r19-mod2-battle/result.json` 保留 FAIL，因此不能把原生异常限定为温重开；该初始牌组初始化路径未计为通过。再次冷启动使用已验证的普通347／350初始牌组，随后接口give601与202，23次合法语义操作实际完成对战胜负，伞叶在真实战斗中选择2次、所有技能错误为0、临时effect roots为0。

`r19-mod2-battle-final/result.json` 曾因测试要求终局attack pending也归零而 FAIL；实际终局为LoseEffect，最后致死攻击开始但after-marker停在后方，started19/completed18，pending1/1。只读核原版LoseByHealth→LossProccessor把Lose加到当前响应组，Lose继承UnresolvableBlockingEffect且IsResolved固定false，处理器不再Shift；因此不能为通过测试强推结束标记。保留旧FAIL，独立当前状态审计 `r19-mod2-battle-audit/result.json` 明确验证完整胜负与终局保留的scalar bookkeeping，不声称队列彻底排空或生命周期回收。未来battle测试已改为严格核这个终局结构；非终局套件仍要求pending为0。源与APK未改。

## R19 最终交付

同一 R19 的原版 `r19-original-regression-result.json` 17项全PASS、36次语义操作完成胜利；真实APK/script散列与构建产物完全一致。随后 `r19-original-isolation.json` 确认active=false、攻击扩展generated=0、伞叶selections=0、临时根为0。

`r19-release-handoff/result.json` 最终8项全PASS：真实安装包指纹、原版/改版收据与三缓存、正常入口无跳过、返回键不能入Unity，以及最后无extra正常启动停在用户必选资源界面。最后已校验缓存为Rev4 mod2。机器汇总存 `dist/release-summary.json`，人读总表存 `docs/02-verification.md`；源码、独立MD、构建和失败历史均留在mod2-runtime，原B4/v6/mod2/资料库保持。

当前交付为技能实现与已定义验收矩阵通过，已知调试建局原生异常仍未根治。未新增音频，未扩AI独立预测模型，未把321笔专项伤害、8项原版动画队列或原版整局检查扩大成99张全部组合与逐帐美术通过。
