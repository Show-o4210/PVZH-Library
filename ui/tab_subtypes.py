# ui/tab_subtypes.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QSpinBox, QLineEdit, QPushButton, QScrollArea,
                               QGridLayout, QCheckBox, QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, Signal
import config
import i18n
from core_utils import signal_blocker


class TabSubtypes(QWidget):
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.model = None
        self.logic_checkboxes = {}
        self.display_checkboxes = {}
        self._loading = False
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.add_group = QGroupBox()
        add_layout = QHBoxLayout()
        self.new_sub_id = QSpinBox()
        self.new_sub_id.setRange(42, 2147483647)
        self.new_sub_name = QLineEdit()
        self.btn_add_sub = QPushButton()
        self.btn_add_sub.clicked.connect(self.add_custom_subtype)
        add_layout.addWidget(self.new_sub_id)
        add_layout.addWidget(self.new_sub_name)
        add_layout.addWidget(self.btn_add_sub)
        self.add_group.setLayout(add_layout)
        layout.addWidget(self.add_group)

        self.sync_subtypes_cb = QCheckBox()
        self.sync_subtypes_cb.setChecked(True)
        self.sync_subtypes_cb.stateChanged.connect(self.on_sync_toggled)
        layout.addWidget(self.sync_subtypes_cb)

        lists_layout = QHBoxLayout()

        self.logic_group = QGroupBox()
        self.logic_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.logic_scroll = QScrollArea()
        self.logic_scroll.setWidgetResizable(True)
        logic_layout = QVBoxLayout()
        logic_layout.addWidget(self.logic_scroll)
        self.logic_group.setLayout(logic_layout)
        lists_layout.addWidget(self.logic_group)

        self.display_group = QGroupBox()
        self.display_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.display_scroll = QScrollArea()
        self.display_scroll.setWidgetResizable(True)
        display_layout = QVBoxLayout()
        display_layout.addWidget(self.display_scroll)
        self.display_group.setLayout(display_layout)
        lists_layout.addWidget(self.display_group)

        layout.addLayout(lists_layout)
        self.refresh_subtypes_grids()

    def retranslate_ui(self):
        self.add_group.setTitle(i18n.t("sub.add_group"))
        self.new_sub_name.setPlaceholderText(i18n.t("sub.name_ph"))
        self.btn_add_sub.setText(i18n.t("sub.save_local"))
        self.sync_subtypes_cb.setText(i18n.t("sub.sync"))
        self.logic_group.setTitle(i18n.t("sub.logic_group"))
        self.display_group.setTitle(i18n.t("sub.display_group"))

    def refresh_subtypes_grids(self, preserve_checked=True):
        logic_checked = set()
        display_checked = set()
        if preserve_checked:
            logic_checked = {k for k, cb in self.logic_checkboxes.items() if cb.isChecked()}
            display_checked = {k for k, cb in self.display_checkboxes.items() if cb.isChecked()}

        logic_widget = QWidget()
        logic_grid = QGridLayout(logic_widget)
        display_widget = QWidget()
        display_grid = QGridLayout(display_widget)

        self.logic_checkboxes.clear()
        self.display_checkboxes.clear()

        sorted_keys = sorted(config.SUBTYPES.keys())
        row, col = 0, 0
        for key in sorted_keys:
            val = config.SUBTYPES[key]
            cb_logic = QCheckBox(f"[{key}] {val}")
            if key in logic_checked:
                cb_logic.setChecked(True)
            cb_logic.stateChanged.connect(lambda state, k=key: self.on_logic_changed(k, state))
            self.logic_checkboxes[key] = cb_logic
            logic_grid.addWidget(cb_logic, row, col)

            cb_display = QCheckBox(f"[{key}] {val}")
            if key in display_checked:
                cb_display.setChecked(True)
            cb_display.setEnabled(not self.sync_subtypes_cb.isChecked())
            cb_display.stateChanged.connect(lambda *args: self._emit_changed())
            self.display_checkboxes[key] = cb_display
            display_grid.addWidget(cb_display, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        self.logic_scroll.setWidget(logic_widget)
        self.display_scroll.setWidget(display_widget)

    def _emit_changed(self):
        if not self._loading:
            self.data_changed.emit()

    def on_logic_changed(self, key, state):
        if self._loading:
            return
        if self.sync_subtypes_cb.isChecked():
            with signal_blocker(self.display_checkboxes.get(key)):
                if key in self.display_checkboxes:
                    self.display_checkboxes[key].setChecked(state == Qt.Checked.value)
        self.data_changed.emit()

    def on_sync_toggled(self, state):
        if self._loading:
            return
        is_sync = state == Qt.Checked.value
        for key, cb in self.display_checkboxes.items():
            cb.setEnabled(not is_sync)
            if is_sync:
                with signal_blocker(cb):
                    cb.setChecked(self.logic_checkboxes[key].isChecked())
        self.data_changed.emit()

    def add_custom_subtype(self):
        sub_id = self.new_sub_id.value()
        sub_name = self.new_sub_name.text().strip()
        if not sub_name:
            QMessageBox.warning(self, i18n.t("common.error"), i18n.t("sub.empty_name"))
            return
        if config.is_builtin_subtype(sub_id):
            QMessageBox.warning(self, i18n.t("common.error"), i18n.t("sub.builtin", id=sub_id))
            return
        if sub_id in config.CUSTOM_SUBTYPES:
            result = QMessageBox.question(
                self, i18n.t("common.confirm"), i18n.t("sub.overwrite", id=sub_id)
            )
            if result != QMessageBox.Yes:
                return
        success, error_msg = config.save_custom_subtype(sub_id, sub_name)
        if success:
            self.new_sub_name.clear()
            self.new_sub_id.setValue(sub_id + 1)
            self.refresh_subtypes_grids(preserve_checked=True)
            QMessageBox.information(self, i18n.t("common.success"), i18n.t("sub.saved", id=sub_id))
        else:
            QMessageBox.critical(
                self, i18n.t("common.save_failed"), i18n.t("sub.save_fail", err=error_msg)
            )

    def sync_to_model(self, model):
        if self._loading:
            return
        model.logic_subtypes = [key for key, cb in self.logic_checkboxes.items() if cb.isChecked()]
        model.display_subtypes = [key for key, cb in self.display_checkboxes.items() if cb.isChecked()]

    def set_model(self, new_model):
        self.model = new_model
        self.update_ui(self.model)

    def update_ui(self, model):
        self._loading = True
        try:
            logic_set = set(model.logic_subtypes or [])
            display_set = set(model.display_subtypes or [])
            should_sync = logic_set == display_set
            with signal_blocker(
                self, self.sync_subtypes_cb,
                *self.logic_checkboxes.values(),
                *self.display_checkboxes.values(),
            ):
                self.sync_subtypes_cb.setChecked(should_sync)
                for key, cb in self.logic_checkboxes.items():
                    cb.setChecked(key in logic_set)
                for key, cb in self.display_checkboxes.items():
                    cb.setChecked(key in display_set)
                    cb.setEnabled(not should_sync)
        finally:
            self._loading = False
