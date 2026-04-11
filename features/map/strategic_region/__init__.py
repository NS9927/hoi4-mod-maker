"""
战略区域 feature - 手动分组省份到 region + weather 预设 + naval_terrain.
"""

from features.base import BaseFeature


class StrategicRegionFeature(BaseFeature):
    id = "map.strategic_region"
    display_name = "战略区域"
    category = "map"
