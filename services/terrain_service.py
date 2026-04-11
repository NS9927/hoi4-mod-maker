"""
地形 / 高度自动生成服务.

从 tile_map (陆/海/湖) 自动生成 terrain_map 和 height_map.
"""

from __future__ import annotations

import numpy as np

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_LAND, TILE_LAKE, TILE_SEA,
    OCEAN_HEIGHT, LAND_BASE_HEIGHT, SEA_LEVEL,
)
from data.terrain_types import DEFAULT_TERRAIN_FOR_TILE, TERRAIN_PALETTE_INDEX


def auto_terrain(tile_map: np.ndarray) -> np.ndarray:
    """按 tile_map 默认规则生成 terrain_map."""
    terrain = np.zeros_like(tile_map, dtype=np.uint8)
    for tile_type, terrain_name in DEFAULT_TERRAIN_FOR_TILE.items():
        mask = tile_map == tile_type
        terrain[mask] = TERRAIN_PALETTE_INDEX[terrain_name]
    return terrain


def auto_height(tile_map: np.ndarray) -> np.ndarray:
    """从 tile_map 自动生成高度图: 陆地平原 + 高斯模糊 + 陆海分明."""
    from scipy.ndimage import gaussian_filter

    hm = np.full((MAP_HEIGHT, MAP_WIDTH), OCEAN_HEIGHT, dtype=np.float32)

    land_mask = tile_map == TILE_LAND
    lake_mask = tile_map == TILE_LAKE
    sea_mask = tile_map == TILE_SEA

    hm[land_mask] = LAND_BASE_HEIGHT
    hm[lake_mask] = SEA_LEVEL - 5

    hm = gaussian_filter(hm, sigma=8)

    hm[sea_mask] = np.minimum(hm[sea_mask], SEA_LEVEL - 1)
    hm[land_mask] = np.maximum(hm[land_mask], SEA_LEVEL + 1)

    # HOI4 要求顶底行高度接近海平面（vanilla 顶底行 ~89），否则加载崩溃
    hm[0, :] = np.minimum(hm[0, :], SEA_LEVEL)
    hm[-1, :] = np.minimum(hm[-1, :], SEA_LEVEL)

    return np.clip(hm, 0, 255).astype(np.uint8)


def smooth_height(height_map: np.ndarray, sigma: float = 4.0) -> np.ndarray:
    """高斯平滑现有 heightmap."""
    from scipy.ndimage import gaussian_filter
    hm = height_map.astype(np.float32)
    hm = gaussian_filter(hm, sigma=sigma)
    return np.clip(hm, 0, 255).astype(np.uint8)
