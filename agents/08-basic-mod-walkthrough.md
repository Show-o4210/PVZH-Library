# 08 · 从原包到可复查成品：独立基础示例

这一章为第一次接手本仓库的Agent提供可执行起点。只需本仓库、用户提供的原包、Python和UnityPy，**不依赖作者电脑的mod1/mod2、native dump或GUI编辑器**。

示例仅做离线构建，不连接设备、不修改正在使用的Mod。它采用入口README中已核对的三份输入哈希；其他版本会拒绝构建，需要先按[01章](01-bundles-and-scope.md)重新调查，不能删除哈希检查后盲跑。

## 准备工作

先查看AGENTS.md、Git状态和用户现有成果。确认任务是新工程还是对现有改版追加：新工程保留原包，累计工程从原包按顺序重放已完成修改，不能遗漏既有需求。

使用已有Python与UnityPy。示例在Python3.14、UnityPy1.25.0验证过；不强制更换其他已兼容工具。可先执行：

```powershell
python -c "import sys, UnityPy; print(sys.version); print(UnityPy.__version__)"
```

如果确实缺少UnityPy，按项目依赖或用户环境装入局部虚拟环境。使用哪个Python就通过同一个解释器执行 `python -m pip`，不持久修改PATH。

## 输入与命令

在用户项目内准备独立输入目录，放入 `card_data_1`、`data_assets_29`、`cn_8` 三文件。示例没有捆绑或下载游戏原包。

从仓库根目录执行，替换路径为本次用户给出的绝对路径：

```powershell
python .\agents\examples\basic_mod.py --input 'C:\work\pvzh-example\input' --output 'C:\work\pvzh-example\out-v1'
```

`--output`必须是尚不存在的新目录。默认卡为小豆丁326；测试僵尸阵营映射可另外构建：

```powershell
python .\agents\examples\basic_mod.py --input 'C:\work\pvzh-example\input' --output 'C:\work\pvzh-example\out-zombie' --guid 350
```

两个示例输出是独立实验，不能当作包含之前Nighter改动的累计版本部署。409本身被排除，以免示例重复追加冬青原生技能。

## 本例实际改变什么

| 范围 | 实际修改 | 数据证据 |
|---|---|---|
| 单个可定位Fighter | 2费3力量4生命，并追加冬青的打出冻结能力 | SunCost、Attack、Health的BaseValue与三个display字段同步；只复制409的能力实体 |
| 阵营 | 植物冻相邻僵尸；僵尸冻相邻植物 | 只改新追加实体内的敌方ComponentType，保留全类型串和原能力 |
| 僵尸任务200 | 双方30生命，高、平、平、平、水 | InitialHealth与五条LaneType；其余关卡字段保留 |
| 开场标题 | 第一段原开场消息改为僵王博士的示例标题 | 克隆原消息字段，Narrator=2，TextKey指向新键；其他消息保留 |
| 中文 | 卡牌长短说明追加真实技能，新增标题键 | 以prefabName定位CSV键，只重写目标逻辑记录 |

代码入口为 [examples/basic_mod.py](examples/basic_mod.py)。`component()`定位entity的顶层组件，`walk()`检查递归节点，`edit_cards()`修改卡牌，`edit_level()`修改单关，`edit_csv()`保留非目标物理行，`pack()`执行单TextAsset替换与回读校验。

`schema_check()`按原卡每种类型的数据字段检查新节点，另对原包中实际存储System.Type的字段检查完整串，能拒绝把Plants或HighgroundTerrain简称写入类型字段。字段集合相同仍不证明枚举值、目标含义和时机正确，必须按原包实例核对。

## 如何改成下一次任务

1. 用本次原始cards及CN建立GUID／prefabName／中文卡名映射，先处理昵称和数字简写。不同版本不要依赖本例GUID表。
2. 在原包搜索已实现同一时机、目标和效果的卡，保存完整模板。给自身、被打出单位、事件来源、英雄、路线选择分别写明查询，不能混用SelfQuery与TargetQuery。
3. 将本例edit函数改成用户明确要求的改动；若只改卡牌，关卡沿用原包或当前工程应保留的版本，不自动套用示例30生命。
4. 保留旧能力还是替换旧能力由需求决定。追加时新AbilityGroupId不撞已有组；替换时同步special_abilities与ShowTriggeredIcon。后续RevealTrigger等持续能力也要核对图标，不能只改能力树。
5. 新增卡／隐藏技能先找原骨架，GUID唯一，Card.Guid同步，复用模型；记录哪些是不可收集的召唤副本。检查CreateCard与GrantTriggeredAbility引用。例子本身没有新增卡定义。
6. 中文同时更新shortDesc、longDesc，按需求更新name、flavorText及关卡标题；仅承诺已写入的效果。没有可靠原版路径的内容按用户授权处理，并列明精确差异。

场景能力另见[02章](02-fighters-and-board-abilities.md)，英雄、背景、AI卡组与消息结构见[03章](03-levels-and-localization.md)，定时授予和墓碑案例见[06章](06-large-card-remix.md)、[07章](07-hearty-sneaky-remix.md)。不要把人类章节中的教学省略写法或自动翻译结果导入引擎。

## 成品验证与交付

本例build-report.json记录UnityPy版本、输入输出SHA-256、唯一改变的对象、卡牌与关卡字段、中文键及静态结果。构建还检查：

- 原输入哈希前后相同，原卡集合未增减，仅选中GUID改变，原有能力顺序保留。
- 只改计划中的关卡字段，其他字段深度相等。
- 非目标中文逻辑记录和值不变，目标键唯一；用原物理行复制保留其他引号、标点和空行。
- 输出重新UnityPy读取后文本与待写入值相同；以序列化文件名与path_id对齐，三个Bundle均只改指定TextAsset，所有其他对象原始字节不变。

这些是静态验证，**示例未做游戏启动或战斗实测**。实际项目部署前按[04章](04-device-verification.md)创建不可覆盖的版本化设备备份，并验证整套包引用一致：卡表移除场景GUID时，不能留下引用它的旧关卡包。

验收范围遵循用户要求。若只要求能进入游戏，就记录新构建主界面截图及启动后的设备哈希；若要求战斗效果，则追加相应场景实测。不要把未执行的检查写成PASS。
