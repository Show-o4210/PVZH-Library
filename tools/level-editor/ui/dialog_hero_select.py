# ui/dialog_hero_select.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTabWidget, QListWidget, QListWidgetItem, QLineEdit, QLabel
)
from PySide6.QtCore import Qt, QSize
from constants import PLANT_HEROES, ZOMBIE_HEROES
from theme import apply_dialog_theme
from i18n import t, localized_name


class HeroSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("hero.title"))
        self.resize(720, 560)

        self.selected_hero_id = None
        self.selected_hero_name = None
        self.selected_faction = None

        apply_dialog_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(14)

        title = QLabel(t("hero.title"))
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(t("hero.search_ph"))
        self.search_bar.textChanged.connect(self._filter_all_tabs)
        layout.addWidget(self.search_bar)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.list_plants = self._create_list()
        self.list_zombies = self._create_list()

        self.tabs.addTab(self.list_plants, t("hero.plants_tab"))
        self.tabs.addTab(self.list_zombies, t("hero.zombies_tab"))

        for h in PLANT_HEROES:
            self._add_item(self.list_plants, localized_name(h), h[0], 0)
        for h in ZOMBIE_HEROES:
            self._add_item(self.list_zombies, localized_name(h), h[0], 1)

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


    def _create_list(self):
        lw = QListWidget()
        lw.setObjectName("gridSelectList")
        lw.setViewMode(QListWidget.IconMode)
        lw.setResizeMode(QListWidget.Adjust)
        lw.setSpacing(12)
        lw.setWordWrap(True)
        lw.setGridSize(QSize(200, 92))
        lw.itemDoubleClicked.connect(self._accept_selection)
        return lw

    def _add_item(self, list_widget, name, h_id, faction):
        item = QListWidgetItem(f"{name}\n{h_id}")
        item.setData(Qt.UserRole, (h_id, name, faction))
        item.setToolTip(f"{name} ({h_id})")
        list_widget.addItem(item)

    def _filter_all_tabs(self, text):
        terms = [term for term in text.lower().split() if term]
        for lw in (self.list_plants, self.list_zombies):
            for i in range(lw.count()):
                item = lw.item(i)
                haystack = item.text().lower()
                item.setHidden(not all(term in haystack for term in terms))

    def _filter_current_tab(self, text):
        self._filter_all_tabs(text)

    def _accept_selection(self):
        current_list = self.tabs.currentWidget()
        selected_items = current_list.selectedItems()
        if selected_items:
            self.selected_hero_id, self.selected_hero_name, self.selected_faction = selected_items[0].data(Qt.UserRole)
            self.accept()
