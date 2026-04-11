"""
State feature - State 分组 + 进阶字段编辑.
"""

from features.base import BaseFeature


class StateFeature(BaseFeature):
    id = "map.state"
    display_name = "State"
    category = "map"
    # 1.0 已实现, page/renderer 在同目录
