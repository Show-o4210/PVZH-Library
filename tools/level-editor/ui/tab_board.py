# ui/tab_board.py
from PySide6.QtWidgets import (
    QVBoxLayout, QGridLayout, QGroupBox, QLabel, QComboBox,
    QTextEdit, QPushButton, QHBoxLayout, QWidget, QFrame,
    QScrollArea, QMessageBox
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt, QEvent
from ui.base_components import BaseTab
from i18n import t

# 尝试导入独立的卡牌编辑器，如果尚未创建，请确保存在 dialog_lane_cards.py
try:
    from ui.dialog_lane_cards import LaneCardsDialog
except ImportError:
    pass # 预留容错

class BoardConfigTab(BaseTab):
    def __init__(self, data_manager):
        super().__init__(data_manager)
        self.internal_clipboard_cards = [] 
        self.active_lane_idx = -1 # 当前选中的道路索引（用于快捷键操作）

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)

        # ==========================================
        # 1. 全局场地能力 (BoardAbilities)
        # ==========================================
        self.ab_group = QGroupBox(t("board.abilities_group"))
        ab_layout = QVBoxLayout(self.ab_group)
        ab_layout.setContentsMargins(20, 30, 20, 20)
        
        self.abilities_te = QTextEdit()
        self.abilities_te.setPlaceholderText(t("board.abilities_ph"))
        self.abilities_te.setMaximumHeight(70)
        self.abilities_te.textChanged.connect(self.ui_changed)
        ab_layout.addWidget(self.abilities_te)
        
        layout.addWidget(self.ab_group)

        # ==========================================
        # 2. 战场分路卡片组：滚动区域，防止卡片过高挤爆界面
        # ==========================================
        self.lane_main_group = QGroupBox(t("board.lanes_group"))
        self.lane_main_group.setMinimumHeight(360)

        lane_group_layout = QVBoxLayout(self.lane_main_group)
        lane_group_layout.setContentsMargins(12, 28, 12, 12)
        lane_group_layout.setSpacing(0)

        # 滚动区域
        lane_scroll = QScrollArea()
        lane_scroll.setWidgetResizable(True)
        lane_scroll.setFrameShape(QFrame.NoFrame)
        lane_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lane_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        lane_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        # 滚动内容容器
        lane_scroll_content = QWidget()
        lane_scroll_content.setStyleSheet("background: transparent;")

        self.lane_layout = QVBoxLayout(lane_scroll_content)
        self.lane_layout.setContentsMargins(4, 4, 12, 4)
        self.lane_layout.setSpacing(12)

        self.lanes = []

        for i in range(5):
            lane_frame = QFrame()
            lane_frame.setObjectName("lane_card")

            # 你可以调这里：卡片高度变高也不会挤爆外层
            lane_frame.setMinimumHeight(130)

            # 样式交由主窗口全局主题控制（支持深色模式）
            lane_frame.installEventFilter(self)

            ll = QHBoxLayout(lane_frame)
            ll.setContentsMargins(18, 14, 18, 14)
            ll.setSpacing(16)

            title = QLabel(f"LANE {i + 1}")
            title.setFixedWidth(62)
            title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            title.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #475569;
                    font-size: 12px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }
            """)
            ll.addWidget(title)

            cb = QComboBox()
            cb.setFixedWidth(120)
            self._fill_lane_type_combo(cb)
            cb.currentIndexChanged.connect(self.ui_changed)
            ll.addWidget(cb)

            status_container = QWidget()
            status_container.setStyleSheet("background: transparent;")

            sl = QVBoxLayout(status_container)
            sl.setContentsMargins(8, 0, 8, 0)
            sl.setSpacing(6)

            status_summary = QLabel("EMPTY")
            status_summary.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #94A3B8;
                    font-size: 11px;
                    font-weight: 700;
                }
            """)

            status_detail = QLabel(t("board.no_cards"))
            status_detail.setWordWrap(True)
            status_detail.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #64748B;
                    font-size: 13px;
                    line-height: 1.4;
                }
            """)

            sl.addWidget(status_summary)
            sl.addWidget(status_detail)
            sl.addStretch()

            ll.addWidget(status_container, 1)

            edit_btn = QPushButton(t("board.edit_cards"))
            edit_btn.setObjectName("secondaryButton")
            edit_btn.setFixedWidth(150)
            edit_btn.clicked.connect(lambda chk=False, idx=i: self._open_card_editor(idx))
            ll.addWidget(edit_btn)

            self.lanes.append({
                "frame": lane_frame,
                "type_cb": cb,
                "summary": status_summary,
                "detail": status_detail,
                "edit_btn": edit_btn,
                "cards_data": []
            })

            self.lane_layout.addWidget(lane_frame)

        self.lane_layout.addStretch()

        lane_scroll.setWidget(lane_scroll_content)
        lane_group_layout.addWidget(lane_scroll)

        # 这里给滚动区一个伸缩权重，让它吃掉主要空间
        layout.addWidget(self.lane_main_group, 1)
        
        # 3. 快捷键提示
        self.hint = QLabel(t("board.shortcut_hint"))
        self.hint.setStyleSheet("color: #64748B; font-size: 12px; margin-left: 5px;")
        layout.addWidget(self.hint)
        layout.addStretch()

        # 注册全局快捷键
        self._setup_shortcuts()

    def _fill_lane_type_combo(self, cb, keep_value=None):
        current = keep_value if keep_value is not None else (cb.currentData() if cb.count() else None)
        cb.blockSignals(True)
        cb.clear()
        cb.addItem(t("board.lane_flat"), 1)
        cb.addItem(t("board.lane_heights"), 0)
        cb.addItem(t("board.lane_water"), 2)
        if current is not None:
            idx = cb.findData(current)
            if idx >= 0:
                cb.setCurrentIndex(idx)
        cb.blockSignals(False)

    def retranslate_ui(self):
        self.ab_group.setTitle(t("board.abilities_group"))
        self.abilities_te.setPlaceholderText(t("board.abilities_ph"))
        self.lane_main_group.setTitle(t("board.lanes_group"))
        self.hint.setText(t("board.shortcut_hint"))
        for i, lane in enumerate(self.lanes):
            self._fill_lane_type_combo(lane["type_cb"])
            lane["edit_btn"].setText(t("board.edit_cards"))
            self._update_lane_status(i)

    # ==========================================
    # 焦点与快捷键逻辑
    # ==========================================
    def eventFilter(self, obj, event):
        """拦截鼠标点击事件，用于高亮选中的道路卡片"""
        if event.type() == QEvent.MouseButtonPress:
            for i, lane in enumerate(self.lanes):
                if obj == lane["frame"]:
                    self._set_active_lane(i)
                    break
        return super().eventFilter(obj, event)

    def _set_active_lane(self, idx):
        """设置当前激活的道路，并更新边框颜色（使用属性驱动主题样式）"""
        self.active_lane_idx = idx

        for i, lane in enumerate(self.lanes):
            frame = lane["frame"]
            frame.setProperty("active", "true" if i == idx else "false")
            # 强制刷新动态属性对应的 QSS
            frame.style().unpolish(frame)
            frame.style().polish(frame)
            frame.update()

    def _setup_shortcuts(self):
        """绑定编辑器级别的快捷键"""
        QShortcut(QKeySequence.Copy, self).activated.connect(self._shortcut_copy)
        QShortcut(QKeySequence.Paste, self).activated.connect(self._shortcut_paste)
        QShortcut(QKeySequence.Delete, self).activated.connect(self._shortcut_delete)
        QShortcut(QKeySequence("Backspace"), self).activated.connect(self._shortcut_delete)

    def _shortcut_copy(self):
        if self.active_lane_idx >= 0:
            self.internal_clipboard_cards = list(self.lanes[self.active_lane_idx]["cards_data"])

    def _shortcut_paste(self):
        if self.active_lane_idx >= 0 and self.internal_clipboard_cards is not None:
            self.lanes[self.active_lane_idx]["cards_data"] = list(self.internal_clipboard_cards)
            self._update_lane_status(self.active_lane_idx)
            self.ui_changed.emit()

    def _shortcut_delete(self):
        if self.active_lane_idx >= 0:
            self.lanes[self.active_lane_idx]["cards_data"] = []
            self._update_lane_status(self.active_lane_idx)
            self.ui_changed.emit()

    # ==========================================
    # 数据展示与更新逻辑
    # ==========================================
    def _update_lane_status(self, idx):
        """利用 data_manager 的卡牌索引，将 GUID 翻译为可视化的中文连缀"""
        cards = self.lanes[idx]["cards_data"]
        summary = self.lanes[idx]["summary"]
        detail = self.lanes[idx]["detail"]
        
        if not cards:
            summary.setText("EMPTY")
            summary.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
            detail.setText(t("board.no_cards"))
            detail.setStyleSheet("color: #94A3B8; font-size: 13px;")
        else:
            summary.setText(t("board.contains_n", n=len(cards)))
            summary.setStyleSheet("color: #3B82F6; font-size: 11px; font-weight: bold;")
            
            # 翻译卡牌名称
            names = []
            for guid in cards:
                name = "Unknown"
                # 如果你在 data_manager.py 中成功解析了 index.json，这里就能发挥作用
                if hasattr(self.dm, 'card_index') and self.dm.card_index:
                    for g, n in self.dm.card_index:
                        if g == guid:
                            name = n
                            break
                names.append(f"[{name}]")
            
            detail.setText(" ➞ ".join(names))
            # 不硬编码近黑文字，便于深色主题继承全局前景色
            detail.setStyleSheet("font-size: 13px; font-weight: bold;")

    def _open_card_editor(self, idx):
        """呼出独立道路卡牌编辑器"""
        if "LaneCardsDialog" not in globals():
            QMessageBox.critical(self, t("msg.missing_component_title"), t("msg.missing_component"))
            return

        card_index_data = getattr(self.dm, "card_index", None) or []
        if not card_index_data:
            QMessageBox.warning(self, t("msg.empty_card_index_title"), t("msg.empty_card_index"))

        dialog = LaneCardsDialog(self.lanes[idx]["cards_data"], card_index_data, self)
        if dialog.exec():
            self.lanes[idx]["cards_data"] = dialog.result_cards
            self._update_lane_status(idx)
            self.ui_changed.emit()
            self._set_active_lane(idx)  # 编辑完后自动将焦点保持在这条路

    # ==========================================
    # JSON 读写接口
    # ==========================================
    def load_data(self, config):
        # 1. 恢复 BoardAbilities
        abilities = config.get("BoardConfig", {}).get("BoardAbilities", [])
        self.abilities_te.blockSignals(True)
        self.abilities_te.setPlainText(", ".join(map(str, abilities)))
        self.abilities_te.blockSignals(False)

        # 2. 恢复 LaneEntries（不足 5 路时重置剩余道路，避免残留上一次数据）
        entries = config.get("BoardConfig", {}).get("LaneEntries", []) or []
        default_lane_types = [0, 1, 1, 1, 2]
        for i in range(5):
            if i < len(entries):
                lane_cfg = entries[i] or {}
                lane_type = lane_cfg.get("LaneType", default_lane_types[i])
                cards = list(lane_cfg.get("Cards", []) or [])
            else:
                lane_type = default_lane_types[i]
                cards = []

            idx_map = self.lanes[i]["type_cb"].findData(lane_type)
            if idx_map >= 0:
                self.lanes[i]["type_cb"].setCurrentIndex(idx_map)
            self.lanes[i]["cards_data"] = cards
            self._update_lane_status(i)

    def save_data(self, config):
        if "BoardConfig" not in config or not isinstance(config.get("BoardConfig"), dict):
            config["BoardConfig"] = {}

        # 1. 保存 BoardAbilities
        raw_text = self.abilities_te.toPlainText()
        config["BoardConfig"]["BoardAbilities"] = [
            int(x.strip()) for x in raw_text.split(",") if x.strip().isdigit()
        ]

        # 2. 保存 LaneEntries（自动补齐到 5 路，避免 KeyError / IndexError）
        entries = config["BoardConfig"].setdefault("LaneEntries", [])
        if not isinstance(entries, list):
            entries = []
            config["BoardConfig"]["LaneEntries"] = entries

        while len(entries) < 5:
            entries.append({"LaneType": 1, "Cards": []})

        for i in range(5):
            if not isinstance(entries[i], dict):
                entries[i] = {"LaneType": 1, "Cards": []}
            entries[i]["LaneType"] = self.lanes[i]["type_cb"].currentData()
            entries[i]["Cards"] = list(self.lanes[i]["cards_data"])
