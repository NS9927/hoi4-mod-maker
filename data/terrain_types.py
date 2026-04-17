"""
HOI4 地形类型定义 — 颜色编码和属性
"""
from typing import NamedTuple


class TerrainType(NamedTuple):
    """地形类型"""
    name: str           # 内部名称
    name_cn: str        # 中文名称
    name_en: str        # 英文名称
    color: tuple[int, int, int]  # terrain.bmp 中的 RGB 颜色
    height_base: int    # 高度图基础灰度值
    tree_density: int   # 树木密度 (0=无树, 255=密林) — trees.bmp 用反转: 255=无树, 0=密林


# HOI4 标准地形类型及其 terrain.bmp 颜色编码
TERRAIN_TYPES = {
    "ocean":    TerrainType("ocean",    "海洋", "Ocean",    (0, 0, 255),     40,   255),
    "lakes":    TerrainType("lakes",    "湖泊", "Lakes",    (0, 255, 255),   90,   255),
    "plains":   TerrainType("plains",   "平原", "Plains",   (255, 129, 66),  120,  230),
    "forest":   TerrainType("forest",   "森林", "Forest",   (89, 199, 85),   130,  60),
    "hills":    TerrainType("hills",    "丘陵", "Hills",    (248, 255, 153), 160,  200),
    "mountain": TerrainType("mountain", "山地", "Mountain", (124, 135, 125), 220,  240),
    "desert":   TerrainType("desert",   "沙漠", "Desert",   (255, 63, 0),    110,  255),
    "marsh":    TerrainType("marsh",    "沼泽", "Marsh",    (76, 96, 35),    100,  120),
    "jungle":   TerrainType("jungle",   "丛林", "Jungle",   (127, 191, 0),   125,  30),
    "urban":    TerrainType("urban",    "城市", "Urban",    (128, 128, 128), 125,  255),
}

# terrain.bmp 使用 8 位索引色调色板
# 索引号必须与原版 common/terrain/00_terrain.txt 的 color={} 值一致
# 从原��� G:/SteamLibrary/.../common/terrain/00_terrain.txt 第323-356行实际验证
TERRAIN_PALETTE_INDEX = {
    "ocean":    15,   # ocean_15: type=ocean, color={15}
    "lakes":    14,   # forest_14: type=lakes, color={14}
    "plains":   0,    # terrain_0: type=plains, color={0}
    "forest":   1,    # terrain_1: type=forest, color={1}
    "hills":    17,   # hills_blend: type=hills, color={17}
    "mountain": 11,   # desert: type=mountain, color={11}
    "desert":   3,    # desert: type=desert, color={3}
    "marsh":    9,    # terrain_9: type=marsh, color={9}
    "jungle":   21,   # jungle_18: type=jungle, color={21}
    "urban":    13,   # forest_13: type=urban, color={13}
}

# 根据地块类型自动分配的默认地形
DEFAULT_TERRAIN_FOR_TILE = {
    0: "ocean",    # TILE_UNDEFINED → 海洋
    1: "plains",   # TILE_LAND → 平原
    2: "ocean",    # TILE_SEA → 海洋
    3: "lakes",    # TILE_LAKE → 湖泊
}

# State 分类等级（按人口/开发度）
STATE_CATEGORIES = [
    "wasteland",    # 荒地
    "pastoral",     # 田园
    "tiny",         # 极小
    "small",        # 小
    "town",         # 镇
    "large_town",   # 大镇
    "city",         # 城市
    "large_city",   # 大城市
    "megalopolis",  # 特大城市
]

# 河流颜色编码
RIVER_COLORS = {
    "source":       (255, 0, 0),       # 河流源头
    "flow_marker":  (0, 255, 0),       # 起始流向标记
    "fork":         (255, 252, 0),     # 分叉点
    "merge_start":  (0, 200, 0),       # 合并点起始
    "merge_end":    (0, 100, 0),       # 合并点结束
    "background":   (255, 255, 255),   # 背景（白色）
}

# 河流宽度用蓝色通道值表示
# (0, 0, 蓝色值)，值越小河流越宽
RIVER_WIDTH_NARROW = 255    # 最窄
RIVER_WIDTH_WIDE = 1        # 最宽


class GraphicalTerrain(NamedTuple):
    """terrain.bmp 的 graphical terrain 条目 (来自 00_terrain.txt terrain={} 块)"""
    id: str                # 原版条目名: "terrain_0", "desert_mountain" 等
    type: str              # provincial terrain 类型: plains/forest/mountain 等
    palette_index: int     # terrain.bmp 调色板索引
    texture: int           # atlas0.dds 贴图编号 (0-15)
    name_cn: str           # 中文显示名
    perm_snow: bool        # 永雪覆盖
    spawn_city: bool       # 自动生成城市模型


# 原版 00_terrain.txt terrain={} 块全部条目
GRAPHICAL_TERRAINS: list[GraphicalTerrain] = [
    GraphicalTerrain("terrain_0",             "plains",   0,  1,  "平原",           False, False),
    GraphicalTerrain("terrain_1",             "forest",   1,  4,  "森林",           False, False),
    GraphicalTerrain("desert_mountain",       "hills",    2,  3,  "沙漠丘陵",       False, False),
    GraphicalTerrain("desert",                "desert",   3,  9,  "沙漠",           False, False),
    GraphicalTerrain("terrain_4",             "forest",   4,  5,  "森林(变体)",     False, False),
    GraphicalTerrain("terrain_5",             "plains",   5,  0,  "平原(变体)",     False, False),
    GraphicalTerrain("terrain_6",             "mountain", 6,  11, "山地",           False, False),
    GraphicalTerrain("terrain_7",             "desert",   7,  12, "沙漠(变体)",     False, False),
    GraphicalTerrain("desert_hills",          "desert",   8,  14, "沙漠丘陵",       False, False),
    GraphicalTerrain("terrain_9",             "marsh",    9,  6,  "沼泽",           False, False),
    GraphicalTerrain("terrain_10",            "mountain", 10, 13, "山地(变体)",     False, False),
    GraphicalTerrain("desert_mountain_11",    "mountain", 11, 11, "沙漠山地",       False, False),
    GraphicalTerrain("desert_12",             "desert",   12, 8,  "沙漠(岩地)",     False, False),
    GraphicalTerrain("forest_13",             "urban",    13, 10, "城市",           False, True),
    GraphicalTerrain("forest_14",             "lakes",    14, 255, "湖泊",          False, False),
    GraphicalTerrain("ocean_15",              "ocean",    15, 9,  "海洋",           False, False),
    GraphicalTerrain("snow_16",               "mountain", 16, 11, "雪山",           True,  False),
    GraphicalTerrain("hills_blend",           "hills",    17, 2,  "丘陵",           False, False),
    GraphicalTerrain("mountain_variation_sand","mountain", 18, 7,  "沙色山地",      False, False),
    GraphicalTerrain("plains_snow",           "plains",   19, 0,  "雪原",           True,  False),
    GraphicalTerrain("mountain_variation_grass","mountain",20, 7,  "草地山地",      False, False),
    GraphicalTerrain("jungle_18",             "jungle",   21, 4,  "丛林",           False, False),
    GraphicalTerrain("jungle_blend_18",       "jungle",   22, 5,  "丛林(变体)",     False, False),
    GraphicalTerrain("jungle_mountain",       "mountain", 27, 7,  "丛林山地",       False, False),
    GraphicalTerrain("desert_mountain_tops",  "mountain", 31, 15, "沙漠山顶",       False, False),
]

# 调色板索引 → GraphicalTerrain 快速查找
GRAPHICAL_TERRAIN_BY_INDEX: dict[int, GraphicalTerrain] = {
    gt.palette_index: gt for gt in GRAPHICAL_TERRAINS
}

# 调色板索引 → provincial terrain type 名称 (用于 definition.csv)
PALETTE_TO_TYPE: dict[int, str] = {
    gt.palette_index: gt.type for gt in GRAPHICAL_TERRAINS
}

# 按 provincial terrain type 分组的可画变体 (排除 ocean/lakes)
PAINTABLE_GROUPS: dict[str, list[GraphicalTerrain]] = {}
for _gt in GRAPHICAL_TERRAINS:
    if _gt.type not in ("ocean", "lakes"):
        PAINTABLE_GROUPS.setdefault(_gt.type, []).append(_gt)


# ── 本地化显示名 ──────────────────────────────────────────────
# UI 显示地形名时调这两个 helper，会根据当前语言返回中/英文。
# 为什么不把 name_en 直接塞进 NamedTuple：
#   GRAPHICAL_TERRAINS 25 条、位置参数已排好，改结构要全量改；
#   用查 i18n 表的方式隔离中英文，减少 churn。

def terrain_display_name(tt: "TerrainType") -> str:
    """TerrainType 的本地化显示名（跟随 ui.i18n 当前语言）。"""
    from ui.i18n import get_language
    return tt.name_en if get_language() == "en" else tt.name_cn


def graphical_terrain_display_name(gt: "GraphicalTerrain") -> str:
    """GraphicalTerrain 的本地化显示名（key=gt_<id>，在 ui/i18n.py 注册）。"""
    from ui.i18n import tr
    return tr(f"gt_{gt.id}")
