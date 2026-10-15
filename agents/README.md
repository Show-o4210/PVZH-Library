# PVZH Agent 工作指南（按任务逐步扩展）

本目录为执行任务的Agent提供最短资料路径、已核对字段和验证要求。基础覆盖属性、原版技能复用／重写、场景规则、单关、中文和回包部署；2026-10-15新增运行时技能契约与语义测试入口。基础示例仍自包含；高级指南依据R19案例，完整测试运行时不随库提供。

## 阅读顺序

初次接手先读 [08独立基础示例](08-basic-mod-walkthrough.md) 和 [09维护与证据](09-maintenance-and-evidence.md)，再按任务选择：

1. [01-bundles-and-scope.md](01-bundles-and-scope.md)：输入定位、UnityPy 读写、差异校验。
2. [02-fighters-and-board-abilities.md](02-fighters-and-board-abilities.md)：冬青技能移植、双方阵营、三头花生式生命值覆盖。
3. [03-levels-and-localization.md](03-levels-and-localization.md)：僵尸任务 200、真实对话结构、CSV 增量编辑。
4. [04-device-verification.md](04-device-verification.md)：ADB 部署、回退和实测证据。
5. [05-smarty-card-remix.md](05-smarty-card-remix.md)：七张聪明卡改版、冻结状态筛选、消灭来源、双重打击结构、无法精确表达的效果与启动验收。
6. [06-large-card-remix.md](06-large-card-remix.md)：74项多职业追加、进化与友方伤害、授予定时自毁、召唤副本、路线附加目标、伤害重定向、延迟资源修正陷阱、版本备份与启动验收。
7. [07-hearty-sneaky-remix.md](07-hearty-sneaky-remix.md)：20项健壮与狡猾追加、增益接收者阶段自毁、负资源、高地互斥、墓碑现身事件、换血备选、召唤副本、前版保留与启动证据。
8. [08-basic-mod-walkthrough.md](08-basic-mod-walkthrough.md)：用户原包→单卡属性与技能→单关→中文→静态验证；[可执行示例](examples/basic_mod.py)不需要本机mod1/mod2脚本。
9. [09-maintenance-and-evidence.md](09-maintenance-and-evidence.md)：当前案例统计、资料优先级、维护与证据边界；[2026-10-11检查记录](verification-2026-10-11.md)。
10. [10-runtime-skills-workflow.md](10-runtime-skills-workflow.md)：JSON与Gadget实现层选择、私有规则契约、效果池与引用ABI、窄动画兼容。
11. [11-semantic-testing-and-evidence.md](11-semantic-testing-and-evidence.md)：实际profile、无坐标出牌／抽卡／召唤、合法流程、原生异常停止、终局与验收分层。

只做基础改版时不必通读高级章节。处理新技能或已有语义接口时先读10／11，再按链接查[第21章](../21.语义调试与技能扩展实战/README.md)；资源切换查[第20章05](../20.工程体验跃迁-资源门卫与教程跳过/05.必选资源切换实战/README.md)。本轮归档校验见[2026-10-15检查记录](verification-2026-10-15.md)。

## 证据范围

2026-10-08 针对用户提供的 `card_data_1`、`data_assets_29`、`cn_8` 解包核对，UnityPy 1.25.0。相同文件名不保证版本相同；换一批输入必须重新读取并记录 SHA-256。

| 输入 | SHA-256 |
|---|---|
| card_data_1 | e2579da5636125f82b86a85fba829459810b4ca41b1980528771b80da9c80201 |
| data_assets_29 | 37fd5f5af67dda86664b76e9bfefe1878b281cf8a1af05afec7a4282bf7b3007 |
| cn_8 | 950fc91396daf74f0a8e93b78d57662b8580818e8ffa38f5f74838a7ceed2bd7 |

mod1与mod2是用户工作区中的交付工程，不是本仓库依赖。[examples/basic_mod.py](examples/basic_mod.py)提供仓库内独立入口；其他章节中的工程路径只用于标识当时的证据位置。

R19证据另绑定其APK、脚本、Rev4资源和ARM64库，不沿用上表输入指纹。原mod2第三版的93张变更与18条舍弃是历史统计；R19追加运行时后为99张原卡变更、17张扩展卡／14类规则，音频仍排除。不要把新结果回写成旧第三版已逐项战斗通过。
