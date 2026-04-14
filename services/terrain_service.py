"""
地形 / 高度自动生成服务.

从 tile_map (陆/海/湖) 自动生成 terrain_map 和 height_map.
smart_auto_terrain: 基于高度图 + Perlin 噪声的智能地形生成.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_LAND, TILE_LAKE, TILE_SEA,
    OCEAN_HEIGHT, LAND_BASE_HEIGHT, SEA_LEVEL,
)
from data.terrain_types import (
    DEFAULT_TERRAIN_FOR_TILE, TERRAIN_PALETTE_INDEX,
    PAINTABLE_GROUPS,
)


def auto_terrain(tile_map: np.ndarray) -> np.ndarray:
    """按 tile_map 默认规则生成 terrain_map (旧版简单映射)."""
    terrain = np.zeros_like(tile_map, dtype=np.uint8)
    for tile_type, terrain_name in DEFAULT_TERRAIN_FOR_TILE.items():
        mask = tile_map == tile_type
        terrain[mask] = TERRAIN_PALETTE_INDEX[terrain_name]
    return terrain


# ── 智能地形生成 ─────────────────────────────────────────

@dataclass(frozen=True)
class TerrainGenConfig:
    """智能地形生成参数 — UI 暴露给用户调节。"""
    # 高度阈值 (对应 heightmap 0-255)
    plains_max: int = 115       # 低于此 → 平原/森林
    hills_min: int = 130        # 高于此 → 丘陵
    mountain_min: int = 165     # 高于此 → 山地
    snow_min: int = 210         # 高于此 → 雪山

    # 森林: 平原区域中一部分变森林
    forest_noise_threshold: float = 0.1   # 噪声 > 此值 → 森林 (越低森林越多)

    # 沙漠: 纬度带 + 低海拔
    desert_band_y_min: float = 0.20   # 纬度上界 (地图 y 比例)
    desert_band_y_max: float = 0.80   # 纬度下界
    desert_noise_threshold: float = 0.15  # 噪声 > 此值 → 沙漠

    # 丛林: 赤道附近的森林区
    jungle_band_y_min: float = 0.35
    jungle_band_y_max: float = 0.65
    jungle_probability: float = 0.5   # 赤道森林变丛林的概率

    # 噪声参数
    noise_scale: float = 80.0        # 边界扰动尺度
    noise_amplitude: float = 20.0    # 高度偏移量 (像素)
    scatter_scale: float = 12.0      # 散点尺度 (越小越碎)
    scatter_strength: float = 0.65   # 散点阈值 (越低越多斑点)

    # 种子
    seed: int = 42


def smart_auto_terrain(
    height_map: np.ndarray,
    tile_map: np.ndarray,
    config: TerrainGenConfig | None = None,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """基于高度图 + Perlin 噪声的智能地形生成。

    Parameters
    ----------
    height_map : uint8 高度图
    tile_map : uint8 地块类型图 (TILE_LAND/SEA/LAKE)
    config : 生成参数，None 时用默认值
    mask : bool 数组，只生成 mask==True 的区域 (局部重塑用)

    Returns
    -------
    terrain_map : uint8 地形索引图
    """
    from domain.noise import perlin_2d

    if config is None:
        config = TerrainGenConfig()

    h, w = height_map.shape
    terrain = np.full((h, w), 15, dtype=np.uint8)  # 默认海洋

    # 1. 生成噪声层 (降采样加速)
    ds = 4 if h > 1024 else 1
    boundary_noise = perlin_2d((h, w), scale=config.noise_scale,
                               octaves=4, seed=config.seed, downsample=ds)
    forest_noise = perlin_2d((h, w), scale=config.noise_scale * 0.7,
                             octaves=3, seed=config.seed + 100, downsample=ds)
    desert_noise = perlin_2d((h, w), scale=config.noise_scale * 0.6,
                             octaves=3, seed=config.seed + 200, downsample=ds)
    scatter_noise = perlin_2d((h, w), scale=config.scatter_scale,
                              octaves=2, seed=config.seed + 300, downsample=ds)
    variant_noise = perlin_2d((h, w), scale=config.scatter_scale * 2,
                              octaves=2, seed=config.seed + 400, downsample=ds)

    # 2. 扰动高度 (Perlin 偏移让边界有机化)
    perturbed = height_map.astype(np.float32) + boundary_noise * config.noise_amplitude

    # 3. 基础分层
    land = tile_map == TILE_LAND
    lake = tile_map == TILE_LAKE
    sea = tile_map == TILE_SEA

    # 纬度参数
    y_ratio = np.linspace(0, 1, h, dtype=np.float32)[:, None]  # (h, 1)

    # 平原层
    is_low = perturbed < config.plains_max
    plains_mask = land & is_low

    # 森林: 平原中噪声较高的区域
    is_forest = plains_mask & (forest_noise > config.forest_noise_threshold)
    is_plains = plains_mask & ~is_forest

    # 丛林: 赤道附近的森林
    in_jungle_band = (y_ratio >= config.jungle_band_y_min) & (y_ratio <= config.jungle_band_y_max)
    jungle_prob_mask = (variant_noise + 1) / 2 < config.jungle_probability  # 归一化到[0,1]
    is_jungle = is_forest & in_jungle_band & jungle_prob_mask
    is_forest = is_forest & ~is_jungle

    # 沙漠: 非赤道、低海拔、噪声匹配
    in_desert_band = (y_ratio < config.desert_band_y_min) | (y_ratio > config.desert_band_y_max)
    is_desert = is_plains & in_desert_band & (desert_noise > config.desert_noise_threshold)
    is_plains = is_plains & ~is_desert

    # 丘陵层
    is_mid = (perturbed >= config.plains_max) & (perturbed < config.mountain_min)
    is_hills = land & is_mid

    # 山地层
    is_high = (perturbed >= config.mountain_min) & (perturbed < config.snow_min)
    is_mountain = land & is_high

    # 雪山层
    is_snow = land & (perturbed >= config.snow_min)

    # 沼泽: 低海拔 + 特定噪声区域 (少量点缀)
    is_marsh = is_plains & (scatter_noise > 0.7) & (perturbed < config.plains_max - 10)
    is_plains = is_plains & ~is_marsh

    # 4. 分配基础 palette index
    terrain[is_plains] = 0     # plains terrain_0
    terrain[is_forest] = 1     # forest terrain_1
    terrain[is_jungle] = 21    # jungle_18
    terrain[is_desert] = 3     # desert
    terrain[is_hills] = 17     # hills_blend
    terrain[is_mountain] = 6   # mountain terrain_6
    terrain[is_snow] = 16      # snow_16
    terrain[is_marsh] = 9      # marsh terrain_9
    terrain[lake] = 14         # lakes
    terrain[sea] = 15          # ocean

    # 5. 图形变体散布 (制造斑点效果)
    _apply_variants(terrain, scatter_noise, variant_noise, config, land)

    # 6. 海/湖保护 (最后一步，确保绝对不被覆盖)
    terrain[sea] = 15
    terrain[lake] = 14

    # 7. 如果有 mask，只返回 mask 区域
    if mask is not None:
        return terrain, mask

    return terrain


def _apply_variants(
    terrain: np.ndarray,
    scatter: np.ndarray,
    variant: np.ndarray,
    config: TerrainGenConfig,
    land: np.ndarray,
) -> None:
    """在大区域内撒不同图形变体的散点，制造自然斑点效果。"""
    threshold = config.scatter_strength

    # 森林区域撒森林变体 (index 4)
    forest_mask = (terrain == 1) & (scatter > threshold)
    terrain[forest_mask] = 4  # terrain_4 (森林变体)

    # 平原区域撒平原变体 (index 5)
    plains_mask = (terrain == 0) & (scatter < -threshold)
    terrain[plains_mask] = 5  # terrain_5 (平原变体)

    # 山地区域撒变体
    mt_mask = terrain == 6
    # 用 variant_noise 分配不同山地变体
    terrain[mt_mask & (variant > 0.3)] = 10   # terrain_10
    terrain[mt_mask & (variant > 0.5)] = 20   # mountain_variation_grass
    terrain[mt_mask & (variant < -0.3)] = 11  # desert_mountain_11

    # 沙漠区域撒变体
    desert_mask = terrain == 3
    terrain[desert_mask & (scatter > threshold)] = 7    # terrain_7
    terrain[desert_mask & (scatter < -threshold)] = 12  # desert_12
    terrain[desert_mask & (variant > 0.4)] = 8          # desert_hills

    # 丘陵区域部分变沙漠丘陵
    hills_mask = terrain == 17
    terrain[hills_mask & (variant < -0.5)] = 2   # desert_mountain (hills variant)

    # 丛林区域撒变体
    jungle_mask = terrain == 21
    terrain[jungle_mask & (scatter > threshold)] = 22  # jungle_blend

    # 雪山区域部分变草地山
    snow_edge = (terrain == 16) & (variant > 0.3) & (scatter < 0)
    terrain[snow_edge] = 19  # plains_snow


@dataclass(frozen=True)
class HeightGenConfig:
    """高度图生成参数。"""
    # 基础高度
    coast_height: int = 97      # 海岸线基础高度 (刚过海平面95)
    inland_max: int = 130       # 内陆最高基础值 (距离场上限)
    # 距离场
    distance_power: float = 0.35 # 距海岸距离的幂次
    distance_scale: float = 250.0 # 距离归一化尺度 (像素)
    # 噪声 — 制造山脉和谷地
    noise_scale: float = 200.0   # 大尺度噪声 (山脉走向)
    noise_amplitude: float = 200.0 # 噪声最大高度偏移 (实际约±100)
    detail_scale: float = 50.0   # 小尺度噪声 (地形细节)
    detail_amplitude: float = 35.0
    # 平滑
    smooth_sigma: float = 3.0    # 最终高斯平滑 (小值保留山峰)
    # 种子
    seed: int = 42


def smart_auto_height(
    tile_map: np.ndarray,
    config: HeightGenConfig | None = None,
) -> np.ndarray:
    """智能高度图生成: 海岸距离场 + Perlin 噪声山脉 + 平滑。

    生成自然的高度起伏: 海岸低、内陆高、有山脉和谷地。
    """
    from scipy.ndimage import gaussian_filter, distance_transform_edt
    from domain.noise import perlin_2d

    if config is None:
        config = HeightGenConfig()

    h, w = tile_map.shape
    land = tile_map == TILE_LAND
    lake = tile_map == TILE_LAKE
    sea = (tile_map == TILE_SEA) | (tile_map == 0)

    # 1. 计算到海岸的距离场 (陆地像素到最近海洋的距离)
    coast_dist = distance_transform_edt(land).astype(np.float32)
    # 归一化: 0(海岸) → 1(内陆深处)
    max_dist = max(config.distance_scale, 1.0)
    dist_norm = np.clip(coast_dist / max_dist, 0, 1)
    # 幂次映射: 让海岸附近快速升高
    dist_factor = np.power(dist_norm, config.distance_power)

    # 2. 基础高度: 海岸 → 内陆渐变 (先平滑，保留大轮廓)
    base = config.coast_height + dist_factor * (config.inland_max - config.coast_height)
    base = gaussian_filter(base, sigma=config.smooth_sigma)

    # 3. Perlin 噪声叠加 (大尺度=山脉, 小尺度=细节)
    #    加在平滑后面，这样噪声不会被削掉
    ds = 4 if h > 1024 else 1
    mountain_noise = perlin_2d((h, w), scale=config.noise_scale,
                               octaves=4, seed=config.seed, downsample=ds)
    detail_noise = perlin_2d((h, w), scale=config.detail_scale,
                             octaves=3, seed=config.seed + 500, downsample=ds)

    hm = base + mountain_noise * config.noise_amplitude + detail_noise * config.detail_amplitude

    # 4. 轻微平滑噪声边缘 (sigma=2 只磨毛刺，不削山峰)
    hm = gaussian_filter(hm, sigma=2.0)

    # 5. 强制约束
    hm[sea] = OCEAN_HEIGHT
    hm[lake] = SEA_LEVEL - 5
    hm[land] = np.maximum(hm[land], SEA_LEVEL + 1)  # 陆地不低于海平面

    # HOI4 要求顶底行高度接近海平面
    hm[0, :] = np.minimum(hm[0, :], SEA_LEVEL)
    hm[-1, :] = np.minimum(hm[-1, :], SEA_LEVEL)

    return np.clip(hm, 0, 255).astype(np.uint8)


def auto_height(tile_map: np.ndarray) -> np.ndarray:
    """从 tile_map 自动生成高度图 (调用智能版本)."""
    return smart_auto_height(tile_map)


def smooth_height(height_map: np.ndarray, sigma: float = 4.0) -> np.ndarray:
    """高斯平滑现有 heightmap."""
    from scipy.ndimage import gaussian_filter
    hm = height_map.astype(np.float32)
    hm = gaussian_filter(hm, sigma=sigma)
    return np.clip(hm, 0, 255).astype(np.uint8)
