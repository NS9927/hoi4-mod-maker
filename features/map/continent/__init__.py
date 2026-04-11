"""
大陆分区 feature - 多洲定义 + 省份指派.
"""

from features.base import BaseFeature


class ContinentFeature(BaseFeature):
    id = "map.continent"
    display_name = "大陆分区"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
