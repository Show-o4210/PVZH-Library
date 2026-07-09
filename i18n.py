# i18n.py
"""界面中/英文本地化。技能节点库名称见 localization.py（随语言切换）。"""

from __future__ import annotations

from typing import Callable, Dict, List

LANG_ZH = "zh"
LANG_EN = "en"
SUPPORTED = (LANG_ZH, LANG_EN)

_current = LANG_ZH
_listeners: List[Callable[[str], None]] = []

# key -> { zh: str, en: str }
STRINGS: Dict[str, Dict[str, str]] = {
    # ---- App ----
    "app.name": {"zh": "PvZ Heroes 幻影引擎", "en": "PvZ Heroes Phantom Engine"},
    "app.version": {"zh": "v2.1", "en": "v2.1"},
    "app.title": {"zh": "PvZ Heroes 幻影引擎 v2.1", "en": "PvZ Heroes Phantom Engine v2.1"},
    "app.dirty_mark": {"zh": "*", "en": "*"},
    "app.saved_to": {"zh": "已保存至 {name}", "en": "Saved to {name}"},
    "app.no_project": {"zh": "未加载工程", "en": "No project loaded"},

    # ---- Sidebar tabs ----
    "tab.project": {"zh": "工程大厅", "en": "Projects"},
    "tab.basic": {"zh": "基础属性", "en": "Basic"},
    "tab.subtypes": {"zh": "种族配置", "en": "Subtypes"},
    "tab.tags": {"zh": "标签配置", "en": "Tags"},
    "tab.abilities": {"zh": "特殊能力", "en": "Abilities"},
    "tab.logic": {"zh": "技能逻辑", "en": "Logic"},
    "tab.export": {"zh": "封包导出", "en": "Export"},
    "tab.theme": {"zh": "主题设置", "en": "Theme"},
    "tab.help": {"zh": "使用说明", "en": "Help"},

    # ---- Common ----
    "common.ok": {"zh": "确定", "en": "OK"},
    "common.cancel": {"zh": "取消", "en": "Cancel"},
    "common.yes": {"zh": "是", "en": "Yes"},
    "common.no": {"zh": "否", "en": "No"},
    "common.success": {"zh": "成功", "en": "Success"},
    "common.error": {"zh": "错误", "en": "Error"},
    "common.warning": {"zh": "警告", "en": "Warning"},
    "common.confirm": {"zh": "确认", "en": "Confirm"},
    "common.browse": {"zh": "浏览...", "en": "Browse..."},
    "common.save_failed": {"zh": "保存失败", "en": "Save failed"},
    "common.not_found": {"zh": "未找到", "en": "Not found"},
    "common.import_failed": {"zh": "导入失败", "en": "Import failed"},
    "common.lang": {"zh": "界面语言", "en": "Language"},
    "common.lang.zh": {"zh": "中文", "en": "中文"},
    "common.lang.en": {"zh": "English", "en": "English"},
    "common.lang.hint": {
        "zh": "切换后立即刷新全部界面文案（含技能节点库、参数名与自然语言描述）。",
        "en": "UI strings refresh immediately, including skill nodes, params, and ability descriptions.",
    },

    # ---- Dialogs (main) ----
    "dlg.unsaved_title": {"zh": "未保存的修改", "en": "Unsaved changes"},
    "dlg.unsaved_project": {
        "zh": "工作台有未保存的修改，是否先保存到当前工程？\n（选「否」将丢弃工作台未保存内容并继续）",
        "en": "Workbench has unsaved changes. Save to the current project first?\n(No discards unsaved work and continues)",
    },
    "dlg.unsaved_card": {
        "zh": "加载新卡牌将覆盖工作台当前内容。是否先保存？",
        "en": "Loading another card will overwrite the workbench. Save first?",
    },
    "dlg.exit_title": {"zh": "退出确认", "en": "Exit"},
    "dlg.exit_body": {"zh": "有未保存的修改，确定退出吗？", "en": "There are unsaved changes. Exit anyway?"},
    "dlg.no_project_title": {"zh": "未加载工程", "en": "No project"},
    "dlg.no_project_body": {
        "zh": "请先在【工程大厅】新建或选择一个工程，再保存卡牌。",
        "en": "Create or open a project in Projects before saving a card.",
    },
    "dlg.save_fail_body": {
        "zh": "无法写入工程文件，请检查磁盘权限。",
        "en": "Could not write the project file. Check disk permissions.",
    },
    "dlg.guid_missing": {"zh": "在文件中找不到 GUID: {guid}", "en": "GUID not found in file: {guid}"},
    "dlg.import_ok": {"zh": "卡牌 {guid} 已成功导入工作台！", "en": "Card {guid} imported to workbench."},
    "dlg.import_err": {"zh": "解析异常: {err}", "en": "Parse error: {err}"},

    # ---- Project tab ----
    "proj.list_group": {"zh": "📁 本地工程列表 (.phantom)", "en": "📁 Local projects (.phantom)"},
    "proj.new": {"zh": "➕ 新建 Mod 工程", "en": "➕ New mod project"},
    "proj.roster_group": {"zh": "📜 当前 Mod 包含的卡牌", "en": "📜 Cards in current mod"},
    "proj.status_none": {"zh": "请先选择或新建一个工程", "en": "Select or create a project first"},
    "proj.status_active": {
        "zh": "当前激活工程: {name} (双击卡牌去编辑)",
        "en": "Active project: {name} (double-click a card to edit)",
    },
    "proj.new_card": {"zh": "✨ 在工作台新建一张卡牌", "en": "✨ New card on workbench"},
    "proj.del_card": {"zh": "🗑️ 从当前 Mod 移除选中卡牌", "en": "🗑️ Remove selected card from mod"},
    "proj.new_dialog_title": {"zh": "新建工程", "en": "New project"},
    "proj.new_dialog_label": {
        "zh": "请输入新 Mod 工程名称 (如: PVZ_Rebalance):",
        "en": "Enter mod project name (e.g. PVZ_Rebalance):",
    },
    "proj.del_confirm": {
        "zh": "确定要从当前 Mod 中移除卡牌 {guid} 吗？",
        "en": "Remove card {guid} from the current mod?",
    },
    "proj.custom_card": {"zh": "自定义卡牌", "en": "Custom card"},

    # ---- Basic tab ----
    "basic.quick": {"zh": "⚡ 快速操作", "en": "⚡ Quick actions"},
    "basic.save": {"zh": "💾 保存当前修改到工程 (Ctrl + S)", "en": "💾 Save to project (Ctrl+S)"},
    "basic.save_hint": {
        "zh": "💡 提示：在软件任何 Tab 按下 Ctrl + S 均可快速保存",
        "en": "💡 Tip: Ctrl+S saves from any tab",
    },
    "basic.import_label": {"zh": "从 JSON 导入:", "en": "Import from JSON:"},
    "basic.import_placeholder": {"zh": "选择原始 {name}...", "en": "Select source {name}..."},
    "basic.import_btn": {"zh": "⬇️ 导入到工作台", "en": "⬇️ Import to workbench"},
    "basic.guid_prefix": {"zh": "GUID: ", "en": "GUID: "},
    "basic.group_id": {"zh": "标识与预制体", "en": "Identity & prefab"},
    "basic.guid": {"zh": "GUID:", "en": "GUID:"},
    "basic.local_name": {"zh": "本地译名:", "en": "Local name:"},
    "basic.local_name_ph": {"zh": "自动读取...", "en": "Auto..."},
    "basic.prefab": {"zh": "Prefab:", "en": "Prefab:"},
    "basic.group_def": {"zh": "卡牌定义 (分类、系列)", "en": "Card definition"},
    "basic.faction": {"zh": "阵营 (Faction):", "en": "Faction:"},
    "basic.base_id": {"zh": "类型 (Base ID):", "en": "Base ID:"},
    "basic.color": {"zh": "职业 (Color):", "en": "Class (Color):"},
    "basic.rarity": {"zh": "稀有度 (Rarity):", "en": "Rarity:"},
    "basic.set": {"zh": "系列 (Set):", "en": "Set:"},
    "basic.set_rarity_key": {"zh": "系列/稀有度主键:", "en": "Set/rarity key:"},
    "basic.group_stats": {"zh": "数值与造价", "en": "Stats & crafting"},
    "basic.craft": {"zh": "火花造价:", "en": "Sparks:"},
    "basic.buy": {"zh": "买:", "en": "Buy:"},
    "basic.sell": {"zh": "卖:", "en": "Sell:"},
    "basic.cost": {"zh": "费用:", "en": "Cost:"},
    "basic.attack": {"zh": "攻击:", "en": "Attack:"},
    "basic.health": {"zh": "生命:", "en": "Health:"},
    "basic.enable": {"zh": "启用", "en": "Enable"},
    "basic.group_flags": {"zh": "核心标记 (Flags)", "en": "Core flags"},
    "basic.flag_ignore": {"zh": "无视上限", "en": "Ignore deck limit"},
    "basic.flag_power": {"zh": "超能力", "en": "Superpower"},
    "basic.flag_primary": {"zh": "英雄大招", "en": "Signature superpower"},
    "basic.flag_trick": {"zh": "锦囊", "en": "Trick"},
    "basic.flag_surprise": {"zh": "僵尸回合打出", "en": "Surprise (zombie turn)"},
    "basic.flag_env": {"zh": "环境", "en": "Environment"},
    "basic.flag_board": {"zh": "场景能力", "en": "Board ability"},
    "basic.group_ui_abil": {"zh": "UI 能力标签 (special_abilities)", "en": "UI ability tags (special_abilities)"},
    "basic.group_aff": {"zh": "AI 倾向性 (Affinities)", "en": "AI affinities"},
    "basic.sub_aff": {"zh": "种族倾向:", "en": "Subtype affinities:"},
    "basic.sub_aff_w": {"zh": "种族权重:", "en": "Subtype weights:"},
    "basic.tag_aff": {"zh": "标签倾向:", "en": "Tag affinities:"},
    "basic.tag_aff_w": {"zh": "标签权重:", "en": "Tag weights:"},
    "basic.card_aff": {"zh": "卡牌倾向:", "en": "Card affinities:"},
    "basic.card_aff_w": {"zh": "卡牌权重:", "en": "Card weights:"},
    "basic.unknown_card": {"zh": "未知/自定义卡牌", "en": "Unknown / custom card"},
    "basic.import_path_err": {"zh": "导入路径不正确！", "en": "Invalid import path."},
    "basic.pick_json": {"zh": "选择原始 JSON 数据池", "en": "Select card JSON pool"},

    # ---- Subtypes ----
    "sub.add_group": {"zh": "新增自定义种族", "en": "Add custom subtype"},
    "sub.name_ph": {"zh": "例如: 机甲 (Mech)", "en": "e.g. Mech"},
    "sub.save_local": {"zh": "保存到本地库", "en": "Save to local library"},
    "sub.sync": {
        "zh": "保持【底层逻辑种族】自动同步到【UI显示种族】",
        "en": "Keep logic subtypes synced to display subtypes",
    },
    "sub.logic_group": {
        "zh": "底层逻辑种族 (Components生效，可作为隐藏触发)",
        "en": "Logic subtypes (components; can be hidden triggers)",
    },
    "sub.display_group": {
        "zh": "UI显示层种族 (展示给玩家看的标签)",
        "en": "Display subtypes (player-facing tags)",
    },
    "sub.empty_name": {"zh": "种族名称不能为空！", "en": "Subtype name cannot be empty."},
    "sub.builtin": {"zh": "ID {id} 是内置种族，无法覆盖！", "en": "ID {id} is a built-in subtype and cannot be overwritten."},
    "sub.overwrite": {"zh": "ID {id} 已存在自定义种族，是否覆盖？", "en": "Custom subtype ID {id} exists. Overwrite?"},
    "sub.saved": {"zh": "新种族 [{id}] 已同步至本地库", "en": "Subtype [{id}] saved to local library."},
    "sub.save_fail": {"zh": "无法写入本地文件：\n{err}", "en": "Cannot write local file:\n{err}"},

    # ---- Tags ----
    "tags.sync": {
        "zh": "保持【逻辑标签】自动同步到【显示标签】",
        "en": "Keep logic tags synced to display tags",
    },
    "tags.logic_group": {
        "zh": "底层逻辑标签 (实际生效，例如: destroy)",
        "en": "Logic tags (gameplay, e.g. destroy)",
    },
    "tags.display_group": {"zh": "UI显示标签 (仅作展示)", "en": "Display tags (UI only)"},
    "tags.input_ph": {"zh": "输入标签后按回车添加...", "en": "Type a tag and press Enter..."},
    "tags.delete": {"zh": "删除选中的标签", "en": "Delete selected tags"},
    "tags.load_lib": {"zh": "载入本地常用标签库", "en": "Load local tag library"},
    "tags.save_lib": {"zh": "将当前标签保存为常用库", "en": "Save current tags as library"},

    # ---- Abilities ----
    "abil.basic_group": {"zh": "✨ 基础特殊能力 (独立组件)", "en": "✨ Basic abilities (components)"},
    "abil.triggered_group": {
        "zh": "⚡ 赋予触发类能力 (GrantedTriggeredAbilities)",
        "en": "⚡ Granted triggered abilities",
    },
    "abil.add": {"zh": "➕ 添加至列表", "en": "➕ Add to list"},
    "abil.double": {"zh": "💥 双重攻击 (ID:{id})", "en": "💥 Double strike (ID:{id})"},
    "abil.overshoot": {"zh": "🎯 先攻 (ID:{id})", "en": "🎯 Overshoot (ID:{id})"},
    "abil.custom": {"zh": "🧩 自定义能力代码", "en": "🧩 Custom ability code"},
    "abil.row_double": {"zh": "💥 双重攻击", "en": "💥 Double strike"},
    "abil.row_overshoot": {"zh": "🎯 先攻", "en": "🎯 Overshoot"},
    "abil.row_custom": {"zh": "🧩 自定义能力", "en": "🧩 Custom ability"},
    "abil.unknown": {"zh": "未知能力", "en": "Unknown ability"},
    "abil.dmg_prefix": {"zh": "伤害: ", "en": "Dmg: "},
    "abil.id_prefix": {"zh": "ID: ", "en": "ID: "},
    "abil.val_prefix": {"zh": "数值: ", "en": "Value: "},
    "abil.vt_fixed": {"zh": "固定数值 (0)", "en": "Fixed (0)"},
    "abil.vt_pct": {"zh": "百分比 (1)", "en": "Percent (1)"},
    "abil.vt_mul": {"zh": "倍数 (2)", "en": "Multiplier (2)"},

    # ---- Export ----
    "export.group": {"zh": "📦 幻影引擎打包车间", "en": "📦 Bundle pack workshop"},
    "export.info": {
        "zh": "🚀 将当前工程中的所有修改，一次性编译并注入游戏底包中。",
        "en": "🚀 Compile all project cards and inject them into the game asset bundle.",
    },
    "export.src": {"zh": "游戏原版 AB 包 (In): ", "en": "Original AB bundle (In): "},
    "export.out": {"zh": "生成的 Mod AB 包 (Out):", "en": "Mod AB output (Out):"},
    "export.pack": {"zh": "💎 编译当前工程并生成 Mod (.assets)", "en": "💎 Build mod bundle (.assets)"},
    "export.pick_src": {"zh": "选择原版 Bundle", "en": "Select original bundle"},
    "export.pick_out": {"zh": "选择输出路径", "en": "Select output path"},
    "export.no_project": {
        "zh": "当前没有加载任何工程！请先去【工程大厅】新建或读取工程。",
        "en": "No project loaded. Create or open one in Projects.",
    },
    "export.empty": {
        "zh": "当前工程是空的！没有任何卡牌可以打包。",
        "en": "Project is empty — nothing to pack.",
    },
    "export.path_missing": {"zh": "请先填写原包和导出路径！", "en": "Fill in source and output paths."},
    "export.ok_title": {"zh": "🎉 编译成功", "en": "🎉 Build succeeded"},
    "export.ok_body": {"zh": "工程 [{name}] 编译完毕！\n{msg}", "en": "Project [{name}] built.\n{msg}"},
    "export.fail_title": {"zh": "💥 编译失败", "en": "💥 Build failed"},
    "export.err_title": {"zh": "💥 打包异常", "en": "💥 Pack error"},
    "export.err_body": {"zh": "发生错误：\n{err}", "en": "Error:\n{err}"},

    # ---- Theme ----
    "theme.info_group": {"zh": "🎨 主题设置", "en": "🎨 Theme"},
    "theme.info": {
        "zh": "选择你喜欢的界面主题。所有颜色、透明度、边框样式都会实时切换。\n部分主题支持玻璃态效果，提供更现代的视觉体验。",
        "en": "Pick a UI theme. Colors, opacity and borders update live.\nSome themes use a glass look.",
    },
    "theme.current_group": {"zh": "📌 当前主题", "en": "📌 Current theme"},
    "theme.list_group": {"zh": "✨ 可选主题", "en": "✨ Available themes"},
    "theme.apply": {"zh": "🎨 应用此主题", "en": "🎨 Apply theme"},
    "theme.reset": {"zh": "🔄 重置为默认主题", "en": "🔄 Reset to default"},
    "theme.current": {"zh": "当前主题：{name} — {desc}", "en": "Current: {name} — {desc}"},
    "theme.lang_group": {"zh": "🌐 语言 / Language", "en": "🌐 Language"},

    # ---- Help ----
    "help.title": {"zh": "📖 使用说明", "en": "📖 Help"},

    # ---- Logic panel ----
    "logic.hide_palette": {"zh": "隐藏组件库", "en": "Hide palette"},
    "logic.show_palette": {"zh": "显示组件库", "en": "Show palette"},
    "logic.hide_inspector": {"zh": "隐藏检查器", "en": "Hide inspector"},
    "logic.show_inspector": {"zh": "显示检查器", "en": "Show inspector"},
    "logic.new_group": {"zh": "➕ 新建技能组", "en": "➕ New ability group"},
    "logic.expand": {"zh": "📂 全部展开", "en": "📂 Expand all"},
    "logic.collapse": {"zh": "📁 全部折叠", "en": "📁 Collapse all"},
    "logic.undo": {"zh": "↩️ 撤销", "en": "↩️ Undo"},
    "logic.redo": {"zh": "↪️ 重做", "en": "↪️ Redo"},
    "logic.palette": {"zh": "🎨 组件库 (右键管理预设)", "en": "🎨 Palette (right-click presets)"},
    "logic.search_ph": {
        "zh": "🔍 搜索组件 (中文名 / 引擎类名)...",
        "en": "🔍 Search components (label or class name)...",
    },
    "logic.workspace": {"zh": "🌳 工作区 (右键更换/禁用)", "en": "🌳 Workspace (right-click)"},
    "logic.card_tab": {"zh": "🃏 当前卡牌技能", "en": "🃏 Card abilities"},
    "logic.desc_group": {"zh": "📝 技能自然语言描述", "en": "📝 Natural-language description"},
    "logic.inspector": {"zh": "🛠️ 属性检查器", "en": "🛠️ Inspector"},
    "logic.pick_node": {"zh": "请在工作区中选择一个节点", "en": "Select a node in the workspace"},
    "logic.pick_outline": {"zh": "请在大纲中选择一个节点", "en": "Select a node in the outline"},
    "logic.ability_group": {"zh": "📦 技能组", "en": "📦 Ability group"},
    "logic.ability_group_no_param": {
        "zh": "📦 技能组 (无属性可编)",
        "en": "📦 Ability group (no params)",
    },
    "logic.no_params": {"zh": "当前节点没有可编辑参数。", "en": "No editable parameters."},
    "logic.preset_root": {"zh": "⭐ 我的自定义预设", "en": "⭐ My presets"},
    "logic.cat_trigger": {"zh": "🟢 触发器", "en": "🟢 Triggers"},
    "logic.cat_filter": {"zh": "🟡 过滤器", "en": "🟡 Filters"},
    "logic.cat_target": {"zh": "🟠 目标选取", "en": "🟠 Targets"},
    "logic.cat_composite": {"zh": "🔗 复合逻辑门", "en": "🔗 Composite queries"},
    "logic.cat_query": {"zh": "🔵 原子条件", "en": "🔵 Queries"},
    "logic.cat_effect": {"zh": "🔴 基础执行", "en": "🔴 Effects"},
    "logic.cat_complex": {"zh": "🟥 复合执行 (需条件)", "en": "🟥 Complex effects"},
    "logic.other_nodes": {"zh": "📁 其他通用节点", "en": "📁 Other nodes"},
    "logic.paste_fail": {
        "zh": "当前选中的节点位置不合法，无法粘贴。",
        "en": "Cannot paste into the selected location.",
    },
    "logic.pick_parent": {
        "zh": "请在工作区中选中要插入的父节点。",
        "en": "Select a parent node in the workspace.",
    },
    "logic.insert_fail_preset": {
        "zh": "当前选中的位置无法插入该预设，请检查嵌套规则。",
        "en": "Cannot insert this preset here. Check nesting rules.",
    },
    "logic.insert_fail_node": {
        "zh": "当前选中的位置无法插入该组件，请检查嵌套规则。",
        "en": "Cannot insert this component here. Check nesting rules.",
    },
    "logic.save_preset": {"zh": "保存预设", "en": "Save preset"},
    "logic.save_preset_name": {"zh": "起个名字：", "en": "Name:"},
    "logic.del_preset": {
        "zh": "确定要删除预设 '{name}' 吗？",
        "en": "Delete preset '{name}'?",
    },
    "logic.hint": {"zh": "提示", "en": "Tip"},
    "logic.fail": {"zh": "失败", "en": "Failed"},
    "logic.enable": {"zh": "启用", "en": "Enable"},
    "logic.raw_unknown": {"zh": "⚠️ 未识别组件 ({name})", "en": "⚠️ Unknown component ({name})"},
    "logic.preset_tab": {"zh": "📦 预设: {name}", "en": "📦 Preset: {name}"},
    "logic.translate_fail": {"zh": "翻译生成失败: {err}", "en": "Description failed: {err}"},
    "logic.empty_desc": {
        "zh": "暂无技能配置。\n(请在左侧双击组件添加，或在上方新建技能组)",
        "en": "No abilities yet.\n(Double-click palette items or create an ability group)",
    },

    # ---- Bundle packer messages (user-facing) ----
    "pack.no_bundle": {"zh": "找不到原始 Bundle 文件: {path}", "en": "Original bundle not found: {path}"},
    "pack.no_asset": {
        "zh": "在 Bundle 中未找到名为 '{name}' 的数据节点！请确认原包是否正确。",
        "en": "No data node named '{name}' in the bundle. Check the source file.",
    },
    "pack.ok": {"zh": "AssetBundle 注入并打包成功！", "en": "AssetBundle injected and packed successfully."},
    "pack.fatal": {"zh": "打包发生严重异常: {err}", "en": "Fatal pack error: {err}"},
}


def get_language() -> str:
    return _current


def t(key: str, **kwargs) -> str:
    """取当前语言文案；缺键时回退中文再回退 key。"""
    entry = STRINGS.get(key)
    if not entry:
        text = key
    else:
        text = entry.get(_current) or entry.get(LANG_ZH) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def set_language(lang: str, notify: bool = True) -> bool:
    global _current
    if lang not in SUPPORTED:
        return False
    if lang == _current:
        return True
    _current = lang
    if notify:
        for cb in list(_listeners):
            try:
                cb(lang)
            except Exception as e:
                print(f"i18n listener error: {e}")
    return True


def register_listener(callback: Callable[[str], None]):
    if callback not in _listeners:
        _listeners.append(callback)


def unregister_listener(callback: Callable[[str], None]):
    if callback in _listeners:
        _listeners.remove(callback)


def app_title(extra: str | None = None) -> str:
    base = t("app.title")
    if extra:
        return f"{base} - [{extra}]"
    return base
