# theme.py
"""全局主题：主窗口与所有弹窗共用，避免 dialog 硬编码浅色样式。"""
from __future__ import annotations

import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme_config.json")

DEFAULT_THEME_CONFIG = {
    "theme": "light",
    "light": {
        "bg": "#F8FAFC",
        "card_bg": "#FFFFFF",
        "text": "#1F2937",
        "label_text": "#475569",
        "title_text": "#0F172A",
        "border": "#E2E8F0",
        "border_hover": "#CBD5E1",
        "input_bg": "#FFFFFF",
        "primary_blue": "#2563EB",
        "hover_blue": "#1D4ED8",
        "pressed_blue": "#1E40AF",
        "primary_purple": "#7C3AED",
        "hover_purple": "#6D28D9",
        "item_hover": "#F8FAFC",
        "item_selected": "#EFF6FF",
        "item_selected_text": "#1D4ED8",
        "scrollbar_handle": "#CBD5E1",
        "scrollbar_hover": "#94A3B8",
        "danger_bg": "#FEF2F2",
        "danger_text": "#DC2626",
        "danger_border": "#FECACA",
    },
    "dark": {
        "bg": "#0F172A",
        "card_bg": "#1E293B",
        "text": "#F1F5F9",
        "label_text": "#94A3B8",
        "title_text": "#F8FAFC",
        "border": "#334155",
        "border_hover": "#475569",
        "input_bg": "#0F172A",
        "primary_blue": "#3B82F6",
        "hover_blue": "#60A5FA",
        "pressed_blue": "#2563EB",
        "primary_purple": "#8B5CF6",
        "hover_purple": "#A78BFA",
        "item_hover": "#334155",
        "item_selected": "#1E3A8A",
        "item_selected_text": "#60A5FA",
        "scrollbar_handle": "#475569",
        "scrollbar_hover": "#64748B",
        "danger_bg": "#7F1D1D",
        "danger_text": "#FECACA",
        "danger_border": "#991B1B",
    },
}


def load_theme_config() -> dict:
    """读取或生成 theme_config.json。"""
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 合并缺省色板，避免旧配置缺 key
            merged = json.loads(json.dumps(DEFAULT_THEME_CONFIG))
            if isinstance(data, dict):
                if "theme" in data:
                    merged["theme"] = data["theme"]
                # 保留语言偏好（由 i18n 模块写入），避免主题读写覆盖
                if "language" in data:
                    merged["language"] = data["language"]
                for mode in ("light", "dark"):
                    if isinstance(data.get(mode), dict):
                        merged[mode].update(data[mode])
            return merged
        except Exception:
            pass

    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_THEME_CONFIG, f, indent=4, ensure_ascii=False)
    except Exception:
        pass
    return json.loads(json.dumps(DEFAULT_THEME_CONFIG))


def save_theme_config(config_data: dict) -> None:
    try:
        # 合并写入，避免覆盖仅由其它模块维护的字段（如 language）
        existing = {}
        if os.path.exists(_CONFIG_PATH):
            try:
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, dict):
                    existing = {}
            except Exception:
                existing = {}
        if isinstance(config_data, dict):
            existing.update(config_data)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def is_dark_theme() -> bool:
    return load_theme_config().get("theme", "light") == "dark"


def get_theme_colors(is_dark: bool | None = None) -> dict:
    cfg = load_theme_config()
    if is_dark is None:
        is_dark = cfg.get("theme", "light") == "dark"
    return dict(cfg["dark"] if is_dark else cfg["light"])


def get_theme_stylesheet(is_dark: bool | None = None) -> str:
    """主窗口 + 弹窗通用 QSS。"""
    if is_dark is None:
        is_dark = is_dark_theme()
    colors = get_theme_colors(is_dark)

    bg = colors.get("bg", "#F8FAFC")
    card_bg = colors.get("card_bg", "#FFFFFF")
    text = colors.get("text", "#1F2937")
    label_text = colors.get("label_text", "#475569")
    title_text = colors.get("title_text", "#0F172A")
    border = colors.get("border", "#E2E8F0")
    border_hover = colors.get("border_hover", "#CBD5E1")
    input_bg = colors.get("input_bg", "#FFFFFF")

    primary_blue = colors.get("primary_blue", "#2563EB")
    hover_blue = colors.get("hover_blue", "#1D4ED8")
    pressed_blue = colors.get("pressed_blue", "#1E40AF")

    primary_purple = colors.get("primary_purple", "#7C3AED")
    hover_purple = colors.get("hover_purple", "#6D28D9")

    item_hover = colors.get("item_hover", "#F8FAFC")
    item_selected = colors.get("item_selected", "#EFF6FF")
    item_selected_text = colors.get("item_selected_text", "#1D4ED8")

    scrollbar_handle = colors.get("scrollbar_handle", "#CBD5E1")
    scrollbar_hover = colors.get("scrollbar_hover", "#94A3B8")

    danger_bg = colors.get("danger_bg", "#FEF2F2")
    danger_text = colors.get("danger_text", "#DC2626")
    danger_border = colors.get("danger_border", "#FECACA")

    return f"""
        /* ===== 窗口根 ===== */
        QMainWindow, QDialog, QWidget#centralWidget, QWidget#rightPanel {{
            background-color: {bg};
            color: {text};
        }}

        QWidget#centralWidget {{
            background-color: {bg};
        }}

        QToolBar {{
            background-color: {card_bg};
            border-bottom: 1px solid {border};
            spacing: 6px;
            padding: 4px;
        }}

        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 6px 12px;
            color: {text};
            font-weight: bold;
        }}

        QToolButton:hover {{
            background-color: {item_hover};
            border: 1px solid {border_hover};
        }}

        QToolButton:pressed {{
            background-color: {item_selected};
            color: {primary_blue};
        }}

        QStatusBar {{
            background-color: {card_bg};
            border-top: 1px solid {border};
            color: {label_text};
        }}

        QWidget {{
            color: {text};
            font-family: "Segoe UI", "Microsoft YaHei";
            font-size: 13px;
        }}

        /* ===== 标签 ===== */
        QLabel {{
            background: transparent;
            color: {label_text};
            font-weight: 500;
        }}

        QLabel#field_label, QLabel#fieldLabel, QLabel#sectionHint,
        QLabel#dialog_subtitle, QLabel#hintLabel, QLabel#hint_label,
        QLabel#mutedLabel, QLabel#countLabel {{
            background: transparent;
            color: {label_text};
        }}

        QLabel#dialogTitle, QLabel#dialog_title, QLabel#sectionTitle,
        QLabel#section_label, QLabel#gridDialogTitle {{
            color: {title_text};
            font-weight: 700;
            background: transparent;
        }}

        QLabel#dialogTitle, QLabel#dialog_title, QLabel#gridDialogTitle {{
            font-size: 18px;
            font-weight: 800;
        }}

        QLabel#dialog_title {{
            font-size: 22px;
        }}

        QLabel#sectionTitle {{
            font-size: 15px;
        }}

        QLabel#dialog_subtitle, QLabel#hintLabel, QLabel#hint_label {{
            font-size: 12px;
            font-weight: 400;
        }}

        QFrame#dialogDivider {{
            background-color: {border};
            border: none;
            max-height: 1px;
            min-height: 1px;
        }}

        /* ===== 输入控件 ===== */
        QLineEdit,
        QTextEdit,
        QPlainTextEdit,
        QSpinBox,
        QComboBox {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 9px 12px;
            selection-background-color: {item_selected};
            selection-color: {item_selected_text};
        }}

        QLineEdit:hover,
        QTextEdit:hover,
        QPlainTextEdit:hover,
        QSpinBox:hover,
        QComboBox:hover {{
            border: 1px solid {border_hover};
            background-color: {input_bg};
        }}

        QLineEdit:focus,
        QTextEdit:focus,
        QPlainTextEdit:focus,
        QSpinBox:focus,
        QComboBox:focus {{
            border: 1px solid {primary_blue};
            background-color: {input_bg};
        }}

        QComboBox:disabled {{
            color: {label_text};
            background-color: {card_bg};
            border: 1px solid {border};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 32px;
            background: transparent;
        }}

        QComboBox::down-arrow {{
            image: none;
            width: 0px;
            height: 0px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {card_bg};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {item_selected};
            selection-color: {item_selected_text};
            outline: none;
        }}

        QSpinBox::up-button,
        QSpinBox::down-button {{
            border: none;
            background: transparent;
            width: 24px;
        }}

        QSpinBox::up-arrow,
        QSpinBox::down-arrow {{
            width: 0px;
            height: 0px;
        }}

        /* Completer 弹出列表 */
        QAbstractItemView {{
            background-color: {card_bg};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {item_selected};
            selection-color: {item_selected_text};
            outline: none;
        }}

        /* ===== 按钮 ===== */
        QPushButton {{
            background-color: {primary_blue};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 9px 18px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background-color: {hover_blue};
        }}

        QPushButton:pressed {{
            background-color: {pressed_blue};
        }}

        QPushButton#secondaryButton, QPushButton#ghost_btn,
        QPushButton#secondary_btn, QPushButton#selectButton {{
            background-color: {card_bg};
            color: {primary_blue};
            border: 1px solid {border};
        }}

        QPushButton#secondaryButton:hover, QPushButton#ghost_btn:hover,
        QPushButton#secondary_btn:hover, QPushButton#selectButton:hover {{
            background-color: {item_hover};
            border: 1px solid {border_hover};
        }}

        QPushButton#selectButton {{
            color: {text};
            text-align: left;
            font-weight: 600;
            padding: 10px 14px;
        }}

        QPushButton#searchSelectButton {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 10px 14px;
            text-align: left;
            font-weight: 500;
            min-height: 32px;
        }}

        QPushButton#searchSelectButton:hover {{
            background-color: {item_hover};
            border: 1px solid {border_hover};
        }}

        QPushButton#searchSelectButton:pressed {{
            background-color: {item_selected};
            border: 1px solid {primary_blue};
        }}

        QPushButton#primary_btn {{
            background-color: {primary_blue};
            color: white;
        }}

        QPushButton#primary_btn:hover {{
            background-color: {hover_blue};
        }}

        QPushButton#primary_btn:pressed {{
            background-color: {pressed_blue};
        }}

        QPushButton#danger_btn, QPushButton#dangerButton, QPushButton#danger_btn_cards {{
            background-color: {danger_bg};
            color: {danger_text};
            border: 1px solid {danger_border};
        }}

        QPushButton#danger_btn:hover, QPushButton#dangerButton:hover,
        QPushButton#danger_btn_cards:hover {{
            background-color: {danger_bg};
            border: 1px solid {danger_text};
        }}

        QPushButton#purpleButton {{
            background-color: {primary_purple};
            color: white;
        }}

        QPushButton#purpleButton:hover {{
            background-color: {hover_purple};
        }}

        /* ===== 分组 / 卡片 ===== */
        QGroupBox {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 16px;
            margin-top: 12px;
            padding: 18px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
            color: {label_text};
            font-weight: 600;
            background-color: {bg};
        }}

        QWidget#shieldRow, QFrame#panel_card, QFrame#formCard, QFrame#cardFrame {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
        }}

        QFrame#lane_card {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 14px;
        }}

        QFrame#lane_card:hover {{
            border: 1px solid {border_hover};
            background-color: {item_hover};
        }}

        QFrame#lane_card[active="true"] {{
            background-color: {item_selected};
            border: 1px solid {primary_blue};
            border-radius: 14px;
        }}

        /* ===== Tab ===== */
        QTabWidget::pane {{
            border: 1px solid {border};
            background: {card_bg};
            border-radius: 16px;
            top: -1px;
        }}

        QTabBar::tab {{
            background: transparent;
            color: {label_text};
            padding: 10px 18px;
            margin-right: 4px;
            border-radius: 10px;
            font-weight: 500;
        }}

        QTabBar::tab:hover {{
            background-color: {item_hover};
            color: {text};
        }}

        QTabBar::tab:selected {{
            background-color: {item_selected};
            color: {primary_blue};
        }}

        QSplitter::handle {{
            background: transparent;
        }}

        QSplitter::handle:hover {{
            background: {border};
        }}

        /* ===== 滚动条 ===== */
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical {{
            background: {scrollbar_handle};
            border-radius: 5px;
            min-height: 32px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {scrollbar_hover};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}

        QScrollBar:horizontal {{
            background: transparent;
            height: 10px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal {{
            background: {scrollbar_handle};
            border-radius: 5px;
            min-width: 32px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {scrollbar_hover};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ===== 列表（弹窗网格 / 普通列表） ===== */
        QListWidget {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 6px;
            outline: none;
            color: {text};
        }}

        QListWidget::item {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 12px 10px;
            margin: 4px;
            color: {text};
        }}

        QListWidget::item:hover {{
            background-color: {item_hover};
            border: 1px solid {border_hover};
        }}

        QListWidget::item:selected {{
            background-color: {item_selected};
            border: 1px solid {primary_blue};
            color: {primary_blue};
            font-weight: 600;
        }}

        /* 网格选择弹窗：无外框列表 */
        QListWidget#gridSelectList {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 4px;
        }}

        QListWidget#gridSelectList::item {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 14px 10px;
            margin: 6px;
            color: {text};
            min-height: 58px;
        }}

        QListWidget#gridSelectList::item:hover {{
            background-color: {item_hover};
            border: 1px solid {border_hover};
        }}

        QListWidget#gridSelectList::item:selected {{
            background-color: {item_selected};
            border: 1px solid {primary_blue};
            color: {primary_blue};
            font-weight: 600;
        }}

        /* 事件编辑弹窗：列表项承载自定义卡片，背景透明 */
        QListWidget#eventCardList {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 0px;
        }}

        QListWidget#eventCardList::item {{
            background-color: transparent;
            border: none;
            margin: 2px 0px;
            padding: 0px;
        }}

        QListWidget#eventCardList::item:hover,
        QListWidget#eventCardList::item:selected {{
            background-color: transparent;
            border: none;
        }}

        QListWidget::drop-indicator {{
            background-color: {primary_blue};
            height: 3px;
            border-radius: 1px;
        }}

        /* ===== 复选框 ===== */
        QCheckBox {{
            background-color: {card_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 12px 14px;
            spacing: 10px;
            font-weight: 500;
        }}

        QCheckBox:hover {{
            background-color: {item_hover};
            border: 1px solid {border_hover};
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid {border};
            background-color: {input_bg};
        }}

        QCheckBox::indicator:checked {{
            background-color: {primary_blue};
            border: 1px solid {primary_blue};
        }}

        /* 弹窗内紧凑复选框（无卡片感） */
        QCheckBox#plainCheck {{
            background: transparent;
            border: none;
            border-radius: 0px;
            padding: 4px 2px;
        }}

        QCheckBox#plainCheck:hover {{
            background: transparent;
            border: none;
        }}

        /* ===== 消息框 ===== */
        QMessageBox {{
            background-color: {bg};
            color: {text};
        }}

        QMessageBox QLabel {{
            color: {text};
        }}
    """


def apply_dialog_theme(dialog) -> None:
    """给独立 QDialog 应用当前主题（不依赖是否继承主窗口 QSS）。"""
    dialog.setStyleSheet(get_theme_stylesheet())


def apply_app_theme(app, is_dark: bool | None = None) -> None:
    """应用到 QApplication，覆盖 QMessageBox 等无 parent 的窗口。"""
    if is_dark is None:
        is_dark = is_dark_theme()
    app.setStyleSheet(get_theme_stylesheet(is_dark))
