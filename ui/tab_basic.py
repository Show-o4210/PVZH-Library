# ui/tab_basic.py
"""基础属性标签页 - 移除硬编码样式，由全局主题控制"""

import uuid
import json
import os
from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QSpinBox, 
                               QComboBox, QPushButton, QHBoxLayout, QCheckBox, 
                               QGroupBox, QVBoxLayout, QScrollArea, QLabel, QGridLayout, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
import config
import i18n
from core_utils import signal_blocker

class TabBasic(QWidget):
    data_changed = Signal()
    save_requested = Signal()
    import_requested = Signal(str, int)

    def __init__(self, initial_model=None):
        super().__init__()
        self.root_ability_checkboxes = {}
        self.model = initial_model
        self._form_labels = {}
        self._setup_ui()
        self.retranslate_ui()
        if self.model:
            self.update_ui(self.model)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        self.quick_group = QGroupBox()
        quick_layout = QVBoxLayout(self.quick_group)

        save_btn_layout = QHBoxLayout()
        self.btn_save = QPushButton()
        self.btn_save.setMinimumHeight(40)
        self.btn_save.clicked.connect(self.save_requested.emit)

        self.hint_label = QLabel()
        self.hint_label.setStyleSheet("color: #888; font-size: 11px;")

        save_btn_layout.addWidget(self.btn_save, 3)
        save_btn_layout.addWidget(self.hint_label, 2)
        quick_layout.addLayout(save_btn_layout)

        import_layout = QHBoxLayout()
        self.lbl_import = QLabel()
        import_layout.addWidget(self.lbl_import)

        self.import_path_edit = QLineEdit()
        default_json = os.path.join(config.DATA_DIR, config.DEFAULT_CARD_JSON)
        if os.path.exists(default_json):
            self.import_path_edit.setText(default_json)

        self.btn_browse = QPushButton()
        self.btn_browse.clicked.connect(self._browse_import_path)

        self.import_guid_spin = QSpinBox()
        self.import_guid_spin.setRange(1, 2147483647)

        self.btn_do_import = QPushButton()
        self.btn_do_import.clicked.connect(self._handle_import_click)

        import_layout.addWidget(self.import_path_edit, 3)
        import_layout.addWidget(self.btn_browse, 1)
        import_layout.addWidget(self.import_guid_spin, 1)
        import_layout.addWidget(self.btn_do_import, 2)
        quick_layout.addLayout(import_layout)

        main_layout.addWidget(self.quick_group)

        # ================= 原有属性编辑区 =================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form = QFormLayout(container)

        def _row(form_layout, key, widget):
            lab = QLabel()
            self._form_labels[key] = lab
            form_layout.addRow(lab, widget)

        self.guid_group = QGroupBox()
        guid_form = QFormLayout()
        self.guid_spin = QSpinBox()
        self.guid_spin.setRange(1, 2147483647)
        _row(guid_form, "guid", self.guid_spin)
        self.card_name_display = QLineEdit()
        self.card_name_display.setReadOnly(True)
        _row(guid_form, "local_name", self.card_name_display)
        self.prefab_input = QLineEdit()
        _row(guid_form, "prefab", self.prefab_input)
        self.guid_group.setLayout(guid_form)
        form.addRow(self.guid_group)

        self.type_group = QGroupBox()
        type_form = QFormLayout()
        self.faction_combo = QComboBox()
        for key, val in config.FACTIONS.items():
            self.faction_combo.addItem(val, key)
        _row(type_form, "faction", self.faction_combo)
        self.baseid_combo = QComboBox()
        for key, val in config.BASE_IDS.items():
            self.baseid_combo.addItem(val, key)
        _row(type_form, "base_id", self.baseid_combo)
        self.color_combo = QComboBox()
        for key, val in config.COLORS.items():
            self.color_combo.addItem(val, key)
        _row(type_form, "color", self.color_combo)
        self.rarity_combo = QComboBox()
        for key, info in config.RARITIES.items():
            self.rarity_combo.addItem(info["name"], key)
        _row(type_form, "rarity", self.rarity_combo)
        self.set_combo = QComboBox()
        for key, val in config.SETS.items():
            self.set_combo.addItem(val, key)
        _row(type_form, "set", self.set_combo)
        self.set_rarity_key_input = QLineEdit()
        _row(type_form, "set_rarity_key", self.set_rarity_key_input)
        self.type_group.setLayout(type_form)
        form.addRow(self.type_group)

        self.stats_group = QGroupBox()
        stats_form = QFormLayout()
        craft_layout = QHBoxLayout()
        self.craft_buy_spin = QSpinBox()
        self.craft_buy_spin.setRange(0, 2147483647)
        self.craft_sell_spin = QSpinBox()
        self.craft_sell_spin.setRange(0, 2147483647)
        self.lbl_buy = QLabel()
        self.lbl_sell = QLabel()
        craft_layout.addWidget(self.lbl_buy)
        craft_layout.addWidget(self.craft_buy_spin)
        craft_layout.addWidget(self.lbl_sell)
        craft_layout.addWidget(self.craft_sell_spin)
        _row(stats_form, "craft", craft_layout)
        self.cost_spin = QSpinBox()
        self.cost_spin.setRange(0, 2147483647)
        _row(stats_form, "cost", self.cost_spin)
        attack_layout = QHBoxLayout()
        self.attack_cb = QCheckBox()
        self.attack_spin = QSpinBox()
        self.attack_spin.setRange(0, 2147483647)
        self.attack_cb.toggled.connect(self.attack_spin.setEnabled)
        attack_layout.addWidget(self.attack_cb)
        attack_layout.addWidget(self.attack_spin)
        _row(stats_form, "attack", attack_layout)
        health_layout = QHBoxLayout()
        self.health_cb = QCheckBox()
        self.health_spin = QSpinBox()
        self.health_spin.setRange(0, 2147483647)
        self.health_cb.toggled.connect(self.health_spin.setEnabled)
        health_layout.addWidget(self.health_cb)
        health_layout.addWidget(self.health_spin)
        _row(stats_form, "health", health_layout)
        self.stats_group.setLayout(stats_form)
        form.addRow(self.stats_group)

        self.flags_group = QGroupBox()
        flags_layout = QGridLayout()
        self.flag_ignore_limit = QCheckBox()
        self.flag_is_power = QCheckBox()
        self.flag_is_primary_power = QCheckBox()
        self.flag_is_trick = QCheckBox()
        self.flag_is_surprise = QCheckBox()
        self.flag_is_env = QCheckBox()
        self.flag_is_board = QCheckBox()
        flags_layout.addWidget(self.flag_ignore_limit, 0, 0)
        flags_layout.addWidget(self.flag_is_power, 0, 1)
        flags_layout.addWidget(self.flag_is_primary_power, 0, 2)
        flags_layout.addWidget(self.flag_is_trick, 1, 0)
        flags_layout.addWidget(self.flag_is_surprise, 1, 1)
        flags_layout.addWidget(self.flag_is_env, 1, 2)
        flags_layout.addWidget(self.flag_is_board, 1, 3)
        self.flags_group.setLayout(flags_layout)
        form.addRow(self.flags_group)

        self.abilities_group = QGroupBox()
        abilities_layout = QVBoxLayout()
        for key, note in config.ROOT_ABILITY_PRESETS.items():
            cb = QCheckBox(f"{key} - {note}")
            cb.stateChanged.connect(lambda *args: self.data_changed.emit())
            self.root_ability_checkboxes[key] = cb
            abilities_layout.addWidget(cb)
        self.abilities_group.setLayout(abilities_layout)
        form.addRow(self.abilities_group)

        self.affinities_group = QGroupBox()
        aff_form = QFormLayout()
        self.sub_aff_input = QLineEdit()
        _row(aff_form, "sub_aff", self.sub_aff_input)
        self.sub_aff_w_input = QLineEdit()
        _row(aff_form, "sub_aff_w", self.sub_aff_w_input)
        self.tag_aff_input = QLineEdit()
        _row(aff_form, "tag_aff", self.tag_aff_input)
        self.tag_aff_w_input = QLineEdit()
        _row(aff_form, "tag_aff_w", self.tag_aff_w_input)
        self.card_aff_input = QLineEdit()
        _row(aff_form, "card_aff", self.card_aff_input)
        self.card_aff_w_input = QLineEdit()
        _row(aff_form, "card_aff_w", self.card_aff_w_input)
        self.affinities_group.setLayout(aff_form)
        form.addRow(self.affinities_group)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # 信号绑定
        self.guid_spin.valueChanged.connect(self.refresh_card_name)
        self.baseid_combo.currentIndexChanged.connect(self.on_card_type_changed)
        self.faction_combo.currentIndexChanged.connect(self.on_card_type_changed)
        
        input_widgets = [
            self.guid_spin, self.cost_spin, self.attack_spin, self.health_spin, 
            self.craft_buy_spin, self.craft_sell_spin, self.color_combo, 
            self.rarity_combo, self.set_combo, self.prefab_input, 
            self.set_rarity_key_input, self.sub_aff_input, self.sub_aff_w_input, 
            self.tag_aff_input, self.tag_aff_w_input, self.card_aff_input, 
            self.card_aff_w_input, self.attack_cb, self.health_cb, 
            self.flag_ignore_limit, self.flag_is_power, self.flag_is_primary_power,
            self.flag_is_trick, self.flag_is_surprise, self.flag_is_env, self.flag_is_board
        ]

        for widget in input_widgets:
            if isinstance(widget, (QSpinBox, QComboBox)):
                if isinstance(widget, QComboBox):
                    widget.currentIndexChanged.connect(lambda *args: self.data_changed.emit())
                else:
                    widget.valueChanged.connect(lambda *args: self.data_changed.emit())
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda *args: self.data_changed.emit())
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(lambda *args: self.data_changed.emit())

    def retranslate_ui(self):
        self.quick_group.setTitle(i18n.t("basic.quick"))
        self.btn_save.setText(i18n.t("basic.save"))
        self.hint_label.setText(i18n.t("basic.save_hint"))
        self.lbl_import.setText(i18n.t("basic.import_label"))
        self.import_path_edit.setPlaceholderText(
            i18n.t("basic.import_placeholder", name=config.DEFAULT_CARD_JSON)
        )
        self.btn_browse.setText(i18n.t("common.browse"))
        self.import_guid_spin.setPrefix(i18n.t("basic.guid_prefix"))
        self.btn_do_import.setText(i18n.t("basic.import_btn"))

        self.guid_group.setTitle(i18n.t("basic.group_id"))
        self.type_group.setTitle(i18n.t("basic.group_def"))
        self.stats_group.setTitle(i18n.t("basic.group_stats"))
        self.flags_group.setTitle(i18n.t("basic.group_flags"))
        self.abilities_group.setTitle(i18n.t("basic.group_ui_abil"))
        self.affinities_group.setTitle(i18n.t("basic.group_aff"))

        mapping = {
            "guid": "basic.guid",
            "local_name": "basic.local_name",
            "prefab": "basic.prefab",
            "faction": "basic.faction",
            "base_id": "basic.base_id",
            "color": "basic.color",
            "rarity": "basic.rarity",
            "set": "basic.set",
            "set_rarity_key": "basic.set_rarity_key",
            "craft": "basic.craft",
            "cost": "basic.cost",
            "attack": "basic.attack",
            "health": "basic.health",
            "sub_aff": "basic.sub_aff",
            "sub_aff_w": "basic.sub_aff_w",
            "tag_aff": "basic.tag_aff",
            "tag_aff_w": "basic.tag_aff_w",
            "card_aff": "basic.card_aff",
            "card_aff_w": "basic.card_aff_w",
        }
        for k, ik in mapping.items():
            if k in self._form_labels:
                self._form_labels[k].setText(i18n.t(ik))

        self.card_name_display.setPlaceholderText(i18n.t("basic.local_name_ph"))
        self.lbl_buy.setText(i18n.t("basic.buy"))
        self.lbl_sell.setText(i18n.t("basic.sell"))
        self.attack_cb.setText(i18n.t("basic.enable"))
        self.health_cb.setText(i18n.t("basic.enable"))
        self.flag_ignore_limit.setText(i18n.t("basic.flag_ignore"))
        self.flag_is_power.setText(i18n.t("basic.flag_power"))
        self.flag_is_primary_power.setText(i18n.t("basic.flag_primary"))
        self.flag_is_trick.setText(i18n.t("basic.flag_trick"))
        self.flag_is_surprise.setText(i18n.t("basic.flag_surprise"))
        self.flag_is_env.setText(i18n.t("basic.flag_env"))
        self.flag_is_board.setText(i18n.t("basic.flag_board"))

    def _browse_import_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("basic.pick_json"), "", "JSON Files (*.json)"
        )
        if path:
            self.import_path_edit.setText(path)

    def _handle_import_click(self):
        path = self.import_path_edit.text().strip()
        guid = self.import_guid_spin.value()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, i18n.t("common.error"), i18n.t("basic.import_path_err"))
            return
        self.import_requested.emit(path, guid)

    def refresh_card_name(self):
        guid = self.guid_spin.value()
        card_info = config.KNOWN_CARDS.get(guid)
        self.card_name_display.setText(
            card_info["name"] if card_info else i18n.t("basic.unknown_card")
        )
        if not getattr(self, "_loading", False):
            self.data_changed.emit()

    def on_card_type_changed(self):
        base_id = self.baseid_combo.currentData() or ""
        faction = self.faction_combo.currentData() or ""
        
        is_board_template = (base_id == "BoardAbility")
        is_trick = "OneTimeEffect" in base_id and not is_board_template
        is_env = "Environment" in base_id
        is_fighter = not is_trick and not is_env and not is_board_template
        is_zombie = "Zombies" in faction

        with signal_blocker(self.attack_cb, self.health_cb, self.flag_is_trick, 
                            self.flag_is_surprise, self.flag_is_env, self.flag_is_board):
            self.attack_cb.setChecked(is_fighter)
            self.health_cb.setChecked(is_fighter)
            self.attack_spin.setEnabled(is_fighter)
            self.health_spin.setEnabled(is_fighter)
            self.flag_is_trick.setChecked(is_trick)
            self.flag_is_env.setChecked(is_env)
            self.flag_is_surprise.setChecked(is_zombie and (is_trick or is_env))
            self.flag_is_board.setChecked(is_board_template)
        self.data_changed.emit()

    def _parse_csv_to_list(self, text, as_type=str):
        return [as_type(item.strip()) for item in text.split(',') if item.strip()]

    def sync_to_model(self, model):
        if getattr(self, "_loading", False):
            return
        model.guid = self.guid_spin.value()
        model.prefab_name = self.prefab_input.text().strip()
        model.faction = self.faction_combo.currentData()
        model.base_id = self.baseid_combo.currentData()
        model.color = self.color_combo.currentData()
        model.rarity_key = self.rarity_combo.currentData()
        model.set_name = self.set_combo.currentData()
        model.set_and_rarity_key = self.set_rarity_key_input.text().strip()
        model.crafting_buy = self.craft_buy_spin.value()
        model.crafting_sell = self.craft_sell_spin.value()
        model.cost = self.cost_spin.value()
        model.has_attack = self.attack_cb.isChecked()
        model.attack = self.attack_spin.value()
        model.has_health = self.health_cb.isChecked()
        model.health = self.health_spin.value()

        model.ignore_deck_limit = self.flag_ignore_limit.isChecked()
        model.is_power = self.flag_is_power.isChecked()
        model.is_primary_power = self.flag_is_primary_power.isChecked()

        model.is_trick = self.flag_is_trick.isChecked()
        model.is_surprise = self.flag_is_surprise.isChecked()
        model.is_environment = self.flag_is_env.isChecked()
        model.is_board_ability = self.flag_is_board.isChecked()

        model.root_special_abilities = [
            key for key, cb in self.root_ability_checkboxes.items() if cb.isChecked()
        ]
        model.subtype_affinities = self._parse_csv_to_list(self.sub_aff_input.text(), str)
        model.subtype_affinity_weights = self._parse_csv_to_list(self.sub_aff_w_input.text(), float)
        model.tag_affinities = self._parse_csv_to_list(self.tag_aff_input.text(), str)
        model.tag_affinity_weights = self._parse_csv_to_list(self.tag_aff_w_input.text(), float)
        model.card_affinities = self._parse_csv_to_list(self.card_aff_input.text(), int)
        model.card_affinity_weights = self._parse_csv_to_list(self.card_aff_w_input.text(), float)

    def _set_combo_by_data(self, combo, target_data):
        if target_data is None: return
        idx = combo.findData(target_data)
        if idx == -1 and isinstance(target_data, str):
            for i in range(combo.count()):
                if str(combo.itemData(i)).lower() == target_data.lower():
                    idx = i
                    break
        if idx >= 0: combo.setCurrentIndex(idx)

    def set_model(self, new_model):
        self.model = new_model
        self.update_ui(self.model)

    def update_ui(self, model):
        self._loading = True
        try:
            self._update_ui_impl(model)
        finally:
            self._loading = False

    def _update_ui_impl(self, model):
        with signal_blocker(self, self.baseid_combo, self.faction_combo, self.attack_cb, self.health_cb,
                            self.flag_is_trick, self.flag_is_surprise, self.flag_is_env, self.flag_is_board,
                            self.guid_spin, *self.root_ability_checkboxes.values()):
            self.guid_spin.setValue(model.guid)
            card_info = config.KNOWN_CARDS.get(model.guid)
            self.card_name_display.setText(
                card_info["name"] if card_info else i18n.t("basic.unknown_card")
            )
            self.prefab_input.setText(model.prefab_name)
            
            self._set_combo_by_data(self.faction_combo, model.faction)
            self._set_combo_by_data(self.baseid_combo, model.base_id)
            self._set_combo_by_data(self.color_combo, model.color)
            self._set_combo_by_data(self.rarity_combo, model.rarity_key)
            self._set_combo_by_data(self.set_combo, model.set_name)
            
            self.set_rarity_key_input.setText(model.set_and_rarity_key)
            self.craft_buy_spin.setValue(model.crafting_buy)
            self.craft_sell_spin.setValue(model.crafting_sell)
            self.cost_spin.setValue(model.cost)
            
            self.attack_cb.setChecked(model.has_attack)
            self.attack_spin.setEnabled(model.has_attack)
            self.attack_spin.setValue(model.attack)
            
            self.health_cb.setChecked(model.has_health)
            self.health_spin.setEnabled(model.has_health)
            self.health_spin.setValue(model.health)
            
            self.flag_ignore_limit.setChecked(model.ignore_deck_limit)
            self.flag_is_power.setChecked(model.is_power)
            self.flag_is_primary_power.setChecked(model.is_primary_power)
            
            self.flag_is_trick.setChecked(model.is_trick)
            self.flag_is_surprise.setChecked(model.is_surprise)
            self.flag_is_env.setChecked(model.is_environment)
            self.flag_is_board.setChecked(model.is_board_ability)
            
            for key, cb in self.root_ability_checkboxes.items():
                cb.setChecked(key in model.root_special_abilities)
                
            self.sub_aff_input.setText(", ".join(map(str, model.subtype_affinities)))
            self.sub_aff_w_input.setText(", ".join(map(str, model.subtype_affinity_weights)))
            self.tag_aff_input.setText(", ".join(model.tag_affinities))
            self.tag_aff_w_input.setText(", ".join(map(str, model.tag_affinity_weights)))
            self.card_aff_input.setText(", ".join(map(str, model.card_affinities)))
            self.card_aff_w_input.setText(", ".join(map(str, model.card_affinity_weights)))