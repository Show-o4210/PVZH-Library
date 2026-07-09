# ui/tab_theme.py
"""主题设置页面 - 允许用户切换和预览主题"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QListWidget, QListWidgetItem, QLabel, QTextEdit,
                               QPushButton, QScrollArea, QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette

from constants import get_theme_list, get_theme, set_current_theme, build_qss_from_theme
from theme_preset import GLASS_QSS
import i18n


class ThemePreviewCard(QFrame):
    """主题预览卡片"""
    
    def __init__(self, theme_key: str, theme_data: dict, parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.theme_data = theme_data
        self.setup_ui()
        self.apply_preview_style()
    
    def setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 主题名称
        self.name_label = QLabel(self.theme_data["name"])
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        layout.addWidget(self.name_label)
        
        # 主题描述
        self.desc_label = QLabel(self.theme_data["description"])
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.desc_label)
        
        # 颜色预览条
        colors_widget = QWidget()
        colors_layout = QHBoxLayout(colors_widget)
        colors_layout.setContentsMargins(0, 10, 0, 10)
        colors_layout.setSpacing(5)
        
        colors = self.theme_data["colors"]
        preview_colors = [
            (colors["primary"], "主色"),
            (colors["secondary"], "辅色"),
            (colors["text_main"], "文字"),
            (colors["bg_dark"], "背景"),
        ]
        
        for color, name in preview_colors:
            color_block = QLabel()
            color_block.setFixedSize(40, 25)
            # 提取实际颜色值（处理rgba格式）
            if color.startswith("rgba"):
                # 从 rgba(r,g,b,a) 提取 rgb 部分用于显示
                import re
                match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+)', color)
                if match:
                    hex_color = f"#{int(match.group(1)):02x}{int(match.group(2)):02x}{int(match.group(3)):02x}"
                    color_block.setStyleSheet(f"background-color: {hex_color}; border-radius: 3px;")
                else:
                    color_block.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            else:
                color_block.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            color_block.setToolTip(name)
            colors_layout.addWidget(color_block)
        
        colors_layout.addStretch()
        layout.addWidget(colors_widget)
        
        self.apply_btn = QPushButton(i18n.t("theme.apply"))
        self.apply_btn.setFixedHeight(32)
        layout.addWidget(self.apply_btn)
    
    def apply_preview_style(self):
        """应用预览卡片样式"""
        self.setStyleSheet("""
            ThemePreviewCard {
                background-color: rgba(30, 30, 40, 150);
                border: 1px solid rgba(77, 168, 218, 40);
                border-radius: 8px;
            }
            ThemePreviewCard:hover {
                border: 1px solid #4da8da;
                background-color: rgba(77, 168, 218, 20);
            }
        """)


class TabTheme(QWidget):
    """主题设置标签页"""

    theme_changed = Signal(str)
    language_changed = Signal(str)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        self.retranslate_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.lang_group = QGroupBox()
        lang_layout = QVBoxLayout(self.lang_group)
        self.lang_hint = QLabel()
        self.lang_hint.setWordWrap(True)
        self.lang_hint.setStyleSheet("color: #aaa; padding: 6px;")
        lang_layout.addWidget(self.lang_hint)
        lang_btn_row = QHBoxLayout()
        self.btn_lang_zh = QPushButton()
        self.btn_lang_en = QPushButton()
        self.btn_lang_zh.setCheckable(True)
        self.btn_lang_en.setCheckable(True)
        self.btn_lang_zh.clicked.connect(lambda: self._set_language(i18n.LANG_ZH))
        self.btn_lang_en.clicked.connect(lambda: self._set_language(i18n.LANG_EN))
        lang_btn_row.addWidget(self.btn_lang_zh)
        lang_btn_row.addWidget(self.btn_lang_en)
        lang_btn_row.addStretch()
        lang_layout.addLayout(lang_btn_row)
        layout.addWidget(self.lang_group)

        self.info_group = QGroupBox()
        info_layout = QVBoxLayout(self.info_group)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #aaa; padding: 10px;")
        info_layout.addWidget(self.info_label)
        layout.addWidget(self.info_group)

        self.current_group = QGroupBox()
        current_layout = QHBoxLayout(self.current_group)
        self.current_theme_label = QLabel()
        self.current_theme_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        current_layout.addWidget(self.current_theme_label)
        current_layout.addStretch()
        layout.addWidget(self.current_group)

        self.theme_group = QGroupBox()
        theme_layout = QVBoxLayout(self.theme_group)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(scroll_content)
        theme_layout.addWidget(scroll)
        layout.addWidget(self.theme_group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.reset_btn = QPushButton()
        self.reset_btn.clicked.connect(self.reset_to_default)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        self.load_themes()
        self.update_current_theme_display()
        self._sync_lang_buttons()

    def retranslate_ui(self):
        self.lang_group.setTitle(i18n.t("theme.lang_group"))
        self.lang_hint.setText(i18n.t("common.lang.hint"))
        self.btn_lang_zh.setText(i18n.t("common.lang.zh"))
        self.btn_lang_en.setText(i18n.t("common.lang.en"))
        self.info_group.setTitle(i18n.t("theme.info_group"))
        self.info_label.setText(i18n.t("theme.info"))
        self.current_group.setTitle(i18n.t("theme.current_group"))
        self.theme_group.setTitle(i18n.t("theme.list_group"))
        self.reset_btn.setText(i18n.t("theme.reset"))
        self.update_current_theme_display()
        self.load_themes()
        self._sync_lang_buttons()

    def _sync_lang_buttons(self):
        lang = i18n.get_language()
        self.btn_lang_zh.setChecked(lang == i18n.LANG_ZH)
        self.btn_lang_en.setChecked(lang == i18n.LANG_EN)

    def _set_language(self, lang: str):
        if lang == i18n.get_language():
            self._sync_lang_buttons()
            return
        i18n.set_language(lang, notify=True)
        self.language_changed.emit(lang)
        self._sync_lang_buttons()

    def load_themes(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        themes = get_theme_list()
        row, col = 0, 0
        max_cols = 2
        for theme_key, theme_name in themes:
            theme_data = get_theme(theme_key)
            card = ThemePreviewCard(theme_key, theme_data)
            card.apply_btn.clicked.connect(lambda checked, tk=theme_key: self.apply_theme(tk))
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def apply_theme(self, theme_key: str):
        if self.main_window:
            self.main_window.switch_theme(theme_key)
            self.update_current_theme_display()
            self.theme_changed.emit(theme_key)

    def update_current_theme_display(self):
        from constants import get_current_theme, get_theme
        current_key = get_current_theme()
        theme_data = get_theme(current_key)
        self.current_theme_label.setText(
            i18n.t("theme.current", name=theme_data["name"], desc=theme_data["description"])
        )

    def refresh_theme_display(self):
        self.update_current_theme_display()
        self.load_themes()

    def reset_to_default(self):
        self.apply_theme("PhantomDeep")