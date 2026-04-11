"""Land 模式渲染: tile_map (陆/海/湖) → BGRA 显示缓冲."""


def render(canvas) -> None:
    from ui.canvas_widget import _TILE_BGRA
    for tile_type, (b, g, r, a) in _TILE_BGRA.items():
        mask = canvas._tile_map == tile_type
        canvas._display_buffer[mask, 0] = b
        canvas._display_buffer[mask, 1] = g
        canvas._display_buffer[mask, 2] = r
        canvas._display_buffer[mask, 3] = a


def partial_render(canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    from ui.canvas_widget import _TILE_BGRA
    region = canvas._tile_map[y0:y1, x0:x1]
    buf = canvas._display_buffer[y0:y1, x0:x1]
    for tile_type, (b, g, r, a) in _TILE_BGRA.items():
        mask = region == tile_type
        buf[mask, 0] = b
        buf[mask, 1] = g
        buf[mask, 2] = r
        buf[mask, 3] = a
