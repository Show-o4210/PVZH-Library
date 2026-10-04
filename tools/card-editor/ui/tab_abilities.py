# ui/tab_abilities.py
"""特殊能力标签页 - 移除硬编码样式，由全局主题控制"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
                               QSpinBox, QComboBox, QScrollArea, QLabel, 
                               QGroupBox, QPushButton, QFrame)
from PySide6.QtCore import Signal, Qt
import config
import i18n
from constants import TRIGGERED_ABILITY_GUIDS
from core_utils import signal_blocker


class AbilityRow(QFrame):
    """动态能力行：包含名称/参数和删除按钮"""
    removed = Signal(object)
    changed = Signal()

    def __init__(self, ability_type, data=None):
        super().__init__()
        self.ability_type = ability_type  # "DoubleStrike", "Overshoot", or "Custom"
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        self.label = QLabel()
        self.label.setMinimumWidth(100)
        self.label.setStyleSheet("font-weight: bold; border: none;")
        layout.addWidget(self.label)

        self.params = data or {"g": 0, "vt": 0, "va": 0}
        self.val_input = None
        self.guid_input = None
        self.vt_input = None

        if ability_type == "Overshoot":
            self.params["g"] = TRIGGERED_ABILITY_GUIDS["Overshoot"]
            self.params["vt"] = 1
            self.val_input = QSpinBox()
            self.val_input.setMinimumHeight(28)
            self.val_input.setRange(1, 99)
            self.val_input.setValue(self.params.get("va", 2))
            self.val_input.valueChanged.connect(lambda x: self.changed.emit())
            layout.addWidget(self.val_input)

        elif ability_type == "DoubleStrike":
            self.params = {"g": TRIGGERED_ABILITY_GUIDS["DoubleStrike"], "vt": 0, "va": 0}
            layout.addStretch()

        elif ability_type == "Custom":
            self.guid_input = QSpinBox()
            self.guid_input.setMinimumHeight(28)
            self.guid_input.setRange(0, 9999)
            self.guid_input.setValue(self.params.get("g", 0))
            self.guid_input.valueChanged.connect(lambda x: self.changed.emit())

            self.vt_input = QComboBox()
            self.vt_input.setMinimumHeight(28)
            self.vt_input.addItem("", 0)
            self.vt_input.addItem("", 1)
            self.vt_input.addItem("", 2)
            self.vt_input.setCurrentIndex(self.params.get("vt", 0))
            self.vt_input.currentIndexChanged.connect(lambda x: self.changed.emit())

            self.val_input = QSpinBox()
            self.val_input.setMinimumHeight(28)
            self.val_input.setRange(0, 9999)
            self.val_input.setValue(self.params.get("va", 0))
            self.val_input.valueChanged.connect(lambda x: self.changed.emit())

            layout.addWidget(self.guid_input)
            layout.addWidget(self.vt_input)
            layout.addWidget(self.val_input)

        layout.addStretch()

        btn_del = QPushButton("❌")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(btn_del)
        self.retranslate_ui()

    def retranslate_ui(self):
        name_map = {
            "DoubleStrike": i18n.t("abil.row_double"),
            "Overshoot": i18n.t("abil.row_overshoot"),
            "Custom": i18n.t("abil.row_custom"),
        }
        self.label.setText(name_map.get(self.ability_type, i18n.t("abil.unknown")))
        if self.ability_type == "Overshoot" and self.val_input:
            self.val_input.setPrefix(i18n.t("abil.dmg_prefix"))
        if self.ability_type == "Custom":
            if self.guid_input:
                self.guid_input.setPrefix(i18n.t("abil.id_prefix"))
            if self.val_input:
                self.val_input.setPrefix(i18n.t("abil.val_prefix"))
            if self.vt_input:
                cur = self.vt_input.currentIndex()
                self.vt_input.blockSignals(True)
                self.vt_input.setItemText(0, i18n.t("abil.vt_fixed"))
                self.vt_input.setItemText(1, i18n.t("abil.vt_pct"))
                self.vt_input.setItemText(2, i18n.t("abil.vt_mul"))
                self.vt_input.setCurrentIndex(cur)
                self.vt_input.blockSignals(False)

    def get_data(self):
        if self.ability_type == "Overshoot":
            self.params["va"] = self.val_input.value() if self.val_input else 2
        elif self.ability_type == "Custom":
            if self.guid_input:
                self.params["g"] = self.guid_input.value()
            if self.vt_input:
                self.params["vt"] = self.vt_input.currentData()
            if self.val_input:
                self.params["va"] = self.val_input.value()
        return self.params.copy()


class TabAbilities(QWidget):
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.ability_rows = [] 
        self.independent_widgets = {} 
        self.model = None
        self._loading = False
        self._setup_ui()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.basic_group.setTitle(i18n.t("abil.basic_group"))
        self.triggered_group.setTitle(i18n.t("abil.triggered_group"))
        self.btn_add.setText(i18n.t("abil.add"))
        cur = self.ability_selector.currentIndex()
        self.ability_selector.blockSignals(True)
        self.ability_selector.clear()
        self.ability_selector.addItem(
            i18n.t("abil.double", id=TRIGGERED_ABILITY_GUIDS["DoubleStrike"]), "DoubleStrike"
        )
        self.ability_selector.addItem(
            i18n.t("abil.overshoot", id=TRIGGERED_ABILITY_GUIDS["Overshoot"]), "Overshoot"
        )
        self.ability_selector.addItem(i18n.t("abil.custom"), "Custom")
        if 0 <= cur < self.ability_selector.count():
            self.ability_selector.setCurrentIndex(cur)
        self.ability_selector.blockSignals(False)
        for row in self.ability_rows:
            row.retranslate_ui()

    def _on_any_change(self):
        """任何UI改变时触发"""
        if self._loading:
            return
        if self.model:
            self.sync_to_model(self.model)
        self.data_changed.emit()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setSpacing(25)

        self.basic_group = QGroupBox()
        basic_layout = QVBoxLayout(self.basic_group)
        basic_layout.setContentsMargins(20, 25, 20, 20)
        basic_layout.setSpacing(12)
        
        # 遍历 config.SPECIAL_ABILITIES 创建控件
        for key, info in config.SPECIAL_ABILITIES.items():
            row_layout = QHBoxLayout()
            cb = QCheckBox(info["name"])
            cb.setMinimumWidth(180)
            cb.setMinimumHeight(28)
            row_layout.addWidget(cb)
            
            param_widget = None
            if info["type"] == "int":
                param_widget = QSpinBox()
                param_widget.setMinimumHeight(28)
                param_widget.setRange(1, 99)
                param_widget.setValue(info["default"])
                param_widget.setPrefix(f"{info['label']}: ")
                param_widget.setEnabled(False)
                row_layout.addWidget(param_widget)
            elif info["type"] in ["combo", "teamup_combo"]:
                param_widget = QComboBox()
                param_widget.setMinimumHeight(28)
                for opt_name, opt_val in info["options"].items():
                    param_widget.addItem(opt_name, opt_val)
                param_widget.setEnabled(False)
                row_layout.addWidget(param_widget)
                
            row_layout.addStretch()
            basic_layout.addLayout(row_layout)
            
            if param_widget:
                cb.toggled.connect(param_widget.setEnabled)
                cb.toggled.connect(lambda checked: self._on_any_change())
                if isinstance(param_widget, QSpinBox):
                    param_widget.valueChanged.connect(lambda x: self._on_any_change())
                elif isinstance(param_widget, QComboBox):
                    param_widget.currentIndexChanged.connect(lambda x: self._on_any_change())
            else:
                cb.stateChanged.connect(lambda state: self._on_any_change())
                
            self.independent_widgets[key] = {"cb": cb, "param": param_widget, "type": info["type"]}
        
        self.main_layout.addWidget(self.basic_group)

        self.triggered_group = QGroupBox()
        self.triggered_layout = QVBoxLayout(self.triggered_group)
        self.triggered_layout.setContentsMargins(20, 25, 20, 20)
        self.triggered_layout.setSpacing(15)
        
        # 添加控制栏
        add_ctrl_layout = QHBoxLayout()
        add_ctrl_layout.setSpacing(15)
        
        self.ability_selector = QComboBox()
        self.ability_selector.setMinimumHeight(32)
        self.ability_selector.setMinimumWidth(220)
        add_ctrl_layout.addWidget(self.ability_selector)

        self.btn_add = QPushButton()
        self.btn_add.setMinimumHeight(32)
        self.btn_add.clicked.connect(lambda: self.add_ability_row())
        add_ctrl_layout.addWidget(self.btn_add)
        add_ctrl_layout.addStretch()
        
        self.triggered_layout.addLayout(add_ctrl_layout)
        
        # 分隔线 - 移除内联样式
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        self.triggered_layout.addWidget(line)

        # 存放动态行的容器
        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(10)
        self.triggered_layout.addLayout(self.rows_container)
        self.triggered_layout.addStretch()
        
        self.main_layout.addWidget(self.triggered_group)
        self.main_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def add_ability_row(self, data=None, ability_type=None):
        """添加新的能力行"""
        if ability_type is None:
            ability_type = self.ability_selector.currentData()
            
        row = AbilityRow(ability_type, data)
        row.removed.connect(self.remove_row)
        row.changed.connect(self._on_any_change)  
        self.rows_container.addWidget(row)
        self.ability_rows.append(row)
        self._on_any_change()

    def remove_row(self, row):
        """删除能力行"""
        self.rows_container.removeWidget(row)
        if row in self.ability_rows:
            self.ability_rows.remove(row)
        row.deleteLater()
        self._on_any_change()

    def clear_all_rows(self, silent=False):
        """清空所有动态行；silent=True 时不回写 model"""
        prev = self._loading
        if silent:
            self._loading = True
        try:
            for row in self.ability_rows[:]:
                self.rows_container.removeWidget(row)
                if row in self.ability_rows:
                    self.ability_rows.remove(row)
                row.deleteLater()
            if not silent:
                self._on_any_change()
        finally:
            if silent:
                self._loading = prev

    def sync_to_model(self, model):
        """将UI数据同步到Model"""
        if not model or self._loading:
            return

        model.triggered_abilities = [row.get_data() for row in self.ability_rows]

        abilities_data = {}
        for key, widgets in self.independent_widgets.items():
            if widgets["cb"].isChecked():
                val = True
                if widgets["type"] == "int":
                    val = widgets["param"].value()
                elif widgets["type"] in ["combo", "teamup_combo"]:
                    val = widgets["param"].currentData()
                abilities_data[key] = val
        model.components_abilities = abilities_data

    def set_model(self, new_model):
        """设置模型并更新UI"""
        self.model = new_model
        self.update_ui(self.model)

    def update_ui(self, model):
        """从Model更新UI（与输入控件双向一致，加载期禁止回写）"""
        if not model:
            return

        self._loading = True
        try:
            widgets_to_block = [w["cb"] for w in self.independent_widgets.values()]
            widgets_to_block += [
                w["param"] for w in self.independent_widgets.values() if w["param"] is not None
            ]
            with signal_blocker(self, *widgets_to_block):
                for key, widgets in self.independent_widgets.items():
                    if key in model.components_abilities:
                        widgets["cb"].setChecked(True)
                        val = model.components_abilities[key]
                        if widgets["type"] == "int" and widgets["param"]:
                            widgets["param"].setValue(int(val))
                            widgets["param"].setEnabled(True)
                        elif widgets["type"] in ["combo", "teamup_combo"] and widgets["param"]:
                            idx = widgets["param"].findData(val)
                            if idx >= 0:
                                widgets["param"].setCurrentIndex(idx)
                            widgets["param"].setEnabled(True)
                    else:
                        widgets["cb"].setChecked(False)
                        if widgets["param"]:
                            widgets["param"].setEnabled(False)

                self.clear_all_rows(silent=True)
                for item in model.triggered_abilities or []:
                    g = item.get("g", 0)
                    atype = "Custom"
                    if g == TRIGGERED_ABILITY_GUIDS.get("DoubleStrike"):
                        atype = "DoubleStrike"
                    elif g == TRIGGERED_ABILITY_GUIDS.get("Overshoot"):
                        atype = "Overshoot"

                    row = AbilityRow(atype, item)
                    row.removed.connect(self.remove_row)
                    row.changed.connect(self._on_any_change)
                    self.rows_container.addWidget(row)
                    self.ability_rows.append(row)
        finally:
            self._loading = False