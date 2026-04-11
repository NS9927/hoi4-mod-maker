"""
高度 feature - heightmap 编辑 + 自动生成.
"""

from features.base import BaseFeature


class HeightFeature(BaseFeature):
    id = "map.height"
    display_name = "高度"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
