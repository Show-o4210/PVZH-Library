# ui/base_components.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QDialog, QListWidget, QListWidgetItem,
    QAbstractItemView, QLabel, QFrame, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QRectF
from PySide6.QtGui import QTextDocument

from theme import apply_dialog_theme, get_theme_colors
from i18n import t


class HTMLDelegate(QStyledItemDelegate):
    """用于在 QListWidget 单元格中渲染 HTML 富文本的委托"""

    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        painter.save()

        muted = get_theme_colors().get("label_text", "#94A3B8")
        doc = QTextDocument()
        text = options.text
        # 将历史硬编码灰色替换为当前主题次级文字色
        text = text.replace("color:#94A3B8", f"color:{muted}")
        text = text.replace("color: #94A3B8", f"color: {muted}")
        html_content = f"<div style='text-align: center; color: inherit;'>{text.replace(chr(10), '<br>')}</div>"
        doc.setHtml(html_content)

        options.text = ""

        style = options.widget.style() if options.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, options, painter, options.widget)

        doc_height = doc.size().height()
        y_offset = (options.rect.height() - doc_height) / 2
        if y_offset < 0:
            y_offset = 0

        painter.translate(options.rect.left(), options.rect.top() + y_offset)
        clip = QRectF(0, 0, options.rect.width(), options.rect.height())
        doc.drawContents(painter, clip)

        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QTextDocument()
        text = options.text
        html_content = f"<div style='text-align: center;'>{text.replace(chr(10), '<br>')}</div>"
        doc.setHtml(html_content)
        width = options.rect.width() if options.rect.width() > 0 else 280
        doc.setTextWidth(width)
        return QSize(width, max(int(doc.size().height()) + 12, 70))


class SearchableGridDialog(QDialog):
    """支持模糊搜索和网格化布局的选择弹窗"""

    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.selected_data = None
        self.all_items = list(items)
        apply_dialog_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        header = QLabel(title)
        header.setObjectName("gridDialogTitle")
        layout.addWidget(header)

        subtitle = QLabel(t("grid.subtitle"))
        subtitle.setObjectName("dialog_subtitle")
        layout.addWidget(subtitle)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(t("grid.search_ph"))
        self.search_bar.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_bar)

        line = QFrame()
        line.setObjectName("dialogDivider")
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("gridSelectList")
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setSpacing(10)
        self.list_widget.setWordWrap(True)
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setGridSize(QSize(290, 100))
        self.list_widget.setIconSize(QSize(0, 0))
        self.list_widget.setItemDelegate(HTMLDelegate(self.list_widget))
        layout.addWidget(self.list_widget, 1)

        self.empty_label = QLabel(t("grid.no_match"))
        self.empty_label.setObjectName("mutedLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        self._populate_items()
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.count_label = QLabel("")
        self.count_label.setObjectName("countLabel")
        btn_layout.addWidget(self.count_label)
        btn_layout.addStretch()

        cancel_btn = QPushButton(t("common.cancel"))
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(t("common.confirm"))
        confirm_btn.clicked.connect(self.accept_selection)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)
        self._update_count()
        self.search_bar.setFocus()

    def _populate_items(self):
        self.list_widget.clear()
        muted = get_theme_colors().get("label_text", "#94A3B8")
        for data_id, display_name in self.all_items:
            item_text = (
                f"{display_name}\n"
                f"<span style='font-size:11px; color:{muted};'>{data_id}</span>"
            )
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, data_id)
            item.setToolTip(f"{display_name}\n{data_id}")
            item.setTextAlignment(Qt.AlignCenter)
            item.setSizeHint(QSize(280, 85))
            self.list_widget.addItem(item)

    def filter_items(self, text):
        keywords = [k for k in text.lower().strip().split() if k]
        visible_count = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # 去掉 HTML 标签做搜索
            raw = item.text()
            while "<" in raw and ">" in raw:
                a, b = raw.find("<"), raw.find(">")
                if a < 0 or b < 0 or b < a:
                    break
                raw = raw[:a] + raw[b + 1 :]
            haystack = raw.lower()
            matched = all(k in haystack for k in keywords)
            item.setHidden(not matched)
            if matched:
                visible_count += 1
        self.empty_label.setVisible(visible_count == 0)
        self.list_widget.setVisible(visible_count > 0)
        self._update_count(visible_count)

    def _update_count(self, visible_count=None):
        if visible_count is None:
            visible_count = self.list_widget.count()
        self.count_label.setText(t("grid.result_count", n=visible_count))

    def accept_selection(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_data = selected_items[0].data(Qt.UserRole)
            self.accept()


class SearchableSelectButton(QPushButton):
    """封装了弹窗选择逻辑的按钮组件"""

    valueChanged = Signal()

    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.title = title
        self.title_key = None  # 可选：i18n key，切换语言时刷新
        self.items = items
        self.current_data = None
        self.clicked.connect(self.open_dialog)
        self.setObjectName("searchSelectButton")
        self.update_display()

    def set_title(self, title):
        self.title = title

    def set_items(self, items):
        self.items = items
        self.update_display()

    def open_dialog(self):
        dialog = SearchableGridDialog(self.title, self.items, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_data:
            self.set_data(dialog.selected_data)

    def set_data(self, data):
        if self.current_data != data:
            self.current_data = data
            self.update_display()
            self.valueChanged.emit()

    def get_data(self):
        return self.current_data

    def update_display(self):
        if not self.current_data:
            self.setText(t("common.click_select"))
            return
        for d_id, d_name in self.items:
            if d_id == self.current_data:
                self.setText(f"{d_name}  ·  {d_id}")
                return
        self.setText(str(self.current_data))


class BaseTab(QWidget):
    """基础标签页类，所有配置页面继承此类"""
    ui_changed = Signal()

    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager

    def load_data(self, config):
        pass

    def save_data(self, config):
        pass

    def retranslate_ui(self):
        """语言切换时由主窗口调用；子类按需覆盖。"""
        pass
