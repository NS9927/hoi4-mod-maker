"""
后勤模式画布渲染.

底层沿用 land 模式的陆海显示, 然后叠加:
- adjacencies: sea=蓝虚线, impassable=红叉, canal=黄线
- railways: 按 level 粗细的彩色线
- supply nodes: 绿圆点

渲染时需要能访问 adjacency_mgr / railway_mgr / supply_mgr, 这些挂在 canvas 实例上.
"""

from __future__ import annotations

import numpy as np

from features.map.land import renderer as land_renderer


def render(canvas) -> None:
    """后勤模式全量渲染: 陆海底图 + 省份边界 (后勤层由 canvas overlay 绘制)."""
    land_renderer.render(canvas)


def partial_render(canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    land_renderer.partial_render(canvas, x0, y0, x1, y1)
