# 601 伞叶单次随机承伤

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/umbrella-rules.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

实现为 `src/mod2-umbrella.js`，导出 `install(enhanced) -> {status, reset, dispose}`。只在 mod2 模式、原版 DamageImmunitySystem 的 EntityModel 等于当前缓存对局时启用。缓存卡表使用原版 GrantAbilityEffectDescriptor 的 reserved AbilityType 1011；原版 601 的 Teamup 保留，1011 不送进原版能力图标枚举。

## 语义与伤害顺序

每笔正 DamageEffect 原本指向有效伞叶时，随机候选为自己和左右相邻路线中的每株植物。同线其他植物不加入；不存在、死亡/标记死亡、已离场、FaceDown 和非植物单位不加入。伞叶自身必须未被沉默并持有 1011。邻线植物被沉默仍可承担伤害。候选按实体 ID 排序，使用当前原版 TriggeredEffectTargetChooser.Rng 的 MtRandom.Next(N)，均匀选择单株的原版随机索引方式；每笔只调用一次，不使用 Math.random，也不重建 seed。

选自己保持原目标直接结算；选邻株只修改同一个 DamageEffect.TargetId 与现有 EffectContext.TargetId。不生成新的伤害、取消原伤害或再走一次整个 damage router。SourceId、PlayerId、EffectEntityId、SpringboardId、原 LaneId、EffectData、Tags、伤害量及队列组号保持原样。普通 DamageRecord、受伤/死亡反应继续由原版处理，本模块不伪造 special bookend 或 History。

边界位于 DamageImmunitySystem.ProcessEffect 的 onEnter：原版正伤害验证之后、接收者免伤/锦囊免疫/护甲/MinHealth/死亡处理之前。因此真正被随机选中的接收者得到自身的防御处理。不能在 ArmorSystem 才换目标，因为原版 DamageImmunity 和 TrickImmunity 早已处理。

原调用链为 `DamageValueValidation → DamageImmunity → TrickImmunity → EffectEntityMultiplier → native Redirector → SourceMultiplier → Armor → MinHealth → HeroBlocking → Deadly → DamageSystem`。对于首次原地换目标的那个伤害包，EffectEntityMultiplier 调用期间临时恢复原目标，返回后恢复随机接收者，保留以原目标攻击/生命为条件的原伤害倍率；仅调整两个整数目标字段，不重新运行乘算。SourceMultiplier 继续原位置执行一次，518 的固定 1 伤害规则继续在 source 乘算后、Armor 前生效。选到免伤接收者而被原版提前取消时，不伪造后续倍率或伤害。

## 一次标记与原生复制

一次选择标记只存于 JavaScript Map，值为整数 ID、序号、当前模型键及布尔状态。伞叶 A 选中邻线伞叶 B 后，同包再次进入相关处理不会让 B 再选一次。原版其他卡牌自己的伤害转移能力保留；它们生成的同笔伤害后续包也继承伞叶已经选择的标记。

传播使用原生 `DamageEffect.DeepCopyFrom`，以及 `DamageEffectRedirectorContext.FromOriginalEffect / ToRedirectedEffect`。这限定为真正复制/重定向该 DamageEffect 的路径，不把标记复制到独立的受伤触发技能所新建的伤害。原 redirect 系统调用返回时清理临时 context Map；DamageEffect 和 context 的原版 HandleReturnToPool 清理各自键。当前 generation/context/GameModel/EntityModel 改变时清空全部 Map 与 RNG 缓存。Map 不持有托管引用，不创建额外 Effect 或 GC handle；对象仍由原版队列、创建者和实例池拥有。

不能在 EffectData 写未知 EffectValue：虽然 EffectData.CopyFrom 会逐项复制泛型字典，但匹配 ELF 的 BitSmasher.Write(EffectValue) 在 `0x2166E54` 检查 0–11，越界在 `0x2166ECC` 调用 ProtoWriter.ThrowEnumException；Write(KeyValuePair<EffectValue,int>) 在 `0x211FFEC` 同样检查、`0x2120064` 抛异常。因此本模块完全不写 proposed reserved int key，也不复用已有倍率/tag 字段承载一次标记。

## 精确挂点与接入

绑定版本 1.67.8 ARM64，ELF SHA256 `18178B2F35959BC3954378A9778CDDD67AAB8A7EF22579EA59D736521EEC8C91`。所有下列入口安装前校验原机器码 16 字节；这些地址均不与 attack/stat 模块已经挂载的 Router、InstanceManager.Return、Armor 地址重叠。

| 挂点 | RVA / 参数 |
|---|---|
| DamageImmunitySystem.ProcessEffect | 0x21BFF50；self, DamageEffect, MethodInfo；self.Entities +0x10 |
| EffectEntityDamageMultiplierSystem.ProcessEffect | 0x21BD3E0；self, DamageEffect, MethodInfo；self.MultiplierCalculator +0x10，其 Model +0x10 |
| DamageEffect.DeepCopyFrom | 0x225DBF0；self/destination, source, InstanceManager, MethodInfo |
| DamageEffect.HandleReturnToPool | 0x225DB80；self, InstanceManager, MethodInfo |
| DamageEffectRedirectorSystem.ProcessEffect | 0x21B0F64；self, DamageEffect, MethodInfo；self.EntityModel +0x18 |
| DamageEffectRedirectorContext.FromOriginalEffect | 0x2268DD8；context, original DamageEffect, MethodInfo |
| DamageEffectRedirectorContext.ToRedirectedEffect | 0x2268E28；context, RedirectedDamageEffect, MethodInfo |
| DamageEffectRedirectorContext.HandleReturnToPool | 0x2268E78；context, InstanceManager, MethodInfo |
| MtRandom.Next(Int32) | 0x219B5E0；通过原版 managed 方法调用 |

需要现有 enhanced API：`mod, live, call, resolve, typeObject, type, component, list, getEntity, integer, boolean, i32, activeMode, ownsRule, generation, event`。无新的 runtime API 需求。live 必须是 cache-only；RNG 优先从当前 context 已实例化的 chooser binding.value 获取，必要时 resolve 已配置 singleton，不执行 Unity Resources 全局扫描。

主模块接入后应把 `status()` 暴露为 `mod2_status.umbrella`，现有 reset/dispose 路径调用对应方法。模块只用 attach，不 replace 共享 Router，不改已有伤害对象的托管引用字段。

## 事件与验收

每笔选择发出 `mod2-umbrella-selected`，包括 `rule, sequence, generation, source_id, player_id, original_target_id, selected_target_id, eligible, damage_amount_before_multipliers, effect_group_id, lane_id, one_time_redirect, selected_self`；`rng` 包含 native kind、Next(Int32)、index、upper_exclusive。amount 是倍率/518/护甲前的输入值，实际最终伤害须读原版 DamageRecord 或状态生命差。

status 包含 selections、self_selected、redirected、repeated_packets_skipped、native_copies_marked、rng_calls、effect_multiplier_original_target_windows、errors、pending_packets、pending_contexts。正伤害测试按实际 selected 断言生命差，不硬编码随机目标；双伞叶应只增加一条选择事件与一次 RNG。处理完所有伤害后 pending_packets 应归零，原 redirect 返回后 pending_contexts 应归零。

源级语法检查、九个实际 ELF 签名校验和本地 mock 已通过。mock 覆盖五株候选/同线排除、原版 RNG 一次调用、原元数据不变、原目标倍率窗口、同包与 native copy/context 一次传播、pool/generation 清理、选自己、0 伤害、原版模式与异模型隔离。它们不是设备技能或动画结果。

AI 的独立预测 EntityModel 和绕开 DamageEffect 的直接 Health.TakeDamage 未扩展。MtRandom.Next 保持原版极小 modulo bias 与重放调用计数，不引入额外 rejection sampling。

## R19 实际验证与尚未覆盖

主代理已完成 [R19 伞叶完整结果](../06.R19实现与验收记录/工程资料索引.md#ref-f4dc6c721c73)，九个 case、17 条检查、225 笔伤害（含五笔零伤害）全部 PASS。每笔都检查选择事件、真实候选集合、原 Source/Player、RNG 次数、所有带生命实体的精确 HP 差、errors 未增加及 pending_packets/pending_contexts 归零。结果使用 headless fixture，无点击、截图或缓存临时改写。

覆盖内容：只有自己时承伤；自己与单邻株均实际被选；两个相邻伞叶每笔只选一次；同线植物与相邻僵尸排除；左右各两株植物连同自己共五株全部实际被选；被选接收者的护甲减少 1；被选免伤植物受伤 0；零伤害不产生额外损失；真实 518 墓碑现身后，僵尸来源 MultiplyDamage2 的原始 7 伤害仍最终为 1，接收者护甲可以继续降到 0，零伤害保持 0。这些是实际结算断言，没有把“候选都曾出现”解释成已经做完随机分布统计证明。

独立补充脚本 `tests/verify_mod2_umbrella_interactions.py` 已由主代理实机运行，[R19 交互结果](../06.R19实现与验收记录/工程资料索引.md#ref-ab90c34fdc90) 两个 case、六条检查、96 笔全部 PASS。合计两个套件为 321 笔，其中五笔零伤害；核心套件和交互套件分别保留完整证据。实际补齐的范围如下：

- `native97`：合法 97 与专用副本位于伞叶邻线；伤害来源使用真实 97，才能满足其 TriggerSourceFilter(Self)。每笔伞叶只选择一次；选择自己/97 后，原版 97 仍把伤害转给 900000203，并要求 native_copies_marked / repeated_packets_skipped 增加；选择已经是专用副本时，97 原版 NotCardGuid 过滤不再转移。再给来源原版 MultiplyDamage2，严格检查每笔 2 只变为 4，不因复制重复乘算。
- `edges`：真实左右边路各只有一个相邻路线，远处植物不加入，不发生路线环绕。若边路为水路，先给手牌叶原版 Aquatic11 再合法打出，不绕过地形条件。

以下明确未做实机验收，不计入 PASS：原 target-dependent EffectEntityMultiplier 窗口与沉默控制者。当前 fixture DamageEffect 不允许指定 EffectEntityId/新描述器；缓存卡 164 的伤害 TargetHealthMultiplier 只选僵尸英雄，596/604 的目标倍率用于 Buff，不能合法制造打给植物 601 的目标生命倍率伤害。SilenceEffect 不在允许 fixture API，原 Grant0–18 没有 Silence，当前缓存卡也没有 SilenceEffectDescriptor。未为构造这些测试修改冻结源码或资源。原版隔离仍由主代理最终 regression 单独验证，不能用 mod2 内的成功代替。
