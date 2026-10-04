# ui/tab_events.py
import copy
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QDialog, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QMessageBox, QCompleter,
    QAbstractItemView, QFrame, QGraphicsDropShadowEffect, QSizePolicy 
)
from PySide6.QtGui import QShortcut, QKeySequence, QColor, QDrag 
from PySide6.QtCore import Qt, Signal
from ui.base_components import BaseTab
from theme import apply_dialog_theme, get_theme_colors, is_dark_theme
from i18n import t



# ==========================================
# 支持拖拽排序并同步底层数据的列表
# ==========================================
class DragDropListWidget(QListWidget):
    order_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(False)

    def startDrag(self, supportedActions):
        """重写拖拽起点：抓取真实卡片的截图，拒绝变成灰色方块"""
        item = self.currentItem()
        if not item:
            return

        widget = self.itemWidget(item)
        if widget:
            # 对卡片进行无背景截图
            pixmap = widget.grab()
            drag = QDrag(self)
            # 获取原生的拖拽数据（保证内部移动逻辑依然生效）
            mimeData = self.model().mimeData([self.indexFromItem(item)])
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            
            # 让鼠标光标位于拖拽图片的中心
            drag.setHotSpot(pixmap.rect().center())
            
            # 执行拖拽
            drag.exec(supportedActions, Qt.MoveAction)
        else:
            super().startDrag(supportedActions)

    def dropEvent(self, event):
        super().dropEvent(event)
        # 拖拽放下后更新数据
        self.order_updated.emit()


# ==========================================
# 卡牌联想输入组件
# ==========================================
class CardInputWidget(QWidget):
    card_selected = Signal(int)

    def __init__(self, card_index, parent=None):
        super().__init__(parent)
        self.card_index = card_index or []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.le = QLineEdit()
        self.le.setPlaceholderText(t("events.card_input_ph"))

        strings = [f"{name} ({guid})" for guid, name in self.card_index]
        self.completer = QCompleter(strings, self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.le.setCompleter(self.completer)

        self.completer.activated.connect(self.le.setText)
        layout.addWidget(self.le, 1)

    def get_guid(self):
        text = self.le.text().strip()
        m = re.search(r"\((\d+)\)", text)
        if m:
            return int(m.group(1))
        if text.isdigit():
            return int(text)

        # 输入了文字但没确认联想项时，尝试取第一个匹配项
        self.completer.setCompletionPrefix(text)
        if self.completer.completionCount() > 0:
            first = self.completer.completionModel().index(0, 0).data()
            if first:
                m2 = re.search(r"\((\d+)\)", first)
                if m2:
                    self.le.setText(first)
                    return int(m2.group(1))
        return None

    def set_guid(self, guid):
        for g, n in self.card_index:
            if g == guid:
                self.le.setText(f"{n} ({g})")
                return
        self.le.setText(str(guid))

# ==========================================
# 自定义事件卡片组件
# ==========================================
class EventCardWidget(QWidget):
    def __init__(self, ev_data, index, card_name_func, parent=None):
        super().__init__(parent)
        self.ev_data = ev_data
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # 【关键修改 1】：强制撑开卡片基础高度，防止太小
        self.setMinimumHeight(76) 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        self.frame = QFrame()
        self.frame.setObjectName("cardFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        alpha = 80 if is_dark_theme() else 25
        shadow.setColor(QColor(0, 0, 0, alpha))
        shadow.setOffset(0, 2)
        self.frame.setGraphicsEffect(shadow)

        fl = QVBoxLayout(self.frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(6)

        title_lbl = QLabel()
        desc_lbl = QLabel()
        
        # 【关键修改 2】：确保长文本能换行，并且能挤占足够的剩余空间
        desc_lbl.setWordWrap(True)
        desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        desc_lbl.setMinimumHeight(32)

        # ====== 数据解析与卡片样式设定 ======
        ev_type = ev_data.get("$type", "")
        title_text = t("events.unknown_title", n=index + 1)
        desc_text = t("events.unknown_desc")
        border_color = "#94A3B8" # 默认灰色

        if "MessageEventConfig" in ev_type:
            turn = ev_data.get("TriggerConfig", {}).get("TurnNumber", 0)
            n_map = {
                0: t("events.narrator_none"),
                1: t("events.narrator_dave"),
                2: t("events.narrator_zomboss"),
            }
            narr = n_map.get(ev_data.get("Narrator", 0), t("common.unknown"))
            title_text = t("events.msg_title", n=index + 1, turn=turn)
            desc_text = t("events.msg_desc", narr=narr, key=ev_data.get("TextKey", ""))
            border_color = "#3B82F6" # 对话事件用蓝色

        elif "AddCardToTopOfDeckConfig" in ev_type:
            fac = t("common.zombies") if ev_data.get("PlayerFaction") == 1 else t("common.plants")
            cards = ev_data.get("CardIds", [])
            preview = "、".join(card_name_func(g) for g in cards[:3]) if cards else ""
            if len(cards) > 3:
                preview += t("events.reward_more", n=len(cards))
            elif not preview:
                preview = t("common.empty")
            title_text = t("events.reward_title", n=index + 1)
            desc_text = t("events.reward_desc", fac=fac, preview=preview)
            border_color = "#10B981" # 奖励发牌用绿色

        elif "MoveCardToTopOfDeckConfig" in ev_type:
            turn = ev_data.get("TurnNumber", 0)
            fac = t("common.zombies") if ev_data.get("PlayerFaction") == 1 else t("common.plants")
            guid = ev_data.get("CardGuid", 0)
            title_text = t("events.draw_title", n=index + 1, turn=turn)
            desc_text = t("events.draw_desc", fac=fac, card=card_name_func(guid))
            border_color = "#F59E0B" # 强制抽卡用橙黄色

        elif "ScriptedTurnEventConfig" in ev_type:
            turn = ev_data.get("TurnNumber", 0)
            plays = ev_data.get("Plays", [{}])
            guid = plays[0].get("CardGuid", 0) if plays else 0
            any_lane = t("common.any")
            lane = plays[0].get("LaneIndex", any_lane) if plays and "LaneIndex" in plays[0] else any_lane
            if lane != any_lane:
                lane = t("events.lane_n", n=lane + 1)
            title_text = t("events.script_title", n=index + 1, turn=turn)
            desc_text = t("events.script_desc", lane=lane, card=card_name_func(guid))
            border_color = "#8B5CF6" # 强制出牌用紫色

        title_lbl.setText(title_text)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {border_color};")
        
        desc_lbl.setText(desc_text)
        muted = get_theme_colors().get("label_text", "#64748B")
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {muted}; font-weight: 400;")

        fl.addWidget(title_lbl)
        fl.addWidget(desc_lbl)

        # 卡片背景跟随主题，左侧色条区分事件类型
        colors = get_theme_colors()
        card_bg = colors.get("card_bg", "#FFFFFF")
        border = colors.get("border", "#E2E8F0")
        self.frame.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: {card_bg};
                border: 1px solid {border};
                border-left: 5px solid {border_color};
                border-radius: 8px;
            }}
        """)
        
        layout.addWidget(self.frame)

# ==========================================
# 主面板：游戏事件配置 Tab
# ==========================================
class GameEventsTab(BaseTab):
    def __init__(self, data_manager):
        super().__init__(data_manager)
        self.events_data = []
        # self.setStyleSheet(APP_STYLE) # Inherit global stylesheet from main window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        self.group = QGroupBox(t("events.group"))
        gl = QVBoxLayout(self.group)
        gl.setContentsMargins(20, 30, 20, 20)
        gl.setSpacing(14)

        title_row = QHBoxLayout()
        self.title = QLabel(t("events.list_title"))
        self.title.setObjectName("sectionTitle")
        self.title.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.hint = QLabel(t("events.list_hint"))
        self.hint.setObjectName("hintLabel")
        title_row.addWidget(self.title)
        title_row.addStretch()
        title_row.addWidget(self.hint)
        gl.addLayout(title_row)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.btn_dialog = self._make_btn(t("events.add_dialog"), self._show_dialog_event_ui, "secondaryButton")
        self.btn_reward = self._make_btn(t("events.add_reward"), self._show_reward_event_ui, "secondaryButton")
        self.btn_force_draw = self._make_btn(t("events.add_force_draw"), self._show_force_draw_ui, "secondaryButton")
        self.btn_scripted = self._make_btn(t("events.add_scripted"), self._show_scripted_turn_ui, "purpleButton")
        btn_layout.addWidget(self.btn_dialog)
        btn_layout.addWidget(self.btn_reward)
        btn_layout.addWidget(self.btn_force_draw)
        btn_layout.addWidget(self.btn_scripted)
        btn_layout.addStretch()
        gl.addLayout(btn_layout)

        self.list_widget = DragDropListWidget()
        self.list_widget.setObjectName("eventCardList")
        self.list_widget.order_updated.connect(self._sync_data_from_list)
        self.list_widget.itemDoubleClicked.connect(self._edit_event)
        gl.addWidget(self.list_widget, 1)

        QShortcut(QKeySequence("Delete"), self.list_widget).activated.connect(self._delete_event)
        QShortcut(QKeySequence("Ctrl+Up"), self.list_widget).activated.connect(lambda: self._move_event(-1))
        QShortcut(QKeySequence("Ctrl+Down"), self.list_widget).activated.connect(lambda: self._move_event(1))

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.del_btn = QPushButton(t("events.delete_selected"))
        self.del_btn.setObjectName("dangerButton")
        self.del_btn.clicked.connect(self._delete_event)
        bottom_layout.addWidget(self.del_btn)
        gl.addLayout(bottom_layout)

        layout.addWidget(self.group, 1)

    def retranslate_ui(self):
        self.group.setTitle(t("events.group"))
        self.title.setText(t("events.list_title"))
        self.hint.setText(t("events.list_hint"))
        self.btn_dialog.setText(t("events.add_dialog"))
        self.btn_reward.setText(t("events.add_reward"))
        self.btn_force_draw.setText(t("events.add_force_draw"))
        self.btn_scripted.setText(t("events.add_scripted"))
        self.del_btn.setText(t("events.delete_selected"))
        self._render_list()

    def _make_btn(self, text, func, object_name=None):
        b = QPushButton(text)
        if object_name:
            b.setObjectName(object_name)
        b.setCursor(Qt.PointingHandCursor)
        b.setAutoDefault(False)
        b.setDefault(False)
        b.clicked.connect(lambda: func())
        return b

    def _card_name(self, guid):
        return next((n for g, n in getattr(self.dm, "card_index", []) if g == guid), f"ID:{guid}")

    # ================== 列表渲染与操作 ==================
    def _render_list(self):
        self.list_widget.clear()
        for idx, ev in enumerate(self.events_data):
            # 创建空白的基础列表项
            item = QListWidgetItem()
            item.setData(Qt.UserRole, ev)
            
            # 创建带有阴影和颜色区分的自定义卡片组件
            card_widget = EventCardWidget(ev, idx, self._card_name)
            
            # 关键：告诉 QListWidget 这一项应该有多高（自适应自定义卡片的高度）
            item.setSizeHint(card_widget.sizeHint())
            
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, card_widget)

    def _sync_data_from_list(self):
        self.events_data = [self.list_widget.item(i).data(Qt.UserRole) for i in range(self.list_widget.count())]
        self.ui_changed.emit()
        self._render_list()

    def _delete_event(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.events_data.pop(row)
            self._render_list()
            self.list_widget.setCurrentRow(min(row, len(self.events_data) - 1))
            self.ui_changed.emit()

    def _move_event(self, offset):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        new_row = row + offset
        if 0 <= new_row < len(self.events_data):
            self.events_data[row], self.events_data[new_row] = self.events_data[new_row], self.events_data[row]
            self._render_list()
            self.list_widget.setCurrentRow(new_row)
            self.ui_changed.emit()

    # ================== 双击编辑路由 ==================
    def _edit_event(self, item):
        row = self.list_widget.row(item)
        ev = self.events_data[row]
        ev_type = ev.get("$type", "")

        if "MessageEventConfig" in ev_type:
            self._show_dialog_event_ui(ev, row)
        elif "AddCardToTopOfDeckConfig" in ev_type:
            self._show_reward_event_ui(ev, row)
        elif "MoveCardToTopOfDeckConfig" in ev_type:
            self._show_force_draw_ui(ev, row)
        elif "ScriptedTurnEventConfig" in ev_type:
            self._show_scripted_turn_ui(ev, row)

    # ================== 弹窗与通用组件 ==================
    def _create_dialog(self, title, width=520, height=320):
        d = QDialog(self)
        d.setWindowTitle(title)
        d.resize(width, height)
        apply_dialog_theme(d)

        outer = QVBoxLayout(d)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        card = QFrame()
        card.setObjectName("formCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        outer.addWidget(card, 1)
        return d, layout

    def _make_save_button(self, text=None, object_name=None):
        btn = QPushButton(text if text is not None else t("events.save"))
        if object_name:
            btn.setObjectName(object_name)
        btn.setCursor(Qt.PointingHandCursor)
        # 关键：避免输入框按回车时触发默认保存按钮。
        btn.setAutoDefault(False)
        btn.setDefault(False)
        return btn

    def _commit_save(self, event, row, dialog):
        if row >= 0:
            self.events_data[row] = event
        else:
            self.events_data.append(event)
        self._render_list()
        self.list_widget.setCurrentRow(row if row >= 0 else len(self.events_data) - 1)
        self.ui_changed.emit()
        dialog.accept()

    def _add_label(self, layout, text, hint=None):
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        if hint:
            h = QLabel(hint)
            h.setObjectName("hintLabel")
            h.setWordWrap(True)
            layout.addWidget(h)

    # ================== 1. 对话事件 ==================
    def _show_dialog_event_ui(self, existing_ev=None, row=-1):
        # 双击编辑时 Qt 会把 item 作为参数传入；只接受 dict 才算编辑现有事件
        if not isinstance(existing_ev, dict):
            existing_ev, row = None, -1

        d, layout = self._create_dialog(
            t("events.edit_dialog") if existing_ev else t("events.add_dialog_title"),
            520, 330,
        )

        self._add_label(layout, t("events.trigger_turn"))
        turn_spin = QSpinBox()
        turn_spin.setMaximum(999)
        layout.addWidget(turn_spin)

        self._add_label(layout, t("events.narrator"))
        nar_cb = QComboBox()
        nar_cb.addItem(t("events.narrator_none_opt"), 0)
        nar_cb.addItem(t("events.narrator_dave_opt"), 1)
        nar_cb.addItem(t("events.narrator_zomboss_opt"), 2)
        layout.addWidget(nar_cb)

        self._add_label(layout, t("events.text_key"), t("events.text_key_hint"))
        key_le = QLineEdit()
        layout.addWidget(key_le)

        if existing_ev:
            turn_spin.setValue(existing_ev.get("TriggerConfig", {}).get("TurnNumber", 0))
            idx = nar_cb.findData(existing_ev.get("Narrator", 0))
            if idx >= 0:
                nar_cb.setCurrentIndex(idx)
            key_le.setText(existing_ev.get("TextKey", ""))

        layout.addStretch()
        btn = self._make_save_button()
        layout.addWidget(btn)

        def _save():
            if not key_le.text().strip():
                QMessageBox.warning(d, t("common.warning"), t("events.text_key_empty"))
                return
            event = {
                "TriggerConfig": {"Type": 1, "CardId": 280, "TurnNumber": turn_spin.value(), "RecordType": 7},
                "DismissConfig": {"Type": 0, "TimeToWait": 0.0},
                "ViewType": 2,
                "X": 0.0,
                "Y": 1.5,
                "TextKey": key_le.text().strip(),
                "Delay": 0.0,
                "MustTapThrough": True,
                "TelemetryEvent": 0,
                "Narrator": nar_cb.currentData(),
                "$type": "PvZCards.Core.Data.MessageEventConfig"
            }
            self._commit_save(event, row, d)

        btn.clicked.connect(_save)
        d.exec()

    # ================== 2. 解密发牌 ==================
    def _show_reward_event_ui(self, existing_ev=None, row=-1):
        if not isinstance(existing_ev, dict):
            existing_ev, row = None, -1

        d, layout = self._create_dialog(
            t("events.edit_reward") if existing_ev else t("events.add_reward_title"),
            620, 560,
        )

        self._add_label(layout, t("events.recv_faction"))
        fac_cb = QComboBox()
        fac_cb.addItem(t("events.faction_plant_opt"), 0)
        fac_cb.addItem(t("events.faction_zombie_opt"), 1)
        layout.addWidget(fac_cb)

        self._add_label(layout, t("events.add_card"), t("events.add_card_hint"))
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        card_input = CardInputWidget(getattr(self.dm, "card_index", []), d)
        input_row.addWidget(card_input, 1)

        add_btn = QPushButton(t("events.add_to_list"))
        add_btn.setObjectName("secondaryButton")
        add_btn.setAutoDefault(False)
        add_btn.setDefault(False)
        add_btn.setCursor(Qt.PointingHandCursor)
        input_row.addWidget(add_btn)
        layout.addLayout(input_row)

        self._add_label(layout, t("events.deck_top_list"), t("events.deck_top_hint"))
        temp_list = DragDropListWidget()
        temp_list.setMinimumHeight(220)
        layout.addWidget(temp_list, 1)

        remove_row = QHBoxLayout()
        remove_row.addStretch()
        remove_btn = QPushButton(t("events.remove_selected"))
        remove_btn.setObjectName("dangerButton")
        remove_btn.setAutoDefault(False)
        remove_btn.setDefault(False)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_row.addWidget(remove_btn)
        layout.addLayout(remove_row)

        if existing_ev:
            idx = fac_cb.findData(existing_ev.get("PlayerFaction", 0))
            if idx >= 0:
                fac_cb.setCurrentIndex(idx)
            for guid in existing_ev.get("CardIds", []):
                name = self._card_name(guid)
                item = QListWidgetItem(f"{name} ({guid})")
                item.setData(Qt.UserRole, guid)
                temp_list.addItem(item)

        def _add_to_temp():
            guid = card_input.get_guid()
            if guid is None:
                QMessageBox.warning(d, t("common.warning"), t("events.invalid_card"))
                return
            name = self._card_name(guid)
            item = QListWidgetItem(f"{name} ({guid})")
            item.setData(Qt.UserRole, guid)
            temp_list.addItem(item)
            temp_list.setCurrentRow(temp_list.count() - 1)
            card_input.le.clear()
            card_input.le.setFocus()

        def _remove_selected():
            r = temp_list.currentRow()
            if r >= 0:
                temp_list.takeItem(r)
                if temp_list.count() > 0:
                    temp_list.setCurrentRow(min(r, temp_list.count() - 1))

        add_btn.clicked.connect(_add_to_temp)
        remove_btn.clicked.connect(_remove_selected)
        QShortcut(QKeySequence("Delete"), temp_list).activated.connect(_remove_selected)
        QShortcut(QKeySequence("Ctrl+Return"), card_input.le).activated.connect(_add_to_temp)
        QShortcut(QKeySequence("Ctrl+Enter"), card_input.le).activated.connect(_add_to_temp)

        layout.addStretch()
        btn = self._make_save_button()
        layout.addWidget(btn)

        def _save():
            final_guids = [temp_list.item(i).data(Qt.UserRole) for i in range(temp_list.count())]
            if not final_guids:
                QMessageBox.warning(d, t("common.warning"), t("events.need_one_card"))
                return
            event = {
                "CardIds": final_guids,
                "PlayerFaction": fac_cb.currentData(),
                "$type": "PvZCards.Core.Data.AddCardToTopOfDeckConfig"
            }
            self._commit_save(event, row, d)

        btn.clicked.connect(_save)
        d.exec()

    # ================== 3. 强制抽卡 ==================
    def _show_force_draw_ui(self, existing_ev=None, row=-1):
        if not isinstance(existing_ev, dict):
            existing_ev, row = None, -1

        d, layout = self._create_dialog(
            t("events.edit_force_draw") if existing_ev else t("events.add_force_draw_title"),
            520, 340,
        )

        self._add_label(layout, t("events.trigger_turn"))
        turn_spin = QSpinBox()
        turn_spin.setMaximum(999)
        layout.addWidget(turn_spin)

        self._add_label(layout, t("events.recv_faction"))
        fac_cb = QComboBox()
        fac_cb.addItem(t("events.faction_plant_opt"), 0)
        fac_cb.addItem(t("events.faction_zombie_opt"), 1)
        layout.addWidget(fac_cb)

        self._add_label(layout, t("events.select_card"))
        card_input = CardInputWidget(getattr(self.dm, "card_index", []), d)
        layout.addWidget(card_input)

        if existing_ev:
            turn_spin.setValue(existing_ev.get("TurnNumber", 0))
            idx = fac_cb.findData(existing_ev.get("PlayerFaction", 0))
            if idx >= 0:
                fac_cb.setCurrentIndex(idx)
            card_input.set_guid(existing_ev.get("CardGuid", 0))

        layout.addStretch()
        btn = self._make_save_button()
        layout.addWidget(btn)

        def _save():
            guid = card_input.get_guid()
            if guid is None:
                QMessageBox.warning(d, t("common.warning"), t("events.need_valid_card"))
                return
            event = {
                "TurnNumber": turn_spin.value(),
                "CardGuid": guid,
                "PlayerFaction": fac_cb.currentData(),
                "$type": "PvZCards.Core.Data.MoveCardToTopOfDeckConfig"
            }
            self._commit_save(event, row, d)

        btn.clicked.connect(_save)
        d.exec()

    # ================== 4. 强制出牌 ==================
    def _show_scripted_turn_ui(self, existing_ev=None, row=-1):
        if not isinstance(existing_ev, dict):
            existing_ev, row = None, -1

        d, layout = self._create_dialog(
            t("events.edit_scripted") if existing_ev else t("events.add_scripted_title"),
            540, 430,
        )

        self._add_label(layout, t("events.trigger_turn"))
        turn_spin = QSpinBox()
        turn_spin.setMaximum(999)
        layout.addWidget(turn_spin)

        self._add_label(layout, t("events.select_play_card"))
        card_input = CardInputWidget(getattr(self.dm, "card_index", []), d)
        layout.addWidget(card_input)

        self._add_label(layout, t("events.select_lane"))
        lane_cb = QComboBox()
        lane_cb.addItem(t("events.lane_any_ai"), -1)
        for i in range(5):
            lane_cb.addItem(t("events.lane_n", n=i + 1), i)
        layout.addWidget(lane_cb)

        surp_cb = QCheckBox(t("events.play_surprise"))
        cont_cb = QCheckBox(t("events.continue_playing"))
        surp_cb.setObjectName("plainCheck")
        cont_cb.setObjectName("plainCheck")
        cont_cb.setChecked(True)
        layout.addWidget(surp_cb)
        layout.addWidget(cont_cb)

        if existing_ev:
            turn_spin.setValue(existing_ev.get("TurnNumber", 0))
            plays = existing_ev.get("Plays", [{}])
            if plays:
                card_input.set_guid(plays[0].get("CardGuid", 0))
                idx = lane_cb.findData(plays[0].get("LaneIndex", -1))
                if idx >= 0:
                    lane_cb.setCurrentIndex(idx)
            surp_cb.setChecked(existing_ev.get("PlayDuringSurprise", False))
            cont_cb.setChecked(existing_ev.get("ContinuePlaying", True))

        layout.addStretch()
        btn = self._make_save_button(object_name="purpleButton")
        layout.addWidget(btn)

        def _save():
            guid = card_input.get_guid()
            if guid is None:
                QMessageBox.warning(d, t("common.warning"), t("events.need_valid_card"))
                return

            play_dict = {"CardGuid": guid}
            if lane_cb.currentData() != -1:
                play_dict["LaneIndex"] = lane_cb.currentData()

            event = {
                "TurnNumber": turn_spin.value(),
                "Plays": [play_dict],
                "PlayDuringSurprise": surp_cb.isChecked(),
                "ContinuePlaying": cont_cb.isChecked(),
                "$type": "PvZCards.Core.Data.ScriptedTurnEventConfig"
            }
            self._commit_save(event, row, d)

        btn.clicked.connect(_save)
        d.exec()

    # ================== 数据装载与保存 ==================
    def load_data(self, config):
        # 深拷贝，避免直接改 UI 列表时污染原始 config 引用
        self.events_data = copy.deepcopy(config.get("GameEvents", []) or [])
        self._render_list()

    def save_data(self, config):
        config["GameEvents"] = copy.deepcopy(self.events_data)
