# 翻译修正交接包 / Translation correction handoff

本目录把已发现的翻译问题、建议文案和版本证据集中存放，供完整开发工程拉取后由维护者或 agent 复核、接入。**本次仅新增交接资料和导航，不修改任何生效词表，不构建 APK。**

## 文件

- [ISSUES.md](ISSUES.md)：原有 39 条记录的索引及未定论项；另新增 ThePrimalPea 的 94 条中英越贡献记录。
- [corrections.json](corrections.json)：逐条 JSON 键、原文、中文参考、建议文案、来源提交、R64 对照和应用状态。它是交接数据，不是可直接加载的翻译词表。
- [CONTRIBUTORS.md](CONTRIBUTORS.md)：ThePrimalPea 的贡献署名、94 条 R64 修订及 18 个文档提交的来源与接入边界。
- [contributor-commits.json](contributor-commits.json)：23 个贡献提交的完整机器清单。
- 本 README：后续接入步骤与验收边界。

## 版本与状态

整理基线：[`1c862f1`](https://github.com/Show-o4210/PvZH-AML/commit/1c862f164328b232da9ca7d74f52b7475b1f39aa)，2026-11-14。每个条目保留完整来源 SHA。

1. **18 条已提交社区修正**：来自 [`e50a7bb`](https://github.com/Show-o4210/PvZH-AML/commit/e50a7bbe82790cb269681444f0b0e173a63ad23a)、[`dcf1bb2`](https://github.com/Show-o4210/PvZH-AML/commit/dcf1bb2acc1761a47d9ef5462d0111c65af133bf)、[`8a66ff4`](https://github.com/Show-o4210/PvZH-AML/commit/8a66ff429da1d13a168ca9ea73904d20f2733d85)。这些修改已在 R44 社区稿及对应历史词表，**不等于实际开发工程或 APK 已采纳**。
2. **21 条条件说明建议**：本次重新比对 R44/R64 与中文词表重建，主要涉及丢失的比较符号、卡牌编号、统计数量、标识符与语义。它们仅在本目录，不修改原词表。中文是翻译参照，不替代原版数据与当前实现。越南语文风仍建议由熟练贡献者审校。
3. 旧条件批次曾记录为 4 文件、22 个值，但其完整未提交 diff 在本工作区不可得；这里没有假称恢复了那个精确补丁。重建范围与旧批次不同，以逐条证据为准。
4. R64 最初发布快照固定为 [`3b67408`](https://github.com/Show-o4210/PvZH-AML/commit/3b674087229d2547087d4aa6726aab80c49126b1)。后续 main 改过 R64 悬浮工具文案，所以不能把当前整目录自动等同于原候选 APK 的逐字快照。本包分别记录原始 R64 与整理时 R64 值。
5. 本库不是完整 Android 工程。未在这里找到并验证当前构建的真实翻译源；**实际加载、构建产物及设备显示均未验证**。不得修改历史快照以伪装已经进入构建。

## 贡献补充

本包现共 **133 条**记录。新增 94 条由 **ThePrimalPea** 提交的中英越词条修订，已存在于当前 R64 仓库词表，是否进入实际构建仍待核验。详见[贡献来源与状态](CONTRIBUTORS.md)。其中协议前缀 `PVZH1` → `PvZH1` 单独标为需复核，不自动采纳。新增记录是贡献归档，不将所有风格调整都称作错误，也不重放已生效的仓库修改。

## 给后续 agent 的执行说明

收到维护者的接入请求后：

1. 先阅读实际工作区根目录及目标目录的 `AGENTS.md`，检查工作树，保留既有修改。本交接包不授予设备、账户、模型 API、提交、推送或发布权限。
2. 确认目标版本、当前分支和构建输入。追踪翻译加载器、生成脚本、语言回退及打包链路，找到真正生效的 source-of-truth。不要仅凭目录叫 R44/R64 或 key 相同就替换。
3. 读 `corrections.json`。按 locale + key 在真实源定位；逐项比较：
   - 当前值已等于建议值：记录“已存在”，跳过。
   - 当前值与记录的旧值、R64 值一致：核对中文、当前实现与原版数据后做最小修改。
   - 当前值已改变、键消失或语义变化：标为冲突，保留新内容，不强行覆盖。
   - 条件统计、卡号和比较运算必须针对目标版本重新核验；不能把旧版数量当作新版永恒真值。
4. 只改用户当前授权的可编辑源。若词表是生成物，修改生成源再重生成；不要批量复制历史 `editor.json` 覆盖新版完整文件。R44 社区稿里的好翻译是移植依据，不是整文件回滚目标。
5. 不改变 JSON 键、GUID、枚举、技术标识符、占位符、转义和游戏富文本标记。涉及卡名，使用目标版本已确认的语言卡名表；不依据机器翻译推断卡牌身份。
6. 执行格式/JSON 解析、重复键检查、键集合与占位符/标记比较；按工程要求运行生成器和相关检查。diff 只应包含目标文案及必要生成物。检查历史稿和当前稿是否需要同步，但不默认重写冻结证据。
7. 构建后核验打包资源／生成代码／DEX 中目标词条，随后在英文和越南文界面实际打开对应积木帮助，检查否定词、≤/≥、卡号与换行。仅字符串存在不证明 UI 实际加载；只打开首页不证明帮助文本正确。
8. 输出逐条结果：`applied / already-present / conflict / deferred`、实际目标文件、采纳提交、目标构建标识，以及“静态 / 构建产物 / 设备 UI”各自通过、失败或未执行的范围。存在未测项时不要宣称全部生效。

可直接给 agent 的任务描述：

> 阅读 `pvzh-launcher/translation-fixes/README.md` 和 `corrections.json`。在当前完整工程定位实际生效的本地化源，按键逐条复核建议，只应用与当前实现一致的修正，保护已有修改和冻结历史快照。先报告冲突，不整文件覆盖；完成工程检查、构建内容核验和已授权的界面验证，逐条记录采纳状态及未测边界。提交、推送和发布仍按本轮授权与仓库规则执行。

## English summary

This folder is a reviewable handoff, not a runtime language pack. It contains 18 corrections reconstructed from three already-published R44 community commits, plus 21 newly reconstructed condition-help proposals. The latter are not claimed to be the exact former uncommitted 22-value batch. Each record carries its source key, old/proposed text, Chinese reference and pinned R64 comparison. Locate the real build input, review conflicts and semantics, preserve placeholders/identifiers, and verify static checks, packaged output and actual UI separately before claiming adoption. Do not bulk-overwrite catalogs or rewrite historical provenance snapshots.

Contributor addendum: 94 R64 catalog revisions by **ThePrimalPea** are now included with attribution and exact commit provenance (133 records total). They already exist in repository catalogs, not necessarily in an APK. Eighteen documentation commits are indexed separately. One protocol-prefix case change is explicitly flagged for review before any adoption.
