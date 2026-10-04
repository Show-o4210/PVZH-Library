# ui/dialog_level_select.py
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem, QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt, QSize
from constants import ALL_HEROES, HERO_ALIASES
from theme import apply_dialog_theme
from i18n import t, get_lang, localized_name

class LevelSelectDialog(QDialog):
    """支持智能解析、分页与全局搜索的 AB 包关卡选择器"""
    def __init__(self, level_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("level.title"))
        self.resize(800, 550)
        apply_dialog_theme(self)
        self.selected_level_id = None
        self.all_raw_data = [] # 存储全部关卡元数据，供全局搜索使用
        self.last_active_tab_index = 1 # 默认初始分类（植物任务）

        self.hero_dict = {}
        for h in ALL_HEROES:
            self.hero_dict[h[0].lower()] = localized_name(h)
        for key, names in HERO_ALIASES.items():
            self.hero_dict[key] = names[1] if get_lang() == "en" else names[0]

        layout = QVBoxLayout(self)

        # ---------------- 搜索区域 ----------------
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(t("level.search_ph"))
        self.search_bar.textChanged.connect(self._on_search)
        
        self.global_cb = QCheckBox(t("level.global_search"))
        self.global_cb.setObjectName("plainCheck")
        self.global_cb.stateChanged.connect(self._on_search)
        
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.global_cb)
        layout.addLayout(search_layout)

        # ---------------- 分页区域 ----------------
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        layout.addWidget(self.tabs)

        self.category_lists = {}

        # 1. 预建一个特殊的搜索结果 Tab (索引 0)，初始隐藏
        self.list_search_results = self._create_list_widget()
        self.tabs.addTab(self.list_search_results, t("level.search_results"))
        self.tabs.setTabVisible(0, False)

        # 2. 预建常用分类
        self._get_or_create_list(t("level.cat_plant"))
        self._get_or_create_list(t("level.cat_zombie"))
        self._get_or_create_list(t("level.cat_botd"))

        # 3. 填充数据
        self._populate_data(level_ids)
        self._remove_empty_tabs()

        self.tabs.currentChanged.connect(self._on_tab_changed)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        confirm_btn = QPushButton(t("level.confirm"))
        confirm_btn.setFixedSize(150, 35)
        confirm_btn.clicked.connect(self._accept_selection)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

    def _create_list_widget(self):
        lw = QListWidget()
        lw.setObjectName("gridSelectList")
        lw.setViewMode(QListWidget.IconMode)
        lw.setResizeMode(QListWidget.Adjust)
        lw.setSpacing(10)
        lw.setWordWrap(True)
        lw.setGridSize(QSize(195, 72))
        lw.itemDoubleClicked.connect(self._accept_selection)
        return lw

    def _get_or_create_list(self, tab_name):
        if tab_name not in self.category_lists:
            lw = self._create_list_widget()
            self.category_lists[tab_name] = lw
            self.tabs.addTab(lw, tab_name)
        return self.category_lists[tab_name]

    def _remove_empty_tabs(self):
        for i in range(self.tabs.count() - 1, 0, -1): # 避开索引0的搜索结果Tab
            if self.tabs.widget(i).count() == 0:
                self.tabs.removeTab(i)

    def _categorize(self, level_id):
        # 升级为 re.search 提高对前缀差异的容错率
        if re.search(r"PVE_Soft_Node_Plant_(\d+)", level_id, re.IGNORECASE):
            n = re.search(r"PVE_Soft_Node_Plant_(\d+)", level_id, re.IGNORECASE).group(1)
            return t("level.cat_plant"), t("level.plant_mission", n=n)

        if re.search(r"PVE_Soft_Node_Zombie_(\d+)", level_id, re.IGNORECASE):
            n = re.search(r"PVE_Soft_Node_Zombie_(\d+)", level_id, re.IGNORECASE).group(1)
            return t("level.cat_zombie"), t("level.zombie_mission", n=n)

        if "botd_" in level_id.lower():
            m = re.search(r"w(?:eek)?(\d+)_?d(?:ay)?(\d+)", level_id, re.IGNORECASE)
            if m:
                return t("level.cat_botd"), t("level.botd_week_day", w=m.group(1), d=m.group(2))
            return t("level.cat_botd"), level_id

        m = re.search(r"(?:Soft_PVE_Deck_(?:Plant|Zombie)_|Patrol_Node_)([a-zA-Z0-9_ ]+)_(\d+)", level_id, re.IGNORECASE)
        if m:
            hero_eng = m.group(1).strip()
            num = m.group(2)
            hero_cn = self.hero_dict.get(hero_eng.lower(), hero_eng)
            prefix = t("level.patrol") if "patrol" in level_id.lower() else t("level.random")
            return (
                t("level.hero_tab", name=hero_cn),
                t("level.hero_mission", hero=hero_cn, prefix=prefix, n=num),
            )

        if "soft_pve_deck_" in level_id.lower():
            return t("level.other_mission"), level_id
        if "patrol_node_" in level_id.lower():
            return t("level.other_patrol"), level_id

        return t("level.other"), level_id

    def _populate_data(self, level_ids):
        for lid in level_ids:
            tab_name, display_name = self._categorize(lid)
            lw = self._get_or_create_list(tab_name)

            item_text = f"{display_name}\n({lid})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, lid)
            item.setToolTip(item_text)
            lw.addItem(item)
            
            # 将数据存入总池，供全局搜索直接抓取
            self.all_raw_data.append((lid, display_name, tab_name, item_text))

    def _on_search(self):
        text = self.search_bar.text().lower()
        is_global = self.global_cb.isChecked()

        if is_global and text:
            # 开启全局搜索：显示专属结果 Tab 并高亮
            self.tabs.setTabVisible(0, True)
            self.tabs.setCurrentIndex(0)
            self.list_search_results.clear()
            
            for lid, display_name, tab_name, item_text in self.all_raw_data:
                if text in lid.lower() or text in display_name.lower():
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, lid)
                    item.setToolTip(f"[{tab_name}] {item_text}") # 提示所属分类
                    self.list_search_results.addItem(item)
        else:
            # 关闭全局搜索：隐藏结果 Tab 并退回常规模式
            self.tabs.setTabVisible(0, False)
            if self.tabs.currentIndex() == 0 and self.tabs.count() > 1:
                self.tabs.setCurrentIndex(self.last_active_tab_index)
                
            self._filter_local_tab(text)

    def _on_tab_changed(self, index):
        if index == 0: return # 搜索结果页自带过滤，不重复触发
        self.last_active_tab_index = index
        if not self.global_cb.isChecked():
            self._filter_local_tab(self.search_bar.text().lower())

    def _filter_local_tab(self, text):
        current_list = self.tabs.currentWidget()
        if not current_list or current_list == self.list_search_results: return
        
        for i in range(current_list.count()):
            item = current_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _accept_selection(self):
        current_list = self.tabs.currentWidget()
        selected_items = current_list.selectedItems()
        if selected_items:
            self.selected_level_id = selected_items[0].data(Qt.UserRole)
            self.accept()
