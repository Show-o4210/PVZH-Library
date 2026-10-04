# PVZH 关卡自定义工具

面向《植物大战僵尸英雄》(PVZH) 的关卡编辑器。支持可视化配置关卡参数、人机/玩家、战场分路、游戏事件，并与 Unity AssetBundle（`data_assets_*`）互相同步。

---

## 功能概览

| 功能 | 说明 |
|------|------|
| 基础配置 | 关卡 ID、人机 ELO、背景场景、核心规则开关 |
| 人机 / 玩家配置 | 英雄、卡组、抽牌/费用/生命、护盾权重表 |
| 战场配置 | 全局场地能力、5 路地形与预置卡牌 |
| 游戏事件 | 剧情对话、解密发牌、强制抽卡、强制出牌（可拖拽排序） |
| 实时 JSON | 左右分屏，UI ↔ JSON 双向同步 |
| AB 包读写 | 从 `data/data_assets_*` 加载关卡，打包输出到 `out/` |
| 主题 | 浅色 / 深色模式（`theme_config.json`） |

---

## 环境要求

- **操作系统**：Windows（推荐）
- **Python**：3.10+（已在 3.13 / 3.14 验证）
- **依赖**：

```bash
pip install -r requirements.txt
```

主要依赖：

- `PySide6` — 图形界面
- `UnityPy` — Unity AssetBundle 读写

---

## 快速开始

### 1. 准备数据

将游戏解包得到的底包放到 `data/` 目录，文件名以 `data_assets` 开头，例如：

```text
level/
├── data/
│   └── data_assets_40      # 底包（必需，用于加载/打包 AB）
├── index.json              # 卡牌 GUID ↔ 中文名
├── decks.json              # 预设卡组库
├── theme_config.json       # 主题配置（可自动生成）
├── main.py
└── 开始.bat
```

> 若存在多个 `data_assets_*`，工具会按文件名中的**数字从大到小**优先读取；同一关卡 ID 只保留数字更大的那份。

### 2. 启动

任选其一：

```bash
# 方式 A：双击
开始.bat

# 方式 B：命令行（请在项目根目录执行）
python main.py
```

### 3. 常用工作流

1. 点击 **「从 AB 包加载关卡」**，在分类/搜索弹窗中选择目标关卡  
2. 在左侧各 Tab 中修改配置（右侧 JSON 会实时更新，也可直接改 JSON）  
3. 导出：
   - **导出 JSON 文件** → 写入 `out/<关卡Id>.json`
   - **打包至 AB 包 (Out)** → 覆盖底包中对应 TextAsset，输出到 `out/data_assets_*`

将 `out/` 中生成的 AB 包替换回游戏侧对应资源即可生效（具体替换方式视你的模组/补丁流程而定）。

---

## 目录结构

```text
level/
├── main.py                 # 主窗口与主题、导入导出
├── data_manager.py         # index.json / decks.json 加载
├── unity_manager.py        # AssetBundle 扫描、提取、回写
├── constants.py            # 英雄列表、场景列表
├── theme_config.json       # 深浅色主题色板
├── index.json              # 卡牌索引
├── decks.json              # 卡组索引
├── data/                   # 输入底包 data_assets_*
├── out/                    # 导出 JSON / 打包后的 AB
├── ui/
│   ├── tab_basic.py        # 基础配置
│   ├── tab_character.py    # 人机/玩家配置
│   ├── tab_board.py        # 战场分路
│   ├── tab_events.py       # 游戏事件
│   ├── dialog_*.py         # 各类选择/编辑弹窗
│   └── base_components.py  # 通用组件
├── requirements.txt
└── 开始.bat
```

---

## 配置说明（节选）

### 关卡核心字段

- `Id`：关卡资源名 / 匹配 AB 内 TextAsset 名称
- `OpponentElo`：人机难度 ELO
- `MustPlayAllPlayableCards` / `DisableSurprisePhase` / `EnableReadySetPlant` / `SkipHeroSelect`：规则开关

### 角色配置（OpponentConfig / PlayerConfig）

- `HeroId`、`DeckId`、`Parameters.Faction`（0 植物 / 1 僵尸）
- `Parameters` 内抽牌、生命、费用、洗牌、护盾条等
- **护盾权重表** `SuperBlockTable.TableEntries`：所有 `RngWeight` **之和必须为 100**，否则无法导出 JSON / 打包 AB

### 战场（BoardConfig）

- `PlantsBoardName` / `ZombiesBoardName`：场景 ID（工具中两者同步为同一场景）
- `BoardAbilities`：能力 GUID 列表
- `LaneEntries`：5 路，每路含 `LaneType`（0 高地 / 1 平地 / 2 水路）与 `Cards`（GUID 列表）

### 游戏事件（GameEvents）

支持类型包括：

| 类型 | `$type` 关键字 |
|------|----------------|
| 剧情对话 | `MessageEventConfig` |
| 解密发牌 | `AddCardToTopOfDeckConfig` |
| 强制抽卡 | `MoveCardToTopOfDeckConfig` |
| 强制出牌 | `ScriptedTurnEventConfig` |

列表支持拖拽排序、双击编辑、Delete 删除、Ctrl+↑/↓ 移动。

---

## 注意事项

1. **底包必需**：加载/打包 AB 都依赖 `data/data_assets_*`。仅导出 JSON 可不依赖 AB。  
2. **打包是覆盖式的**：`打包至 AB 包` 会在已有底包中查找与当前 `Id` 同名的关卡并覆盖；若 `Id` 在底包中不存在会报错。  
3. **护盾权重**：导出前请确保人机与玩家护盾权重各为 100。  
4. **卡牌索引**：`index.json` 用于中文名显示与搜索；缺失时仍可用数字 GUID。  
5. **备份**：修改并替换游戏资源前，请自行备份原始 `data_assets_*`。  
6. **多底包**：文件名数字越大优先级越高；数字重复会报错以避免覆盖顺序不确定。

---

## 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 启动即闪退 / 无窗口 | 未安装 PySide6 | `pip install -r requirements.txt` |
| 找不到 data_assets | `data/` 为空或文件名不符 | 放入以 `data_assets` 开头的底包 |
| AB 包读取失败 | 文件损坏或非 Unity AB | 换一份完整底包；查看报错信息 |
| 打包失败：未找到关卡 | 当前 `Id` 不在底包内 | 先从 AB 加载该关卡，或改回存在的 Id |
| 卡牌显示 Unknown | 缺少 `index.json` 或 GUID 不在索引中 | 补全 `index.json` |
| 护盾导出被拦截 | 权重和 ≠ 100 | 在人机/玩家配置中调整 RNG 权重 |

---

## 开发说明

- UI 与数据分离：各 Tab 实现 `load_data(config)` / `save_data(config)`  
- 主窗口用 `_is_syncing` 互斥锁避免 UI ↔ JSON 互相触发  
- JSON 编辑使用 500ms 防抖解析  
- AssetBundle 读写封装于 `UnityABManager`（兼容 TextAsset 的 `text` / `script` / `m_Script` 字段）

---

## 版本

- 当前版本：**v3.0（模块化重构版）**
- 界面框架：PySide6 + Fusion 风格

---

## 免责声明

本工具仅供学习与私人模组研究使用。请遵守当地法律法规及游戏服务条款，勿用于破坏他人游戏体验或商业侵权用途。
