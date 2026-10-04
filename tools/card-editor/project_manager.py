# project_manager.py
import os
import json
from PySide6.QtCore import QSettings
import config


class ProjectManager:
    """幻影引擎 - 全局工程管理器"""

    def __init__(self):
        self.projects_dir = config.PROJECTS_DIR
        os.makedirs(self.projects_dir, exist_ok=True)

        self.current_project_name = None
        self.project_cards = {}  # 结构: { "GUID(str)": {card_data_dict} }
        self.settings = QSettings("ModdingTool", "PhantomEngine_Project")

        self.auto_load_last_project()

    @staticmethod
    def _norm_guid(guid) -> str:
        return str(guid)

    def auto_load_last_project(self):
        last_proj = self.settings.value("last_project", "")
        if last_proj and self.load_project(last_proj):
            return True
        return False

    def get_all_projects(self):
        """扫描 projects 目录下的所有 .phantom 工程"""
        projects = []
        if not os.path.isdir(self.projects_dir):
            return projects
        for file in os.listdir(self.projects_dir):
            if file.endswith(".phantom"):
                projects.append(file[:-8])
        return sorted(projects)

    def create_project(self, name):
        """新建一个空白工程"""
        self.current_project_name = name
        self.project_cards = {}
        self.settings.setValue("last_project", name)
        self.save_current_project()
        return True

    def load_project(self, name):
        """读取工程文件到内存"""
        filepath = os.path.join(self.projects_dir, f"{name}.phantom")
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            # 兼容未来版本包装格式
            if isinstance(raw, dict) and "cards" in raw and isinstance(raw["cards"], dict):
                self.project_cards = {self._norm_guid(k): v for k, v in raw["cards"].items()}
            else:
                self.project_cards = {self._norm_guid(k): v for k, v in raw.items()}
            self.current_project_name = name
            self.settings.setValue("last_project", name)
            return True
        except Exception as e:
            print(f"读取工程失败: {e}")
            return False

    def save_current_project(self):
        """将内存中的所有卡牌落盘保存到 .phantom 文件"""
        if not self.current_project_name:
            return False

        filepath = os.path.join(self.projects_dir, f"{self.current_project_name}.phantom")
        try:
            os.makedirs(self.projects_dir, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.project_cards, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存工程失败: {e}")
            return False

    def add_or_update_card(self, card_model):
        """从工作台把卡牌保存进工程清单"""
        if not self.current_project_name:
            return False

        card_dict = card_model.generate_json_dict()
        guid_str = self._norm_guid(card_model.guid)
        self.project_cards[guid_str] = card_dict[guid_str]
        return self.save_current_project()

    def delete_card(self, guid):
        """从工程中删除某张卡的修改（guid 可为 int 或 str）"""
        guid_str = self._norm_guid(guid)
        if guid_str in self.project_cards:
            del self.project_cards[guid_str]
            self.save_current_project()
            return True
        return False
