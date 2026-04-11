"""
地形 feature - 10 种地形按省份赋值.
"""

from features.base import BaseFeature


class TerrainFeature(BaseFeature):
    id = "map.terrain"
    display_name = "地形"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
