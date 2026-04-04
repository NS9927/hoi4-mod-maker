"""
省份生成器 — Voronoi 算法，全向量化实现
"""
import numpy as np
from scipy.spatial import KDTree

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_LAND, TILE_SEA, TILE_LAKE,
    FORBIDDEN_COLOR, MIN_PROVINCE_PIXELS,
)


def generate_provinces(
    tile_map: np.ndarray,
    target_count: int = 5000,
    land_density_ratio: float = 3.0,
) -> tuple[np.ndarray, int]:
    """
    基于 Voronoi 算法生成省份（向量化，不使用 Python 循环）。
    """
    land_mask = tile_map == TILE_LAND
    sea_mask = tile_map == TILE_SEA
    lake_mask = tile_map == TILE_LAKE

    land_pixels = int(np.sum(land_mask))
    sea_pixels = int(np.sum(sea_mask))
    lake_pixels = int(np.sum(lake_mask))
    total_pixels = land_pixels + sea_pixels + lake_pixels

    if total_pixels == 0:
        raise ValueError("地图上没有任何有效地块（陆地/海洋/湖泊）")

    # 计算各区域省份数量
    land_weight = land_pixels * land_density_ratio
    sea_weight = sea_pixels
    lake_weight = lake_pixels * 0.5
    total_weight = land_weight + sea_weight + lake_weight or 1

    land_count = max(1, int(target_count * land_weight / total_weight)) if land_pixels > 0 else 0
    sea_count = max(1, int(target_count * sea_weight / total_weight)) if sea_pixels > 0 else 0
    lake_count = max(1, int(target_count * lake_weight / total_weight)) if lake_pixels > 0 else 0

    # 撒种子并分配（按类型分别处理）
    province_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.int32)
    next_id = 1

    for mask, count in [(land_mask, land_count), (sea_mask, sea_count), (lake_mask, lake_count)]:
        if count <= 0 or not np.any(mask):
            continue

        pixel_ys, pixel_xs = np.where(mask)
        n_pixels = len(pixel_ys)
        count = min(count, n_pixels)

        # 随机采样种子点
        indices = np.random.choice(n_pixels, size=count, replace=False)
        seed_ys = pixel_ys[indices]
        seed_xs = pixel_xs[indices]
        seed_coords = np.column_stack([seed_ys, seed_xs])

        # KDTree 批量最近邻查询（向量化核心）
        tree = KDTree(seed_coords)
        pixel_coords = np.column_stack([pixel_ys, pixel_xs])
        _, nearest = tree.query(pixel_coords)

        # 向量化 ID 分配（不用 Python for 循环）
        global_ids = np.arange(next_id, next_id + count, dtype=np.int32)
        province_map[pixel_ys, pixel_xs] = global_ids[nearest]
        next_id += count

    # 后处理：修复 X 型交叉（向量化，很快）
    from core.province_validator import fix_x_crossings
    for _ in range(5):
        if fix_x_crossings(province_map) == 0:
            break

    # 后处理：修复不连续省份
    # 只对小省份做连通性检测，大量省份时跳过以保证速度
    if next_id - 1 <= 1000:
        _fix_non_contiguous_fast(province_map)

    province_count = int(province_map.max())
    return province_map, province_count


def _fix_non_contiguous_fast(province_map: np.ndarray) -> None:
    """
    快速修复不连续省份。
    只处理小碎片（<50像素），大碎片跳过以节省时间。
    """
    from scipy.ndimage import label

    unique_ids, counts = np.unique(province_map, return_counts=True)

    for pid, total_count in zip(unique_ids, counts):
        if pid <= 0:
            continue
        # 跳过很大的省份（不太可能有碎片，即使有也不重要）
        if total_count > 50000:
            continue

        mask = province_map == pid
        labeled, num_features = label(mask)
        if num_features <= 1:
            continue

        # 找最大分量
        comp_counts = np.bincount(labeled.ravel())[1:]  # 跳过 0
        largest = int(np.argmax(comp_counts)) + 1

        # 只处理小碎片
        for comp_id in range(1, num_features + 1):
            if comp_id == largest:
                continue
            if comp_counts[comp_id - 1] > 50:
                continue  # 大碎片跳过

            fragment_mask = labeled == comp_id
            ys, xs = np.where(fragment_mask)

            # 向量化找邻居
            all_neighbors = set()
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny = np.clip(ys + dy, 0, MAP_HEIGHT - 1)
                nx = np.clip(xs + dx, 0, MAP_WIDTH - 1)
                neighbor_vals = province_map[ny, nx]
                for nid in np.unique(neighbor_vals):
                    if nid > 0 and nid != pid:
                        all_neighbors.add(int(nid))

            if all_neighbors:
                province_map[ys, xs] = min(all_neighbors)


def generate_province_colors(province_count: int) -> dict[int, tuple[int, int, int]]:
    """为每个省份生成唯一的 RGB 颜色（向量化）。"""
    rng = np.random.default_rng(42)

    # 一次性生成足够多的随机颜色
    max_attempts = province_count * 2
    r = rng.integers(1, 256, size=max_attempts, dtype=np.uint8)
    g = rng.integers(0, 256, size=max_attempts, dtype=np.uint8)
    b = rng.integers(0, 256, size=max_attempts, dtype=np.uint8)

    colors = {}
    used = {(0, 0, 0)}
    idx = 0
    for pid in range(1, province_count + 1):
        while idx < max_attempts:
            color = (int(r[idx]), int(g[idx]), int(b[idx]))
            idx += 1
            if color not in used:
                used.add(color)
                colors[pid] = color
                break
        else:
            # 极端情况：颜色用完了，再随机
            while True:
                color = (int(rng.integers(1, 256)), int(rng.integers(0, 256)), int(rng.integers(0, 256)))
                if color not in used:
                    used.add(color)
                    colors[pid] = color
                    break

    return colors
