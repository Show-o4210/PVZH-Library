# ui/tab_character.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QScrollArea, QGridLayout, QDialog, QSizePolicy
)
from PySide6.QtCore import Qt
from ui.base_components import BaseTab
from ui.dialog_hero_select import HeroSelectDialog
from ui.dialog_deck_select import DeckSelectDialog
from constants import ALL_HEROES
from i18n import t, localized_name

INT32_MAX = 2147483647


class CharacterConfigTab(BaseTab):
    def __init__(self, data_manager, config_key):
        super().__init__(data_manager)
        self.config_key = config_key
        self.current_hero_id = ""
        self.current_hero_name = ""
        self.current_deck_id = ""

        # self.setStyleSheet(self._style_sheet()) # Inherit global stylesheet from main window

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # =========================
        # 基础参数
        # =========================
        self.bg = QGroupBox(t("char.basic_group"))
        bl = QGridLayout(self.bg)
        bl.setContentsMargins(20, 30, 20, 20)
        bl.setHorizontalSpacing(16)
        bl.setVerticalSpacing(14)
        bl.setColumnStretch(0, 0)
        bl.setColumnStretch(1, 1)

        self.hero_btn = self._make_select_button(t("char.select_hero"))
        self.hero_btn.clicked.connect(self._open_hero_dialog)
        self.lbl_hero = self._make_label(t("char.hero"))
        bl.addWidget(self.lbl_hero, 0, 0)
        bl.addWidget(self.hero_btn, 0, 1)

        self.faction_combo = QComboBox()
        self.faction_combo.addItem(t("char.faction_plant"), 0)
        self.faction_combo.addItem(t("char.faction_zombie"), 1)
        self.faction_combo.setEnabled(False)
        self.lbl_faction = self._make_label(t("char.faction"))
        bl.addWidget(self.lbl_faction, 1, 0)
        bl.addWidget(self.faction_combo, 1, 1)

        self.hp_spin = self._make_spin(20)
        self.draw_spin = self._make_spin(4)
        self.turn_draw_spin = self._make_spin(1)
        self.sun_spin = self._make_spin(1)
        self.super_spin = self._make_spin(1)

        self.lbl_hp = self._make_label(t("char.hp"))
        self.lbl_draw = self._make_label(t("char.draw"))
        self.lbl_turn_draw = self._make_label(t("char.turn_draw"))
        self.lbl_sun = self._make_label(t("char.sun"))
        self.lbl_super = self._make_label(t("char.super"))
        bl.addWidget(self.lbl_hp, 2, 0); bl.addWidget(self.hp_spin, 2, 1)
        bl.addWidget(self.lbl_draw, 3, 0); bl.addWidget(self.draw_spin, 3, 1)
        bl.addWidget(self.lbl_turn_draw, 4, 0); bl.addWidget(self.turn_draw_spin, 4, 1)
        bl.addWidget(self.lbl_sun, 5, 0); bl.addWidget(self.sun_spin, 5, 1)
        bl.addWidget(self.lbl_super, 6, 0); bl.addWidget(self.super_spin, 6, 1)

        self.deck_btn = self._make_select_button(t("char.select_deck"))
        self.deck_btn.clicked.connect(self._open_deck_dialog)
        self.lbl_deck = self._make_label(t("char.deck"))
        bl.addWidget(self.lbl_deck, 7, 0)
        bl.addWidget(self.deck_btn, 7, 1)

        self.deck_manual_le = QLineEdit()
        self.deck_manual_le.setPlaceholderText(t("char.manual_id_ph"))
        self.deck_manual_le.textEdited.connect(self._on_manual_deck_edit)
        self.lbl_manual = self._make_label(t("char.manual_id"))
        bl.addWidget(self.lbl_manual, 8, 0)
        bl.addWidget(self.deck_manual_le, 8, 1)

        layout.addWidget(self.bg)

        # =========================
        # 规则与高级设置
        # =========================
        self.rg = QGroupBox(t("char.rules_group"))
        rl = QGridLayout(self.rg)
        rl.setContentsMargins(20, 30, 20, 20)
        rl.setHorizontalSpacing(18)
        rl.setVerticalSpacing(14)

        self.shuffle_deck = QCheckBox(t("char.shuffle_deck"))
        self.shuffle_super = QCheckBox(t("char.shuffle_super"))
        self.mulligan = QCheckBox(t("char.mulligan"))
        self.die_empty = QCheckBox(t("char.die_empty"))
        self.timed_turns = QCheckBox(t("char.timed_turns"))
        self.create_all = QCheckBox(t("char.create_all"))

        checkboxes = [
            self.shuffle_deck, self.shuffle_super, self.mulligan,
            self.die_empty, self.timed_turns, self.create_all
        ]
        for i, cb in enumerate(checkboxes):
            cb.stateChanged.connect(self.ui_changed)
            rl.addWidget(cb, i // 3, i % 3)

        self.max_hand_spin = self._make_spin(10)
        self.lbl_max_hand = self._make_label(t("char.max_hand"))
        rl.addWidget(self.lbl_max_hand, 2, 0)
        rl.addWidget(self.max_hand_spin, 2, 1)
        layout.addWidget(self.rg)

        # =========================
        # 护盾与格挡规则
        # =========================
        self.sg = QGroupBox(t("char.shield_group"))
        sl = QVBoxLayout(self.sg)
        sl.setContentsMargins(20, 30, 20, 20)
        sl.setSpacing(14)

        shield_top = QHBoxLayout()
        shield_top.setSpacing(12)
        self.lbl_shield_max = self._make_label(t("char.shield_max"))
        shield_top.addWidget(self.lbl_shield_max)
        self.shield_max_spin = self._make_spin(80)
        self.shield_max_spin.setFixedWidth(180)
        shield_top.addWidget(self.shield_max_spin)
        shield_top.addStretch()
        sl.addLayout(shield_top)

        self.shield_table_widget = QWidget()
        self.shield_table_widget.setObjectName("shieldTable")
        self.shield_layout = QVBoxLayout(self.shield_table_widget)
        self.shield_layout.setContentsMargins(0, 0, 0, 0)
        self.shield_layout.setSpacing(10)
        sl.addWidget(self.shield_table_widget)

        self.shield_rows_data = []

        btn_l = QHBoxLayout()
        btn_l.setSpacing(10)
        self.add_btn = QPushButton(t("char.add_shield_row"))
        self.del_btn = QPushButton(t("char.del_shield_row"))
        self.del_btn.setObjectName("secondaryButton")
        self.add_btn.clicked.connect(self._add_shield_row)
        self.del_btn.clicked.connect(self._del_shield_row)
        btn_l.addWidget(self.add_btn)
        btn_l.addWidget(self.del_btn)
        btn_l.addStretch()
        sl.addLayout(btn_l)
        layout.addWidget(self.sg)

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def retranslate_ui(self):
        self.bg.setTitle(t("char.basic_group"))
        self.lbl_hero.setText(t("char.hero"))
        self.lbl_faction.setText(t("char.faction"))
        fac_data = self.faction_combo.currentData()
        self.faction_combo.blockSignals(True)
        self.faction_combo.clear()
        self.faction_combo.addItem(t("char.faction_plant"), 0)
        self.faction_combo.addItem(t("char.faction_zombie"), 1)
        idx = self.faction_combo.findData(fac_data)
        if idx >= 0:
            self.faction_combo.setCurrentIndex(idx)
        self.faction_combo.blockSignals(False)

        self.lbl_hp.setText(t("char.hp"))
        self.lbl_draw.setText(t("char.draw"))
        self.lbl_turn_draw.setText(t("char.turn_draw"))
        self.lbl_sun.setText(t("char.sun"))
        self.lbl_super.setText(t("char.super"))
        self.lbl_deck.setText(t("char.deck"))
        self.lbl_manual.setText(t("char.manual_id"))
        self.deck_manual_le.setPlaceholderText(t("char.manual_id_ph"))
        self.rg.setTitle(t("char.rules_group"))
        self.shuffle_deck.setText(t("char.shuffle_deck"))
        self.shuffle_super.setText(t("char.shuffle_super"))
        self.mulligan.setText(t("char.mulligan"))
        self.die_empty.setText(t("char.die_empty"))
        self.timed_turns.setText(t("char.timed_turns"))
        self.create_all.setText(t("char.create_all"))
        self.lbl_max_hand.setText(t("char.max_hand"))
        self.sg.setTitle(t("char.shield_group"))
        self.lbl_shield_max.setText(t("char.shield_max"))
        self.add_btn.setText(t("char.add_shield_row"))
        self.del_btn.setText(t("char.del_shield_row"))

        # 刷新护盾行标签
        for w_spin, c_spin, row in self.shield_rows_data:
            labels = row.findChildren(QLabel)
            if len(labels) >= 2:
                labels[0].setText(t("char.rng_weight"))
                labels[1].setText(t("char.charge_amount"))

        # 刷新英雄 / 卡组按钮文案
        self._refresh_hero_button()
        if self.current_deck_id and self.deck_manual_le.text().strip() == self.current_deck_id:
            # keep deck display from data
            pass
        elif not self.current_deck_id:
            self.deck_btn.setText(t("char.select_deck"))

    def _refresh_hero_button(self):
        if not self.current_hero_id:
            self.hero_btn.setText(t("char.select_hero"))
            return
        name = ""
        for h in ALL_HEROES:
            if h[0] == self.current_hero_id:
                name = localized_name(h)
                break
        self.current_hero_name = name
        self.hero_btn.setText(
            f"{name} ({self.current_hero_id})" if name else self.current_hero_id
        )

    # =========================
    # UI helpers
    # =========================
    def _style_sheet(self):
        return """
            QWidget {
                color: #111827;
                font-family: "Segoe UI", "Microsoft YaHei";
                font-size: 13px;
            }

            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                margin-top: 12px;
                font-weight: 700;
                color: #0F172A;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px;
                background-color: #F8FAFC;
            }

            QLabel#fieldLabel {
                background: transparent;
                color: #475569;
                font-weight: 600;
                padding-top: 2px;
            }

            QLineEdit, QComboBox, QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #DDE3EA;
                border-radius: 11px;
                padding: 9px 12px;
                min-height: 24px;
                selection-background-color: #BFDBFE;
            }

            QLineEdit:hover, QComboBox:hover, QSpinBox:hover {
                border: 1px solid #CBD5E1;
                background-color: #FFFFFF;
            }

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #60A5FA;
            }

            QComboBox:disabled {
                color: #64748B;
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
            }

            QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: transparent;
                width: 28px;
            }

            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 11px;
                padding: 10px 16px;
                min-height: 24px;
                font-weight: 700;
            }

            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }

            QPushButton#selectButton {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #DDE3EA;
                text-align: left;
                padding: 10px 14px;
                font-weight: 600;
            }

            QPushButton#selectButton:hover {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
            }

            QPushButton#secondaryButton {
                background-color: #F8FAFC;
                color: #334155;
                border: 1px solid #DDE3EA;
            }

            QPushButton#secondaryButton:hover {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
            }

            QCheckBox {
                spacing: 8px;
                color: #334155;
                font-weight: 500;
                padding: 6px 4px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1px solid #CBD5E1;
                background: #FFFFFF;
            }

            QCheckBox::indicator:checked {
                background-color: #2563EB;
                border: 1px solid #2563EB;
            }

            QWidget#shieldRow {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 5px;
                min-height: 32px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """

    def _make_label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        label.setMinimumWidth(110)
        return label

    def _add_row(self, layout, row, label_text, widget):
        layout.addWidget(self._make_label(label_text), row, 0)
        layout.addWidget(widget, row, 1)

    def _make_select_button(self, text):
        btn = QPushButton(text)
        btn.setObjectName("selectButton")
        btn.setMinimumHeight(46)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return btn

    def _make_spin(self, default_val):
        s = QSpinBox()
        s.setRange(0, INT32_MAX)
        s.setValue(default_val)
        s.valueChanged.connect(self.ui_changed)
        return s

    def _add_shield_row(self, weight=33, charge=10):
        row = QWidget()
        row.setObjectName("shieldRow")
        l = QHBoxLayout(row)
        l.setContentsMargins(14, 10, 14, 10)
        l.setSpacing(12)

        w_spin = self._make_spin(weight)
        c_spin = self._make_spin(charge)
        w_spin.setFixedWidth(150)
        c_spin.setFixedWidth(150)

        l.addWidget(self._make_label(t("char.rng_weight")))
        l.addWidget(w_spin)
        l.addSpacing(12)
        l.addWidget(self._make_label(t("char.charge_amount")))
        l.addWidget(c_spin)
        l.addStretch()

        self.shield_layout.addWidget(row)
        self.shield_rows_data.append((w_spin, c_spin, row))
        self.ui_changed.emit()

    def _del_shield_row(self):
        if len(self.shield_rows_data) > 1:
            _w_spin, _c_spin, row = self.shield_rows_data.pop()
            row.deleteLater()
            self.ui_changed.emit()

    # =========================
    # 弹窗与联动逻辑
    # =========================
    def _open_hero_dialog(self):
        dialog = HeroSelectDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_hero_id:
            self.current_hero_id = dialog.selected_hero_id
            self.current_hero_name = dialog.selected_hero_name
            self.hero_btn.setText(f"{self.current_hero_name} ({self.current_hero_id})")

            idx = self.faction_combo.findData(dialog.selected_faction)
            if idx >= 0:
                self.faction_combo.setCurrentIndex(idx)
            self.ui_changed.emit()

    def _hero_match_names(self):
        """返回用于匹配 decks.json 的英雄名列表（含中英文，兼容数据文件中的中文名）。"""
        names = []
        if self.current_hero_name:
            names.append(self.current_hero_name)
        for h in ALL_HEROES:
            if h[0] == self.current_hero_id:
                for n in h[1:]:
                    if n and n not in names:
                        names.append(n)
                break
        return names

    def _open_deck_dialog(self):
        # 推荐卡组按中文名匹配 decks.json，同时传入当前显示名
        match_names = self._hero_match_names()
        primary = match_names[0] if match_names else self.current_hero_name
        dialog = DeckSelectDialog(
            self.dm.deck_db,
            current_hero_name=primary,
            parent=self,
            hero_match_names=match_names,
        )
        if dialog.exec() == QDialog.Accepted and dialog.selected_deck_id:
            self.current_deck_id = dialog.selected_deck_id
            display_text = self.current_deck_id
            for text, d_id in self.dm.deck_db.items():
                if d_id == self.current_deck_id:
                    display_text = f"{text.split('|')[-1].strip()} ({d_id})"
                    break
            self.deck_btn.setText(display_text)
            self.deck_manual_le.setText(self.current_deck_id)
            self.ui_changed.emit()

    def _on_manual_deck_edit(self, text):
        self.current_deck_id = text.strip()
        self.deck_btn.setText(
            t("char.manual_override") if self.current_deck_id else t("char.select_deck")
        )
        self.ui_changed.emit()

    # =========================
    # 数据读写
    # =========================
    def load_data(self, config):
        c = config.get(self.config_key) or {}
        p = c.get("Parameters") or {}

        idx = self.faction_combo.findData(p.get("Faction", 0))
        if idx >= 0:
            self.faction_combo.setCurrentIndex(idx)

        self.current_hero_id = c.get("HeroId", "Citron")
        self.current_hero_name = ""
        for h in ALL_HEROES:
            if h[0] == self.current_hero_id:
                self.current_hero_name = localized_name(h)
                break
        self.hero_btn.setText(
            f"{self.current_hero_name} ({self.current_hero_id})" if self.current_hero_name else self.current_hero_id
        )

        self.current_deck_id = c.get("DeckId", "")
        self.deck_manual_le.setText(self.current_deck_id)
        if self.current_deck_id:
            display_text = self.current_deck_id
            for text, d_id in self.dm.deck_db.items():
                if d_id == self.current_deck_id:
                    display_text = f"{text.split('|')[-1].strip()} ({d_id})"
                    break
            self.deck_btn.setText(display_text)
        else:
            self.deck_btn.setText(t("char.select_deck"))

        self.hp_spin.setValue(p.get("InitialHealth", 20))
        self.draw_spin.setValue(p.get("InitialCardsToDrawFromDeck", 4))
        self.turn_draw_spin.setValue(p.get("NumCardsToDrawPerTurn", 1))
        self.sun_spin.setValue(p.get("InitialSunCount", 1))
        self.super_spin.setValue(p.get("InitialCardsToDrawFromSuperpowerPool", 1))
        self.max_hand_spin.setValue(p.get("MaxHandSize", 10))
        self.shield_max_spin.setValue(p.get("BlockMeterMax", 80))

        self.shuffle_deck.setChecked(p.get("ShuffleDeckAtStartOfGame", True))
        self.shuffle_super.setChecked(p.get("ShuffleSuperpowerPoolAtStartOfGame", True))
        self.mulligan.setChecked(p.get("MulliganAtStartOfGame", True))
        self.die_empty.setChecked(p.get("DiesWhenDrawingOnEmpty", False))
        self.timed_turns.setChecked(p.get("HasTimedTurns", False))
        self.create_all.setChecked(p.get("CreateAllCardsInDeck", False))

        for _w_spin, _c_spin, row in self.shield_rows_data:
            row.deleteLater()
        self.shield_rows_data.clear()

        table_entries = (p.get("SuperBlockTable") or {}).get("TableEntries", []) or []
        for entry in table_entries:
            self._add_shield_row(entry.get("RngWeight", 33), entry.get("ChargeAmount", 10))
        if not self.shield_rows_data:
            self._add_shield_row()

    def save_data(self, config):
        if self.config_key not in config or not isinstance(config.get(self.config_key), dict):
            config[self.config_key] = {}
        c = config[self.config_key]
        if "Parameters" not in c or not isinstance(c.get("Parameters"), dict):
            c["Parameters"] = {}
        p = c["Parameters"]

        c["HeroId"] = self.current_hero_id or "Citron"
        c["DeckId"] = self.deck_manual_le.text().strip()
        p["Faction"] = self.faction_combo.currentData()

        p["InitialHealth"] = self.hp_spin.value()
        p["InitialCardsToDrawFromDeck"] = self.draw_spin.value()
        p["NumCardsToDrawPerTurn"] = self.turn_draw_spin.value()
        p["InitialSunCount"] = self.sun_spin.value()
        p["InitialCardsToDrawFromSuperpowerPool"] = self.super_spin.value()
        p["MaxHandSize"] = self.max_hand_spin.value()
        p["BlockMeterMax"] = self.shield_max_spin.value()

        p["ShuffleDeckAtStartOfGame"] = self.shuffle_deck.isChecked()
        p["ShuffleSuperpowerPoolAtStartOfGame"] = self.shuffle_super.isChecked()
        p["MulliganAtStartOfGame"] = self.mulligan.isChecked()
        p["DiesWhenDrawingOnEmpty"] = self.die_empty.isChecked()
        p["HasTimedTurns"] = self.timed_turns.isChecked()
        p["CreateAllCardsInDeck"] = self.create_all.isChecked()

        if "SuperBlockTable" not in p or not isinstance(p.get("SuperBlockTable"), dict):
            p["SuperBlockTable"] = {"TableEntries": []}
        p["SuperBlockTable"]["TableEntries"] = []
        for w_spin, c_spin, _row in self.shield_rows_data:
            p["SuperBlockTable"]["TableEntries"].append({
                "RngWeight": w_spin.value(),
                "ChargeAmount": c_spin.value()
            })
