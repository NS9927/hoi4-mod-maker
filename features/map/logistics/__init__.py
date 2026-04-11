"""
后勤 feature - adjacencies / 铁路 / 补给节点 统一面板.

三个功能共享一个"后勤" tab, 每个用非模态对话框 + 画布拾取模式.
数据层: domain/managers/{adjacency,railway,supply_node}.py
导出: export/writers/map/{adjacencies,railways,supply_nodes}.py
"""

from features.base import BaseFeature


class LogisticsFeature(BaseFeature):
    id = "map.logistics"
    display_name = "后勤"
    category = "map"
    # 1.0 实现: page.py 侧边栏, 三个 dialog + 三个 tool
