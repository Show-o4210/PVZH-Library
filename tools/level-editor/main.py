# main.py
import sys
import json
import os
from unity_manager import UnityABManager
from ui.dialog_level_select import LevelSelectDialog
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QFileDialog, QToolBar, QMessageBox, QSplitter, QTextEdit, QLabel,
    QDialog
)
from PySide6.QtCore import Qt, QTimer, QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

from data_manager import DataManager, create_default_config
from theme import (
    load_theme_config, save_theme_config, get_theme_stylesheet,
    get_theme_colors, apply_app_theme,
)
from i18n import t, get_lang, toggle_language, init_language
from ui.tab_events import GameEventsTab

# 导入拆分后的模块
from ui.tab_basic import BasicConfigTab
from ui.tab_character import CharacterConfigTab
from ui.tab_board import BoardConfigTab

class JsonHighlighter(QSyntaxHighlighter):
    """一个现代、优雅的 JSON 语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 调色板 (Tailwind 色系搭配)
        color_key = QColor("#2563EB")       # 经典深蓝：键名
        color_string = QColor("#059669")    # 翡翠绿：字符串值
        color_number = QColor("#D97706")    # 琥珀黄：数值
        color_bool = QColor("#7C3AED")      # 罗兰紫：布尔值
        color_null = QColor("#EF4444")      # 珊瑚红：空值 (null)
        color_bracket = QColor("#64748B")   # 蓝灰：括号

        # 键名格式 ("key":)
        key_format = QTextCharFormat()
        key_format.setForeground(color_key)
        key_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*"(?=\s*:)'), key_format))

        # 字符串值格式 (匹配不跟着冒号的字符串，使用 negative lookahead，100% 避免任何 invalid lookbehind 警告)
        string_format = QTextCharFormat()
        string_format.setForeground(color_string)
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*"(?!\s*:)'), string_format))

        # 数值格式
        number_format = QTextCharFormat()
        number_format.setForeground(color_number)
        self.highlighting_rules.append((QRegularExpression(r'\b-?\d+(?:\.\d+)?\b'), number_format))

        # 布尔值格式
        bool_format = QTextCharFormat()
        bool_format.setForeground(color_bool)
        bool_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'\b(true|false)\b'), bool_format))

        # null 值格式
        null_format = QTextCharFormat()
        null_format.setForeground(color_null)
        null_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'\bnull\b'), null_format))

        # 大括号、中括号格式
        bracket_format = QTextCharFormat()
        bracket_format.setForeground(color_bracket)
        self.highlighting_rules.append((QRegularExpression(r'[{}\[\]]'), bracket_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)



class PVZHCustomTool(QMainWindow):
    def __init__(self):
        super().__init__()
        init_language()
        self.setWindowTitle(t("app.title"))
        self.setGeometry(100, 100, 1400, 850) # 加大宽度以适应左右分屏
        
        theme_cfg = load_theme_config()
        self.is_dark = (theme_cfg.get("theme", "light") == "dark")
        self.apply_theme()
        
        self.dm = DataManager()
        self.dm.load_all()
        self.config = create_default_config()
        self._is_syncing = False # 互斥锁，防止 UI 和 JSON 互相触发死循环
        
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        
        tb = QToolBar(t("toolbar.main"))
        tb.setMovable(False)
        self.addToolBar(tb)
        self._toolbar = tb
        # 实例化 AB 管理器
        self.ab_manager = UnityABManager()
        
        self.act_import = tb.addAction(t("toolbar.import_json"), self.import_json)
        self.act_export = tb.addAction(t("toolbar.export_json"), self.export_json)
        tb.addSeparator()
        self.act_load_ab = tb.addAction(t("toolbar.load_ab"), self.load_from_ab)
        self.act_export_ab = tb.addAction(t("toolbar.export_ab"), self.export_to_ab)
        tb.addSeparator()
        self.theme_action = tb.addAction(
            t("toolbar.theme_light") if self.is_dark else t("toolbar.theme_dark"),
            self.toggle_theme,
        )
        self.lang_action = tb.addAction(self._lang_action_text(), self.toggle_language)
        
        # 左右分屏 Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        
        # 左侧：配置标签页
        self.tabs = QTabWidget()
        self.splitter.addWidget(self.tabs)
        
        self.tab_basic = BasicConfigTab(self.dm)
        self.tab_opponent = CharacterConfigTab(self.dm, "OpponentConfig")
        self.tab_player = CharacterConfigTab(self.dm, "PlayerConfig")
        self.tab_board = BoardConfigTab(self.dm)
        self.tab_events = GameEventsTab(self.dm)

        self.tab_modules = [
            ("tab.basic", self.tab_basic),
            ("tab.opponent", self.tab_opponent),
            ("tab.player", self.tab_player),
            ("tab.board", self.tab_board),
            ("tab.events", self.tab_events),
        ]
        
        for key, widget in self.tab_modules:
            self.tabs.addTab(widget, t(key))
            # 监听所有 Tab 发出的变更信号，触发实时的 UI -> JSON 同步
            widget.ui_changed.connect(self.trigger_ui_to_json)
            
        # 右侧：实时 JSON 预览编辑
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout = QHBoxLayout()
        self.json_title_label = QLabel(t("json.preview_title"))
        header_layout.addWidget(self.json_title_label)
        self.json_status_label = QLabel("")
        self.json_status_label.setStyleSheet("color: red; font-weight: bold;")
        header_layout.addWidget(self.json_status_label)
        header_layout.addStretch()
        right_layout.addLayout(header_layout)
        
        self.json_editor = QTextEdit()
        self.json_editor.setFontFamily("Courier")
        self.json_editor.setLineWrapMode(QTextEdit.NoWrap) # 强制不换行，开启底部横向滚动条
        self.json_highlighter = JsonHighlighter(self.json_editor.document())
        # 监听右侧文本修改，使用 QTimer 做 500ms 防抖，触发 JSON -> UI 同步
        self.json_editor.textChanged.connect(self._schedule_json_to_ui)
        self.json_debounce_timer = QTimer(self)
        self.json_debounce_timer.setSingleShot(True)
        self.json_debounce_timer.timeout.connect(self.trigger_json_to_ui)
        
        right_layout.addWidget(self.json_editor)
        self.splitter.addWidget(right_panel)
        
        # 设置左右默认比例 (左边 55%，右边 45%)
        self.splitter.setSizes([770, 630])
        
        self.statusBar().showMessage(t("status.ready"))
        
        # 增加互斥锁：在初始填充 UI 时，禁止 UI 信号触发逆向保存
        self._is_syncing = True 
        self.sync_data_to_ui()
        self._is_syncing = False
        
        self.trigger_ui_to_json() # 初始化完成后，再统一填充一次右侧 JSON

    def _lang_action_text(self):
        # 当前为中文时显示切到 English；当前为英文时显示切到 中文
        return t("toolbar.lang_to_en") if get_lang() == "zh" else t("toolbar.lang_to_zh")

    def retranslate_ui(self):
        """语言切换后刷新主窗口与各 Tab 文案。"""
        self.setWindowTitle(t("app.title"))
        self._toolbar.setWindowTitle(t("toolbar.main"))
        self.act_import.setText(t("toolbar.import_json"))
        self.act_export.setText(t("toolbar.export_json"))
        self.act_load_ab.setText(t("toolbar.load_ab"))
        self.act_export_ab.setText(t("toolbar.export_ab"))
        self.theme_action.setText(
            t("toolbar.theme_light") if self.is_dark else t("toolbar.theme_dark")
        )
        self.lang_action.setText(self._lang_action_text())
        self.json_title_label.setText(t("json.preview_title"))

        for i, (key, widget) in enumerate(self.tab_modules):
            self.tabs.setTabText(i, t(key))
            if hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()

        # 保持数据与显示同步（英雄名等会随语言变化）
        self._is_syncing = True
        self.sync_data_to_ui()
        self._is_syncing = False
        self.statusBar().showMessage(t("status.ready"))

    def toggle_language(self):
        toggle_language()
        self.retranslate_ui()

    def trigger_ui_to_json(self):
        """当左侧 UI 发生变化时，更新右侧的 JSON (带锁定滑条)"""
        if self._is_syncing: return
        self.sync_ui_to_data()
        
        self._is_syncing = True
        
        # 记录当前的滚动条位置
        v_bar = self.json_editor.verticalScrollBar()
        h_bar = self.json_editor.horizontalScrollBar()
        v_pos, h_pos = v_bar.value(), h_bar.value()
        
        # 覆盖文本
        self.json_editor.setPlainText(json.dumps(self.config, indent=4, ensure_ascii=False))
        self.json_status_label.setText("")
        self._set_json_editor_status("normal")
        
        # 恢复滚动条位置
        v_bar.setValue(v_pos)
        h_bar.setValue(h_pos)
        
        self._is_syncing = False

    def _schedule_json_to_ui(self):
        if self._is_syncing: return
        self.json_debounce_timer.start(500) # 停止打字 500ms 后解析

    def trigger_json_to_ui(self):
        """当右侧 JSON 文本手动修改合法时，更新左侧 UI"""
        if self._is_syncing: return
        
        text = self.json_editor.toPlainText().strip()
        if not text: return
        
        try:
            new_config = json.loads(text)
            self.config = new_config
            self.json_status_label.setText("")
            self._set_json_editor_status("ok")
            
            self._is_syncing = True
            self.sync_data_to_ui()
            self._is_syncing = False
            
        except Exception as e:
            # 格式不合法时只亮红框，不中断用户输入，也不弹窗报错
            self.json_status_label.setText(t("json.error"))
            self._set_json_editor_status("error")

    def sync_data_to_ui(self):
        for _, widget in self.tab_modules:
            widget.load_data(self.config)

    def sync_ui_to_data(self):
        for _, widget in self.tab_modules:
            widget.save_data(self.config)

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, t("msg.select_preset"), "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                self._is_syncing = True
                self.sync_data_to_ui()
                self._is_syncing = False
                self.trigger_ui_to_json()
                self.statusBar().showMessage(t("status.loaded", name=os.path.basename(path)))
            except Exception as e:
                QMessageBox.critical(self, t("common.error"), t("msg.load_failed", err=str(e)))

    def export_json(self):
        self.sync_ui_to_data()
        
        def check_shield(cfg_key):
            try:
                entries = self.config[cfg_key]["Parameters"]["SuperBlockTable"]["TableEntries"]
                return sum(int(e.get("RngWeight", 0)) for e in entries) == 100
            except (KeyError, TypeError, ValueError, AttributeError):
                return False

        if not check_shield("OpponentConfig"):
            QMessageBox.warning(self, t("common.warning"), t("msg.shield_opponent"))
            return
        if not check_shield("PlayerConfig"):
            QMessageBox.warning(self, t("common.warning"), t("msg.shield_player"))
            return

        # 优化绝对路径获取，避免因执行环境不同导致的相对路径乱窜问题
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{self.config['Id']}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.statusBar().showMessage(t("status.exported", path=path))
            QMessageBox.information(self, t("common.success"), t("msg.export_ok", path=path))
        except Exception as e:
            QMessageBox.critical(self, t("common.error"), t("msg.export_failed", err=str(e)))

    def load_from_ab(self):
        """从 AB 包中提取数据到 UI"""
        if not self.ab_manager.check_input_exists():
            QMessageBox.warning(self, t("common.warning"), t("msg.ab_missing"))
            return
            
        try:
            self.statusBar().showMessage(t("status.scanning_ab"))
            QApplication.processEvents() # 让 UI 刷新状态栏
            
            level_ids = self.ab_manager.get_all_level_ids()
            if not level_ids:
                QMessageBox.warning(self, t("msg.ab_no_levels_title"), t("msg.ab_no_levels"))
                return
                
            # 召唤高级分页关卡弹窗！
            dialog = LevelSelectDialog(level_ids, self)
            if dialog.exec() == QDialog.Accepted and dialog.selected_level_id:
                target_id = dialog.selected_level_id
                
                # 开始提取 JSON
                ab_config = self.ab_manager.load_level(target_id)
                self.config = ab_config
                
                # 同步到 UI 并锁定互斥锁防止踩踏
                self._is_syncing = True
                self.sync_data_to_ui()
                self._is_syncing = False
                self.trigger_ui_to_json()
                
                self.statusBar().showMessage(t("status.loaded_ab", id=target_id))
                
        except Exception as e:
            QMessageBox.critical(self, t("msg.read_failed_title"), t("msg.read_failed", err=str(e)))


    def export_to_ab(self):
        """将当前 UI 状态打包回 AB 包并输出"""
        if not self.ab_manager.check_input_exists():
            QMessageBox.warning(self, t("common.warning"), t("msg.ab_pack_missing"))
            return
            
        self.sync_ui_to_data()

        def check_shield(cfg_key):
            try:
                entries = self.config[cfg_key]["Parameters"]["SuperBlockTable"]["TableEntries"]
                return sum(int(e.get("RngWeight", 0)) for e in entries) == 100
            except (KeyError, TypeError, ValueError, AttributeError):
                return False

        if not check_shield("OpponentConfig"):
            QMessageBox.warning(self, t("common.warning"), t("msg.shield_opponent"))
            return
        if not check_shield("PlayerConfig"):
            QMessageBox.warning(self, t("common.warning"), t("msg.shield_player"))
            return

        # 使用当前配置里的 Id 字段寻找要覆盖的目标
        target_id = self.config.get("Id", "")
        if not target_id:
            QMessageBox.warning(self, t("common.warning"), t("msg.missing_level_id"))
            return
            
        try:
            self.statusBar().showMessage(t("status.packing", id=target_id))
            QApplication.processEvents()
            
            out_path = self.ab_manager.pack_level(target_id, self.config)
            
            self.statusBar().showMessage(t("status.pack_done"))
            QMessageBox.information(self, t("msg.pack_ok_title"), t("msg.pack_ok", path=out_path))
            
        except Exception as e:
            QMessageBox.critical(self, t("msg.pack_failed_title"), t("msg.pack_failed", err=str(e)))


    def _set_json_editor_status(self, status="normal"):
        """根据主题设置 JSON 预览区边框状态，避免硬编码浅色样式破坏深色模式"""
        colors = get_theme_colors(self.is_dark)
        border = colors.get("border", "#D1D5DB")
        input_bg = colors.get("input_bg", "#FFFFFF")
        text = colors.get("text", "#1F2937")
        width = 1
        if status == "ok":
            border = "#10B981"
        elif status == "error":
            border = "#EF4444"
            width = 2
        self.json_editor.setStyleSheet(
            f"QTextEdit {{ background-color: {input_bg}; color: {text}; "
            f"border: {width}px solid {border}; border-radius: 6px; }}"
        )

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            self.theme_action.setText(t("toolbar.theme_light"))
        else:
            self.theme_action.setText(t("toolbar.theme_dark"))
            
        theme_cfg = load_theme_config()
        theme_cfg["theme"] = "dark" if self.is_dark else "light"
        save_theme_config(theme_cfg)
        
        self.apply_theme()
        # 主题切换后同步刷新 JSON 预览区边框/底色
        self._set_json_editor_status("normal")

    def apply_theme(self):
        sheet = get_theme_stylesheet(self.is_dark)
        self.setStyleSheet(sheet)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(sheet)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_app_theme(app)
    window = PVZHCustomTool()
    window.show()
    sys.exit(app.exec())
