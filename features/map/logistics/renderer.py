"""
后勤模式画布渲染 — 铁路等级着色图.

每个有铁路的省份按等级着色（1=灰蓝 → 5=红）。
比画线段快得多，KR 1027 条铁路也不卡。
"""

from __future__ import annotations


def render(canvas) -> None:
    """后勤模式: 铁路等级着色。"""
    if canvas._railway_color_rgb is not None:
        canvas._display_buffer[:, :, 0] = canvas._railway_color_rgb[:, :, 2]
        canvas._display_buffer[:, :, 1] = canvas._railway_color_rgb[:, :, 1]
        canvas._display_buffer[:, :, 2] = canvas._railway_color_rgb[:, :, 0]
        canvas._display_buffer[:, :, 3] = 255
    else:
        # fallback: 陆海底图
        from features.map.land import renderer as land_renderer
        land_renderer.render(canvas)


def partial_render(canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    buf = canvas._display_buffer[y0:y1, x0:x1]
    if canvas._railway_color_rgb is not None:
        region = canvas._railway_color_rgb[y0:y1, x0:x1]
        buf[:, :, 0] = region[:, :, 2]
        buf[:, :, 1] = region[:, :, 1]
        buf[:, :, 2] = region[:, :, 0]
        buf[:, :, 3] = 255
    else:
        from features.map.land import renderer as land_renderer
        land_renderer.partial_render(canvas, x0, y0, x1, y1)
