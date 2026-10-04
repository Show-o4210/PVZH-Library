# ui/tab_basic.py
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QComboBox, QCheckBox, QGridLayout,
    QSpinBox, QWidget
)
from ui.base_components import BaseTab, SearchableSelectButton
from constants import SCENES
from i18n import t, localized_pairs


BASIC_STYLE = """
    QWidget {
        background-color: #F8FAFC;
        color: #1F2937;
        font-family: "Segoe UI", "Microsoft YaHei";
        font-size: 13px;
    }
    QGroupBox {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        margin-top: 12px;
        padding: 18px;
        font-weight: 700;
        color: #0F172A;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 16px;
        padding: 0px 6px;
        background-color: #F8FAFC;
    }
    QLabel { background: transparent; color: #475569; font-weight: 500; }
    QLabel#sectionHint { color: #94A3B8; font-size: 12px; font-weight: 400; }
    QLineEdit, QComboBox, QSpinBox {
        background-color: #FFFFFF; color: #111827;
        border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 9px 12px; min-height: 24px;
        selection-background-color: #BFDBFE;
    }
    QLineEdit:hover, QComboBox:hover, QSpinBox:hover { border: 1px solid #CBD5E1; }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border: 1px solid #60A5FA; background-color: #FFFFFF;
    }
    QComboBox::drop-down { border: none; width: 30px; background: transparent; }
    QSpinBox::up-button, QSpinBox::down-button { border: none; background: transparent; width: 22px; }
    QSpinBox::up-arrow, QSpinBox::down-arrow { width: 0px; height: 0px; }
    QCheckBox {
        background-color: #FFFFFF; color: #334155;
        border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 12px 14px; spacing: 10px; font-weight: 500;
    }
    QCheckBox:hover { background-color: #F8FAFC; border: 1px solid #CBD5E1; }
    QCheckBox::indicator {
        width: 18px; height: 18px; border-radius: 5px;
        border: 1px solid #CBD5E1; background-color: #FFFFFF;
    }
    QCheckBox::indicator:checked {
        background-color: #2563EB; border: 1px solid #2563EB;
    }
"""


class BasicConfigTab(BaseTab):
    def __init__(self, data_manager):
        super().__init__(data_manager)
        # self.setStyleSheet(BASIC_STYLE) # Inherit global stylesheet from main window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # 1. 关卡基本信息
        self.info_group = QGroupBox(t("basic.info_group"))
        il = QGridLayout(self.info_group)
        il.setContentsMargins(20, 30, 20, 20)
        il.setHorizontalSpacing(16)
        il.setVerticalSpacing(16)
        il.setColumnStretch(1, 1)
        il.setColumnStretch(2, 1)

        self.title_lbl = QLabel(t("basic.section_title"))
        self.title_lbl.setStyleSheet("color: #0F172A; font-size: 14px; font-weight: 700;")
        il.addWidget(self.title_lbl, 0, 0, 1, 3)

        self.hint_lbl = QLabel(t("basic.section_hint"))
        self.hint_lbl.setObjectName("sectionHint")
        il.addWidget(self.hint_lbl, 1, 0, 1, 3)

        self.lbl_level_id = QLabel(t("basic.level_id"))
        il.addWidget(self.lbl_level_id, 2, 0)
        self.id_entry = QLineEdit()
        self.id_entry.setPlaceholderText(t("basic.level_id_ph"))
        self.id_entry.textEdited.connect(self.ui_changed)
        il.addWidget(self.id_entry, 2, 1, 1, 2)

        self.lbl_elo = QLabel(t("basic.elo"))
        il.addWidget(self.lbl_elo, 3, 0)
        elo_wrap = QWidget()
        elo_wrap.setStyleSheet("background: transparent;")
        elo_layout = QHBoxLayout(elo_wrap)
        elo_layout.setContentsMargins(0, 0, 0, 0)
        elo_layout.setSpacing(10)

        self.elo_combo = QComboBox()
        self._refill_elo_combo()
        self.elo_combo.currentIndexChanged.connect(self._on_elo_preset_changed)
        elo_layout.addWidget(self.elo_combo, 1)

        self.elo_spin = QSpinBox()
        self.elo_spin.setRange(0, 99999)
        self.elo_spin.setSingleStep(100)
        self.elo_spin.setValue(1700)
        self.elo_spin.setPrefix(t("basic.elo_custom_prefix"))
        self.elo_spin.valueChanged.connect(self._on_elo_manual_changed)
        elo_layout.addWidget(self.elo_spin, 1)
        il.addWidget(elo_wrap, 3, 1, 1, 2)

        self.lbl_scene = QLabel(t("basic.scene"))
        il.addWidget(self.lbl_scene, 4, 0)
        self.board_btn = SearchableSelectButton(t("basic.select_scene"), localized_pairs(SCENES))
        self.board_btn.valueChanged.connect(self.ui_changed)
        il.addWidget(self.board_btn, 4, 1, 1, 2)
        layout.addWidget(self.info_group)

        # 2. 核心规则开关
        self.rules_group = QGroupBox(t("basic.rules_group"))
        rl = QGridLayout(self.rules_group)
        rl.setContentsMargins(20, 30, 20, 20)
        rl.setHorizontalSpacing(14)
        rl.setVerticalSpacing(14)

        self.must_play = QCheckBox(t("basic.must_play"))
        self.disable_surprise = QCheckBox(t("basic.disable_surprise"))
        self.enable_ready = QCheckBox(t("basic.enable_ready"))
        self.skip_hero = QCheckBox(t("basic.skip_hero"))

        for i, cb in enumerate([
            self.must_play,
            self.disable_surprise,
            self.enable_ready,
            self.skip_hero,
        ]):
            cb.stateChanged.connect(self.ui_changed)
            rl.addWidget(cb, i // 2, i % 2)

        layout.addWidget(self.rules_group)
        layout.addStretch()

    def _refill_elo_combo(self):
        current = self.elo_combo.currentData() if self.elo_combo.count() else None
        self.elo_combo.blockSignals(True)
        self.elo_combo.clear()
        for text_key, val in [
            ("basic.elo_easy", 500),
            ("basic.elo_simple", 1000),
            ("basic.elo_normal", 1700),
            ("basic.elo_hard", 2500),
            ("basic.elo_expert", 3500),
        ]:
            self.elo_combo.addItem(t(text_key), val)
        if current is not None:
            idx = self.elo_combo.findData(current)
            if idx >= 0:
                self.elo_combo.setCurrentIndex(idx)
        self.elo_combo.blockSignals(False)

    def retranslate_ui(self):
        self.info_group.setTitle(t("basic.info_group"))
        self.title_lbl.setText(t("basic.section_title"))
        self.hint_lbl.setText(t("basic.section_hint"))
        self.lbl_level_id.setText(t("basic.level_id"))
        self.id_entry.setPlaceholderText(t("basic.level_id_ph"))
        self.lbl_elo.setText(t("basic.elo"))
        self._refill_elo_combo()
        self.elo_spin.setPrefix(t("basic.elo_custom_prefix"))
        self.lbl_scene.setText(t("basic.scene"))
        self.board_btn.set_title(t("basic.select_scene"))
        self.board_btn.set_items(localized_pairs(SCENES))
        self.rules_group.setTitle(t("basic.rules_group"))
        self.must_play.setText(t("basic.must_play"))
        self.disable_surprise.setText(t("basic.disable_surprise"))
        self.enable_ready.setText(t("basic.enable_ready"))
        self.skip_hero.setText(t("basic.skip_hero"))
        if self.elo_combo.currentIndex() < 0:
            self.elo_combo.setPlaceholderText(t("basic.elo_custom_ph"))

    def _on_elo_preset_changed(self):
        value = self.elo_combo.currentData()
        if value is not None and self.elo_spin.value() != value:
            self.elo_spin.blockSignals(True)
            self.elo_spin.setValue(value)
            self.elo_spin.blockSignals(False)
        self.ui_changed.emit()

    def _on_elo_manual_changed(self, value):
        idx = self.elo_combo.findData(value)
        self.elo_combo.blockSignals(True)
        if idx >= 0:
            self.elo_combo.setCurrentIndex(idx)
        else:
            self.elo_combo.setCurrentIndex(-1)
            self.elo_combo.setPlaceholderText(t("basic.elo_custom_ph"))
        self.elo_combo.blockSignals(False)
        self.ui_changed.emit()

    def _set_elo_value(self, elo):
        self.elo_spin.blockSignals(True)
        self.elo_spin.setValue(int(elo))
        self.elo_spin.blockSignals(False)

        idx = self.elo_combo.findData(int(elo))
        self.elo_combo.blockSignals(True)
        if idx >= 0:
            self.elo_combo.setCurrentIndex(idx)
        else:
            self.elo_combo.setCurrentIndex(-1)
            self.elo_combo.setPlaceholderText(t("basic.elo_custom_ph"))
        self.elo_combo.blockSignals(False)

    def load_data(self, config):
        self.id_entry.setText(config.get("Id", ""))
        self._set_elo_value(config.get("OpponentElo", 1700))

        board = config.get("BoardConfig", {}).get("PlantsBoardName", "GrassKnuckles")
        self.board_btn.set_data(board)

        self.must_play.setChecked(config.get("MustPlayAllPlayableCards", False))
        self.disable_surprise.setChecked(config.get("DisableSurprisePhase", False))
        self.enable_ready.setChecked(config.get("EnableReadySetPlant", True))
        self.skip_hero.setChecked(config.get("SkipHeroSelect", False))

    def save_data(self, config):
        level_id = self.id_entry.text().strip()
        config["Id"] = level_id
        config["OpponentElo"] = self.elo_spin.value()

        if "PreGameConfig" not in config or not isinstance(config.get("PreGameConfig"), dict):
            config["PreGameConfig"] = {"Narrative": ""}

        config["PreGameConfig"]["Name"] = f"Node_{level_id}:Name"
        config["PreGameConfig"]["Description"] = f"Node_{level_id}:Description"

        if "BoardConfig" not in config or not isinstance(config.get("BoardConfig"), dict):
            config["BoardConfig"] = {}

        scene_id = self.board_btn.get_data() or "GrassKnuckles"
        config["BoardConfig"]["PlantsBoardName"] = scene_id
        config["BoardConfig"]["ZombiesBoardName"] = scene_id

        config["MustPlayAllPlayableCards"] = self.must_play.isChecked()
        config["DisableSurprisePhase"] = self.disable_surprise.isChecked()
        config["EnableReadySetPlant"] = self.enable_ready.isChecked()
        config["SkipHeroSelect"] = self.skip_hero.isChecked()
