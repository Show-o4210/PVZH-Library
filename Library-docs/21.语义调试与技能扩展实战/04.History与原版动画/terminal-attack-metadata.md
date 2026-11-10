# 终局中断与攻击 metadata（R19）

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/terminal-attack-metadata.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

2026-10-14；只读复核匹配的 1.67.8 ARM64 原生库、当前冻结源码及主代理提供的设备证据。本记录没有修改技能源码、队列或测试结果。

## 实际整局结果

[R19 整局语义审计](../06.R19实现与验收记录/工程资料索引.md#ref-8fe05f7e69d0) 为 PASS：14 次合法出牌、9 次阶段结束，共 23 个实际游戏动作；最终赢家为僵尸玩家 5，植物玩家 0 的生命为 -1。最后一次 `end_phase(player_id=5)` 的[完整命令记录](../06.R19实现与验收记录/工程资料索引.md#ref-1f6e8745f6e4) 返回 `game_over=true`，`blocking_effect=PvZCards.Engine.Effects.LoseEffect`。

审计记录的最终状态：

| 指标 | 实际值 |
|---|---:|
| attack generated / started / completed | 19 / 19 / 18 |
| attack prevented | 1 |
| pending_attacks / pending_markers | 1 / 1 |
| umbrella selections | 2（自身 1，相邻植物 1） |
| umbrella pending_packets / pending_contexts | 0 / 0 |
| runtime temporary_effect_roots | 0 |
| main / attack / stats / umbrella / grave / animation errors | 全部 0 |

原[整局测试结果](../06.R19实现与验收记录/工程资料索引.md#ref-898a6b792046) 仍保留为 FAIL：它在已经进入原生终局后继续要求最后的攻击书签排空。语义审计没有覆盖或篡改这份失败结果，也没有把尚未执行的书签记作 completed。

## 原版 Lose 链与停队列条件

二进制依据为 `D:\Codex\PVZH\dump\libil2cpp.so`，SHA256 `18178B2F35959BC3954378A9778CDDD67AAB8A7EF22579EA59D736521EEC8C91`；类型与虚函数槽由同目录 `dump.cs` 核对。下面均为 RVA，不能直接当作文件偏移。

1. `LoseByHealthSystem.ProcessEffect`（0x21D3038）查找失败玩家，调用 `LossProccessor.ProcessPotentialLoss`（0x21D3124）。后者从原版池取得 `LoseEffect`，在 0x21D31DC 写入失败玩家 ID，随后于 0x21D3260 使用 `EffectCollection` 接口槽 4，在 0x21D329C 调用 `AddToCurrentGroup(Effect[])`。这是当前伤害产生的原生响应效果。
2. `EffectQueue.Shift`（0x224B810）先在 0x224B830 调用 `MergeResponseEffects`，再合并组响应，最后于 0x224B844 进入 `DoShift`。致死伤害的 Lose 响应因此在尚未结算的攻击后书签之前进入实际队列。
3. `LoseEffect` 原版继承 `UnresolvableBlockingEffect`，没有覆盖其解析方法。`Resolve`（0x224B338）直接 `ret`；`IsResolved`（0x224B33C）执行 `mov w0,wzr; ret`，始终返回 false。
4. `EffectCollectionProcessor.ProcessEffects`（0x224C7D0）在 0x224C8F0–0x224C8FC 调用当前效果的 `IsResolved`。0x224C900 的 `tbz w0,#0,0x224C914` 在 false 时直接退出；只有 true 才在 0x224C90C 调用 `CompleteEffect` 并继续下一轮。因此队列停在 Lose，不会再 Shift 到后面的书签。
5. `GameStateUtils.IsGameOver`（0x219F6B4）通过 `EffectCollection` 槽 7 `Peek` 检查队首终局类型。设备最后状态明确报告队首为 Lose，既证明游戏已结束，也解释为什么后书签没有获得 Router 回调。

这条链与最后一次攻击 `started` 已增加、`completed` 未增加、仅剩一个 after marker 一致。它不是技能实现错误或仍在等待正常阶段的未完成攻击。不得强行解析 Lose、清空原生队列、执行攻击后能力或伪造 completed 来满足排空断言。

## 剩余 metadata 与 GC 引用

实际核对 [mod2-attack.js](../06.R19实现与验收记录/工程资料索引.md#ref-ed2bef2d1b14) 的所有长期容器：

- `frames` 的字段为数字、字符串、布尔值，以及这些标量组成的数组。`identity`、damage pointer keys 均为字符串。
- `markers` 以效果指针的字符串为键，值为 `{frame, stage}`；`damageOwners`、`frontDamageOwners` 同样只保存字符串键与 JS frame/控制者 ID。
- 这些 Map 没有调用 `pin`、没有保存 GC handle，也没有持有托管 Entity/Effect/List 的对象引用。JS NativePointer 或其字符串本身不会构成 IL2CPP GC 根。
- 新建书签经原版返回 List 的 `Insert` / `Add` 成功移交后，`scope.transfer` 立即 `releaseEffect`。返回 List 在回调期间的 `retainEffect(result)` 也在 finally 中释放。攻击后能力新建效果同样入队后释放临时根。

所以 `pending_attacks=1` 与 `pending_markers=1` 是未完成身份记录，不能按数量解释成两个托管强根。设备审计另直接证实 `temporary_effect_roots=0`。真正未执行的 after `StateCheckEffect` 仍由原版队列/List 持有，遵循原生终局生命周期。本结论只说明攻击模块没有额外强根；不声称运行时为初始化、类型或其他服务保存的所有既有根都已释放，长期 fixture 根的独立问题见 [warm fixture 后续评估](../05.实测与建局边界/warm-fixture-followup.md)。

## 按局清理与测试断言

攻击模块的 `reset` 清空 `markers`、`damageOwners`、`frontDamageOwners`、`frames`、`wounded`，并清空 `gameKey/currentQueue`。有三条现有清理路径：

- 当前 `EffectQueue.Reset`（0x224C2E0）进入时匹配 `currentQueue`，触发 `reset('effect-queue-reset')`。
- 下一次成功的 `scoped()` 比较实际 GameModel、EntityModel 和 EffectQueue 指针组合；组合改变时，先 `reset('live-model-changed')`，再使用新的真实模型。
- 显式模块 reset 或 dispose 清理全部 JS metadata。原生池 Return 钩子仅清理被返还效果的对应 pointer keys，本身不将一个未经过 after marker 的 frame 计作 completed。

这不是“初始化命令一发出就必然清零”的承诺：运行时初始化会更新 generation 和 live cache，但攻击模块依靠上述队列重置或首次成功的新模型 scope 清理。计数 generated/started/completed 为累计统计，reset 不倒改历史计数。此次单局终局审计没有验证随后旧 Context 销毁或再次建局的生命周期。

测试应分别记录：非终局正常结算并稳定返回阶段时，仍严格要求 `pending_attacks=0`、`pending_markers=0`；终局则先严格确认原生 `IsGameOver`、Lose 队首、胜负和最终生命，再记录未执行书签与临时根/错误数，不要求 Lose 后的队列排空。下一局进入真实新模型后再独立检查 metadata 清理。终局分类只适用于已证实原生 Lose 的路径，不能作为非终局残留的通用豁免。
