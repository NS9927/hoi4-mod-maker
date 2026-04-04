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
# 索引号必须与原版 HOI4 terrain.bmp 一致（从原版实际数据逆向得到）
TERRAIN_PALETTE_INDEX = {
    "ocean":    15,   # 原版海洋索引
    "lakes":    15,   # 湖泊也用海洋索引
    "plains":   9,    # 平原
    "forest":   1,    # 森林
    "hills":    3,    # 丘陵
    "mountain": 11,   # 山地
    "desert":   7,    # 沙漠
    "marsh":    10,   # 沼泽
    "jungle":   21,   # 丛林
    "urban":    2,    # 城市
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
