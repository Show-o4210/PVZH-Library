# 自然语言原版制卡核心 v1

从中文需求生成可检查的plan，再由程序编译为原版卡牌组件与中文，并可回包`card_data_1`和`cn_8`。模型不写引擎类型、不执行代码；无需本项目的Gadget扩展，也不连接ADB。

这是一版有明确范围的制作后端，还不是面向所有玩家的完整编辑器。当前编辑**可用单位卡**，支持原版能力组合及同阵营原版单位的完整能力包复制。独立锦囊／环境本体、全部条件查询、移动链、多个手动动作共享目标等尚未开放；不能把这些工具限制说成原版做不到。

copy_native原样保留技能树中的字面GUID引用，不自动把“来源同名卡”改成底卡。报告标明来源引用数量；415来源静态比较通过证明组件包复制保真，不证明所有隐含同名／种族逻辑、循环或动画移植均符合预期。面向玩家的可发布配方仍需要游戏验证白名单。

## 准备

需要Python和已验证的UnityPy 1.25.0；API使用Python标准库，无需额外SDK。仅在现有环境缺少兼容依赖时安装`requirements.txt`。输入目录由用户提供原版`card_data_1`、`cn_8`，库不附带完整游戏数据。

当前登记PVZH 1.67.8／11056的650定义、162种序列化类型。按**规范化卡表内容**锁版本，不要求压缩字节完全一致；未知卡表会拒绝，不能删检查盲用。来源见[native-baselines.json](native-baselines.json)。

## 使用

在本目录执行，路径替换为本次自己的输入和全新输出位置：

```powershell
python cli.py author --input 'C:/work/original' --output 'C:/work/card-v1' --pack --request '把小豆丁改成2费3攻4血，替换原技能，打出时对僵尸英雄造成3点伤害。'
```

程序使用当前进程的`DEEPSEEK_API_KEY`；未配置时通过隐藏输入询问。不要把真实key写进命令行、仓库或提示词。最多两次生成：ready计划不合法时，把真实编译器错误反馈一次；明确clarify／unsupported时停止，不强制模型编造支持。

离线检查或人工准备plan：

```powershell
python cli.py prepare --input 'C:/work/original' --output 'C:/work/prompt-v1' --request '小豆丁打出时冻结相邻路线的所有僵尸，替换原能力。'
python cli.py compile --input 'C:/work/original' --plan examples/plant-damage.plan.json --output 'C:/work/offline-card-v1' --pack
python cli.py inspect --input 'C:/work/original'
```

`prepare`只输出可复查的模型上下文，不发送请求。`inspect`输出从本次输入提取的卡索引、能力集合和来源。默认模型`deepseek-flash`，客户端固定请求DeepSeek官方HTTPS接口，模型名称可由`--model`选择。模型支持与调用方式按2026-10-18核对的[官方入口](https://api-docs.deepseek.com/)和[JSON Output](https://api-docs.deepseek.com/guides/json_mode/)实现；JSON格式正确不代表游戏技能正确。

## 输出

- `plan.json`：模型理解的需求，可在写入前提供给UI审核。
- `card.patch.json`：仅包含目标GUID的原版组件树，适合后续项目／hook适配层。
- `cards.after.json`、`cn.after.csv`：独立候选完整源内容。
- `build-report.json`：输入指纹、改动范围、实际中文、每种组件的原版来源GUID、回包对象及未测状态。
- `--pack`时增加两个经过完整对象比较和TextAsset回读的Bundle；内容没变的Bundle直接保持原字节。
- API使用记录只保存模型、请求ID、token数和完成原因，没有认证头或key。

**每次从原包新建一个单卡实验。**不同输出不能轮流部署后假定累计；后续多卡项目应合并`card.patch.json`并维护独立当前状态、中文与版本记录。现有输出目录会拒绝覆盖。只有完整构建报告为PASS才是可用候选；失败时遗留的中间源文件不能当作完成包。

## 合同与验证

[knowledge.md](knowledge.md)是给模型的简明合同，[plan.schema.json](plan.schema.json)供UI或API做形状校验。最终判定仍在`core.py`，包括同阵营、目标／动作配对、引用存在、递归组件唯一性、原版枚举、属性显示同步、非目标卡／中文不变。规则1001及以上会被拒绝。

API集成可直接导入`NativeCatalog`、`planner.messages/generate`、`write_card`，不需要运行shell。完整方法、能力边界与评测见[第22章](../../22.自然语言原版制卡/README.md)。

```powershell
$env:PVZH_NATIVE_INPUT='C:/work/original'
python -m unittest discover -s tests -v
```

测试没有原包时会明确SKIP需要原包的部分。项目内临时目录继承正常ACL，避免Windows受限令牌与Python 3.14的0700临时目录不兼容。Bundle从内存字节读取，避免残留文件句柄妨碍Windows清理。

离线／模型评测入口：

```powershell
python benchmark.py --input 'C:/work/original' --output 'C:/work/oracle-v1' --pack
python benchmark.py --input 'C:/work/original' --output 'C:/work/replay-v1' --replay benchmarks/recorded --pack
python benchmark.py --input 'C:/work/original' --output 'C:/work/live-v1' --live --pack
```

默认是离线预期检查；replay只回放脱敏的历史模型计划，live才计费，32例最多8个四例批次。公开记录是校准过程中选定的结果，不是最新提示词在全新样本上的一次性成功率；历史误拒绝与回包／评测助手失败见第22章验收。

本工具的PASS仅指需求对照、结构与回包检查，不代表战斗、AI预测、专属动画或所有组合已通过。现有游戏、APK、资源选择器和此前mod均不因本工具改变。后续用户另行授权的独立设备抽样见[第22章04](../../22.自然语言原版制卡/04.API卡牌独立真机抽测.md)，不改变旧构建报告的未测标识。
