# ui/logic/inspector.py
"""属性检查器 - 移除硬编码样式，由全局主题控制"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QFormLayout,
                               QLabel, QSpinBox, QComboBox, QCheckBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
import logic_library
import localization
from core_utils import signal_blocker
import i18n


class LogicInspector(QWidget):
    """属性检查器：动态生成表单，编辑节点参数"""

    param_updated = Signal(object, str, object)

    def __init__(self):
        super().__init__()
        self.widgets = {}
        self._setup_ui()
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.group = QGroupBox()
        group_layout = QVBoxLayout(self.group)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.form = QFormLayout(self.content)
        self.form.setContentsMargins(10, 10, 10, 10)
        self.scroll.setWidget(self.content)

        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)

        group_layout.addWidget(self.title)
        group_layout.addWidget(self.scroll)
        layout.addWidget(self.group)

    def retranslate_ui(self):
        self.group.setTitle(i18n.t("logic.inspector"))
        if not self.widgets:
            self.title.setText(i18n.t("logic.pick_outline"))

    def clear(self):
        """清空所有表单控件"""
        while self.form.count():
            item = self.form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.widgets.clear()

    def load_node(self, item):
        """解析选中节点，动态生成右侧表单"""
        self.clear()
        if not item:
            self.title.setText(i18n.t("logic.pick_outline"))
            return

        node_id = item.data(0, Qt.UserRole)
        if node_id == "AbilityGroup":
            self.title.setText(i18n.t("logic.ability_group_no_param"))
            return

        self.title.setText(localization.get_node_name(node_id))

        defn = logic_library.NODE_DEF.get(node_id, {})
        schema = defn.get("editable_params", {})
        params = item.data(1, Qt.UserRole) or {}

        if not schema:
            self.form.addRow(QLabel(i18n.t("logic.no_params")))
            return

        for key, config in schema.items():
            name = localization.get_param_name(key)
            
            if config["type"] == "int":
                w = QSpinBox()
                w.setRange(config.get("min", -2147483648), config.get("max", 2147483647))
                with signal_blocker(w):
                    w.setValue(params.get(key, 0))
                w.valueChanged.connect(lambda val, k=key, it=item: self.param_updated.emit(it, k, val))
                
            elif config["type"] == "enum":
                w = QComboBox()
                for opt in config["options"]:
                    w.addItem(localization.get_enum_name(opt), opt)
                    
                with signal_blocker(w):
                    idx = w.findData(params.get(key, config["options"][0]))
                    if idx >= 0:
                        w.setCurrentIndex(idx)
                    
                w.currentIndexChanged.connect(lambda idx, k=key, combo=w, it=item: self.param_updated.emit(it, k, combo.itemData(idx)))
                
            elif config["type"] == "bool":
                w = QCheckBox(i18n.t("logic.enable"))
                with signal_blocker(w):
                    w.setChecked(bool(params.get(key, False)))
                w.stateChanged.connect(lambda state, k=key, it=item: self.param_updated.emit(it, k, state == Qt.Checked.value))

            elif config["type"] in ["string", "component_picker", "terrain_picker"]:
                w = QComboBox()
                w.setEditable(True)
                
                if config["type"] == "component_picker":
                    w.addItems([
                        "PvZCards.Engine.Components.Zombies, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "PvZCards.Engine.Components.Plants, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "PvZCards.Engine.Components.Lane, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "PvZCards.Engine.Components.FaceDown, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "PvZCards.Engine.Components.Environment, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null"
                    ])
                elif config["type"] == "terrain_picker":
                    w.addItems([
                        "PvZCards.Engine.Components.GrassTerrain, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "PvZCards.Engine.Components.WaterTerrain, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null",
                        "PvZCards.Engine.Components.HighgroundTerrain, EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null"
                    ])

                with signal_blocker(w):
                    curr_val = params.get(key, "")
                    idx = w.findText(curr_val)
                    if idx >= 0:
                        w.setCurrentIndex(idx)
                    else:
                        w.setCurrentText(curr_val)

                w.currentTextChanged.connect(lambda text, k=key, it=item: self.param_updated.emit(it, k, text))

            self.widgets[key] = w
            self.form.addRow(f"{name}:", w)

        # 针对 Target 组件联动保护
        if node_id == "PrimaryTargetFilter" and "SelectionType" in self.widgets:
            def sync_target(idx):
                sel_type = self.widgets["SelectionType"].itemData(idx)
                if sel_type in ["All", "Manual"]:
                    with signal_blocker(self.widgets["NumTargets"]):
                        self.widgets["NumTargets"].setValue(0)
                    self.param_updated.emit(item, "NumTargets", 0)
            self.widgets["SelectionType"].currentIndexChanged.connect(sync_target)