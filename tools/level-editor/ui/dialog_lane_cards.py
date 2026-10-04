# ui/dialog_lane_cards.py
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QCompleter,
    QLabel, QMessageBox, QAbstractItemView, QFrame, QWidget
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
from ui.base_components import SearchableGridDialog
from theme import apply_dialog_theme
from i18n import t


class LaneCardsListWidget(QListWidget):
    """道路卡牌列表：支持多选、拖拽排序。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAlternatingRowColors(False)



class LaneCardsDialog(QDialog):
    def __init__(self, current_cards, card_index, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("lane.title"))
        self.resize(620, 680)
        self.setMinimumSize(560, 560)

        self.result_cards = list(current_cards)
        self.card_index = card_index

        self.completion_strings = [f"{name} ({guid})" for guid, name in self.card_index]
        self.guid_to_name = {guid: name for guid, name in self.card_index}

        apply_dialog_theme(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(16)

        title = QLabel(t("lane.heading"))
        title.setObjectName("dialog_title")
        root.addWidget(title)

        subtitle = QLabel(t("lane.subtitle"))
        subtitle.setObjectName("dialog_subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        # === 输入卡片 ===
        input_card = QFrame()
        input_card.setObjectName("panel_card")
        input_card_layout = QVBoxLayout(input_card)
        input_card_layout.setContentsMargins(16, 16, 16, 16)
        input_card_layout.setSpacing(10)

        input_label = QLabel(t("lane.add_section"))
        input_label.setObjectName("section_label")
        input_card_layout.addWidget(input_label)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.input_le = QLineEdit()
        self.input_le.setPlaceholderText(t("lane.input_ph"))

        self.completer = QCompleter(self.completion_strings)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.input_le.setCompleter(self.completer)
        self.input_le.returnPressed.connect(self._add_from_input)
        self.completer.activated.connect(self._on_completer_activated)

        add_btn = QPushButton(t("lane.add"))
        add_btn.setObjectName("primary_btn")
        add_btn.clicked.connect(self._add_from_input)

        browse_btn = QPushButton(t("lane.browse_all"))
        browse_btn.setObjectName("secondary_btn")
        browse_btn.clicked.connect(self._open_grid_browser)

        input_layout.addWidget(self.input_le, 1)
        input_layout.addWidget(add_btn)
        input_layout.addWidget(browse_btn)
        input_card_layout.addLayout(input_layout)
        root.addWidget(input_card)

        # === 列表卡片 ===
        list_card = QFrame()
        list_card.setObjectName("panel_card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(16, 16, 16, 16)
        list_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        self.count_label = QLabel(t("lane.current_cards"))
        self.count_label.setObjectName("section_label")
        hint_label = QLabel(t("lane.list_hint"))
        hint_label.setObjectName("hint_label")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()
        header_layout.addWidget(hint_label)
        list_layout.addLayout(header_layout)

        self.list_widget = LaneCardsListWidget()
        self.list_widget.model().rowsMoved.connect(self._sync_result_from_list)
        list_layout.addWidget(self.list_widget, 1)

        list_actions = QHBoxLayout()
        list_actions.setSpacing(10)

        del_btn = QPushButton(t("lane.delete_selected"))
        del_btn.setObjectName("danger_btn")
        del_btn.clicked.connect(self._delete_selected)

        clear_btn = QPushButton(t("lane.clear_list"))
        clear_btn.setObjectName("ghost_btn")
        clear_btn.clicked.connect(self._clear_all)

        list_actions.addWidget(del_btn)
        list_actions.addWidget(clear_btn)
        list_actions.addStretch()
        list_layout.addLayout(list_actions)

        root.addWidget(list_card, 1)

        # === 快捷键 ===
        QShortcut(QKeySequence("Delete"), self).activated.connect(self._delete_selected)
        QShortcut(QKeySequence("Backspace"), self).activated.connect(self._delete_selected)

        # === 底部按钮 ===
        footer = QHBoxLayout()
        footer.addStretch()

        cancel_btn = QPushButton(t("common.cancel"))
        cancel_btn.setObjectName("ghost_btn")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton(t("lane.save_close"))
        confirm_btn.setObjectName("primary_btn")
        confirm_btn.clicked.connect(self.accept)

        footer.addWidget(cancel_btn)
        footer.addWidget(confirm_btn)
        root.addLayout(footer)

        self._refresh_list()


    def _on_completer_activated(self, text):
        self.input_le.setText(text)
        self._add_from_input()

    def _resolve_guid_from_text(self, text):
        text = text.strip()
        if not text:
            return None

        m = re.search(r"\((\d+)\)", text)
        if m:
            return int(m.group(1))

        if text.isdigit():
            return int(text)

        if self.completer.completionCount() > 0:
            first_match = self.completer.completionModel().index(0, 0).data()
            if first_match:
                m2 = re.search(r"\((\d+)\)", first_match)
                if m2:
                    self.input_le.setText(first_match)
                    return int(m2.group(1))
        return None

    def _add_from_input(self):
        guid = self._resolve_guid_from_text(self.input_le.text())
        if guid is None:
            QMessageBox.warning(self, t("lane.invalid_title"), t("lane.invalid_input"))
            return

        self.result_cards.append(guid)
        self._refresh_list(select_last=True)
        self.input_le.clear()
        self.input_le.setFocus()

    def _open_grid_browser(self):
        grid_items = [(guid, name) for guid, name in self.card_index]
        dialog = SearchableGridDialog(t("lane.pick_card"), grid_items, self)

        if dialog.exec() == QDialog.Accepted and dialog.selected_data:
            self.result_cards.append(dialog.selected_data)
            self._refresh_list(select_last=True)
            # 浏览添加后也清空输入框
            self.input_le.clear()
            self.input_le.setFocus()

    def _delete_selected(self):
        selected_rows = sorted(
            [self.list_widget.row(item) for item in self.list_widget.selectedItems()],
            reverse=True
        )
        if not selected_rows:
            return

        for row in selected_rows:
            if 0 <= row < len(self.result_cards):
                self.result_cards.pop(row)

        self._refresh_list()

    def _clear_all(self):
        if not self.result_cards:
            return

        reply = QMessageBox.question(
            self,
            t("lane.clear_confirm_title"),
            t("lane.clear_confirm_body"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.result_cards.clear()
            self._refresh_list()

    def _sync_result_from_list(self):
        new_cards = []
        for i in range(self.list_widget.count()):
            new_cards.append(self.list_widget.item(i).data(Qt.UserRole))
        self.result_cards = new_cards
        self._refresh_list()

    def _refresh_list(self, select_last=False):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        for index, guid in enumerate(self.result_cards, start=1):
            name = self.guid_to_name.get(guid, t("lane.unknown_card"))
            item = QListWidgetItem(f"{index:02d}. {name}\nID: {guid}")
            item.setData(Qt.UserRole, guid)
            item.setToolTip(f"{name} ({guid})")
            self.list_widget.addItem(item)

        self.list_widget.blockSignals(False)

        self.count_label.setText(t("lane.current_cards_n", n=len(self.result_cards)))

        if select_last and self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)
