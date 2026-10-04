# PVZH 图书馆

> 一份面向《植物大战僵尸：英雄》（Plants vs. Zombies Heroes，PVZH）Mod 开发者的中文资料库、工具与 Mod 项目入口。

这里整理了 PVZH 的游戏数据、Unity AssetBundle、卡牌逻辑、本地化、贴图、动画、音频、关卡、底层静态 Patch 及 Mod Base 能力扩展等内容。资料以实际拆包、修改和调试经验为基础，希望帮助后来者少走弯路，也让散落在社区中的经验能够长期保存。

## 从这里开始

- 第一次接触 PVZH Mod：从 [前言](前言.md) 和 [00. 游戏介绍](00.游戏介绍/README.md) 开始。
- 准备实际修改资源：先阅读 [01. 工具链介绍](01.工具链介绍/README.md)。
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

克隆一次即可获取所有项目；各项目保留自己的依赖、输入输出目录和入口。请先进入对应子目录，再按其 README 安装与运行，例如：

```bash
git clone https://github.com/Show-o4210/PVZH-Library.git
cd PVZH-Library/tools/card-editor
python -m pip install -r requirements.txt
python main.py
```

关卡编辑器同样在 `tools/level-editor/` 内运行 `python main.py`；音频和本地卡库使用各自的流水线或构建脚本。建议按项目建立独立虚拟环境。原 00～20 章节和资源目录保持原路径，迁移来源与 Git 历史说明见 [MIGRATION.md](MIGRATION.md)。

## 内容导航

| 章节 | 内容 |
| --- | --- |
| [00. 游戏介绍](00.游戏介绍/README.md) | 引擎版本、资源目录与入门避坑 |
| [01. 工具链介绍](01.工具链介绍/README.md) | AssetStudio、UABEA、Unity、移动端及社区工具 |
| [02. 卡牌数据说明](02.卡牌数据说明/README.md) | 卡牌 JSON、组件结构、技能逻辑树与复制模板 |
| [03. 本地化说明](03.本地化说明/README.md) | 本地化文件、键名规范及富文本标记 |
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
| [20. 工程体验跃迁：资源门卫与教程跳过](20.工程体验跃迁-资源门卫与教程跳过/README.md) | Pre-Unity 资源门卫架构、2880个Bundle秒解与FTUE跳过 |
| [资源](资源/) | 示例文件、索引、旧笔记及实战素材 |

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
