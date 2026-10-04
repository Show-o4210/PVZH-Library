# ui/tab_tags.py
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QCheckBox)
from PySide6.QtCore import Qt, Signal
import config
import i18n
from core_utils import signal_blocker


class TabTags(QWidget):
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.model = None
        self._loading = False
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.sync_tags_cb = QCheckBox()
        self.sync_tags_cb.setChecked(True)
        self.sync_tags_cb.stateChanged.connect(self.on_sync_tags_toggled)
        layout.addWidget(self.sync_tags_cb)

        self.logic_group = QGroupBox()
        logic_layout = QVBoxLayout()
        self.logic_tag_input = QLineEdit()
        self.logic_tag_input.returnPressed.connect(self.add_logic_tag)
        logic_layout.addWidget(self.logic_tag_input)
        self.logic_tag_list = QListWidget()
        self.logic_tag_list.itemChanged.connect(self.on_logic_tag_changed)
        logic_layout.addWidget(self.logic_tag_list)
        self.logic_group.setLayout(logic_layout)
        layout.addWidget(self.logic_group)

        self.display_group = QGroupBox()
        display_layout = QVBoxLayout()
        self.display_tag_input = QLineEdit()
        self.display_tag_input.returnPressed.connect(self.add_display_tag)
        self.display_tag_input.setEnabled(False)
        display_layout.addWidget(self.display_tag_input)
        self.display_tag_list = QListWidget()
        self.display_tag_list.itemChanged.connect(self.on_display_tag_changed)
        display_layout.addWidget(self.display_tag_list)
        self.display_group.setLayout(display_layout)
        layout.addWidget(self.display_group)

        self.btn_delete = QPushButton()
        self.btn_delete.clicked.connect(self.delete_selected_tag)
        layout.addWidget(self.btn_delete)

        self.btn_load_saved = QPushButton()
        self.btn_load_saved.clicked.connect(self.load_saved_tags)
        layout.addWidget(self.btn_load_saved)

        self.btn_save_local = QPushButton()
        self.btn_save_local.clicked.connect(self.save_tags_local)
        layout.addWidget(self.btn_save_local)

    def retranslate_ui(self):
        self.sync_tags_cb.setText(i18n.t("tags.sync"))
        self.logic_group.setTitle(i18n.t("tags.logic_group"))
        self.display_group.setTitle(i18n.t("tags.display_group"))
        self.logic_tag_input.setPlaceholderText(i18n.t("tags.input_ph"))
        self.display_tag_input.setPlaceholderText(i18n.t("tags.input_ph"))
        self.btn_delete.setText(i18n.t("tags.delete"))
        self.btn_load_saved.setText(i18n.t("tags.load_lib"))
        self.btn_save_local.setText(i18n.t("tags.save_lib"))

    def _get_raw_text(self, text):
        return re.sub(r'^\d+\.\s*', '', text)

    def _renumber_list(self, list_widget):
        list_widget.blockSignals(True)
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            raw_text = self._get_raw_text(item.text())
            item.setText(f"{i + 1}. {raw_text}")
        list_widget.blockSignals(False)

    def create_editable_item(self, text):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        return item

    def _emit_changed(self):
        if not self._loading:
            self.data_changed.emit()

    def add_logic_tag(self):
        text = self.logic_tag_input.text().strip()
        if text:
            self.logic_tag_list.addItem(self.create_editable_item(text))
            self.logic_tag_input.clear()
            if self.sync_tags_cb.isChecked():
                self.display_tag_list.addItem(self.create_editable_item(text))
            self._renumber_list(self.logic_tag_list)
            self._renumber_list(self.display_tag_list)
            self._emit_changed()

    def add_display_tag(self):
        text = self.display_tag_input.text().strip()
        if text:
            self.display_tag_list.addItem(self.create_editable_item(text))
            self.display_tag_input.clear()
            self._renumber_list(self.display_tag_list)
            self._emit_changed()

    def on_logic_tag_changed(self, item):
        if self._loading:
            return
        self._renumber_list(self.logic_tag_list)
        if self.sync_tags_cb.isChecked():
            self.display_tag_list.blockSignals(True)
            self.display_tag_list.clear()
            for i in range(self.logic_tag_list.count()):
                raw = self._get_raw_text(self.logic_tag_list.item(i).text())
                self.display_tag_list.addItem(self.create_editable_item(raw))
            self._renumber_list(self.display_tag_list)
            self.display_tag_list.blockSignals(False)
        self._emit_changed()

    def on_display_tag_changed(self, item):
        if self._loading:
            return
        self._renumber_list(self.display_tag_list)
        self._emit_changed()

    def delete_selected_tag(self):
        for item in self.logic_tag_list.selectedItems():
            row = self.logic_tag_list.row(item)
            self.logic_tag_list.takeItem(row)
            if self.sync_tags_cb.isChecked():
                raw_text = self._get_raw_text(item.text())
                for i in range(self.display_tag_list.count()):
                    if self._get_raw_text(self.display_tag_list.item(i).text()) == raw_text:
                        self.display_tag_list.takeItem(i)
                        break
        for item in self.display_tag_list.selectedItems():
            self.display_tag_list.takeItem(self.display_tag_list.row(item))
        self._renumber_list(self.logic_tag_list)
        self._renumber_list(self.display_tag_list)
        self._emit_changed()

    def on_sync_tags_toggled(self, state):
        if self._loading:
            return
        is_sync = state == Qt.Checked.value
        self.display_tag_input.setEnabled(not is_sync)
        if is_sync:
            self.display_tag_list.clear()
            for i in range(self.logic_tag_list.count()):
                raw_text = self._get_raw_text(self.logic_tag_list.item(i).text())
                self.display_tag_list.addItem(self.create_editable_item(raw_text))
            self._renumber_list(self.display_tag_list)
        self._emit_changed()

    def load_saved_tags(self):
        config.load_custom_tags()
        for tag in config.SAVED_LOGIC_TAGS:
            self.logic_tag_list.addItem(self.create_editable_item(tag))
        for tag in config.SAVED_DISPLAY_TAGS:
            self.display_tag_list.addItem(self.create_editable_item(tag))
        self._renumber_list(self.logic_tag_list)
        self._renumber_list(self.display_tag_list)
        self._emit_changed()

    def save_tags_local(self):
        logic = [self._get_raw_text(self.logic_tag_list.item(i).text())
                 for i in range(self.logic_tag_list.count())]
        display = [self._get_raw_text(self.display_tag_list.item(i).text())
                   for i in range(self.display_tag_list.count())]
        config.save_tags_to_local(logic, display)

    def sync_to_model(self, model):
        if self._loading:
            return
        model.logic_tags = [
            self._get_raw_text(self.logic_tag_list.item(i).text())
            for i in range(self.logic_tag_list.count())
        ]
        model.display_tags = [
            self._get_raw_text(self.display_tag_list.item(i).text())
            for i in range(self.display_tag_list.count())
        ]

    def set_model(self, new_model):
        self.model = new_model
        self.update_ui(self.model)

    def update_ui(self, model):
        self._loading = True
        try:
            logic = list(model.logic_tags or [])
            display = list(model.display_tags or [])
            should_sync = logic == display
            with signal_blocker(self, self.sync_tags_cb, self.logic_tag_list, self.display_tag_list):
                self.sync_tags_cb.setChecked(should_sync)
                self.display_tag_input.setEnabled(not should_sync)
                self.logic_tag_list.clear()
                for tag in logic:
                    self.logic_tag_list.addItem(self.create_editable_item(tag))
                self.display_tag_list.clear()
                for tag in display:
                    self.display_tag_list.addItem(self.create_editable_item(tag))
                self._renumber_list(self.logic_tag_list)
                self._renumber_list(self.display_tag_list)
        finally:
            self._loading = False
