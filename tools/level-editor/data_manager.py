# data_manager.py
import os
import sys
import json

class DataManager:
    """负责处理所有外部资源的加载、解析和路径管理，不直接参与UI绘制"""
    
    def __init__(self):
        self.card_db = {}
        self.deck_db = {}
        self.card_index = []

    def load_all(self):
        self.deck_db = self._load_deck_database("decks.json")
        self.card_index = self._load_card_index_json("index.json")

    def _load_card_index_json(self, filename):
        """解析 index.json 返回 [(GUID, 中文名), ...] 格式"""
        resource_path = self.get_resource_path(filename)
        if not os.path.exists(resource_path): 
            return []
        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 提取 GUID 并转为 int，提取 NAME_CN
                return [(int(item["GUID"]), item["NAME_CN"]) for item in data]
        except Exception as e:
            print(f"读取 index.json 失败: {e}")
            return []

    @staticmethod
    def get_resource_path(filename):
        """处理打包后资源访问路径的安全方法"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                meipass_path = os.path.join(base_path, filename)
                if os.path.exists(meipass_path): 
                    return meipass_path
                current_dir = os.path.dirname(os.path.abspath(sys.executable))
                current_path = os.path.join(current_dir, filename)
                if os.path.exists(current_path): 
                    return current_path
                return meipass_path
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                return os.path.join(base_path, filename)
        except Exception:
            return filename

    def _load_card_database(self, filename):
        card_db = {}
        resource_path = self.get_resource_path(filename)
        if not os.path.exists(resource_path): 
            return card_db
            
        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "——————" in line:
                        parts = line.split("——————")
                        if len(parts) >= 3:
                            card_db[parts[-1].strip()] = int(parts[0].strip())
            return card_db
        except Exception:
            return card_db

    def _load_deck_database(self, filename):
        """解析 JSON 格式的卡组数据库"""
        deck_db = {}
        resource_path = self.get_resource_path(filename)
        if not os.path.exists(resource_path): 
            return deck_db
            
        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    form = item.get("form", "未分类")
                    cn_name = item.get("cn", "未命名")
                    deck_id = item.get("id", "")
                    
                    if deck_id:
                        # 拼装成 UI 组件需要的显示格式，例如: "急冻魔 (PVE关卡) | 急冻魔 PVE关卡 001"
                        display_text = f"{form} | {cn_name}"
                        deck_db[display_text] = deck_id
            return deck_db
        except Exception as e:
            print(f"读取卡组 JSON 失败: {e}")
            return deck_db

def create_default_config():
    """生成初始的空白/默认关卡配置字典"""
    return {
        "Id": "PVE_Soft_Node_Zombie_200",
        "Status": 0,
        "MustPlayAllPlayableCards": False,
        "DisableSurprisePhase": False,
        "DelayHeroIntros": False,
        "HideSurpriseVisual": False,
        "DisableDynamicDifficulty": False,
        "EloGainMultiplier": 1.0,
        "OpponentElo": 1700,
        "EnableReadySetPlant": True,
        "SkipHeroSelect": False,
        "OpponentConfig": {
            "Parameters": {
                "Faction": 0, "InitialCardsToDrawFromDeck": 4, "InitialCardsToDrawFromSuperpowerPool": 1,
                "NumCardsToDrawPerTurn": 1, "InitialSunCount": 1, "ShuffleDeckAtStartOfGame": True,
                "ShuffleSuperpowerPoolAtStartOfGame": True, "MulliganAtStartOfGame": True, "MaxHandSize": 10,
                "InitialHealth": 20, "SuperBlockChance": 15, "DiesWhenDrawingOnEmpty": True,
                "HasTimedTurns": False, "CreateAllCardsInDeck": False,
                "SuperBlockTable": {"TableEntries": [{"RngWeight": 33, "ChargeAmount": 10}, {"RngWeight": 34, "ChargeAmount": 20}, {"RngWeight": 33, "ChargeAmount": 30}]},
                "BlockMeterMax": 80, "SuperBlockHealthThreshold": 2147483647
            },
            "HeroSelection": 0, "HeroId": "Citron", "DeckId": "Soft_PVE_Deck_Plant_Citron_020", "SuperblockMultiplier": 0.0
        },
        "PlayerConfig": {
            "Parameters": {
                "Faction": 1, "InitialCardsToDrawFromDeck": 4, "InitialCardsToDrawFromSuperpowerPool": 1,
                "NumCardsToDrawPerTurn": 1, "InitialSunCount": 1, "ShuffleDeckAtStartOfGame": True,
                "ShuffleSuperpowerPoolAtStartOfGame": True, "MulliganAtStartOfGame": True, "MaxHandSize": 10,
                "InitialHealth": 20, "SuperBlockChance": 15, "DiesWhenDrawingOnEmpty": True,
                "HasTimedTurns": False, "CreateAllCardsInDeck": False,
                "SuperBlockTable": {"TableEntries": [{"RngWeight": 33, "ChargeAmount": 10}, {"RngWeight": 34, "ChargeAmount": 20}, {"RngWeight": 33, "ChargeAmount": 30}]},
                "BlockMeterMax": 80, "SuperBlockHealthThreshold": 2147483647
            },
            "HeroSelection": 1, "HeroId": "CptBrainz", "DeckId": "", "SuperblockMultiplier": 0.0
        },
        "BoardConfig": {
            "LaneEntries": [{"LaneType": 0, "Cards": []}, {"LaneType": 1, "Cards": []}, {"LaneType": 1, "Cards": []}, {"LaneType": 1, "Cards": []}, {"LaneType": 2, "Cards": []}],
            "BoardAbilities": [], "PlantsBoardName": "GrassKnuckles", "ZombiesBoardName": "GrassKnuckles"
        },
        "PreGameConfig": {"Name": "Node:Name", "Description": "Node:Description", "Narrative": ""},
        "PostGameConfig": {"RewardPackId": "", "Narrative": "", "RewardPackIds": []},
        "RepresentationConfig": {"Type": 5, "Id": "Citron", "Guid": 103},
        "GameEvents": []
    }