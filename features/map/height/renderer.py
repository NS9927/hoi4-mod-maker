"""Height 模式渲染: height_map → 等高线彩色显示.

编辑器用彩色地形图方便区分高低，导出的 heightmap.bmp 仍为灰度。
颜色方案 (BGRA):
  0-40   深蓝 (深海)
  40-90  浅蓝 (浅海)
  90-95  青色 (海平面)
  95-130 绿色 (平原)
  130-160 黄绿 (丘陵)
  160-200 棕色 (山地)
  200-240 深棕 (高山)
  240-255 白色 (雪顶)
"""

import numpy as np

# 构建 256 级高度 → BGRA 颜色查找表
_HEIGHT_COLOR_LUT = np.zeros((256, 4), dtype=np.uint8)

# 色带定义: (起始高度, 结束高度, 起始RGB, 结束RGB)
_BANDS = [
    (0,   40,  (20,  40,  80),  (30,  60, 120)),   # 深海: 深蓝
    (40,  90,  (60,  90, 140),  (100, 140, 180)),   # 浅海: 浅蓝
    (90,  95,  (140, 180, 180), (160, 200, 180)),   # 海平面: 青色过渡
    (95,  130, (80,  160, 80),  (140, 190, 100)),   # 平原: 绿色
    (130, 160, (160, 190, 100), (200, 200, 80)),    # 丘陵: 黄绿
    (160, 200, (160, 140, 60),  (140, 100, 50)),    # 山地: 棕色
    (200, 240, (120, 80,  40),  (100, 70,  50)),    # 高山: 深棕
    (240, 256, (200, 200, 210), (255, 255, 255)),   # 雪顶: 白色
]

for lo, hi, (r0, g0, b0), (r1, g1, b1) in _BANDS:
    span = max(hi - lo, 1)
    for v in range(lo, min(hi, 256)):
        t = (v - lo) / span
        r = int(r0 + (r1 - r0) * t)
        g = int(g0 + (g1 - g0) * t)
        b = int(b0 + (b1 - b0) * t)
        _HEIGHT_COLOR_LUT[v] = (b, g, r, 255)  # BGRA


def render(canvas) -> None:
    canvas._display_buffer[:] = _HEIGHT_COLOR_LUT[canvas._height_map]


def partial_render(canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    canvas._display_buffer[y0:y1, x0:x1] = (
        _HEIGHT_COLOR_LUT[canvas._height_map[y0:y1, x0:x1]]
    )
