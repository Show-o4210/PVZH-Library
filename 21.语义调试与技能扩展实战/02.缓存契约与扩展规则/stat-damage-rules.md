# 力量与伤害扩展

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/stat-damage-rules.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

实现文件为 `src/mod2-stat-damage.js`，导出 `install(api)`。仅在 mod2 模式、当前真实对局的实体模型中生效；本代理未操作 ADB。

## 326：无法获得力量

缓存 `card_data` 使用原版 `GrantAbilityEffectDescriptor` 组件，AbilityType=1009，AbilityValue=0。0 是本卡的力量上限，规则由组件决定，不按 GUID 硬编码。

实现分三层：

1. 普通 `BuffEffect` 进入原版值验证前将正 AttackDelta 改为 0，HealthDelta 不变。纯加攻效果因此由原版验证器取消；同时加血的效果仍正常执行。`BuffSystem` 入口提供直接原版调用的兜底。
2. 原版 `SetStatSystem` 和 `StatUtils.ModifyStat` 只调整 Attack 类型的正 Add 或超出上限的 Set；Health、费用及太阳值保持原调用。`ModifiableInt.AddModifier` 仅匹配目标的 AttackValue 对象，清零正 OriginalAmount/AdditiveAmount，覆盖持续光环与延期激活的力量修正，不用删除或手工替换托管 modifier 列表。
3. `ModifiableIntCalculator.CalculateValue`、`Attack.CalculateAttack`、`AttackCalculator.CalculateAttack` 的返回值仅对标记单位的真实 AttackValue 截到上限，覆盖直接设值/复制属性后的原版力量读取。负修正保持原版逻辑。

对象缓存同时检查 EntityModel/generation/NextEntityId、实际实体、Card GUID、Attack 组件与 AttackValue 指针；组件增删、力量效果及对局重置使缓存失效。不会把 Health.MaxHealth、SunCounter 等 ModifiableInt 误当作力量值。

这是力量增益禁用，不是禁攻。原版健康值代替力量的 `AttackOverride` 仍保持原语义。直接读裸 `BaseValue` 内存的额外新代码不属于已覆盖的原版计算 API；AI 独立预测模型不执行此扩展。

## 518：僵尸造成的伤害固定为 1

缓存组件 AbilityType=1010，AbilityValue=1。只有标记实体实际仍是某条路线的 fighter，并且没有原版 `FaceDown` 组件时规则有效；手牌、尚未现身的墓碑、被弹回、已由原版死亡检查移除的实体不提供规则。518 保留原版墓碑，故其全场伤害规则在原版现身处理移除 FaceDown 后才启用。此现身限制仅用于战场伤害来源，不全局改变 326 在手牌或墓碑中的力量限制。同步战斗中死亡移除的边界沿用原版 Lane 成员关系，不提前引入额外死亡判定。

通过反汇编 `EffectSystemBinder.BindDamageEffectSystems` 并解析 `.rela.dyn` 到 `script.json` 的原版泛型方法名，核对顺序如下：

`DamageValueValidation → DamageImmunity → TrickImmunity → EffectEntityMultiplier → Redirector → SourceMultiplier → Armor → MinHealth → HeroBlocking → Deadly → DamageSystem → LoseByHealth`

模块在 `ArmorSystem.ProcessEffect` 的入口调整仍为正的僵尸伤害。此位置位于两类伤害乘算之后、装甲与其他防御之前；已经被免疫取消或变成 0 的伤害不会重新变成 1。装甲、最小生命保护和超级格挡仍可将 1 降为 0 或取消。

来源判定优先使用 `DamageEffect.SourceId` 对应实体的 Owner；来源就是玩家实体时直接比较玩家 ID。若原来源已经不存在/不带 Owner，依次检查原版 PlayerId 与 SpringboardId/Owner。无法可靠归属的伤害保留原行为并记录 `damage-source-unknown`，不假定为僵尸。Owner 判定能覆盖僵尸玩家的单位、技能、锦囊及直接玩家来源。

这是实际 DamageEffect 处理链规则，原版最终 DamageRecord 会记录处理后的真实伤害，未将 1010 传给原版能力图标或 UI。直接绕过效果队列调用 `Health.TakeDamage` 的额外代码不在此覆盖中；当前新技能应继续通过原版 DamageEffect 队列。

## 挂钩与版本保护

参考 1.67.8 ARM64 `libil2cpp.so`（SHA256 开头 18178b2f）。每个挂钩安装前核对 8 字节机器码，另核对伤害绑定函数版本。没有重复挂 `EffectRouter`，避免前一个攻击模块的 Frida trampoline 影响第二个模块的原码校验。

| 原版方法 | RVA |
|---|---|
| EffectValueValidationSystem.ProcessEffect(BuffEffect) | 0x21BC2BC |
| BuffSystem.ProcessEffect | 0x21C9078 |
| SetStatSystem.ProcessEffect | 0x21B8288 |
| StatUtils.ModifyStat | 0x21D3B74 |
| ModifiableInt.AddModifier | 0x2273A10 |
| ModifiableIntCalculator.CalculateValue | 0x224FFF8 |
| Attack.CalculateAttack | 0x22684B0 |
| AttackCalculator.CalculateAttack | 0x21E45CC |
| ArmorSystem.ProcessEffect | 0x21AD834 |
| Entity.AddComponent(Type) | 0x224CB2C |
| Entity.RemoveComponent(Type) | 0x224CEE8 |
| EntityModel.Reset | 0x224E350 |

主运行时需提供 `mod/live/call/component/list/i32/integer/boolean/type/event/activeMode/ownsRule`，可选 generation。无需新的序列化 IL2CPP 类型、非法原版 Grant 枚举、外部托管 List 或全局图标映射。

## 验收要求与状态

`status()` 提供 buff_suppressed、sets_suppressed、modifiers_suppressed、calculations_capped、zombie_damage_fixed、unknown_damage_ownership、errors 和明确覆盖范围。事件前缀为 `mod2-stat-damage-*`，正力量阻止与伤害固定分别记录真实来源、目标、改前/改后数值。error 或来源未知不能当作该案例验收通过。

必须测试：326 普通加攻+加血（0 力量、生命正常增长）、纯加攻、SetStat/CopyStats、持续光环与光环移除、延期增益、手牌增益、变形/回手后的对象重置；普通单位力量不受影响。

518 必须测试：墓碑尚未现身不启用规则，现身后启用；僵尸大力量普通/额外攻击、乘算伤害、锦囊与技能伤害、装甲挡成 0、免伤、最小生命保护和超级格挡；植物伤害保持原量；518 不在场/离场后规则取消；多个 518 不把 1 重复乘算；已取消或原 0 伤害不被复活。切回原版应验证同样伤害与力量的原版结果。

墓碑测试必须从僵尸手牌合法打出 518。原版 CreateCardEffect 的直接召唤会让该卡 face-up：卡模板的 `PlaysFaceDown` 仍在，但没有表示当前墓碑状态的 `FaceDown`，不能用它测试“现身前不生效”。`tests/verify_mod2_stats.py` 的 marked_holder 已改为 give + legal_plays + play，并明确断言牌离开手牌、位于路线且具有 FaceDown；现身继续使用原版阶段推进，保留现身前后、来源、防御与离场伤害断言。

主代理 R14 初次回归已通过三个 326 用例；source518 初次失败发生在上述测试设置断言，尚未检验其伤害规则。这次只修正测试设置，不改变编译技能模块；修正后的完整 stats 回归待新证据记录。

合法墓碑设置的后续 R14 source518 回归已验证：墓碑时僵尸伤害保持 7，现身后单位与英雄来源的伤害为 1，植物伤害仍为 7，0 伤害保持 0。离场测试还需遵守原版死亡时序：单独注入 DestroyCardEffect 可以只添加 MarkedForDeath，目标生命仍为正且 LaneElement 尚在，不能立即把“标记死亡”当作“已离场”。测试的 destroy_and_wait_for_departure 记录标记与路线，每次 settled 后检查真实 lanes，最多推进 6 个正常阶段，只有目标不存在或已无路线时才验证僵尸伤害恢复为 7；不按 MarkedForDeath 或 0 生命跳过仍在路线的实体。修正后的离场及完整回归仍待新证据，保留此前失败报告。

当前完成的是类型/机器码/处理顺序核对与 JavaScript 语法检查。真机逻辑与 History/画面结果以主代理候选 APK 验收证据为准。
