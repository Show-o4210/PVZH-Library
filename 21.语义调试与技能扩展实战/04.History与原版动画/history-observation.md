# 原版 History 的显式只读快照

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/history-observation.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

[mod2-history.js](../06.R19实现与验收记录/工程资料索引.md#ref-fe1f0a1936e9) 只在明确调用 `records()` 时，读取当前真实对局 History 仍持有的记录。它不挂任何 native hook，不创建记录，不调整动画队列，也不操作界面或发截图。

## 模块接口与启动隔离

```javascript
const observer = require('./mod2-history').install(extensionApi);
observer.status();                         // 纯 JavaScript 状态
observer.records({ since: 0, limit: 100 }); // 显式 UnityMain 命令中读取快照
observer.reset();                          // 纯 JavaScript
observer.dispose();                        // 纯 JavaScript
```

主运行时通过 `mod2_history` 命令调用 `records()`。该命令须使用既有 UnityMain 调度，等出牌、目标选择和效果结算完成后再查询。本模块不修改主运行时。

`install()`、`status()`、`reset()` 和 `dispose()` 均不调用 live、Resources、DI 或其他原生方法；也不会安装 AddRecord、EffectRouter 或 History 清理的全局拦截。状态明确返回 `mode:"explicit-snapshot"`、`native_hooks_installed:0` 和 `native_queries_on_install:0`。这使可选观察器不参与游戏建局过程。

仅 `records()` 会查找当前 live 对局，再从其 context 解析 History。解析失败时保留错误计数、`last_error` 和 `last_snapshot_succeeded:false`，不向核心技能传播观察异常。状态中的 `native_history_bound` 只代表最近一次成功绑定，须结合 generation 和本次快照成功标记判断；空数组不能直接证明没有生成过记录。

## 快照覆盖范围

**这不是完整 History 事件日志。** 原版消费者可能已经读取并清空 History，查询时已经消费的记录无法恢复。模块始终报告 `coverage:"records-visible-at-explicit-query-only"`、`complete_history:false` 和 `visual_verification:"history-snapshot-only"`。不能凭两个快照之间缺少某个类型，断言原版未发出它；也不能把跨快照拼接的数组当作完整无缺失的结算链。

每次查询只读取当前 History.Records 拥有的有效指针，并在本次调用内转为普通 JavaScript 数据。查询结束后不保存任何原生 record 指针，不 pin 原版记录。缓冲最多 300 条；一次快照最多解析当前列表新后缀中的最后 300 条。`dropped` 统计 JavaScript 缓冲淘汰，`snapshot_truncated` 统计因单次数量上限未读取的条数。二者都不统计原版已经消费、无法看到的记录。

`since` 排除已经观察过的序号；`limit` 范围 1–300，默认 300。`cursor` 是观察器单调递增的序号，属于快照观察编号，不是游戏原生记录 ID。reset、清空或切换对局不会复用旧序号。

用当前 `List<Record>` 的数量与 `_version` 判断是否只有追加：只追加时读取新增后缀；发生清空、移除或列表替换时开启新的 `snapshot_epoch`。这避免把回池后复用的同一指针误认成旧记录。每条记录附 `native_list_index`，表示它在对应快照 epoch 列表中的位置；只在同一条成功快照内讨论可见顺序。模型或 generation 变化时清空旧缓冲，隔离对局证据。

## 原版结构依据

本次核对 B4 ARM64 libil2cpp，SHA-256 `18178b2f35959bc3954378a9778cddd67aab8a7ef22579ea59d736521eec8c91`，结合相同版本 dump.cs 和 script.json。

| 原版结构／方法 | 布局／RVA | 当前用途 |
|---|---|---|
| PvZCards.Engine.History.Records | `List<Record>` 指针 0x18 | 显式读取当前列表 |
| List<Record> | items 0x10、size 0x18、version 0x1C | 只读范围校验与新后缀判断 |
| 托管 Record[] | length 0x18、首元素 0x20 | 只读当前有效元素 |
| PvZCards.Engine.Record | RecordType 0x10、Data 0x18 | 原版记录类型与字段 |
| Record.GetDictionary | 0x224EF30 | 通过现有调用接口读取原版字典 |
| History.GetRecords | 0x224E754 | 反汇编确认其返回 Records 字段；当前不需调用 |
| History.AddRecord(Record) | 0x224E6A8 | 仅保留原版机制调查信息，当前不挂钩 |
| EffectRouter.ProcessEffect | 0x2249E74 | 当前观察器不挂钩 |

History、Record 和 EffectRouter 的命名空间均为 `PvZCards.Engine`。AddRecord 参数是 `PvZCards.Engine.Record`，不是 `PvZCards.Engine.Records.Record`。原版具体结果记录的派生类可位于其他 namespace。

原版 History.AddRecord(Type)（0x224E5F0）和 AddRecord<T> 共享体（0x2384118）先把记录加入 History，随后各系统填字段，所以查询须在原版结算完成后进行。不能在初始 append 时读取未完成字段。

## 记录内容

每条已解析记录包含观察 sequence、generation、时间、实际托管 record_type 和原版 RecordType 数值。字典通过原版 Record.GetDictionary 访问，读取前检查 ContainsKey；只把实际 Int32 或明确列出的原版整数枚举转换为数值，未知对象省略。

主要字段包括：

- source_id、target_id、effect_entity_id、effect_group_id、ability_group_id。
- source_guid、target_guid：读取时实体仍存在且有 Card 组件才提供，否则为 null。
- card_id、card_guid：RecordKey.CardIdData=36 若实际类型为 `PvZCards.Engine.Records.CardIdData`，读取其 EntityId（0x10）与 CardGuid（0x14）。可用于创建后即消灭的实体关联，不依赖它查询时仍在场；同记录存在 key6 时以 CardIdData 的实体 ID 为准。
- trigger_type：RecordKey 29 中原版 Type 的文本；无法读取时仅记录对象类型。
- damage_amount、absolute_health、health_delta、attack_delta。
- current_value、new_base_value、new_buff_delta、card_stat_type。
- amount_incremented、attempted_amount_incremented、available_sun、total_sun。
- is_on_self_play、is_excluded_from_groups，以及实际存在的授予能力类型／数值。

缺失的键保持缺失，不填虚构的 source、group 或动画结果。来源标记为 `explicit-History.Records-snapshot`；`records_created_by_observer` 固定为 0。AI 使用的独立 context／History 不作为当前 live 对局快照来源。

## 技能与动画证据

在合法出牌前查询 cursor，合法出牌及目标选择完成后查询 `records({since:cursor})`，与前后状态一起保存。若一份快照中恰好保留了完整可见链，可按来源、组号和 native_list_index 比较 Start、结果和 End；若记录已消费，必须诚实标注观察缺失，而不能补造原版记录。

| 需求 | 可见时应观察的原版记录与状态 |
|---|---|
| 87 墓碑立即现身 | 原卡 Play／TriggeredAbilityStartRecord、RevealRecord、TriggeredAbilityEndRecord；目标仍存活且 FaceDown 移除 |
| 202 当前生命交换 | 两条目标不同的 SetStatRecord，其 CurrentValue 对应换血前另一方 HP；实际 Health 一致 |
| 106 下回合扣阳光 | 下一回合 SunCountIncrementedRecord 后的 GainSunRecord；尝试量 -3，实际增量可因 0 下限截断 |
| 464 攻击后伤害 | 实际 DamageRecord、来源、目标、数值及状态 |
| 658 攻击后弹射 | 实际 ReturnToHandFromPlayRecord 和手牌／场上状态 |
| 253 攻击英雄后减属性 | 实际 BuffRecord 及状态；未造成伤害的攻击需另用攻击事件证明触发 |

当前默认禁用所有扩展动作的额外 special bookend 包装。合法 PlayTrigger 原有外层 Start/End 保持，由本次原版结算组围绕响应结果自然记录。被动攻击、手动 fixture 与延期任务只追加原生结果；没有本次真实父链时，不借用已完成的 EffectEntity。106 债务结算只有真实 GainSunRecord 也符合设计。

R5 的 202 受伤双方 fixture 曾因额外包装失败：借用旧 PlayTrigger 并重写结果 EffectEntityId／Context，使两条 SetStat 被原版条件／目标验证取消。Start/End 自身可以出现，因此 bookends 不能证明内部技能成功。确切路径见 [卡数据与 History](../02.缓存契约与扩展规则/card-data-and-history.md#额外动画封装的已知失败与默认禁用)。

History 记录存在不证明实际屏幕播放了动画。headless fixture 缺 CardView，只提供规则与可见 History 快照证据；正常渲染对局的 processor 和画面验收仍是另两步。本轮不因观察功能阻塞技能实现，也不恢复悬浮窗。

## 失败记录与当前验收边界

- R6／R7：早期 hook 观察器把 Record 参数 fullname 写错，安装失败；已查明精确命名空间。
- R8：hook 安装通过，但首个 start_fixture 出现原生空地址访问错误。新全局回调会在建局期调用 live／Resources 查找及 DI；这是新增的高风险重入路径。尚无完整 native backtrace，不能断言具体哪条原生指令导致错误。
- 后续候选：彻底移除全部观察器 native hooks，install/status 不再查上下文，仅显式 records 查询当前列表。不能为了观察完整链重新默认启用启动期回调。

重写后已通过 JavaScript 语法检查及本地 mock：安装／状态／reset／dispose 零原生调用、快照字段读取、追加去重、清空与池指针复用、generation 隔离、无上下文降级、300 条上限。没有操作 ADB。真机快照解析与候选稳定性仍由主代理验收；静态及 mock 检查不替代设备证据。
