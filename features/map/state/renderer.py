"""State 模式渲染.

三层叠加, 让用户编辑省份归属时一眼看清"哪个国家 / 哪个州 / 选中的属于谁":

  1. **底色 = state 色 ⊗ 国家色 50/50 混合** (assigned 区域)
     未分配 state 退化为纯 state 色, 没有国家数据则不混合.
  2. **国家边界 = 3 像素白色加粗线**, 只画在两个已分配国家之间
     (跳过海洋 / 未分配区域).
  3. **选中国家高亮** = 选中州的 owner 那一国, 全部像素叠加暖黄色调,
     可立刻看出"这国家还有别的州在哪". 通过 canvas._highlight_country_rgb 传入.

性能: 国家边界 mask 缓存到 canvas, 只在 country_rgb / assigned_mask 变化时重算.
"""
import numpy as np


_HL_BGR = np.array([80, 230, 255], dtype=np.uint16)  # 暖黄色 (BGR)


def _compute_country_borders(country_rgb, assigned_mask):
    """两个已分配国家间的边界 mask, 加粗到 ~3 像素厚."""
    h, w = country_rgb.shape[:2]
    borders = np.zeros((h, w), dtype=bool)

    diff_v = (country_rgb[:-1] != country_rgb[1:]).any(axis=2)
    a_v = assigned_mask[:-1] & assigned_mask[1:]
    border_v = diff_v & a_v
    borders[:-1, :] |= border_v
    borders[1:, :] |= border_v

    diff_h = (country_rgb[:, :-1] != country_rgb[:, 1:]).any(axis=2)
    a_h = assigned_mask[:, :-1] & assigned_mask[:, 1:]
    border_h = diff_h & a_h
    borders[:, :-1] |= border_h
    borders[:, 1:] |= border_h

    borders = (
        borders
        | np.roll(borders, 1, axis=0) | np.roll(borders, -1, axis=0)
        | np.roll(borders, 1, axis=1) | np.roll(borders, -1, axis=1)
    )
    return borders


def _get_country_borders_cached(canvas):
    rgb = getattr(canvas, "_country_color_rgb", None)
    mask = getattr(canvas, "_country_assigned_mask", None)
    if rgb is None or mask is None:
        return None
    cache = getattr(canvas, "_state_country_borders_cache", None)
    key = (id(rgb), id(mask))
    if cache and cache[0] == key:
        return cache[1]
    borders = _compute_country_borders(rgb, mask)
    canvas._state_country_borders_cache = (key, borders)
    return borders


def _highlight_mask(country_rgb, assigned_mask, highlight_rgb):
    if country_rgb is None or assigned_mask is None or highlight_rgb is None:
        return None
    hr, hg, hb = highlight_rgb
    return (
        assigned_mask
        & (country_rgb[:, :, 0] == hr)
        & (country_rgb[:, :, 1] == hg)
        & (country_rgb[:, :, 2] == hb)
    )


def _fill_blended(buf, state_rgb, country_rgb, mask) -> None:
    """state 色 ⊗ 国家色 50/50 写进 BGRA 缓冲. mask 之外只用 state 色."""
    if state_rgb is None:
        buf[..., 0] = 40
        buf[..., 1] = 40
        buf[..., 2] = 40
        buf[..., 3] = 255
        return
    if country_rgb is not None and mask is not None:
        blend = (
            (state_rgb.astype(np.uint16) + country_rgb.astype(np.uint16)) >> 1
        ).astype(np.uint8)
        rgb = np.where(mask[..., None], blend, state_rgb)
    else:
        rgb = state_rgb
    buf[..., 0] = rgb[..., 2]  # B
    buf[..., 1] = rgb[..., 1]  # G
    buf[..., 2] = rgb[..., 0]  # R
    buf[..., 3] = 255


def _draw_borders(buf, borders) -> None:
    buf[borders, 0] = 255
    buf[borders, 1] = 255
    buf[borders, 2] = 255
    buf[borders, 3] = 255


def _draw_highlight(buf, hl_mask) -> None:
    """选中国家像素与暖黄按 7:9 混合 (黄占 ~56%, 比纯涂色保留更多原信息)."""
    if hl_mask is None or not hl_mask.any():
        return
    cur = buf[hl_mask, :3].astype(np.uint16)
    new = (cur * 7 + _HL_BGR * 9) >> 4
    buf[hl_mask, :3] = new.astype(np.uint8)


def render(canvas) -> None:
    state_rgb = canvas._state_color_rgb
    country_rgb = getattr(canvas, "_country_color_rgb", None)
    mask = getattr(canvas, "_country_assigned_mask", None)
    highlight_rgb = getattr(canvas, "_highlight_country_rgb", None)

    _fill_blended(canvas._display_buffer, state_rgb, country_rgb, mask)

    borders = _get_country_borders_cached(canvas)
    if borders is not None:
        _draw_borders(canvas._display_buffer, borders)

    hl = _highlight_mask(country_rgb, mask, highlight_rgb)
    _draw_highlight(canvas._display_buffer, hl)


def partial_render(canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    state_rgb = canvas._state_color_rgb
    country_rgb = getattr(canvas, "_country_color_rgb", None)
    mask = getattr(canvas, "_country_assigned_mask", None)
    highlight_rgb = getattr(canvas, "_highlight_country_rgb", None)

    buf = canvas._display_buffer[y0:y1, x0:x1]
    s_region = state_rgb[y0:y1, x0:x1] if state_rgb is not None else None
    c_region = country_rgb[y0:y1, x0:x1] if country_rgb is not None else None
    m_region = mask[y0:y1, x0:x1] if mask is not None else None
    _fill_blended(buf, s_region, c_region, m_region)

    borders_full = _get_country_borders_cached(canvas)
    if borders_full is not None:
        _draw_borders(buf, borders_full[y0:y1, x0:x1])

    hl_full = _highlight_mask(country_rgb, mask, highlight_rgb)
    if hl_full is not None:
        _draw_highlight(buf, hl_full[y0:y1, x0:x1])
