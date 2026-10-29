# PVZH 图书馆

> 一份面向《植物大战僵尸：英雄》（Plants vs. Zombies Heroes，PVZH）Mod 开发者的中文资料库、工具与 Mod 项目入口。

2026-10-29：启动器与手机工作台的当前资料入口更新至 [R48 功能与验收概览](24.启动器工作台与手机编辑/README.md)。包括手动卡牌／积木／组件块、快速与专家模式、资源手动检查、交互媒体、文言文字包和手机界面优化。这里提供自包含文档与筛选摘要；完整 Android 工程、安装包和设备备份仍独立保存，克隆本库不能直接构建 R48。AI成功率、成本和完整对局的未测边界保留。

这里整理了 PVZH 的游戏数据、Unity AssetBundle、卡牌逻辑、本地化、贴图、动画、音频、关卡、底层静态 Patch 及 Mod Base 能力扩展等内容。资料以实际拆包、修改和调试经验为基础，希望帮助后来者少走弯路，也让散落在社区中的经验能够长期保存。

## 从这里开始

- 第一次接触 PVZH Mod：从 [前言](前言.md) 和 [00. 游戏介绍](00.游戏介绍/README.md) 开始。
- 了解当前手机启动器、卡牌工作台和组件编辑：从 [第24章](24.启动器工作台与手机编辑/README.md) 开始；Agent从 [22](agents/22-mobile-workbench-and-release-scope.md) 进入。
- 准备实际修改资源：先阅读 [01. 工具链介绍](01.工具链介绍/README.md)。
- 修改植物／僵尸任务1～200：先读[关卡资料统一索引](09.关卡修改/INDEX.md)，按需展开参数、事件、场景和CN；该入口同时维护已知错误与当前实测状态。
- 使用Agent执行基础改版：从 [Agent工作指南](agents/README.md) 与 [独立基础示例](agents/08-basic-mod-walkthrough.md) 开始，先核对用户原包，再读取本次任务需要的章节。
- 使用语义接口验证卡牌或扩展原版无法表达的技能：阅读 [21.语义调试与技能扩展实战](21.语义调试与技能扩展实战/README.md)，Agent从 [运行时技能工作流](agents/10-runtime-skills-workflow.md) 与 [语义测试与证据](agents/11-semantic-testing-and-evidence.md) 进入。
- 用中文和AI API制作纯原版能力卡牌：阅读[22.自然语言原版制卡](22.自然语言原版制卡/README.md)及[独立制作核心](tools/natural-card-author/README.md)，Agent从[13](agents/13-natural-language-native-cards.md)进入。
- 让AI自主选择资料、分块查询与同任务比较：阅读[第22章08](22.自然语言原版制卡/08.按需资料工具与同任务对照.md)及[本轮摘要](22.自然语言原版制卡/按需资料验收摘要.json)，保留失败、Token开销和原引擎范围。
- 理解新GUID、独立中文与原版美术复用：阅读[23.卡牌身份与资源映射](23.卡牌身份与资源映射/README.md)，Agent从[14](agents/14-card-identity-and-assets.md)进入；R9产品经验与公开工具v1分开。
- 管理多Mod与玩家新卡生命周期：阅读[资源包映射与外国ZIP](20.工程体验跃迁-资源门卫与教程跳过/06.多Mod资源映射与外国ZIP实测.md)、[本地身份与服务器边界](23.卡牌身份与资源映射/05.本地新卡身份与服务器裸GUID边界.md)；Agent从[15](agents/15-multimod-player-lifecycle.md)进入，R9历史与后续产品证据分开。
- 管理全局实验能力、AI许可和冷启动状态：阅读[第21章08](21.语义调试与技能扩展实战/08.实验能力登记与冷启动许可/README.md)，Agent从[16](agents/16-experimental-capabilities-and-launch.md)进入；运行支持与AI固定配方独立登记，完整安全启动尚未实现。
- 只想查某一类内容：直接通过下方目录进入对应章节。

> [!IMPORTANT]
> 修改前请备份游戏原文件与存档。不同游戏版本、Unity 工具版本和设备环境可能存在差异，请尽量一次只改一处并及时验证。

## 工具与 Mod

| 项目 | 位置 | 用途 | 依赖 |
| --- | --- | --- | --- |
| PVZH Card Editor / 幻影引擎 | [tools/card-editor](tools/card-editor/README.md) | 卡牌 JSON、技能逻辑树与 AB 打包 | Python 3.10+、PySide6、UnityPy |
| PVZH Level Editor | [tools/level-editor](tools/level-editor/README.md) | 关卡配置、剧情事件与 AB 打包 | Python 3.10+、PySide6、UnityPy |
| PVZH Audio Tool | [tools/audio-tool](tools/audio-tool/README.md) | Wwise 音频解包、替换与回包 | Python、UnityPy；外部音频工具见项目说明 |
| Local Inventory Mod | [mods/local-inventory](mods/local-inventory/README.md) | 本地卡库合并与 ARM64 静态补丁 | Python、Keystone；独立构建流程 |
| 自然语言原版制卡核心 | [tools/natural-card-author](tools/natural-card-author/README.md) | 中文→plan→原版组件／CN／Bundle；外部API与离线校验 | Python、UnityPy；联网生成时使用自己的DeepSeek API key |

克隆一次即可获取上述五个项目；各项目保留自己的依赖、输入输出目录和入口。第21章是文档与检查摘要，不包含完整调试运行时或游戏APK；第22章提供原版制作核心，仍需自己的原版数据。请先进入对应子目录，再按其 README 安装与运行，例如：

```bash
git clone https://github.com/Show-o4210/PVZH-Library.git
cd PVZH-Library/tools/card-editor
python -m pip install -r requirements.txt
python main.py
```

关卡编辑器同样在 `tools/level-editor/` 内运行 `python main.py`；音频和本地卡库使用各自的流水线或构建脚本。建议按项目建立独立虚拟环境。原00～20章节和资源目录保持原路径，后续经验另在21～24章归档；迁移来源与Git历史说明见 [MIGRATION.md](MIGRATION.md)。

## 内容导航

| 章节 | 内容 |
| --- | --- |
| [00. 游戏介绍](00.游戏介绍/README.md) | 引擎版本、资源目录与入门避坑 |
| [01. 工具链介绍](01.工具链介绍/README.md) | AssetStudio、UABEA、Unity、移动端及社区工具 |
| [02. 卡牌数据说明](02.卡牌数据说明/README.md) | 卡牌 JSON、组件结构、技能逻辑树与复制模板 |
| [03. 本地化说明](03.本地化说明/README.md) | 本地化文件、共享标记、批量翻译与名称同步、文言中文包实战及验收边界 |
| [04. 贴图简单修改](04.贴图简单修改/README.md) | 贴图定位、导出、替换、尺寸与格式 |
| [05. 贴图中级修改](05.贴图中级修改/README.md) | A/B 包、指针重定向、节点插入与异常排查 |
| [06. 动画修改](06.动画修改/README.md) | Unity 2D 动画、动作重定向与实战分析 |
| [07. 音频修改](07.音频修改/README.md) | 音频定位、WEM/SoundBank 替换、BGM 提取编排与动态核对 |
| [08. 加入新组件：视频](08.加入新组件-视频/README.md) | VideoPlayer 注入、PPtr 重绑与网格处理 |
| [09. 关卡修改](09.关卡修改/README.md) | 关卡 JSON、剧情事件及可视化编辑 |
| [10. 卡组与 AI 构筑修改](10.卡组与AI构筑修改/README.md) | 卡组结构、AI 构筑与本地调试 |
| [11. 静态高级实战](11.静态高级实战/README.md) | `libil2cpp.so` 静态 Patch 与本地卡库合并 |
| [12. 静态高级实战 2](12.静态高级实战2/README.md) | Mod Base 能力扩展、Grant 赋甲与 UI 双轨 |
| [13. 贴图资源拼接](13.贴图资源拼接/README.md) | Unity 2D 部件还原、idle 首帧拼接与批量 Python 脚本 |
| [14. 动画资源提取](14.动画资源提取/README.md) | AnimationClip 离线还原、固定画布渲染、MP4/MOV 与批量提取 |
| [15. 动态运行时初探](15.动态运行时初探/README.md) | Frida 动态插桩、IL2CPP 符号映射与双轨 Hook 基础 |
| [16. 免 Root 移动端落地](16.免Root移动端落地/README.md) | Frida Gadget 嵌入、Smali 启动劫持与长期签名规范 |
| [17. Unity 引擎动态交互](17.Unity引擎动态交互/README.md) | Unity 线程安全、UnitySynchronizationContext 调度实战 |
| [18. 现代原生浮窗 UI 混合开发](18.现代原生浮窗UI混合开发/README.md) | 原生浮窗架构、防渲染转圈死锁与高版本滚动条避坑 |
| [19. 良性 Mod 实战：离线卡组分享](19.良性Mod实战-离线卡组分享/README.md) | PVZH1 协议设计、卡牌合规校验与原生持久化实战 |
| [20. 工程体验跃迁：资源门卫与教程跳过](20.工程体验跃迁-资源门卫与教程跳过/README.md) | Pre-Unity资源门卫、全量资源与FTUE、原版／mod2必选切换及交付校验 |
| [21. 语义调试与技能扩展实战](21.语义调试与技能扩展实战/README.md) | 无坐标测试、缓存与Gadget合同、效果所有权、History／动画、R19验收、第四批组合动作、全局实验能力与冷启动许可 |
| [22. 自然语言原版制卡](22.自然语言原版制卡/README.md) | 原版知识索引、AI计划合同、确定性编译、DeepSeek评测与后续UI／hook边界 |
| [23. 卡牌身份与资源映射](23.卡牌身份与资源映射/README.md) | GUID／prefabName／中文Key、Manifest与Bundle内部资产、R9新卡复用原版资源、累计编辑与真机证据 |
| [24. 启动器工作台与手机编辑](24.启动器工作台与手机编辑/README.md) | 截至R48的功能、手工组件块、AI模式边界、资源／媒体／文字包、界面名称与分层验收 |
| [资源](资源/) | 示例文件、索引、旧笔记及实战素材 |
| [Agent工作指南](agents/README.md) | 基础制作、运行时技能工作流、语义测试、证据边界、设备回退与独立基础示例 |

## 适合谁

- 想制作或研究 PVZH Mod 的玩家；
- 需要查询卡牌、关卡和本地化数据结构的开发者；
- 正在研究 Unity AssetBundle、UABEA 或 Wwise 修改流程的人；
- 希望了解 PVZH 静态 Patch 与资源注入实践的进阶 Modder。

## 使用说明

本仓库以技术研究、学习交流和资料保存为目的，与 EA、PopCap 或《植物大战僵尸：英雄》官方无关。仓库中的游戏名称、角色和相关素材，其权利归原权利人所有。请勿将资料用于破坏游戏服务、影响他人体验或其他违规用途。

如果文档中的步骤与你的环境不一致，优先确认游戏版本、Unity 版本、工具版本和目标文件是否匹配。欢迎通过 Issue 或 Pull Request 补充资料、修正文档。

## 许可协议

本仓库原资料库部分的**原创文档与整理结构**采用  
[知识共享 署名—非商业性使用—相同方式共享 4.0 国际 (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 许可。

| 文件 | 说明 |
| --- | --- |
| [LICENSES.md](LICENSES.md) | 多许可证目录边界；四个导入项目保留 MIT 许可与原作者声明 |
| [LICENSE](LICENSE) | 正式许可声明（CC BY-NC-SA 4.0） |
| [许可与使用条款.md](许可与使用条款.md) | **中文详细条款**（署名方式、非商业边界、禁止换皮与收款码顶替等） |

**你可以**：学习自用、非商业转载与分享、在署名并采用相同许可的前提下修改后再发布。  
**你必须**：保留作者署名（休切尔 / Show-o4210）、作品名「PVZH 图书馆」、官方仓库链接与许可声明。  
**你不可以**：删除署名后整包换皮、冒充原作者、将本文档作为付费主体出售，或去掉来源后单独挂自己的收款码夺走署名成果。

`tools/card-editor/`、`tools/level-editor/`、`tools/audio-tool/` 和 `mods/local-inventory/` 中的项目原创内容分别采用各目录内的 MIT 许可；上面的非商业与相同方式共享条件仅适用于资料库 CC 许可覆盖的内容。

游戏官方资源、导出数据与第三方工具**不在**本许可授权范围内。完整约定以 [许可与使用条款.md](许可与使用条款.md) 为准。

```text
作者：休切尔（Show-o4210）
许可：CC BY-NC-SA 4.0
官方仓库：https://github.com/Show-o4210/PVZH-Library
主页：https://github.com/Show-o4210
```

## 支持作者

整理、验证和编写这些内容花费了大量时间。如果这座小小的图书馆帮到了你，欢迎请作者喝杯饮料。赞赏完全自愿，感谢你的支持！

<p align="center">
  <img src="support.png" alt="作者赞赏码" width="360">
</p>

> 上图赞赏渠道仅属于原作者。第三方镜像若展示收款信息，必须同时清晰标注原作者与官方仓库，不得冒充原作者。详见 [许可与使用条款.md](许可与使用条款.md)。

---

愿每一次踩坑，最后都能变成后来者脚下的一块路标。

<!-- R25-library:pharaoh-transform -->
2026-10-24追加：[全场变形保留当前攻血与原生子效果](21.语义调试与技能扩展实战/10.全场变形保留当前攻血与原生子效果/README.md)及[Agent21](agents/21-pharaoh-transform-and-child-effects.md)整理Android R25法老案例；私有1026、NotCheats与连续Buff边界、221条真实引擎检查、历史失败/未测和视听限制分别保存。

<!-- R26-library:configurable-new-cards -->
2026-10-24追加：[可配置新卡获取与手机Mod列表](23.卡牌身份与资源映射/06.可配置新卡获取与手机Mod列表.md)与[Agent15后续](agents/15-multimod-player-lifecycle.md#r26-可配置获取后续)说明获取/身份保护分离、原生库存持久化、Silver启动修复、封面及冷启动证据；历史失败和最终结果分别留存。

<!-- R28-library:original-resource-names -->
2026-10-25追加：[原版资源名校验与自动获取启动故障](23.卡牌身份与资源映射/07.原版资源名校验与自动获取启动故障.md)说明合法空格/单引号、650定义分类、可信模板白名单和补卡Hook初始化前置；主机、实际APK与设备拥有权／冷重启状态分别记录。

<!-- R29-library:mod-runtime-and-continuity -->
2026-10-25 R29范围归档：[Mod内能力与启动健康恢复](21.语义调试与技能扩展实战/11.Mod内能力与启动健康恢复/README.md)和[本地新卡连续性与同账户保护](23.卡牌身份与资源映射/08.本地新卡连续性与同账户保护.md)已补RC4真实AI制卡／继续修改／拒绝／确认关卡后采纳、900002普通模板获取及正式加载。自动重启受Android37限制，手动图标恢复通过；当前对局按用户要求跳过，实际新卡与精确下回合结算为USER_SKIPPED，不能称全技能稳定或官方同步已验。RC2连续性观察保留独立版本边界。
