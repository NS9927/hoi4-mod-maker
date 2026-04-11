"""
河流 feature - 河流绘制 + HOI4 色板.
"""

from features.base import BaseFeature


class RiverFeature(BaseFeature):
    id = "map.river"
    display_name = "河流"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
