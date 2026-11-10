# 咖啡僵尸墓碑保留修复

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/coffee-grave-preserve.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

此修复只保留 mod2 的咖啡自毁义务 `900000302`。不修改缓存卡牌表，不添加新触发事件或人为 History 记录。原版模式、其他授予技能、攻击和生命重置继续走原版路径。

## 原因与原生证据

`mod2/request-batch3.txt` 第 9 行及第 28 行确认：咖啡打出时得到增益的僵尸，在锦囊阶段开始时被消灭。旧说明另外明确，藏进墓碑且仍在场的接收者应被消灭，弹回手牌的接收者不在消灭范围内。

R14 的 `evidence/r14-static-rest/coffee.json`、`commands.jsonl` 显示：咖啡正常打出后存在三个 `SurprisePhaseStartTrigger` 实体。弹回一个接收者、另一个接收者被 346 藏进墓碑后，对应授予实体逐个消失；剩余 `GrantedTriggeredAbilities` / `EffectEntities` 组件名称不能证明内部技能仍存在。正常揭墓后，墓碑接收者未自毁。该失败与 R15 首次保护失败均保留；修正后的 R16 真机用例已通过，见下文。

静态证据来自与 B4 相同的 `D:/Codex/PVZH/dump/dump.cs`、`script.json` 和 `libil2cpp.so`：

| 原生位置 | 作用 |
| --- | --- |
| `GravestoneMaker.TurnCardIntoGravestone` / `0x21BEBA8` | 先重置永久属性和授予能力，再添加 FaceDown、写原版墓碑记录。其 `Model@0x10` 用于当前对局归属核对。 |
| `CardResetter.RemovePermanentComponents` / `0x21DE2B0` | 调用授予能力重置器，GTA 重置器字段在 `0x38`。 |
| `GrantableTriggeredAbilityResetter.Reset` / `0x21D60BC` | 获取 GTA，进入 `RemoveGrantedAbilities` / `0x21D6130`。 |
| `AbilityCounter.ClearCount` / `0x2269584` | 将 `Count@0x14` 清零。 |
| `AbilityCounter.IsActive` / `0x2269690` | `IsPersistent@0x28 || Count > 0`。 |
| `RemoveAllEffectEntities` / `0x21D6344` | 移除不再 active 的 counter 所属真实授予实体。 |
| `GrantedTriggeredAbilities.RemoveTemporaryCounters` / `0x2269E9C` | 删除非 persistent counter，并归还实例池。 |

`AbilityCounter` 的 `Guid@0x10`、`EntityIds@0x18`、`IsPersistent@0x28` 及 GTA 的 `Counters@0x10` 均来自实际 dump。Effect/Descriptor 没有可序列化的 Persistent 字段；普通授予固定调用 `GrantAbility` / `0x2269740`。不存在可通过添加 JSON bool 完成的持久化。

## 修复与接入

`src/mod2-grave-preserve.js` 导出 `install(api) -> {status(), reset(), dispose()}`。应传入 `mod2-skills.js` 已有的 `enhanced` API，以获得经过 profile 校验的 `activeMode` 和 cache-only `live`。例如父模块自行接入：

```js
const gravePreserve=require('./mod2-grave-preserve').install(enhanced);
// 在主 status() 中加入 grave_preserve:gravePreserve.status()
// 在主 reset()/dispose() 中调用同名方法。
```

安装同时验证方法 metadata 首指针等于 `base + 0x21BEBA8` 和入口八字节 `fe0f1df8f65701a9`。安装不获取当前对局，不进行 Unity 全局对象扫描。原生 callback 只使用已有当前对局缓存，并确认 Maker 的 Model 和 card 实例均属于当前 EntityModel，排除 AI 模型。

进入墓碑转换时，保存该 counter 的 Count 与 Persistent，临时设置 Persistent=true。原版重置依然清 Count，但 IsActive 保持 true，因此保留原有技能实体及 counter。原生函数返回后恢复 Count 和原始 Persistent。重复嵌套调用只保存一次，最外层返回时才恢复。

每次调用直接通过已存在的 `il2cpp_gchandle_new/free` 导出建立、释放局部根：entity 与 counter 均 pinned=true。GTA 由 entity 的原生组件引用拥有，counter 由 GTA 的原生列表拥有；本模块没有修改任何 C# 引用字段。GC 根不能阻止实例池归还，因此恢复前再次确认 counter 的 GUID、类型和原 GTA 列表归属，防止写入已被重置或复用的对象。进入失败会回滚已经保护的项，正常退出逐项恢复并释放根。dispose 若遇到尚未返回的调用，先禁用新保护，待最后一个调用退出后拆钩。

仅在该墓碑转换方法内暂时改变 Persistent。没有在普通 Grant 时永久化，也没有截断 ReturnToHand 原生重置，所以弹回手牌仍清掉临时自毁能力。原版阶段顺序为植物出牌结束 → 揭墓碑 → 锦囊开始，不添加 `RevealPhaseEndTrigger`。

## 验收用例

1. mod2 同场给三个僵尸施放合法咖啡：留一个在场；用合法 346 藏起一个；另一个弹回手牌。墓碑转换事件应有一组 `preserved/restored`，状态中的 active roots 和 protected counters 应回到 0。
2. 墓碑中的接收者仍保留真实 `900000302` 授予实体；原版正常揭墓后进入锦囊，两名仍在场的接收者都通过原版 DestroyCardEffect 自毁。手牌接收者仍在手牌。
3. 手中接收者在截止阶段前重新合法打出：弹回时技能已清除，重新打出不会复活旧咖啡义务。若它再次获得新咖啡增益，则只按这次新授予处理。
4. 给单个接收者多次咖啡、连续藏墓，或重复进入同一墓碑转换：不会复制授予实体、永久设置 Persistent、泄漏 GC 根或新增重复销毁。
5. 原版 profile 和没有该 counter 的墓碑转换均无保护事件；其他 stats/buffs/GTA 继续原版重置。

本地语法检查和 10 项 mock 回归通过，覆盖保护范围、还原和根释放逻辑。R15 第一次真机调用在建立 GC 根时报告 `expected an integer`，未发生保护写入；已把 native bool 参数改为整数 `1`（签名仍为 `bool`，与底座 Frida FFI 用法一致），mock 也增加了这个 ABI 限制。

## R16 已有设备证据

[R16 咖啡用例](../06.R19实现与验收记录/工程资料索引.md#ref-0b10c78290a3) **5 项全部 PASS**：两个已知接收者真实获得 +1/+1 与狂热；后登场的僵尸没有旧咖啡增益；一个接收者弹回手牌；另一个接收者由合法346藏进墓碑；正常阶段推进至锦囊后，仍在场的已知接收者被消灭，晚登场单位及手牌接收者保留。

[原始命令及状态](../06.R19实现与验收记录/工程资料索引.md#ref-45d21dc8e34a)中，咖啡 case 的 grave_preserve 从保护0次变为 `preserved=1, restored=1, errors=0`，结尾 `active_invocations=0, protected_counters=0, active_gc_roots=0`。它同时验证了实际 native 保护、生效后的技能结果和退出释放，不能再称为仅本地 mock。

本次 [继承静态完整套件](../06.R19实现与验收记录/工程资料索引.md#ref-cafe9d491e00) 为 **8 case / 37 checks 全 PASS**，其中咖啡5项、547严格原版移动→减益→自然Discard链10项均通过。这些用例采用逻辑 / 原生记录验收，不表示咖啡全部专属动画或所有组合均已完成。

上列第3项“弹回后再次打出”以及多次咖啡、嵌套墓碑转换、原版模式与其他授予能力的全部真机交互矩阵尚未独立跑完；本地 mock 覆盖其中保护范围和嵌套恢复机制。R16 当前证据已经确认本轮发现的“同一接收者藏墓导致自毁义务消失”得到修复。
