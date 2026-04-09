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

    # 后处理：修复不连续省份（所有省份都跑，避免碎片占用 65536 边界配额）
    _fix_non_contiguous_fast(province_map)

    # 合并碎片会改变像素，可能产生新的 X-crossings，再修一轮
    for _ in range(5):
        if fix_x_crossings(province_map) == 0:
            break

    # 后处理：压实 ID（消灭 gap）
    # 关键：碎片合并后某些 ID 可能完全消失，必须重新编号成 1..N 连续
    # 否则 definition.csv 会出现空洞 ID，触发"Province X has no pixels"错误，
    # 并导致所有后续省份属性串位（HOI4 文档明确警告的灾难性 bug）
    province_count = compact_province_ids(province_map)
    return province_map, province_count


def auto_classify_water(tile_map: np.ndarray) -> int:
    """
    自动把"被陆地包围的 sea 像素"转换成 lake。
    规则：找到 sea 像素的所有连通分量，最大的保留为 sea（主洋），
    其余全部转为 lake（内陆水域）。

    考虑横向 wrap：地图东西连接，所以 wrap 处的连通也算上。
    返回转换的像素数。
    """
    from scipy.ndimage import label

    sea_mask = tile_map == TILE_SEA
    if not sea_mask.any():
        return 0

    # 4 连通标记
    struct = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int32)
    labeled, n_comps = label(sea_mask, structure=struct)
    if n_comps <= 1:
        return 0

    # 处理横向 wrap：把最左列和最右列上同行 sea 的连通分量合并
    # 用 union-find 思路：找出哪些 label 通过 wrap 连接
    parent = list(range(n_comps + 1))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    left_col = labeled[:, 0]
    right_col = labeled[:, -1]
    for y in range(tile_map.shape[0]):
        l = left_col[y]
        r = right_col[y]
        if l > 0 and r > 0:
            union(int(l), int(r))

    # 重映射到根 label
    root_map = np.zeros(n_comps + 1, dtype=np.int32)
    for i in range(1, n_comps + 1):
        root_map[i] = find(i)
    merged = root_map[labeled]

    # 找最大根连通分量
    counts = np.bincount(merged.ravel())
    counts[0] = 0  # 排除背景
    main_root = int(counts.argmax())

    # 把非主根的 sea 像素改成 lake
    to_lake = sea_mask & (merged != main_root)
    converted = int(to_lake.sum())
    if converted > 0:
        tile_map[to_lake] = TILE_LAKE
    return converted


def compact_province_ids(province_map: np.ndarray) -> int:
    """
    将 province_map 中的 ID 压实成 1..N 连续整数（消除 gap）。
    原地修改。返回压实后的省份总数。

    使用 np.unique 的 inverse 索引一次性向量化重映射。
    """
    unique_ids = np.unique(province_map)
    # 第 0 个一定是 0（背景），保持为 0
    if unique_ids[0] != 0:
        # 没有 0 背景的情况：所有 ID 整体偏移
        new_ids = np.arange(1, len(unique_ids) + 1, dtype=np.int32)
        mapping = dict(zip(unique_ids.tolist(), new_ids.tolist()))
    else:
        # 0 → 0，其他 → 1..N 连续
        new_ids = np.zeros(len(unique_ids), dtype=np.int32)
        new_ids[1:] = np.arange(1, len(unique_ids), dtype=np.int32)
        mapping = dict(zip(unique_ids.tolist(), new_ids.tolist()))

    # 向量化重映射
    if unique_ids.max() < 1_000_000:
        # 小范围：用 LUT 加速
        lut = np.zeros(unique_ids.max() + 1, dtype=np.int32)
        for old, new in mapping.items():
            lut[old] = new
        province_map[:] = lut[province_map]
    else:
        # 极端范围：用 np.searchsorted
        sorted_old = unique_ids
        idx = np.searchsorted(sorted_old, province_map.ravel())
        province_map[:] = new_ids[idx].reshape(province_map.shape)

    return int(province_map.max())


def _fix_non_contiguous_fast(province_map: np.ndarray) -> None:
    """
    修复不连续省份：所有非主体碎片都合并到邻居。
    HOI4 文档明确：每个不连通碎片单独占用 65536 边界配额，必须清零。
    """
    from scipy.ndimage import label

    unique_ids, counts = np.unique(province_map, return_counts=True)

    for pid, total_count in zip(unique_ids, counts):
        if pid <= 0:
            continue

        mask = province_map == pid
        labeled, num_features = label(mask)
        if num_features <= 1:
            continue

        # 找最大分量保留，其余全部合并到邻居
        comp_counts = np.bincount(labeled.ravel())[1:]
        largest = int(np.argmax(comp_counts)) + 1

        for comp_id in range(1, num_features + 1):
            if comp_id == largest:
                continue

            fragment_mask = labeled == comp_id
            ys, xs = np.where(fragment_mask)

            # 找碎片的邻居 ID
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
