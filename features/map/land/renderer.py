"""Land 模式渲染: tile_map (陆/海/湖) → BGRA 显示缓冲.

new_land_mask 上的像素会额外覆盖一层鲜黄色（BGRA），让用户在"新大陆"模式下
能一眼看到刚画上、还没生成省份的那片区域。
"""

# 新大陆高亮色（BGRA）— 鲜亮黄，和普通陆地绿区分开
_NEW_LAND_HIGHLIGHT = (60, 230, 255, 255)


def _overlay_new_land(canvas, buf, region_mask=None, y0: int = 0, x0: int = 0) -> None:
    """把 new_land_mask 的像素覆盖成高亮色。region_mask 可选, 用于局部渲染。"""
    nlm = getattr(canvas, "new_land_mask", None)
    if nlm is None or not nlm.any():
        return
    if region_mask is None:
        mask = nlm
    else:
        mask = nlm[y0:y0 + buf.shape[0], x0:x0 + buf.shape[1]]
    if not mask.any():
        return
    b, g, r, a = _NEW_LAND_HIGHLIGHT
    buf[mask, 0] = b
    buf[mask, 1] = g
    buf[mask, 2] = r
    buf[mask, 3] = a


def render(canvas) -> None:
    from ui.canvas_widget import _TILE_BGRA
    for tile_type, (b, g, r, a) in _TILE_BGRA.items():
        mask = canvas._tile_map == tile_type
        canvas._display_buffer[mask, 0] = b
        canvas._display_buffer[mask, 1] = g
        canvas._display_buffer[mask, 2] = r
        canvas._display_buffer[mask, 3] = a
    _overlay_new_land(canvas, canvas._display_buffer)


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
    _overlay_new_land(canvas, buf, region_mask=True, y0=y0, x0=x0)
