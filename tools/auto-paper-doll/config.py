import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "1_input_bundles")
SKINS_DIR = os.path.join(BASE_DIR, "2_new_skins")
TEMPLATES_DIR = os.path.join(BASE_DIR, "3_templates")
ANIMS_DIR = os.path.join(BASE_DIR, "4_animations")
OUTPUT_DIR = os.path.join(BASE_DIR, "5_output_bundles")

TEMPLATE_MAP = {
    1001: "Sprite",
    1002: "Texture2D",
    1003: "GameObject",
    1004: "Transform",
    1005: "SpriteRenderer",
}

_TYPE_TO_ROLE = {
    "Sprite": "sprite",
    "Texture2D": "texture",
    "GameObject": "gameobject",
    "Transform": "transform",
    "SpriteRenderer": "renderer",
}

ASSET_IDS = {
    _TYPE_TO_ROLE[type_name]: path_id
    for path_id, type_name in TEMPLATE_MAP.items()
}

SPRITE_ID = ASSET_IDS["sprite"]
TEXTURE_ID = ASSET_IDS["texture"]
GAMEOBJECT_ID = ASSET_IDS["gameobject"]
TRANSFORM_ID = ASSET_IDS["transform"]
RENDERER_ID = ASSET_IDS["renderer"]

ROOT_POSITION = (0.55, 0.0, -0.43)
CHARACTER_POSITION = (0.0, 2.0, 0.0)
CHARACTER_SCALE = (1.0, 1.0, 1.0)
CHARACTER_NODE_NAME = "character"

SHIP_CONTAINER_MARKER = "/ship/"
SHIP_INHAND_MARKER = "generatedsprites/inhand"
SHIP_TEXTURE_SIZE = 256

DEFAULT_PIXELS_TO_UNITS = 75
DEFAULT_Y_OFFSET = CHARACTER_POSITION[1]

TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")

SCRIPT_VERSION = "2.6"

# 盲缝为默认配对标准；设为 True 时，皮肤文件名匹配大根 PathID 可优先覆盖盲缝
ENABLE_PATH_ID_PAIRING = False

PROGRESS_FILE = os.path.join(BASE_DIR, "progress.md")

PAIRING_MODE_LABELS = {
    "blind": "盲缝（顺序分配）",
    "path_id": "PathID 精确配对（保留）",
    "blind_single": "盲缝（唯一皮肤）",
    "blind_shared": "盲缝（共用皮肤）",
    "manual": "手动指定",
    "unmatched": "未配对",
    "failed": "扫描失败",
}


def init_folders():
    for folder in [INPUT_DIR, SKINS_DIR, TEMPLATES_DIR, ANIMS_DIR, OUTPUT_DIR]:
        os.makedirs(folder, exist_ok=True)