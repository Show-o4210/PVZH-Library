# ui/tab_help.py
"""使用说明 / 内嵌 README 展示页"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLabel
import i18n

HELP_MARKDOWN_ZH = r"""
# 幻影引擎使用说明

PvZ Heroes 自定义卡牌工具 —— 在图形界面中编辑卡牌数据、技能逻辑，并打包注入游戏 AssetBundle。

---

## 1. 快速上手

1. 打开 **工程大厅**，新建或选择一个 `.phantom` 工程  
2. 点击「在工作台新建一张卡牌」，或双击列表中的卡进入编辑  
3. 在 **基础属性 / 种族 / 标签 / 特殊能力 / 技能逻辑** 中修改  
4. 按 **Ctrl+S** 或点「保存当前修改到工程」  
5. 打开 **封包导出**，确认原包路径与输出路径后点击编译  
6. 将输出文件替换/挂载到游戏对应资源位置（按你的 mod 加载方式）

---

## 2. 各页面说明

| 页面 | 作用 |
|------|------|
| 工程大厅 | 管理多个 Mod 工程与卡牌清单 |
| 基础属性 | GUID、费用、攻防、阵营、系列、Flags、UI 能力标签、AI 倾向 |
| 种族配置 | 逻辑种族与显示种族；可新增自定义种族到本地库 |
| 标签配置 | 逻辑 Tags 与显示 Tags；可保存/载入常用标签库 |
| 特殊能力 | 独立组件能力（溅射、组队等）+ 触发类（双重攻击/先攻） |
| 技能逻辑 | 可视化技能树：触发器 → 过滤 → 目标 → 效果 |
| 封包导出 | 将**整个工程**的所有卡注入原版 cards 资源 |
| 主题设置 | 切换界面主题与 **中/英文界面语言** |
| 使用说明 | 本页 |

---

## 3. 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+S | 保存当前工作台卡牌到工程 |
| Ctrl+E | 执行封包导出 |
| Ctrl+Z / Ctrl+Y | 技能逻辑撤销 / 重做（焦点在逻辑页） |
| Ctrl+Shift+Z | 技能逻辑重做 |
| Ctrl+C / Ctrl+V | 技能节点复制 / 粘贴 |
| Delete | 删除选中技能节点 |
| Ctrl+滚轮 | 加速滚动（部分区域） |

---

## 4. 数据与路径

程序目录（与 `main.py` 同级）下：

- `projects/` —— 工程文件 `*.phantom`
- `data/` —— 默认原版数据（如 `card_data_5` / `card_data_5.json`）
- `out/` —— 建议的导出目录
- `custom_subtypes.json` / `custom_tags.json` / `custom_presets.json` —— 本地库
- `uuid.txt` —— 已知卡牌 GUID 与译名

路径基于程序所在目录解析，不依赖从哪里启动。

---

## 5. 语言

在 **主题设置** 页可切换 **中文 / English**。界面壳层、技能节点库、参数/枚举名与自然语言描述会一并切换。组件库搜索同时支持显示名与引擎类名。

---

## 6. 依赖与运行

```text
pip install -r requirements.txt
python main.py
```

或双击 `开始.bat`。

需要：Python 3.10+、PySide6、UnityPy。

---

## 7. 常见问题

**保存没反应？** 需要先创建/选中工程。  
**改了 GUID 列表还有旧卡？** 保存时会删除旧 GUID。  
**技能描述不对？** 确认已添加 Effect 节点。  
**未识别组件？** 树中显示「未识别组件」，导出会原样保留。

祝改卡顺利！
"""

HELP_MARKDOWN_EN = r"""
# Phantom Engine — Help

A GUI tool for Plants vs. Zombies Heroes card mods: edit card data & ability logic, then pack into a Unity AssetBundle.

---

## 1. Quick start

1. Open **Projects**, create or select a `.phantom` project  
2. Create a new card, or double-click a card to edit  
3. Edit **Basic / Subtypes / Tags / Abilities / Logic**  
4. Press **Ctrl+S** to save into the project  
5. Open **Export**, set paths, build the mod bundle  
6. Deploy the output with your usual mod loading method  

---

## 2. Tabs

| Tab | Purpose |
|-----|---------|
| Projects | Manage mod projects and card lists |
| Basic | GUID, cost, stats, faction, flags, UI tags, affinities |
| Subtypes | Logic & display subtypes; custom subtypes library |
| Tags | Logic & display tags; local tag library |
| Abilities | Component abilities + granted triggered abilities |
| Logic | Visual ability tree (triggers → filters → targets → effects) |
| Export | Inject **all project cards** into the `cards` asset |
| Theme | UI themes + **Chinese / English** language |
| Help | This page |

---

## 3. Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save workbench card to project |
| Ctrl+E | Run export packer |
| Ctrl+Z / Ctrl+Y | Logic undo / redo (focus in Logic tab) |
| Ctrl+Shift+Z | Logic redo |
| Ctrl+C / Ctrl+V | Copy / paste logic nodes |
| Delete | Delete selected logic nodes |
| Ctrl+Wheel | Faster scrolling in some views |

---

## 4. Paths

Relative to the app folder (`main.py`):

- `projects/` — `*.phantom` projects  
- `data/` — stock data (`card_data_5`, `card_data_5.json`)  
- `out/` — suggested export folder  
- `custom_*.json` — local libraries  
- `uuid.txt` — known GUID names  

---

## 5. Language

Switch **中文 / English** on the **Theme** tab. Shell UI, skill node library, param/enum labels, and natural-language ability descriptions all switch together. Palette search matches both display labels and engine class names.

---

## 6. Run

```text
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+, PySide6, UnityPy.

---

Happy modding!
"""

# 兼容旧引用
HELP_MARKDOWN = HELP_MARKDOWN_ZH


class TabHelp(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self.title = QLabel()
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(self.title)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.title.setText(i18n.t("help.title"))
        md = HELP_MARKDOWN_EN if i18n.get_language() == i18n.LANG_EN else HELP_MARKDOWN_ZH
        self.browser.setMarkdown(md)
