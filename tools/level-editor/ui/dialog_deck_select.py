# ui/dialog_deck_select.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem, QLabel
)
from PySide6.QtCore import Qt, QSize
from theme import apply_dialog_theme
from i18n import t


class DeckSelectDialog(QDialog):
    def __init__(self, deck_db, current_hero_name="", parent=None, hero_match_names=None):
        super().__init__(parent)
        self.setWindowTitle(t("deck.title"))
        self.resize(860, 620)

        self.selected_deck_id = None
        self.deck_db = deck_db
        self.current_hero_name = current_hero_name
        # 兼容中英文：decks.json 多为中文英雄名，英文界面下需同时匹配中文名
        self.hero_match_names = list(hero_match_names) if hero_match_names else (
            [current_hero_name] if current_hero_name else []
        )
        self.category_lists = {}

        apply_dialog_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(14)

        title = QLabel(t("deck.title"))
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(t("deck.search_ph"))
        self.search_bar.textChanged.connect(self._filter_current_tab)
        layout.addWidget(self.search_bar)

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.tabs.currentChanged.connect(lambda _idx: self._filter_current_tab(self.search_bar.text()))
        layout.addWidget(self.tabs, 1)

        self.list_recommended = self._create_list_widget()
        self.tabs.addTab(
            self.list_recommended,
            t("deck.recommended", name=current_hero_name or t("common.none")),
        )

        self._populate_data()

        if self.list_recommended.count() == 0 and self.tabs.count() > 1:
            self.tabs.setCurrentIndex(1)
            self.tabs.setTabText(0, t("deck.recommended_none"))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton(t("common.cancel"))
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton(t("common.confirm"))
        confirm_btn.setMinimumSize(132, 42)
        confirm_btn.clicked.connect(self._accept_selection)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)


    def _create_list_widget(self):
        lw = QListWidget()
        lw.setObjectName("gridSelectList")
        lw.setViewMode(QListWidget.IconMode)
        lw.setResizeMode(QListWidget.Adjust)
        lw.setSpacing(12)
        lw.setWordWrap(True)
        lw.setGridSize(QSize(264, 112))
        lw.itemDoubleClicked.connect(self._accept_selection)
        return lw

    def _populate_data(self):
        for display_text, deck_id in self.deck_db.items():
            parts = display_text.split('|')
            form_raw = parts[0].strip() if len(parts) > 1 else t("common.uncategorized")
            cn_name = parts[-1].strip()
            item_text = f"{cn_name}\n{deck_id}"
            search_text = f"{display_text} {deck_id} {cn_name} {form_raw}"

            if self.hero_match_names and any(n and n in display_text for n in self.hero_match_names):
                self._add_item(self.list_recommended, item_text, deck_id, search_text)

            if "预设" in form_raw:
                tab_name = t("deck.cat_preset")
            elif "PVE" in form_raw:
                tab_name = t("deck.cat_pve")
            elif "教程" in form_raw or "FTUE" in form_raw:
                tab_name = t("deck.cat_tutorial")
            elif "挑战" in form_raw or "BOTD" in form_raw:
                tab_name = t("deck.cat_daily")
            elif "活动" in form_raw:
                tab_name = t("deck.cat_event")
            else:
                tab_name = f"📁 {form_raw}"

            if tab_name not in self.category_lists:
                new_list = self._create_list_widget()
                self.category_lists[tab_name] = new_list
                self.tabs.addTab(new_list, tab_name)

            self._add_item(self.category_lists[tab_name], item_text, deck_id, search_text)

    def _add_item(self, list_widget, text, data, search_text):
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, data)
        item.setData(Qt.UserRole + 1, search_text.lower())
        item.setToolTip(text.replace("\n", "\nID: "))
        list_widget.addItem(item)

    def _filter_current_tab(self, text):
        terms = [term for term in text.lower().split() if term]
        current_list = self.tabs.currentWidget()
        if current_list is None:
            return
        for i in range(current_list.count()):
            item = current_list.item(i)
            haystack = item.data(Qt.UserRole + 1) or item.text().lower()
            item.setHidden(not all(term in haystack for term in terms))

    def _accept_selection(self):
        current_list = self.tabs.currentWidget()
        if current_list is None:
            return
        selected_items = current_list.selectedItems()
        if selected_items:
            self.selected_deck_id = selected_items[0].data(Qt.UserRole)
            self.accept()
