"""
省份 feature - 合并 / 切割 / 套索扩张.
"""

from features.base import BaseFeature


class ProvinceFeature(BaseFeature):
    id = "map.province"
    display_name = "省份"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
