"""River 模式渲染: 陆地底图 + 河流叠加."""

import numpy as np

from features.map.land import renderer as land_renderer
from domain.managers.river import VALID_RIVER_VALUES


def _make_river_mask(river_data: np.ndarray) -> np.ndarray:
    """河流像素 mask: 所有有效河流值 (含 0=源头)."""
    mask = np.zeros(river_data.shape, dtype=bool)
    for v in VALID_RIVER_VALUES:
        mask |= (river_data == v)
    return mask


def render(canvas) -> None:
    from ui.canvas_widget import _RIVER_COLOR_LUT
    # 先渲染陆地作为底图
    land_renderer.render(canvas)
    river_mask = _make_river_mask(canvas._river_map)
    if np.any(river_mask):
        colors = _RIVER_COLOR_LUT[canvas._river_map]
        canvas._display_buffer[river_mask] = colors[river_mask]


def partial_render(canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    from ui.canvas_widget import _RIVER_COLOR_LUT
    land_renderer.partial_render(canvas, x0, y0, x1, y1)
    region = canvas._river_map[y0:y1, x0:x1]
    river_mask = _make_river_mask(region)
    if np.any(river_mask):
        buf = canvas._display_buffer[y0:y1, x0:x1]
        colors = _RIVER_COLOR_LUT[region]
        buf[river_mask] = colors[river_mask]
