# constants.py
# 英雄 / 场景：(ID, 中文名, 英文名)
# 植物英雄
PLANT_HEROES = [
    ("BetaCarrotina", "贝塔胡萝卜蒂娜", "Beta-Carrotina"),
    ("Chomper", "霸王大嘴花", "Chompzilla"),
    ("Citron", "香橼猎手", "Citron"),
    ("Grass_Knuckles", "拳王菜", "Grass Knuckles"),
    ("NightCap", "暗夜菇", "Nightcap"),
    ("Penelopea", "绿影侠", "Green Shadow"),
    ("Rose", "玫瑰", "Rose"),
    ("Scortchwood", "火爆队长", "Captain Combustible"),
    ("Spudow", "土豆仔", "Spudow"),
    ("Sunflower", "耀斑花", "Solar Flare"),
    ("WallKnight", "坚果骑士", "Wall-Knight"),
]

# 僵尸英雄
ZOMBIE_HEROES = [
    ("CptBrainz", "超尸", "Super Brainz"),
    ("BrainFreeze", "急冻魔", "Brain Freeze"),
    ("Cyborg", "锈铁侠", "Rustbolt"),
    ("Disco", "霹雳舞王", "Electric Boogaloo"),
    ("Gargantuar", "摔跤狂", "The Smash"),
    ("HugeGigantacu", "至尊大王", "Huge-Gigantacus"),
    ("Impfinity", "无穷小子", "Impfinity"),
    ("Neptuna", "海妖", "Neptuna"),
    ("Professor", "僵点子教授", "Professor Brainstorm"),
    ("Witch", "不死女妖", "Immorticia"),
    ("ZMech", "Z机甲", "Z-Mech"),
]

# 全英雄列表（用于搜索和兜底）
ALL_HEROES = PLANT_HEROES + ZOMBIE_HEROES

# 场景列表 (Scene_ID, 中文名, 英文名)
SCENES = [
    # ===== 正式英雄场景 =====
    ("BrainFreeze", "急冻魔冰原", "Brain Freeze Glacier"),
    ("Citron", "香橼太空站", "Citron Space Station"),
    ("Disco", "舞王迪斯科", "Disco Floor"),
    ("GrassKnuckles", "拳王菜海滩", "Grass Knuckles Beach"),
    ("Impfinity", "无穷小子游乐园", "Impfinity Amusement Park"),
    ("Neptuna", "海妖海底", "Neptuna Undersea"),
    ("NightCap", "暗夜菇忍者屋", "Nightcap Ninja House"),
    ("Professor", "僵点子教授大学", "Professor University"),
    ("Rose", "玫瑰城堡", "Rose Castle"),
    ("ZMech", "Z机甲工厂", "Z-Mech Factory"),

    # ===== 原版地图/通用地图 =====
    ("Arcade", "游戏厅", "Arcade"),
    ("ArenaInSpace", "太空竞技场", "Arena in Space"),
    ("Backyard", "后院", "Backyard"),
    ("CastlePuttPutt", "城堡高尔夫", "Castle Putt-Putt"),
    ("Greenhouse", "温室", "Greenhouse"),
    ("HauntedMansion", "鬼屋", "Haunted Mansion"),
    ("Junkyard", "垃圾场", "Junkyard"),
    ("Mine", "矿洞", "Mine"),
    ("ShadowFalls", "暗影瀑布", "Shadow Falls"),
    ("Stadium", "体育场", "Stadium"),
    ("Zombopolis", "僵尸都市", "Zombopolis"),

    # ===== 教学/基础场景 =====
    ("Lawn_Plants", "植物草坪", "Plant Lawn"),
    ("Lawn_Plants_tutorial", "植物教程草坪", "Plant Tutorial Lawn"),
    ("Lawn_Zombies", "僵尸草坪", "Zombie Lawn"),

    # ===== 活动/节日场景 =====
    ("Feastivus", "冬季盛典", "Feastivus"),
    ("Luckofthezombie", "僵尸幸运节", "Luck of the Zombie"),
    ("Springening", "春季活动", "Springening"),
    ("Valenbrainz", "情尸节", "Valenbrainz"),
    ("RoseRedPromo", "玫瑰红宣传图", "Rose Red Promo"),

    # ===== 特殊事件场景 =====
    ("CaptCombustible", "爆燃树桩", "Captain Combustible"),
    ("LightTorchwood", "火炬树桩", "Light Torchwood"),
    ("MeteorZ", "陨石Z", "Meteor Z"),
]

# 关卡选择器中英雄别名 (小写 ID -> 中文名, 英文名)
HERO_ALIASES = {
    "greenshadow": ("绿影侠", "Green Shadow"),
    "solarflare": ("耀斑花", "Solar Flare"),
    "chompzilla": ("霸王大嘴花", "Chompzilla"),
    "captaincombustible": ("火爆队长", "Captain Combustible"),
    "cptcombust": ("火爆队长", "Captain Combustible"),
    "scorchwood": ("火爆队长", "Captain Combustible"),
    "grassknuckles": ("拳王菜", "Grass Knuckles"),
    "grasskuckles": ("拳王菜", "Grass Knuckles"),
    "superbrainz": ("超尸", "Super Brainz"),
    "thesmash": ("摔跤狂", "The Smash"),
    "the smash": ("摔跤狂", "The Smash"),
    "rustbolt": ("锈铁侠", "Rustbolt"),
    "electricboogaloo": ("霹雳舞王", "Electric Boogaloo"),
    "profbrainstorm": ("僵点子教授", "Professor Brainstorm"),
    "immorticia": ("不死女妖", "Immorticia"),
    "hugegigantacus": ("至尊大王", "Huge-Gigantacus"),
    "aquazombie": ("水路僵尸(测试)", "Aqua Zombie (Test)"),
    "sirstrangealot": ("奇怪爵士(测试)", "Sir Strangealot (Test)"),
}
