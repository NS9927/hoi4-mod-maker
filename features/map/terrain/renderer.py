"""Terrain 模式渲染: terrain_map → 颜色 LUT."""


def render(canvas) -> None:
    from ui.canvas_widget import _TERRAIN_COLOR_LUT
    canvas._display_buffer[:] = _TERRAIN_COLOR_LUT[canvas._terrain_map]


def partial_render(canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    from ui.canvas_widget import _TERRAIN_COLOR_LUT
    canvas._display_buffer[y0:y1, x0:x1] = (
        _TERRAIN_COLOR_LUT[canvas._terrain_map[y0:y1, x0:x1]]
    )
