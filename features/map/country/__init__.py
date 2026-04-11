"""
国家 feature - 国家 CRUD + 颜色/政党/首都.
"""

from features.base import BaseFeature


class CountryFeature(BaseFeature):
    id = "map.country"
    display_name = "国家"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
