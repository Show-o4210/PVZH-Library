# 继承静态技能抽样测试覆盖

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/static-test-coverage.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

`tests/verify_mod2_static.py` 包含 8 类可执行用例。主代理 R16 真机完整执行已全部通过：8类、37项检查，全部无 unverified。R17仅将87动画兼容默认开启，profile revision 3不变，最终复验待主代理补充。本次整理仅改文档，没有操作 ADB 或改动测试、运行时、卡包。

## 已核对的真机现状

完整证据见 [R16 result.json](../06.R19实现与验收记录/工程资料索引.md#ref-cafe9d491e00)。R14/R15的单类证据保留如下，最新完整重跑同时覆盖所有类别。

| 用例 | 已有结果与范围 | 原始证据 |
| --- | --- | --- |
| freeze 134/143 | R16 PASS，2项：143 单独自冻仍活着；134 在场时冻结/消灭链收敛 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-17f759685989)、[早期R14](../06.R19实现与验收记录/工程资料索引.md#ref-dad8bf5aa2ad) |
| reflection 316→77 | R16 PASS，3项：11 HP 自伤耗尽，正常死亡阶段后原路线恰一株 77，双方英雄未受伤 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-156ccfb40ede)、[早期R14](../06.R19实现与验收记录/工程资料索引.md#ref-f378ea527c5a) |
| banana472 | R16 PASS，6项：空陆地、边缘、占位、水路反例及合法整轮战斗 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-9f2b666a2425)、[早期R14](../06.R19实现与验收记录/工程资料索引.md#ref-2e4797f2f1a5) |
| copter286 | R16 PASS，3项：真实 900000204 创建先于同实体消灭，原 176 保留，路线可再次占用 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-0df39721d958)、[早期R14](../06.R19实现与验收记录/工程资料索引.md#ref-b91a94c72814) |
| grave252 | R16 PASS，3项：合法87揭其他墓碑不触发252；揭252自身后恰一次重藏可见同伴，并收敛 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-cb6fec8bff9a)、[早期R15](../06.R19实现与验收记录/工程资料索引.md#ref-ef5b275df261) |
| redirect97 | R16 PASS，5项：副本/攻击对照、原生伤害、无副本回退及真实 ExtraAttack 转伤 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-108d6813b459)、[早期R15](../06.R19实现与验收记录/工程资料索引.md#ref-36124b640f28) |
| diver547 | R16 PASS，10项：正常揭墓后三分支，包含严格 Move→Buff(-2/-2)→Discard 与真实离场。R15旧PARTIAL及原因保留在下文 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-489676be124f)、[旧R15](../06.R19实现与验收记录/工程资料索引.md#ref-b3e8ca9ac5b6) |
| coffee209 | R16 PASS，5项：实际受益者含墓碑在锦囊阶段自毁，后登场单位和手牌保留；保留1/恢复1，errors0、活动GC roots0 | [R16](../06.R19实现与验收记录/工程资料索引.md#ref-0b10c78290a3)、[状态记录](../06.R19实现与验收记录/工程资料索引.md#ref-45d21dc8e34a)、[旧R15失败](../06.R19实现与验收记录/工程资料索引.md#ref-0dec8f120622) |

## 配置来源

直接用现有 UnityPy 解读 `assets/mod2_profiles/mod2/card_data_1` 的 `cards` TextAsset 后核对目标定义，没有只依据旧文档猜测 GUID。最初设计测试时的历史包 SHA-256：

`cdf3043e53bd2f8717eec1a294bbb85767ad992faec78094b0613fbd0bf12030`

当前 [manifest](../06.R19实现与验收记录/工程资料索引.md#ref-7e27af4d34ef) 为 `profile_revision=3`，改版 card_data SHA-256 为 `c0bf2d71f7b2ad37a52ee81c1ee4e46d69aaf42cf2c07bc9ff6c7842483a7ce5`；本次 revision 的静态修复仅为 97、547。

| GUID | 当前实际配置 | 测试配角依据 |
| --- | --- | --- |
| 97 | 合法打出在本线 CreateCard(900000203)；自身发出的伤害重定向给 `InSameLaneQuery(OriginEntityType=Self)` 选中的该 GUID，原目标排除该 GUID | 350 是无额外技能的原版 1/1 僵尸 |
| 900000203 | 0/1、Teamup、CreateInFront；继承 `InUnopposedLaneQuery` 持续 +1 攻击 | 无对面时 live attack 应为 1，有对面时为 0，不能一直断言 0 |
| 472 | 1/5；本路线 LaneCombatEnd 自毁；死亡时在相邻空陆地创建自身 | 347 为无额外技能的原版 1/1 植物，适合占位 |
| 286 | 锦囊 PlayTrigger 创建 900000204，目标为空僵尸高地/草地 | 176 是独立原版 6/5、无自毁技能的对照 |
| 900000204 | 6/5；EnterBoardTrigger 对自身 DestroyCard | 不通过需要“召唤后仍在场”的 summon API 直接创建它 |
| 547 | 3/2、**PlaysFaceDown**；原版 RevealEffect 重放 PlayTrigger。revision 3 分开授 Aquatic、移动；自身 MoveTrigger 到水路后 -2/-2 | 344 为原版 1/1 Aquatic 僵尸，适合占满水位 |

此前只检查 Gravestone / RevealTrigger 名称而漏掉 PlaysFaceDown，对 547 “直接明牌打出”的判断不正确，现已纠正。需求及原版模板都是墓碑现身语义。续命测试使用原版 BuffEffect 增加**手牌**生命，合法打出后先观察 FaceDown，再通过正常阶段等待原版 Reveal，不删标记或强行触发。

## 四类新增验收

### redirect97

旧配置的 `SameLaneQuery` 要求候选具有 Lane 组件，只适用于路线实体，无法匹配副本单位。revision 3 仅换为原生 `InSameLaneQuery(OriginEntityType=Self)`，比较父卡与候选单位的 LocationList；不是 DamageEffect.LaneId 缺失导致的假失败，也无需改动运行时转伤逻辑。

1. 合法打出 97，先观察本线唯一 900000203 副本真实在场、1 生命和无对面的 1 攻击。
2. 放入真实 350 对手并加生命，观察副本攻击降为 0；副本通过原版 Buff 增加至 3 生命。
3. 用原版 DamageEffect 让 97 对对手造成 1 点伤害：副本恰好减少 1，原目标、97 和双方英雄不受此点伤害，队列恢复可操作。
4. 原版 DestroyCardEffect 标记已观察到的副本，再通过最多 6 次正常阶段动作，确认该实体真正离开路线、进入弃牌堆或已移除，才让 97 再造成 1 点伤害；原目标实际减少 1，证明无替代目标分支没有吞掉伤害或递归创建。97 预先以原版 Buff 增加生命，避免等待死亡处理期间的正常战斗杀死测试来源。
5. 独立新局合法出牌，使用真实 ExtraAttack 让 1 攻97攻击同线敌人：只有副本承受1点，敌方原目标、父卡和双方英雄保持生命不变。

无目标时回退原伤害并非随意制定的行为：B4 `DamageEffectRedirectorSystem.ProcessEffect` 在 `SelectReplacementEffectEntity` 返回 null 时，从 `0x21B1078` 跳至清理上下文；仅非 null 分支会在 `0x21B10F0` 调 Cancel。脚本以实际生命变化验收这一原版行为，没有重新实现重定向算法。

### banana472

使用合法出牌与原版 DestroyCardEffect 分离死亡技能和正常战斗链，路线 ID、索引、高地/水路均来自当前 `state`：

- 两个相邻陆地空位：观察父卡在场后确实死亡，每个合法邻路出现一株新的 1/5 同 GUID 副本。
- 地图边缘：仅创建一株实际存在的陆地邻居，不越界。
- 两个陆地邻路被 347 占住：父卡实际死亡，无复制，两个原占位实体保持不变。
- 水路邻居为空、其余陆地邻路占满：父卡实际死亡，水路仍不接收非两栖副本。
- 独立新局中合法打出 472，正常推进完整一轮：原父卡死亡、存在新的存活副本，副本只在合法陆地且不重叠占位，TurnCounter 确实增加。

正常战斗会按路线继续触发新副本，因此不硬编码整轮结束时必须两株。强制死亡的隔离分支有精确位置/数量断言，整轮分支证明实际 LaneCombatEnd 链有限收敛；两者共同提供触发证据。当前未额外证明每次死亡的 History 精确计数。

所有 fixture Destroy 分支都经过实际死亡处理 helper。它只用正常 `end_phase` 和必要的原版目标/超级格挡选择推进，最多 6 次阶段动作；在源实体真正离开路线后才检查复制数量、路线与占位对照，不能拿 0 生命或被标记死亡代替已经执行亡语。

### copter286

先放置并观察原版 176，合法打出 286。检查手牌实际被消耗，独立 176 仍存活，目标路能再次成功放置普通 350。后两项是对照与占位验收，**不能代替隐藏副本实际成功创建的证明**。

瞬态链要求 `mod2_history` 读取真实 `CreateCardInLaneRecord`，包含 `card_id` 和 `card_guid=900000204`，来源为本次已打出的 286；再找到同一实体 ID 的 `DestroyCardRecord`，创建在先，消灭在后。记录需属于同一 generation 与 snapshot epoch。可见记录明确顺序相反时失败；记录缺失时标 PARTIAL，不能把空场当作自毁通过。

原生创建记录的 CardIdData 使用 RecordKey **36**，字段为 `EntityId@0x10`、`CardGuid@0x14`；只读 observer 若尚未解码该字段，测试会保留原始快照并解释证据缺口，不猜测 GUID，也不合成 History。

### diver547

旧合并实体在生成结果前就验证水路，此时还未执行 Aquatic 授予；移动后再验证高地/空水位条件又会取消扣属性。revision 3 保留墓碑与原版 Reveal→PlayTrigger 路径，拆成三个实体：高地且有空水位时先单独 GrantAquatic，再单独 MoveCardToLanes；最后由自身 MoveTrigger 在水路扣 -2/-2。移动的次目标另限定僵尸空位，减属性实体不再套用已失效的高地/空水位条件。

三个独立合法打出、正常现身分支：

- 对手牌实际 Buff(+0/+3)，证明 3/5 手牌存在，再合法打出到高地；先确认真实 FaceDown 和未获 Aquatic，再正常现身，选择真实合法水路。最终同一实体在水路、带 Aquatic，恰好 1/3且已明牌。
- 原始 3/2 手牌合法打出到高地；打开 History 后跨正常 Reveal 和正常死亡处理观察，要求最终实体真正离场/Discard。当前检查严格要求同卡、同 generation/epoch 的 `CardMoveRecord`（指定水路）→ `BuffRecord`（来源自身、精确 -2/-2）→ `DiscardFromPlayRecord`，可比较的逆序记录失败，缺任一记录保留 PARTIAL。降属性至零后的自然死亡不要求 DestroyCardRecord。
- 用真实 344 占满所有水路，合法打出 547 到高地并等待正常现身；547 留在高地，仍为 3/2，未获 Aquatic，原水位占用者保持不变。不能只根据初次 FaceDown 时没有动作判断条件阻止成功。

## 执行方式与证据

默认运行只输出计划，不启动设备：

```powershell
python -B tests/verify_mod2_static.py --case redirect97 --case banana472 --case copter286 --case diver547
```

由主代理确认候选安装并冷选 mod2 后显式执行；一类可以单独重跑，也能选择多类或 `full`：

```powershell
python -B tests/verify_mod2_static.py --run --case redirect97 --name r12-static-redirect97
python -B tests/verify_mod2_static.py --run --case banana472 --name r12-static-banana472 --case-timeout 180
python -B tests/verify_mod2_static.py --run --case copter286 --case diver547 --name r12-static-transient
python -B tests/verify_mod2_static.py --run --case full --name r12-static-full --case-timeout 180
```

以上名称只作示例；每次必须使用未存在的新 evidence 名称。证据写入 `evidence/<name>/commands.jsonl`、每类 JSON 和 `result.json`。开始时确认实际 `status.resource_profile == mod2`；每次新建 fixture，继承测试模块错误计数与 pending 标记检查。这里保留温重开用于现有测试框架；若需要冷起隔离，主代理应分别 cold-launch 单类并注明，不把隔离通过等同温重开生命周期通过。

History 仅在 copter286 和 diver547 致死分支开启显式快照，没有注册全局 hook。缺少已被消费者清掉的记录时，模型结果与 History 顺序分别判定。测试为 headless 语义验收，不验证可见美术或音频，也不等同 `render=true` 动画队列验收。

每次 fresh 前默认自然等待 2 秒（`--fixture-delay 0..30`），记录等待起止和旧代数；不催动画或清队列。每个独立 fresh 分支使用 session 原有的有界启动预算，启动完成后另开 host 技能检查预算（默认 120 秒，可选 30–600）。访问异常或原生/host 超时停止后续类别，并要求主代理先 force-stop、冷选 mod2 再恢复；脚本不自行发恢复 ADB、不清账户、不截图、不坐标点击。

### R14 反伤死亡阶段的实机澄清

主代理的 `evidence/r14-static-complete/reflection.json` 已观察到 316 从 11 生命通过自伤链降为 0，但它仍保留 LaneElement；当时立即要求新生 77 的旧断言失败。主代理随后仅发送一条正常 `end_phase`，`evidence/r14-reflection-phase-probe.json` 观察到源进入 DiscardPileElement、77 在原路线出现且生命为 6。两份原证据保持不动。

因此 reflection 测试分开记录“实际耗尽 11 生命”和“原版死亡处理后离场并生出唯一 77”。helper 等待真正离场并观察至少一株新 77，再严格检查唯一性、原路线及双方英雄生命不变；没有伪造死亡、手动补召唤或改 native 技能。更新后的完整用例已在 [R14 重跑](../06.R19实现与验收记录/工程资料索引.md#ref-f378ea527c5a)通过，旧失败与 probe 均保留。

R15 的547旧 PARTIAL只源于测试要求了错误的记录类型。[旧JSONL](../06.R19实现与验收记录/工程资料索引.md#ref-c7706118f305)同一实体24、generation6/epoch1已有移动 seq29→Buff(-2/-2) seq32→Discard seq34；严格新版检查已离线接受这条链，并拒绝缺记录、错身份/路线/属性、跨代/epoch及逆序输入。原报告未改写。

新版严格检查在 [R16真机](../06.R19实现与验收记录/工程资料索引.md#ref-489676be124f)已 PASS：同卡24、generation15/epoch2，指定水路15的移动 seq63→自身Buff(-2/-2) seq66→自然Discard seq68，并观察到实体真实进入 DiscardPileElement。它与其余7类一起组成8类37项完整PASS；该结论是技能语义与指定History链验收，不代表全部93张改动卡或可见美术已逐项验证。
