# 第三版继承技能的语义抽样脚本

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/static-acceptance.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

`tests/verify_mod2_static.py` 只在 `--run` 时执行，默认输出本地计划。复用攻击脚本的 Case 与 `start_fixture(reset=False)`，每组新建隔离的真实 engine fixture，保存 unique JSONL 和结果；不安装 APK、不改缓存或账户、不发送触摸坐标、不截图。

## 已编写的四组

| `--case` | 场景与实际证据 |
|---|---|
| `freeze` | 合法打出 143，先证明它在没有 134 时存活并带 Slowed；再新 fixture 放置可见存活的 134，打出 143 后二者离场，证明既有单位真实发生自毁链。 |
| `reflection` | 316 在场且有 11 生命，1 点实际外伤令自伤链耗尽生命；记录 0 生命后，最多 6 次正常阶段动作等待真正离场与本线新生唯一一株 77，双方英雄生命不变。不能把 0 生命仍在场当作死亡完成。 |
| `coffee` | 两个先在场的 350 确认获得 +1/+1 与狂热；后合法打出的 350 仍为 1/1；一个受益者原版弹射进手牌，另一个经合法 346 藏墓碑；进入原版 Surprise 后只消灭仍在场的受益者与咖啡，后登场者和手牌留下。 |
| `grave` | 252 合法登场后，两个已知明牌 350 变墓碑；揭开普通 350 不使 252 发动；揭开 252 后这个刚变明牌的 350 必须重新藏墓碑，且队列恢复。 |

`grave` 的结果明确为 **PARTIAL**：它证明自身现身确实执行了重新藏牌，以及流程能收敛；当前 state/events API 没有 native MixedUpGravedigger 的 History 计数，因此不声称同次现身恰好执行一次。当前脚本也没有把随机位置恰好相同认定为错误。需要原版 History 或窄范围只读效果记录后才能补齐单次计数。

`grave` 使用已有的 `GrantAbilityEffect` 1013 来排入原版 `RevealEffect`，不是删除 FaceDown 标记。其他三个主技能用合法打出和真实阶段触发。咖啡弹射配角用已经支持的 `ReturnToHandFromPlayEffect`，不代替咖啡原技能的授予、增益或自毁。

本机原版类型定义确认：冻结效果的名字是 **`SlowEffect`**，没有额外可写字段。没有找到 `FreezeEffect` 或 `FreezeDuration`；不能向缓存或调试接口写入这些假设名称。当前 `freeze` 用合法 143 自冻，不要求新增 fixture 白名单。

## 调用与超时

候选应已由主代理安装并选择 mod2，再调用：

```powershell
# 只打印四组计划和后续计划，不操作设备
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' tests/verify_mod2_static.py

# 建议先单组运行，使用全新证据名
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' tests/verify_mod2_static.py --run --case reflection --name r6-static-reflection --fail-fast

# full 现在包含首批四组及新增四组；grave 的完整结果可能为 PARTIAL / exit code 2
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' tests/verify_mod2_static.py --run --case full --name r6-static-full
```

`--case` 可重复。每次 fresh 默认自然等待 2 秒，`--fixture-delay` 可调至 0–30 秒；没有清队列或催动动画。每个独立 fresh 分支完成有界启动后，另开默认 120 秒的技能检查预算，`--case-timeout` 可调至 30–600 秒，避免多分支共享一次预算。每次请求前后检查截止时间；这个软截止不能中断正在运行的 native 调用。原 host socket 自带约 25 秒超时；访问异常、传输超时或断开都停止后续组并保留已有结果，由主代理 force-stop 并冷启动恢复，不继续触碰失效现场。

失败保存前后实体、已经通过的检查和具体操作；没有实体变化的“未报错”不能通过。`PASS` 仅代表列出的已观测条件，`PARTIAL` 表示还列有未验证内容；脚本的总结果不会把 PARTIAL 升格为 PASS。

## 已追加的四组

- **97 / 900000203**：原版重定向伤害、副本死亡后无目标分支，及副本继承克制英雄 1 的有敌／无敌属性。
- **472**：路线战斗结束—死亡—相邻创建的顺序，边缘、占位和后续路线同回合级联。
- **286 / 900000204 / 176**：瞬态创建记录先于消灭，原 176 对照保留，不能仅以最终空场验收。
- **547 / 344**：合法打出到高地后先确认 PlaysFaceDown / FaceDown，再等待原版正常现身，验两栖授予、移动、减生命及水路被 344 占位的分支；原版墓碑的 PlayTrigger 会在 RevealEffect 时重放。致死分支等待真正离场，不拿 0 生命代替死亡完成。

执行与证据限制见 [覆盖说明](static-test-coverage.md) 和 [静态风险审查](static-skill-risk-review.md)。所有 fixture Destroy 分支等待正常阶段产生真正的死亡离场后再断言亡语；不写死亡标记、不清队列、不手动补召唤。子代理只进行本地语法、计划及解析检查，没有执行设备验收；实机结果以主代理的 `evidence/<name>/result.json` 为准。
