"""
海岸线平滑 — 在 tile_map 上平滑陆海边界

算法参考 Azgaar Fantasy Map Generator 的海岸线处理:
1. 提取陆海边界像素
2. 对 tile_map 做高斯模糊
3. 用阈值重新二值化（陆/海）
4. 保持湖泊不变

效果：锯齿状海岸线变成自然弧线。
应在生成省份之前使用，这样省份边界自然跟随平滑后的海岸线。
"""
import numpy as np
from scipy.ndimage import gaussian_filter

from data.constants import TILE_LAND, TILE_SEA, TILE_LAKE


def smooth_coastline(
    tile_map: np.ndarray,
    strength: float = 2.0,
) -> np.ndarray:
    """平滑 tile_map 的陆海边界。

    参数:
        tile_map: (H, W) uint8, TILE_LAND/SEA/LAKE
        strength: 平滑强度（高斯 sigma），越大越平滑

    返回:
        新的 tile_map（不修改原数组）
    """
    result = tile_map.copy()

    # 保存湖泊位置（不参与平滑）
    lake_mask = tile_map == TILE_LAKE

    # 陆地二值图：陆地=1，其余=0
    land_float = (tile_map == TILE_LAND).astype(np.float32)

    # 高斯模糊
    blurred = gaussian_filter(land_float, sigma=strength)

    # 阈值化：> 0.5 → 陆地，否则海洋
    new_land = blurred > 0.5

    # 应用
    result[new_land] = TILE_LAND
    result[~new_land] = TILE_SEA

    # 恢复湖泊
    result[lake_mask] = TILE_LAKE

    return result
