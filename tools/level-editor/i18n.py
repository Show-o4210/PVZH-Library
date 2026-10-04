# i18n.py
"""中英本地化：字符串表、语言偏好读写、切换通知。"""
from __future__ import annotations

import json
import os
from typing import Any, Callable

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme_config.json")

SUPPORTED_LANGS = ("zh", "en")
DEFAULT_LANG = "zh"

_current_lang = DEFAULT_LANG
_listeners: list[Callable[[str], None]] = []

# ---------------------------------------------------------------------------
# 字符串表：key -> {zh, en}
# ---------------------------------------------------------------------------
STRINGS: dict[str, dict[str, str]] = {
    # ===== 主窗口 =====
    "app.title": {
        "zh": "PVZH关卡自定义工具 v3.0 (模块化重构版)",
        "en": "PVZH Level Customizer v3.0 (Modular)",
    },
    "toolbar.main": {"zh": "主工具栏", "en": "Main Toolbar"},
    "toolbar.import_json": {"zh": "导入 JSON 文件", "en": "Import JSON"},
    "toolbar.export_json": {"zh": "导出 JSON 文件", "en": "Export JSON"},
    "toolbar.load_ab": {"zh": "📦 从 AB 包加载关卡", "en": "📦 Load Level from AB"},
    "toolbar.export_ab": {"zh": "🚀 打包至 AB 包 (Out)", "en": "🚀 Pack to AB (Out)"},
    "toolbar.theme_light": {"zh": "☀️ 浅色模式", "en": "☀️ Light Mode"},
    "toolbar.theme_dark": {"zh": "🌙 深色模式", "en": "🌙 Dark Mode"},
    "toolbar.lang_to_en": {"zh": "🌐 English", "en": "🌐 English"},
    "toolbar.lang_to_zh": {"zh": "🌐 中文", "en": "🌐 中文"},
    "tab.basic": {"zh": "基础配置", "en": "Basic"},
    "tab.opponent": {"zh": "人机配置", "en": "Opponent"},
    "tab.player": {"zh": "玩家配置", "en": "Player"},
    "tab.board": {"zh": "战场配置", "en": "Board"},
    "tab.events": {"zh": "游戏事件", "en": "Events"},
    "json.preview_title": {
        "zh": "<b>实时 JSON 预览 (支持直接修改)</b>",
        "en": "<b>Live JSON Preview (editable)</b>",
    },
    "json.error": {
        "zh": " JSON 格式错误，暂停同步...",
        "en": " Invalid JSON — sync paused...",
    },
    "status.ready": {"zh": "初始化完成。", "en": "Ready."},
    "status.loaded": {"zh": "成功加载: {name}", "en": "Loaded: {name}"},
    "status.exported": {"zh": "成功导出: {path}", "en": "Exported: {path}"},
    "status.scanning_ab": {
        "zh": "正在扫描 AB 包中的关卡文件，请稍候...",
        "en": "Scanning levels in AB package, please wait...",
    },
    "status.loaded_ab": {
        "zh": "成功从 AB 包加载关卡: {id}",
        "en": "Loaded level from AB: {id}",
    },
    "status.packing": {
        "zh": "正在打包 {id} 到 AB 包，请稍候...",
        "en": "Packing {id} into AB, please wait...",
    },
    "status.pack_done": {"zh": "打包完成！", "en": "Packing complete!"},

    # ===== 通用对话框 / 按钮 =====
    "common.cancel": {"zh": "取消", "en": "Cancel"},
    "common.confirm": {"zh": "确认选择", "en": "Confirm"},
    "common.error": {"zh": "错误", "en": "Error"},
    "common.warning": {"zh": "警告", "en": "Warning"},
    "common.success": {"zh": "成功", "en": "Success"},
    "common.yes": {"zh": "是", "en": "Yes"},
    "common.no": {"zh": "否", "en": "No"},
    "common.click_select": {"zh": "点击选择...", "en": "Click to select..."},
    "common.unknown": {"zh": "未知", "en": "Unknown"},
    "common.empty": {"zh": "空", "en": "Empty"},
    "common.none": {"zh": "无", "en": "None"},
    "common.plants": {"zh": "植物", "en": "Plants"},
    "common.zombies": {"zh": "僵尸", "en": "Zombies"},
    "common.any": {"zh": "任意", "en": "Any"},
    "common.uncategorized": {"zh": "未分类", "en": "Uncategorized"},

    # ===== 消息框 =====
    "msg.load_failed": {"zh": "加载失败: {err}", "en": "Load failed: {err}"},
    "msg.export_failed": {"zh": "导出失败: {err}", "en": "Export failed: {err}"},
    "msg.export_ok": {"zh": "文件已生成:\n{path}", "en": "File written:\n{path}"},
    "msg.shield_opponent": {
        "zh": "人机护盾权重之和必须为 100！",
        "en": "Opponent shield weights must sum to 100!",
    },
    "msg.shield_player": {
        "zh": "玩家护盾权重之和必须为 100！",
        "en": "Player shield weights must sum to 100!",
    },
    "msg.ab_missing": {
        "zh": "找不到原始文件: data 目录下的 data_assets_* 底包文件\n请检查目录结构！",
        "en": "Base AB not found: data/data_assets_* is missing.\nCheck the folder layout!",
    },
    "msg.ab_no_levels": {
        "zh": "AB 包内没有找到符合特征的关卡配置文件！",
        "en": "No level configs found inside the AB package!",
    },
    "msg.ab_no_levels_title": {"zh": "未找到文件", "en": "Nothing Found"},
    "msg.read_failed": {
        "zh": "发生了错误:\n{err}",
        "en": "An error occurred:\n{err}",
    },
    "msg.read_failed_title": {"zh": "读取失败", "en": "Read Failed"},
    "msg.ab_pack_missing": {
        "zh": "必须在 data 目录下有 data_assets_* 作为底包才能打包！",
        "en": "A data/data_assets_* base package is required to pack!",
    },
    "msg.missing_level_id": {
        "zh": "当前配置缺少关卡 Id，无法匹配 AB 包内的目标！",
        "en": "Current config has no Level Id — cannot match AB target!",
    },
    "msg.pack_ok": {
        "zh": "修改后的 AB 包已成功生成至:\n{path}",
        "en": "Modified AB written to:\n{path}",
    },
    "msg.pack_ok_title": {"zh": "打包成功", "en": "Pack Success"},
    "msg.pack_failed": {
        "zh": "发生异常:\n{err}",
        "en": "Exception:\n{err}",
    },
    "msg.pack_failed_title": {"zh": "打包失败", "en": "Pack Failed"},
    "msg.select_preset": {"zh": "选择预设", "en": "Select Preset"},
    "msg.missing_component": {
        "zh": "未找到 LaneCardsDialog，请确认 ui/dialog_lane_cards.py 存在。",
        "en": "LaneCardsDialog not found. Ensure ui/dialog_lane_cards.py exists.",
    },
    "msg.missing_component_title": {"zh": "缺少组件", "en": "Missing Component"},
    "msg.empty_card_index": {
        "zh": "未加载到 index.json，仍可手动输入数字 GUID 添加卡牌。",
        "en": "index.json not loaded. You can still add cards by numeric GUID.",
    },
    "msg.empty_card_index_title": {"zh": "卡牌索引为空", "en": "Empty Card Index"},

    # ===== SearchableGridDialog =====
    "grid.subtitle": {
        "zh": "输入 ID、英文名或中文名进行过滤，双击项目即可选择。",
        "en": "Filter by ID, English or Chinese name. Double-click to select.",
    },
    "grid.search_ph": {"zh": "搜索关键字 / ID ...", "en": "Search keyword / ID..."},
    "grid.no_match": {"zh": "没有找到匹配项", "en": "No matches found"},
    "grid.result_count": {"zh": "共 {n} 个结果", "en": "{n} result(s)"},

    # ===== tab_basic =====
    "basic.info_group": {"zh": "关卡基本信息", "en": "Level Info"},
    "basic.section_title": {"zh": "基础标识", "en": "Identifiers"},
    "basic.section_hint": {
        "zh": "用于控制关卡 ID、AI ELO 和战斗背景。ELO 支持预设与手动输入。",
        "en": "Level ID, AI ELO and battle scene. ELO supports presets and manual input.",
    },
    "basic.level_id": {"zh": "关卡 ID", "en": "Level ID"},
    "basic.level_id_ph": {
        "zh": "例如：PVE_Soft_Node_Zombie_096",
        "en": "e.g. PVE_Soft_Node_Zombie_096",
    },
    "basic.elo": {"zh": "人机难度 ELO", "en": "Opponent ELO"},
    "basic.elo_easy": {"zh": "极易 · 500", "en": "Very Easy · 500"},
    "basic.elo_simple": {"zh": "简单 · 1000", "en": "Easy · 1000"},
    "basic.elo_normal": {"zh": "标准 · 1700", "en": "Normal · 1700"},
    "basic.elo_hard": {"zh": "困难 · 2500", "en": "Hard · 2500"},
    "basic.elo_expert": {"zh": "专家 · 3500", "en": "Expert · 3500"},
    "basic.elo_custom_prefix": {"zh": "自定义 ", "en": "Custom "},
    "basic.elo_custom_ph": {"zh": "自定义 ELO", "en": "Custom ELO"},
    "basic.scene": {"zh": "背景场景", "en": "Scene"},
    "basic.select_scene": {"zh": "选择战斗场景", "en": "Select Battle Scene"},
    "basic.rules_group": {"zh": "核心游戏规则", "en": "Core Rules"},
    "basic.must_play": {
        "zh": "必须出完所有可出的卡牌",
        "en": "Must play all playable cards",
    },
    "basic.disable_surprise": {
        "zh": "禁用僵尸锦囊阶段",
        "en": "Disable zombie Surprise phase",
    },
    "basic.enable_ready": {
        "zh": "启用 Ready-Set-Plant",
        "en": "Enable Ready-Set-Plant",
    },
    "basic.skip_hero": {
        "zh": "跳过英雄出场介绍",
        "en": "Skip hero intro",
    },

    # ===== tab_character =====
    "char.basic_group": {"zh": "基础参数", "en": "Basic Parameters"},
    "char.hero": {"zh": "英雄", "en": "Hero"},
    "char.select_hero": {"zh": "点击选择英雄…", "en": "Click to select hero…"},
    "char.faction": {"zh": "阵营", "en": "Faction"},
    "char.faction_plant": {"zh": "🌱 植物 (0)", "en": "🌱 Plants (0)"},
    "char.faction_zombie": {"zh": "🧟 僵尸 (1)", "en": "🧟 Zombies (1)"},
    "char.hp": {"zh": "初始生命值", "en": "Starting HP"},
    "char.draw": {"zh": "初始抽牌数", "en": "Opening Draw"},
    "char.turn_draw": {"zh": "每回合抽牌", "en": "Cards Per Turn"},
    "char.sun": {"zh": "初始费用", "en": "Starting Sun"},
    "char.super": {"zh": "初始超能力", "en": "Starting Superpowers"},
    "char.deck": {"zh": "卡组预设", "en": "Deck Preset"},
    "char.select_deck": {"zh": "点击选择预设卡组…", "en": "Click to select deck…"},
    "char.manual_id": {"zh": "手动 ID", "en": "Manual ID"},
    "char.manual_id_ph": {
        "zh": "手动输入卡组 ID；这里会覆盖上面的选择",
        "en": "Type a deck ID; overrides the selection above",
    },
    "char.manual_override": {
        "zh": "手动输入已覆盖…",
        "en": "Manual input overrides…",
    },
    "char.rules_group": {"zh": "规则与高级设置", "en": "Rules & Advanced"},
    "char.shuffle_deck": {"zh": "游戏开始洗牌库", "en": "Shuffle deck at start"},
    "char.shuffle_super": {"zh": "超能力池洗牌", "en": "Shuffle superpower pool"},
    "char.mulligan": {"zh": "允许初始换牌", "en": "Allow mulligan"},
    "char.die_empty": {"zh": "牌库空时抽牌死亡", "en": "Die when drawing empty"},
    "char.timed_turns": {"zh": "启用回合计时", "en": "Timed turns"},
    "char.create_all": {"zh": "创建卡组所有卡牌", "en": "Create all deck cards"},
    "char.max_hand": {"zh": "最大手牌数", "en": "Max Hand Size"},
    "char.shield_group": {"zh": "护盾与格挡规则", "en": "Shield & Block"},
    "char.shield_max": {"zh": "护盾条上限值", "en": "Block Meter Max"},
    "char.add_shield_row": {"zh": "＋ 添加概率条目", "en": "＋ Add Weight Entry"},
    "char.del_shield_row": {"zh": "删除最后一条", "en": "Remove Last Entry"},
    "char.rng_weight": {"zh": "权重 RNG", "en": "RNG Weight"},
    "char.charge_amount": {"zh": "增加格挡值", "en": "Charge Amount"},

    # ===== tab_board =====
    "board.abilities_group": {
        "zh": "全局场地能力 (BoardAbilities)",
        "en": "Board Abilities",
    },
    "board.abilities_ph": {
        "zh": "填入能力 GUID，逗号分隔 (例: 1010, 2033)...",
        "en": "Ability GUIDs, comma-separated (e.g. 1010, 2033)...",
    },
    "board.lanes_group": {"zh": "战场详细分路配置", "en": "Lane Configuration"},
    "board.lane_flat": {"zh": "平地 (1)", "en": "Ground (1)"},
    "board.lane_heights": {"zh": "高地 (0)", "en": "Heights (0)"},
    "board.lane_water": {"zh": "水路 (2)", "en": "Water (2)"},
    "board.no_cards": {"zh": "暂无卡牌配置", "en": "No cards configured"},
    "board.edit_cards": {"zh": "编辑卡牌", "en": "Edit Cards"},
    "board.shortcut_hint": {
        "zh": "💡 快捷键提示：点击选中某条道路后，可使用 <b>Delete</b> 清空 | <b>Ctrl+C</b> 复制 | <b>Ctrl+V</b> 粘贴覆盖",
        "en": "💡 Shortcuts: select a lane, then <b>Delete</b> clear | <b>Ctrl+C</b> copy | <b>Ctrl+V</b> paste",
    },
    "board.contains_n": {
        "zh": "CONTAINS {n} CARDS",
        "en": "CONTAINS {n} CARDS",
    },

    # ===== tab_events =====
    "events.group": {"zh": "游戏事件时间轴", "en": "Event Timeline"},
    "events.list_title": {"zh": "事件列表", "en": "Event List"},
    "events.list_hint": {
        "zh": "支持拖拽排序、双击修改、Delete 删除、Ctrl+↑/↓ 移动",
        "en": "Drag to reorder, double-click to edit, Delete to remove, Ctrl+↑/↓ to move",
    },
    "events.add_dialog": {"zh": "添加对话", "en": "Add Dialog"},
    "events.add_reward": {"zh": "解密发牌", "en": "Puzzle Deal"},
    "events.add_force_draw": {"zh": "强制抽卡", "en": "Force Draw"},
    "events.add_scripted": {"zh": "强制出牌", "en": "Scripted Play"},
    "events.delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "events.save": {"zh": "保存事件", "en": "Save Event"},
    "events.unknown_title": {"zh": "#{n}  未知事件", "en": "#{n}  Unknown Event"},
    "events.unknown_desc": {
        "zh": "缺少详细配置信息",
        "en": "No detailed config",
    },
    "events.msg_title": {
        "zh": "#{n}  剧情对话 · 回合 {turn}",
        "en": "#{n}  Dialog · Turn {turn}",
    },
    "events.msg_desc": {
        "zh": "说话者：{narr}  |  文本Key：{key}",
        "en": "Narrator: {narr}  |  TextKey: {key}",
    },
    "events.reward_title": {"zh": "#{n}  解密发牌", "en": "#{n}  Puzzle Deal"},
    "events.reward_desc": {
        "zh": "目标阵营：{fac}  |  发牌列表：{preview}",
        "en": "Faction: {fac}  |  Cards: {preview}",
    },
    "events.reward_more": {
        "zh": " 等 {n} 张",
        "en": " (+{n} total)",
    },
    "events.draw_title": {
        "zh": "#{n}  强制抽卡 · 回合 {turn}",
        "en": "#{n}  Force Draw · Turn {turn}",
    },
    "events.draw_desc": {
        "zh": "目标阵营：{fac}  |  指定卡牌：{card}",
        "en": "Faction: {fac}  |  Card: {card}",
    },
    "events.script_title": {
        "zh": "#{n}  强制出牌 · 回合 {turn}",
        "en": "#{n}  Scripted Play · Turn {turn}",
    },
    "events.script_desc": {
        "zh": "出牌道路：{lane}  |  指定卡牌：{card}",
        "en": "Lane: {lane}  |  Card: {card}",
    },
    "events.lane_n": {"zh": "第 {n} 路", "en": "Lane {n}"},
    "events.narrator_none": {"zh": "无", "en": "None"},
    "events.narrator_dave": {"zh": "戴夫", "en": "Crazy Dave"},
    "events.narrator_zomboss": {"zh": "僵王", "en": "Dr. Zomboss"},
    "events.edit_dialog": {"zh": "编辑对话框事件", "en": "Edit Dialog Event"},
    "events.add_dialog_title": {"zh": "添加对话框事件", "en": "Add Dialog Event"},
    "events.trigger_turn": {"zh": "触发回合", "en": "Trigger Turn"},
    "events.narrator": {"zh": "说话者", "en": "Narrator"},
    "events.narrator_none_opt": {"zh": "无 (0)", "en": "None (0)"},
    "events.narrator_dave_opt": {"zh": "戴夫 (1)", "en": "Crazy Dave (1)"},
    "events.narrator_zomboss_opt": {"zh": "僵王 (2)", "en": "Dr. Zomboss (2)"},
    "events.text_key": {"zh": "文本 Key", "en": "Text Key"},
    "events.text_key_hint": {
        "zh": "例如：DIALOG_LEVEL_01",
        "en": "e.g. DIALOG_LEVEL_01",
    },
    "events.text_key_empty": {
        "zh": "文本 Key 不能为空！",
        "en": "Text Key cannot be empty!",
    },
    "events.edit_reward": {"zh": "编辑解密发牌", "en": "Edit Puzzle Deal"},
    "events.add_reward_title": {"zh": "添加解密发牌", "en": "Add Puzzle Deal"},
    "events.recv_faction": {"zh": "接收阵营", "en": "Receiving Faction"},
    "events.faction_plant_opt": {"zh": "植物 (0)", "en": "Plants (0)"},
    "events.faction_zombie_opt": {"zh": "僵尸 (1)", "en": "Zombies (1)"},
    "events.add_card": {"zh": "添加卡牌", "en": "Add Card"},
    "events.add_card_hint": {
        "zh": "选择联想项不会保存事件；只有点击底部“保存事件”才会写入。按 Ctrl+Enter 可快速添加当前输入。",
        "en": "Picking a suggestion does not save the event. Click “Save Event” to commit. Ctrl+Enter adds current input.",
    },
    "events.add_to_list": {"zh": "添加到列表", "en": "Add to List"},
    "events.deck_top_list": {"zh": "牌库顶卡牌列表", "en": "Top-of-Deck List"},
    "events.deck_top_hint": {
        "zh": "支持拖拽排序；选中后按 Delete 删除。上面的卡会排在列表前方。",
        "en": "Drag to reorder; Delete removes selection. Top items go first.",
    },
    "events.remove_selected": {"zh": "移除选中", "en": "Remove Selected"},
    "events.invalid_card": {
        "zh": "请选择有效的卡牌，或直接输入数字 GUID。",
        "en": "Select a valid card, or type a numeric GUID.",
    },
    "events.need_one_card": {
        "zh": "请至少添加一张卡牌！",
        "en": "Add at least one card!",
    },
    "events.edit_force_draw": {"zh": "编辑强制抽卡", "en": "Edit Force Draw"},
    "events.add_force_draw_title": {
        "zh": "添加强制抽卡事件",
        "en": "Add Force Draw Event",
    },
    "events.select_card": {"zh": "选择卡牌", "en": "Select Card"},
    "events.need_valid_card": {
        "zh": "请选择有效的卡牌！",
        "en": "Please select a valid card!",
    },
    "events.edit_scripted": {"zh": "编辑强制出牌", "en": "Edit Scripted Play"},
    "events.add_scripted_title": {"zh": "添加强制出牌", "en": "Add Scripted Play"},
    "events.select_play_card": {
        "zh": "选择要打出的卡牌",
        "en": "Card to Play",
    },
    "events.select_lane": {
        "zh": "指定打出的道路",
        "en": "Target Lane",
    },
    "events.lane_any_ai": {
        "zh": "让 AI 任意发挥（不指定）",
        "en": "Let AI decide (unspecified)",
    },
    "events.play_surprise": {
        "zh": "在锦囊阶段打出（PlayDuringSurprise）",
        "en": "Play during Surprise (PlayDuringSurprise)",
    },
    "events.continue_playing": {
        "zh": "出完牌后继续允许操作（ContinuePlaying）",
        "en": "Continue playing after (ContinuePlaying)",
    },
    "events.card_input_ph": {
        "zh": "输入卡牌名 / GUID，选择联想项后点添加，或按 Ctrl+Enter 添加",
        "en": "Card name / GUID; pick suggestion then add, or Ctrl+Enter",
    },

    # ===== dialog_level_select =====
    "level.title": {
        "zh": "从 AB 包选择关卡提取",
        "en": "Select Level from AB",
    },
    "level.search_ph": {
        "zh": "搜索 (支持中文名或原始ID)...",
        "en": "Search (name or raw ID)...",
    },
    "level.global_search": {
        "zh": "🌍 全局搜索 (跨分类)",
        "en": "🌍 Global search (all tabs)",
    },
    "level.search_results": {"zh": "🔍 搜索结果", "en": "🔍 Search Results"},
    "level.cat_plant": {"zh": "🌱 植物任务", "en": "🌱 Plant Missions"},
    "level.cat_zombie": {"zh": "🧟 僵尸任务", "en": "🧟 Zombie Missions"},
    "level.cat_botd": {"zh": "🧩 每日解密", "en": "🧩 Daily Puzzle"},
    "level.confirm": {"zh": "确认提取关卡", "en": "Extract Level"},
    "level.plant_mission": {"zh": "植物任务关 {n}", "en": "Plant Mission {n}"},
    "level.zombie_mission": {"zh": "僵尸任务关 {n}", "en": "Zombie Mission {n}"},
    "level.botd_week_day": {
        "zh": "第{w}周 第{d}天",
        "en": "Week {w} Day {d}",
    },
    "level.patrol": {"zh": "巡逻", "en": "Patrol"},
    "level.random": {"zh": "随机", "en": "Random"},
    "level.hero_mission": {
        "zh": "{hero} {prefix}关卡 {n}",
        "en": "{hero} {prefix} Level {n}",
    },
    "level.other_mission": {"zh": "🎲 其他任务关", "en": "🎲 Other Missions"},
    "level.other_patrol": {"zh": "🎲 其他巡逻关", "en": "🎲 Other Patrols"},
    "level.other": {"zh": "📁 其他", "en": "📁 Other"},

    # ===== dialog_deck_select =====
    "deck.title": {"zh": "选择卡组", "en": "Select Deck"},
    "deck.search_ph": {
        "zh": "搜索当前分类：中文名 / ID / form；可输入多个关键词…",
        "en": "Search current tab: name / ID / form; multi-keywords ok…",
    },
    "deck.recommended": {
        "zh": "⭐ 推荐 ({name})",
        "en": "⭐ Recommended ({name})",
    },
    "deck.recommended_none": {"zh": "⭐ 推荐 (无)", "en": "⭐ Recommended (None)"},
    "deck.cat_preset": {"zh": "🎒 预设卡组", "en": "🎒 Presets"},
    "deck.cat_pve": {"zh": "⚔️ PVE关卡", "en": "⚔️ PVE Levels"},
    "deck.cat_tutorial": {"zh": "🎓 新手教程", "en": "🎓 Tutorial"},
    "deck.cat_daily": {"zh": "📅 每日挑战", "en": "📅 Daily Challenge"},
    "deck.cat_event": {"zh": "🧧 活动关卡", "en": "🧧 Event Levels"},

    # ===== dialog_hero_select =====
    "hero.title": {"zh": "选择英雄", "en": "Select Hero"},
    "hero.search_ph": {
        "zh": "搜索英雄名称或 ID，可输入多个关键词…",
        "en": "Search hero name or ID; multi-keywords ok…",
    },
    "hero.plants_tab": {"zh": "🌱 植物英雄", "en": "🌱 Plant Heroes"},
    "hero.zombies_tab": {"zh": "🧟 僵尸英雄", "en": "🧟 Zombie Heroes"},

    # ===== dialog_lane_cards =====
    "lane.title": {"zh": "编辑道路卡牌", "en": "Edit Lane Cards"},
    "lane.heading": {"zh": "道路卡牌编辑", "en": "Lane Card Editor"},
    "lane.subtitle": {
        "zh": "输入卡牌名、拼音关键字或 GUID 添加；列表支持多选删除与拖拽排序。",
        "en": "Add by name, pinyin keyword or GUID. Multi-select delete and drag-reorder supported.",
    },
    "lane.add_section": {"zh": "添加卡牌", "en": "Add Card"},
    "lane.input_ph": {
        "zh": "输入名称 / 拼音 / GUID，按 Enter 添加最匹配项",
        "en": "Name / pinyin / GUID, Enter adds best match",
    },
    "lane.add": {"zh": "添加", "en": "Add"},
    "lane.browse_all": {"zh": "浏览全部卡牌", "en": "Browse All Cards"},
    "lane.current_cards": {"zh": "当前道路上的卡牌", "en": "Cards on this lane"},
    "lane.current_cards_n": {
        "zh": "当前道路上的卡牌 · {n} 张",
        "en": "Cards on this lane · {n}",
    },
    "lane.list_hint": {
        "zh": "拖拽调整顺序 · Delete 删除",
        "en": "Drag to reorder · Delete to remove",
    },
    "lane.delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "lane.clear_list": {"zh": "清空列表", "en": "Clear List"},
    "lane.save_close": {"zh": "保存并关闭", "en": "Save & Close"},
    "lane.invalid_input": {
        "zh": "无法识别该卡牌，请检查输入内容或使用浏览全部卡牌。",
        "en": "Cannot resolve that card. Check input or use Browse All.",
    },
    "lane.invalid_title": {"zh": "无效输入", "en": "Invalid Input"},
    "lane.clear_confirm_title": {"zh": "确认清空", "en": "Confirm Clear"},
    "lane.clear_confirm_body": {
        "zh": "确定要清空当前道路上的所有卡牌吗？",
        "en": "Clear all cards on this lane?",
    },
    "lane.unknown_card": {"zh": "未知卡牌", "en": "Unknown Card"},
    "lane.pick_card": {"zh": "选择要添加的卡牌", "en": "Pick a Card to Add"},

    # 额外通用
    "level.hero_tab": {"zh": "🎲 {name}", "en": "🎲 {name}"},
}


def _read_lang_from_config() -> str:
    if not os.path.exists(_CONFIG_PATH):
        return DEFAULT_LANG
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        lang = data.get("language", DEFAULT_LANG)
        if lang in SUPPORTED_LANGS:
            return lang
    except Exception:
        pass
    return DEFAULT_LANG


def _write_lang_to_config(lang: str) -> None:
    data: dict[str, Any] = {}
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    data["language"] = lang
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def init_language(lang: str | None = None) -> str:
    """启动时初始化当前语言（默认从 theme_config.json 读取）。"""
    global _current_lang
    _current_lang = lang if lang in SUPPORTED_LANGS else _read_lang_from_config()
    return _current_lang


def get_lang() -> str:
    return _current_lang


def is_zh() -> bool:
    return _current_lang == "zh"


def set_language(lang: str, *, notify: bool = True, persist: bool = True) -> str:
    """切换语言。notify=True 时通知所有监听者重绘 UI。"""
    global _current_lang
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    if lang == _current_lang and not notify:
        return _current_lang
    _current_lang = lang
    if persist:
        _write_lang_to_config(lang)
    if notify:
        for cb in list(_listeners):
            try:
                cb(lang)
            except Exception:
                pass
    return _current_lang


def toggle_language() -> str:
    """中英互切并持久化、通知监听者。"""
    next_lang = "en" if _current_lang == "zh" else "zh"
    return set_language(next_lang)


def add_language_listener(callback: Callable[[str], None]) -> None:
    if callback not in _listeners:
        _listeners.append(callback)


def remove_language_listener(callback: Callable[[str], None]) -> None:
    if callback in _listeners:
        _listeners.remove(callback)


def t(key: str, /, **kwargs: Any) -> str:
    """取当前语言文案；缺失时回退中文，再回退 key 本身。"""
    entry = STRINGS.get(key)
    if not entry:
        text = key
    else:
        text = entry.get(_current_lang) or entry.get("zh") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def localized_name(item: tuple) -> str:
    """(id, zh_name[, en_name]) -> 当前语言显示名。"""
    if not item:
        return ""
    if len(item) >= 3 and _current_lang == "en" and item[2]:
        return item[2]
    return item[1] if len(item) >= 2 else str(item[0])


def localized_pairs(items: list | tuple) -> list[tuple]:
    """将 (id, zh[, en]) 列表转为 [(id, display_name), ...]。"""
    return [(it[0], localized_name(it)) for it in items]


# 模块导入时加载偏好
init_language()
