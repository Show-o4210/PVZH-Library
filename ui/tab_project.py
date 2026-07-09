# ui/tab_project.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QListWidget, QPushButton, QInputDialog, QMessageBox,
                               QSplitter, QListWidgetItem, QLabel)
from PySide6.QtCore import Qt, Signal
import i18n


class TabProject(QWidget):
    edit_card_requested = Signal(dict)
    project_switch_requested = Signal(str)

    def __init__(self, project_manager):
        super().__init__()
        self.pm = project_manager
        self._setup_ui()
        self.retranslate_ui()
        self.refresh_project_list()
        self.refresh_card_roster()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        self.proj_group = QGroupBox()
        proj_layout = QVBoxLayout(self.proj_group)

        self.btn_new_proj = QPushButton()
        self.btn_new_proj.clicked.connect(self.create_new_project)
        proj_layout.addWidget(self.btn_new_proj)

        self.proj_list = QListWidget()
        self.proj_list.itemClicked.connect(self._on_project_clicked)
        proj_layout.addWidget(self.proj_list)
        splitter.addWidget(self.proj_group)

        self.roster_group = QGroupBox()
        roster_layout = QVBoxLayout(self.roster_group)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #aaa; font-weight: bold;")
        roster_layout.addWidget(self.status_label)

        self.card_list = QListWidget()
        self.card_list.setAlternatingRowColors(True)
        self.card_list.itemDoubleClicked.connect(self.on_card_double_clicked)
        roster_layout.addWidget(self.card_list)

        btn_layout = QHBoxLayout()
        self.btn_new_card = QPushButton()
        self.btn_new_card.clicked.connect(lambda: self.edit_card_requested.emit({}))
        self.btn_del_card = QPushButton()
        self.btn_del_card.clicked.connect(self.delete_selected_card)
        btn_layout.addWidget(self.btn_new_card)
        btn_layout.addWidget(self.btn_del_card)
        roster_layout.addLayout(btn_layout)

        splitter.addWidget(self.roster_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

    def retranslate_ui(self):
        self.proj_group.setTitle(i18n.t("proj.list_group"))
        self.btn_new_proj.setText(i18n.t("proj.new"))
        self.roster_group.setTitle(i18n.t("proj.roster_group"))
        self.btn_new_card.setText(i18n.t("proj.new_card"))
        self.btn_del_card.setText(i18n.t("proj.del_card"))
        self.refresh_card_roster()

    def refresh_project_list(self):
        self.proj_list.clear()
        for p in self.pm.get_all_projects():
            item = QListWidgetItem(f"📦 {p}")
            item.setData(Qt.UserRole, p)
            self.proj_list.addItem(item)
            if p == self.pm.current_project_name:
                item.setSelected(True)

    def refresh_card_roster(self):
        self.card_list.clear()
        if not self.pm.current_project_name:
            self.status_label.setText(i18n.t("proj.status_none"))
            self.card_list.setEnabled(False)
            return

        self.card_list.setEnabled(True)
        self.status_label.setText(
            i18n.t("proj.status_active", name=self.pm.current_project_name)
        )

        import config
        for guid, cdata in self.pm.project_cards.items():
            try:
                gid = int(guid)
                name = config.KNOWN_CARDS.get(gid, {}).get("name", i18n.t("proj.custom_card"))
            except (TypeError, ValueError):
                name = i18n.t("proj.custom_card")
            prefab = str(cdata.get("prefabName", "") or "")
            item = QListWidgetItem(f"[{guid}] {name} - {prefab[:10]}...")
            item.setData(Qt.UserRole, str(guid))
            self.card_list.addItem(item)

    def create_new_project(self):
        name, ok = QInputDialog.getText(
            self, i18n.t("proj.new_dialog_title"), i18n.t("proj.new_dialog_label")
        )
        if ok and name.strip():
            self.project_switch_requested.emit(f"__create__:{name.strip()}")

    def _on_project_clicked(self, item):
        proj_name = item.data(Qt.UserRole)
        if proj_name:
            self.project_switch_requested.emit(str(proj_name))

    def apply_project_load(self, proj_name):
        self.pm.load_project(proj_name)
        self.refresh_project_list()
        self.refresh_card_roster()

    def apply_project_create(self, name):
        self.pm.create_project(name)
        self.refresh_project_list()
        self.refresh_card_roster()

    def on_card_double_clicked(self, item):
        guid = item.data(Qt.UserRole)
        card_data = self.pm.project_cards.get(guid)
        if card_data:
            self.edit_card_requested.emit(card_data)

    def delete_selected_card(self):
        selected = self.card_list.selectedItems()
        if not selected:
            return
        guid = selected[0].data(Qt.UserRole)
        reply = QMessageBox.question(
            self, i18n.t("common.confirm"), i18n.t("proj.del_confirm", guid=guid)
        )
        if reply == QMessageBox.Yes:
            self.pm.delete_card(guid)
            self.refresh_card_roster()
