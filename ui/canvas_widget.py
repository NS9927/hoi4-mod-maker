"""兼容层 — 旧代码通过 ui.canvas_widget 引用 MapCanvas 和颜色 LUT。"""
from views.canvas.widget import MapCanvas
from views.canvas.luts import (
    _TILE_BGRA,
    _TERRAIN_COLOR_LUT,
    _TERRAIN_DISPLAY_COLORS,
    _RIVER_COLOR_LUT,
    _PROVINCE_COLOR_LUT,
    _PROVINCE_COLOR_LUT_SIZE,
)
