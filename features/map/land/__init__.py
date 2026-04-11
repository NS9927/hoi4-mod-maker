"""
大陆 feature - 陆海湖画笔 + Voronoi 省份生成.
"""

from features.base import BaseFeature


class LandFeature(BaseFeature):
    id = "map.land"
    display_name = "大陆"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
