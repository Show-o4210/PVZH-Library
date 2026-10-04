# ui_main.py
import json
import html
import re
from PySide6.QtWidgets import (QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QStackedWidget, QSplitter, 
                               QApplication, QListWidget, QListWidgetItem, QPushButton)
from PySide6.QtCore import Qt, QSettings, QObject, QEvent, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QKeySequence, QShortcut

from card_model import CardModel
from ui.tab_basic import TabBasic
from ui.tab_subtypes import TabSubtypes
from ui.tab_tags import TabTags
from ui.tab_abilities import TabAbilities
from ui.logic.panel_main import PanelLogic
from ui.tab_export import TabExport
from ui.tab_theme import TabTheme
from ui.tab_help import TabHelp
from project_manager import ProjectManager
from ui.tab_project import TabProject

from widgets import ArenaBackgroundWidget
from constants import get_theme_list, get_current_theme, set_current_theme, build_qss_from_theme
import i18n

APP_VERSION = "2.1"


class FastScrollFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                scroll_area = None
                if hasattr(obj, 'verticalScrollBar'):
                    scroll_area = obj
                elif hasattr(obj, 'parent') and hasattr(obj.parent(), 'verticalScrollBar'):
                    scroll_area = obj.parent()

                if scroll_area:
                    vbar = scroll_area.verticalScrollBar()
                    delta = event.angleDelta().y()
                    if delta != 0:
                        step = vbar.singleStep() * 10
                        if delta > 0:
                            vbar.setValue(vbar.value() - step)
                        else:
                            vbar.setValue(vbar.value() + step)
                        return True
        return super().eventFilter(obj, event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1400, 900)
        self.model = CardModel()
        self.pm = ProjectManager()
        self._is_syncing = False
        self._dirty = False
        self._original_guid = self.model.guid
        self._tab_meta = []  # (icon, title_key)

        self.settings = QSettings("ModdingTool", "PvZHeroesEditor")

        saved_lang = self.settings.value("language", i18n.LANG_ZH)
        i18n.set_language(saved_lang if saved_lang in i18n.SUPPORTED else i18n.LANG_ZH, notify=False)

        saved_theme = self.settings.value("theme", "PhantomDeep")
        set_current_theme(saved_theme)
        self.apply_theme()
        self.setWindowTitle(i18n.app_title())

        self.is_sidebar_pinned = False
        self.sidebar_delay_timer = QTimer(self)
        self.sidebar_delay_timer.setSingleShot(True)
        self.sidebar_delay_timer.timeout.connect(self._do_collapse)

        # JSON 预览防抖，避免每次按键全量重绘
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(120)
        self._preview_timer.timeout.connect(self._do_update_json_preview)

        self._setup_ui()

        geometry = self.settings.value("windowGeometry")
        if geometry:
            self.restoreGeometry(geometry)

        splitter_state = self.settings.value("splitterSizes_v3")
        if splitter_state:
            self.splitter.restoreState(splitter_state)

        self.update_json_preview()

    def apply_theme(self):
        qss = build_qss_from_theme()
        self.setStyleSheet(qss)
        if hasattr(self, 'settings'):
            self.settings.setValue("theme", get_current_theme())

    def switch_theme(self, theme_name):
        if set_current_theme(theme_name):
            self.apply_theme()
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if hasattr(widget, "refresh_theme_display"):
                    widget.refresh_theme_display()
            if hasattr(self, "bg_widget") and hasattr(self.bg_widget, "refresh_theme"):
                self.bg_widget.refresh_theme()

    def handle_external_import(self, path, guid):
        """处理来自 Basic 页的外部导入请求"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            guid_str = str(guid)
            if guid_str not in data:
                QMessageBox.warning(
                    self, i18n.t("common.not_found"), i18n.t("dlg.guid_missing", guid=guid_str)
                )
                return

            card_data = data[guid_str]
            self.load_card_to_workbench(card_data)
            self.model.guid = guid
            self._original_guid = guid
            if hasattr(self.tab_basic, "update_ui"):
                self.tab_basic.update_ui(self.model)
            self.update_json_preview(immediate=True)
            self._mark_dirty()

            QMessageBox.information(
                self, i18n.t("common.success"), i18n.t("dlg.import_ok", guid=guid_str)
            )
        except Exception as e:
            QMessageBox.critical(
                self, i18n.t("common.import_failed"), i18n.t("dlg.import_err", err=e)
            )

    def _setup_ui(self):
        self.bg_widget = ArenaBackgroundWidget(self)
        self.setCentralWidget(self.bg_widget)

        main_layout = QHBoxLayout(self.bg_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.fast_scroll_filter = FastScrollFilter(self)

        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(45)
        self.sidebar_container.setObjectName("SidebarContainer")
        sidebar_vbox = QVBoxLayout(self.sidebar_container)
        sidebar_vbox.setContentsMargins(0, 5, 0, 0)
        sidebar_vbox.setSpacing(5)

        self.pin_btn = QPushButton("📌")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setFixedSize(45, 30)
        self.pin_btn.setStyleSheet("background: transparent; border: none; font-size: 16px;")
        self.pin_btn.clicked.connect(self.toggle_sidebar_pin)
        sidebar_vbox.addWidget(self.pin_btn, 0, Qt.AlignHCenter)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMouseTracking(True)
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setStyleSheet("background: transparent; border: none;")
        self.sidebar.installEventFilter(self.fast_scroll_filter)
        sidebar_vbox.addWidget(self.sidebar)

        main_layout.addWidget(self.sidebar_container)

        self.sidebar_anim = QPropertyAnimation(self.sidebar_container, b"minimumWidth")
        self.sidebar_anim.setDuration(300)
        self.sidebar_anim.setEasingCurve(QEasingCurve.OutQuint)
        self.sidebar_container.installEventFilter(self)

        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        self.stacked_widget = QStackedWidget()
        self.splitter.addWidget(self.stacked_widget)

        # ================= 页面注册 =================
        self.tab_project = TabProject(self.pm)
        self.tab_project.edit_card_requested.connect(self.load_card_to_workbench)
        self.tab_project.project_switch_requested.connect(self.handle_project_switch)

        self.tab_basic = TabBasic(self.model)
        self.tab_basic.save_requested.connect(self.save_card_to_project)
        self.tab_basic.import_requested.connect(self.handle_external_import)

        self.tab_subtypes = TabSubtypes()
        self.tab_tags = TabTags()
        self.tab_abilities = TabAbilities()
        self.tab_logic = PanelLogic()
        self.tab_export = TabExport(self.pm)
        self.tab_theme = TabTheme(self)
        self.tab_theme.language_changed.connect(self.apply_language)
        self.tab_help = TabHelp()

        self._register_tab("🏠", "tab.project", self.tab_project)
        self._register_tab("📋", "tab.basic", self.tab_basic)
        self._register_tab("🧬", "tab.subtypes", self.tab_subtypes)
        self._register_tab("🏷️", "tab.tags", self.tab_tags)
        self._register_tab("✨", "tab.abilities", self.tab_abilities)
        self._register_tab("🛠️", "tab.logic", self.tab_logic)
        self._register_tab("💾", "tab.export", self.tab_export)
        self._register_tab("🎨", "tab.theme", self.tab_theme)
        self._register_tab("📖", "tab.help", self.tab_help)

        self.sidebar.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
        self.retranslate_ui()

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setUndoRedoEnabled(False)  # 避免抢走技能逻辑 Ctrl+Z/Y
        self.json_preview.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.json_preview.setStyleSheet("""
            QTextEdit { 
                background-color: #1e1e1e; 
                border: 1px solid #333333;
                border-radius: 6px;
            }
        """)
        self.json_preview.installEventFilter(self.fast_scroll_filter)
        if hasattr(self.json_preview, 'viewport'):
            self.json_preview.viewport().installEventFilter(self.fast_scroll_filter)

        preview_layout.addWidget(self.json_preview)
        self.splitter.addWidget(preview_container)
        self.splitter.setSizes([900, 500])

        tabs_with_data = [
            self.tab_basic, self.tab_subtypes, self.tab_tags,
            self.tab_abilities, self.tab_logic,
        ]
        for tab in tabs_with_data:
            if hasattr(tab, "data_changed"):
                tab.data_changed.connect(self.sync_ui_to_model_only)

        from PySide6.QtWidgets import QScrollArea
        for i in range(self.stacked_widget.count()):
            tab_widget = self.stacked_widget.widget(i)
            if hasattr(tab_widget, "findChild"):
                for scroll_area in tab_widget.findChildren(QScrollArea):
                    if scroll_area and hasattr(scroll_area, 'viewport'):
                        scroll_area.viewport().installEventFilter(self.fast_scroll_filter)
            tab_widget.installEventFilter(self.fast_scroll_filter)

        self._setup_shortcuts()

    def handle_project_switch(self, request: str):
        """工程切换 / 新建，带未保存确认"""
        if self._dirty:
            reply = QMessageBox.question(
                self,
                i18n.t("dlg.unsaved_title"),
                i18n.t("dlg.unsaved_project"),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                if not self.save_card_to_project():
                    return

        if request.startswith("__create__:"):
            name = request.split(":", 1)[1]
            self.tab_project.apply_project_create(name)
            self._set_clean()
            self.setWindowTitle(i18n.app_title(name))
            return

        if request == self.pm.current_project_name:
            self.tab_project.refresh_card_roster()
            return

        self.tab_project.apply_project_load(request)
        self._set_clean()
        self.setWindowTitle(i18n.app_title(request))

    def toggle_sidebar_pin(self):
        self.is_sidebar_pinned = self.pin_btn.isChecked()
        self.pin_btn.setText("📍" if self.is_sidebar_pinned else "📌")

    def _setup_shortcuts(self):
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_card_to_project)

        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.quick_export)

    def quick_export(self):
        # 导出前自动同步并尝试保存
        self.sync_ui_to_model_only()
        if self.pm.current_project_name and self._dirty:
            self.save_card_to_project()
        if hasattr(self.tab_export, "export_card"):
            self.tab_export.export_card()
        elif hasattr(self.tab_export, "pack_to_bundle"):
            self.tab_export.pack_to_bundle()

    def _register_tab(self, icon, title_key, widget_instance):
        item = QListWidgetItem(f"{icon}  {i18n.t(title_key)}")
        self.sidebar.addItem(item)
        self.stacked_widget.addWidget(widget_instance)
        self._tab_meta.append((icon, title_key))

    def apply_language(self, lang: str):
        """主题页切换语言后刷新全界面"""
        i18n.set_language(lang, notify=False)
        self.settings.setValue("language", lang)
        self.retranslate_ui()

    def retranslate_ui(self):
        for i, (icon, key) in enumerate(self._tab_meta):
            item = self.sidebar.item(i)
            if item:
                item.setText(f"{icon}  {i18n.t(key)}")
        for i in range(self.stacked_widget.count()):
            w = self.stacked_widget.widget(i)
            if hasattr(w, "retranslate_ui"):
                w.retranslate_ui()
        # 标题保持当前工程状态
        if self._dirty:
            self._mark_dirty()
        else:
            self._set_clean()

    def eventFilter(self, obj, event):
        if obj == self.sidebar_container:
            if event.type() == QEvent.Enter:
                self.sidebar_delay_timer.stop()
                self.sidebar_anim.setDuration(300)
                self.sidebar_anim.setEasingCurve(QEasingCurve.OutQuint)
                self.sidebar_anim.setEndValue(180)
                self.sidebar_anim.start()
            elif event.type() == QEvent.Leave:
                if not self.is_sidebar_pinned:
                    self.sidebar_delay_timer.start(500)
        return super().eventFilter(obj, event)

    def _do_collapse(self):
        self.sidebar_anim.setDuration(600)
        self.sidebar_anim.setEasingCurve(QEasingCurve.InOutQuart)
        self.sidebar_anim.setEndValue(45)
        self.sidebar_anim.start()

    def closeEvent(self, event):
        if self._dirty:
            reply = QMessageBox.question(
                self,
                i18n.t("dlg.exit_title"),
                i18n.t("dlg.exit_body"),
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        if hasattr(self, 'settings'):
            self.settings.setValue("windowGeometry", self.saveGeometry())
            if hasattr(self, 'splitter'):
                self.settings.setValue("splitterSizes_v3", self.splitter.saveState())
        super().closeEvent(event)

    def _mark_dirty(self):
        self._dirty = True
        proj = self.pm.current_project_name or i18n.t("app.no_project")
        self.setWindowTitle(i18n.app_title(f"{proj} *"))

    def _set_clean(self):
        self._dirty = False
        proj = self.pm.current_project_name
        if proj:
            self.setWindowTitle(i18n.app_title(proj))
        else:
            self.setWindowTitle(i18n.app_title())

    def sync_ui_to_model_only(self):
        """同步所有 Tab → model，并刷新 JSON 预览；不落盘"""
        if getattr(self, '_is_syncing', False):
            return
        self._is_syncing = True
        try:
            skip = {self.tab_theme, self.tab_project, self.tab_help, self.tab_export}
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if widget in skip:
                    continue
                if hasattr(widget, "sync_to_model"):
                    widget.sync_to_model(self.model)

            # 组件能力与 UI 标签轻量对齐
            if hasattr(self.model, "sync_display_abilities"):
                self.model.sync_display_abilities()
                # 回刷基础页 UI 标签，保证显示一致
                if hasattr(self.tab_basic, "root_ability_checkboxes") and not getattr(
                    self.tab_basic, "_loading", False
                ):
                    from core_utils import signal_blocker
                    with signal_blocker(*self.tab_basic.root_ability_checkboxes.values()):
                        for key, cb in self.tab_basic.root_ability_checkboxes.items():
                            cb.setChecked(key in self.model.root_special_abilities)

            self.update_json_preview()
            self._mark_dirty()
        finally:
            self._is_syncing = False

    def load_card_to_workbench(self, card_data_dict):
        """从大厅双击卡牌，或者新建卡牌，加载进工作台"""
        if self._dirty:
            reply = QMessageBox.question(
                self,
                i18n.t("dlg.unsaved_title"),
                i18n.t("dlg.unsaved_card"),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                if not self.save_card_to_project():
                    return

        if not card_data_dict:
            self.model = CardModel()
        else:
            self.model = CardModel.from_json(card_data_dict)

        self._original_guid = self.model.guid

        self._is_syncing = True
        try:
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if hasattr(widget, "set_model"):
                    widget.set_model(self.model)
        finally:
            self._is_syncing = False
            self.update_json_preview(immediate=True)
            self._set_clean()

        self.sidebar.setCurrentRow(1)

    def save_card_to_project(self):
        """Ctrl+S / 保存按钮：同步并落盘"""
        self.sync_ui_to_model_only()

        if not self.pm.current_project_name:
            QMessageBox.warning(
                self, i18n.t("dlg.no_project_title"), i18n.t("dlg.no_project_body")
            )
            return False

        new_guid = self.model.guid
        old_guid = getattr(self, '_original_guid', None)

        if old_guid is not None and str(old_guid) != str(new_guid):
            self.pm.delete_card(old_guid)

        self._original_guid = new_guid

        ok = self.pm.add_or_update_card(self.model)
        if not ok:
            QMessageBox.critical(
                self, i18n.t("common.save_failed"), i18n.t("dlg.save_fail_body")
            )
            return False

        self.tab_project.refresh_card_roster()
        self._set_clean()
        self.setWindowTitle(
            i18n.app_title(i18n.t("app.saved_to", name=self.pm.current_project_name))
        )
        return True

    def update_json_preview(self, immediate=False):
        if immediate:
            self._preview_timer.stop()
            self._do_update_json_preview()
        else:
            self._preview_timer.start()

    def _do_update_json_preview(self):
        data_dict = self.model.generate_json_dict()
        html_str = self._generate_highlighted_json(data_dict)

        v_bar = self.json_preview.verticalScrollBar()
        h_bar = self.json_preview.horizontalScrollBar()
        v_val = v_bar.value()
        h_val = h_bar.value()

        self.json_preview.setHtml(html_str)
        v_bar.setValue(v_val)
        h_bar.setValue(h_val)

    def _generate_highlighted_json(self, data_dict):
        json_str = json.dumps(data_dict, indent=4, ensure_ascii=False)
        lines = json_str.split('\n')
        html_lines = []

        for line in lines:
            line = html.escape(line)
            line = re.sub(
                r'^(\s*)(&quot;.*?&quot;)(:)',
                r'\1<span style="color:#ce9178;">\2</span>\3', line,
            )
            line = re.sub(
                r'(: \s*)(&quot;.*?&quot;)(,?)$',
                r'\1<span style="color:#9cdcfe;">\2</span>\3', line,
            )
            line = re.sub(
                r'^(\s*)(&quot;.*?&quot;)(,?)$',
                r'\1<span style="color:#9cdcfe;">\2</span>\3', line,
            )
            line = re.sub(
                r'(: \s*)([0-9\.\-]+)(,?)$',
                r'\1<span style="color:#b5cea8;">\2</span>\3', line,
            )
            line = re.sub(
                r'(: \s*)(true|false|null)(,?)$',
                r'\1<span style="color:#569cd6;">\2</span>\3', line,
            )
            line = re.sub(
                r'^(\s*)([0-9\.\-]+)(,?)$',
                r'\1<span style="color:#b5cea8;">\2</span>\3', line,
            )
            line = re.sub(
                r'^(\s*)(true|false|null)(,?)$',
                r'\1<span style="color:#569cd6;">\2</span>\3', line,
            )
            html_lines.append(line)

        body = "\n".join(html_lines)
        return (
            f'<pre style="font-family: Consolas, Monaco, monospace; '
            f'font-size: 13px; line-height: 1.4;">{body}</pre>'
        )

    def refresh_all_ui(self, new_model):
        self.model = new_model
        self._original_guid = new_model.guid
        try:
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if hasattr(widget, "set_model"):
                    widget.set_model(self.model)
        except Exception as e:
            print(f"UI 刷新异常: {e}")
        finally:
            self.update_json_preview(immediate=True)
