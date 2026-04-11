"""
default.map 配置 feature.

控制 HOI4 引擎的地图加载行为. 通过菜单"工具 → 地图配置..." 打开.
"""

from features.base import BaseFeature


class DefaultMapFeature(BaseFeature):
    id = "map.default_map"
    display_name = "地图配置"
    category = "map"
