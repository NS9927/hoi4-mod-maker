"""
省份生成器 — 泊松盘 + Lloyd 松弛，全向量化实现

算法：
1. 泊松盘采样（均匀间距撒种子）
2. KDTree 最近邻分配像素
3. Lloyd 松弛 2 轮（种子移到质心，重新分配）
4. 后处理：X-crossing 修复 + 连通性修复 + ID 压实
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
    target_count: int = 12000,
    land_density_ratio: float = 15.0,
    sea_scale: float = 0.15,
    lloyd_iterations: int = 2,
) -> tuple[np.ndarray, int]:
    """
    基于泊松盘 + Lloyd 松弛生成省份。

    参数:
        tile_map: (H, W) uint8, TILE_LAND/SEA/LAKE
        target_count: 目标省份总数
        land_density_ratio: 陆地密度权重（vs 海洋 1.0）
        sea_scale: 海洋省份密度系数（0.15 = 海洋只生成 15% 的省份密度）
        lloyd_iterations: Lloyd 松弛迭代次数（0=不松弛，2=推荐）
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

    # 计算各区域省份数量 — 海洋用 sea_scale 压低
    land_weight = land_pixels * land_density_ratio
    sea_weight = sea_pixels * sea_scale
    lake_weight = lake_pixels * 0.3
    total_weight = land_weight + sea_weight + lake_weight or 1

    land_count = max(1, int(target_count * land_weight / total_weight)) if land_pixels > 0 else 0
    sea_count = max(1, int(target_count * sea_weight / total_weight)) if sea_pixels > 0 else 0
    lake_count = max(1, int(target_count * lake_weight / total_weight)) if lake_pixels > 0 else 0

    # 撒种子并分配 — 按连通区域分别处理，防止省份跨海
    from scipy.ndimage import label as _label

    province_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.int32)
    next_id = 1

    tile_types = [
        (land_mask, land_count, lloyd_iterations),   # 陆地跑 Lloyd
        (sea_mask, sea_count, 0),                    # 海洋不跑 Lloyd（种子少，速度OK）
        (lake_mask, lake_count, 0),                  # 湖泊不跑 Lloyd
    ]
    for mask, count, region_lloyd in tile_types:
        if count <= 0 or not np.any(mask):
            continue

        # 把同类型区域拆分成连通分量
        labeled, num_regions = _label(mask)
        if num_regions > 1:
            labeled = _merge_wrap_regions(labeled, mask)
            num_regions = int(labeled.max())
        total_type_pixels = int(np.sum(mask))

        for region_id in range(1, num_regions + 1):
            region_mask = labeled == region_id
            pixel_ys, pixel_xs = np.where(region_mask)
            n_pixels = len(pixel_ys)
            if n_pixels == 0:
                continue

            # 按面积比例分配省份数
            region_count = max(1, int(count * n_pixels / total_type_pixels))
            region_count = min(region_count, n_pixels)

            # 检查是否跨 wrap 边界
            crosses_wrap = (pixel_xs.min() == 0 and pixel_xs.max() >= MAP_WIDTH - 1)

            # 泊松盘采样种子（均匀间距）
            seed_ys, seed_xs = _poisson_disk_sample(
                pixel_ys, pixel_xs, region_count, n_pixels
            )
            actual_count = len(seed_ys)

            # KDTree 分配 + Lloyd 松弛
            for lloyd_iter in range(region_lloyd + 1):
                if crosses_wrap:
                    seed_coords = np.column_stack([
                        np.tile(seed_ys, 3),
                        np.concatenate([seed_xs, seed_xs - MAP_WIDTH, seed_xs + MAP_WIDTH]),
                    ])
                    tree = KDTree(seed_coords)
                    pixel_coords = np.column_stack([pixel_ys, pixel_xs])
                    _, nearest = tree.query(pixel_coords)
                    nearest = nearest % actual_count
                else:
                    seed_coords = np.column_stack([seed_ys, seed_xs])
                    tree = KDTree(seed_coords)
                    pixel_coords = np.column_stack([pixel_ys, pixel_xs])
                    _, nearest = tree.query(pixel_coords)

                # Lloyd 松弛：把种子移到各自区域的质心（向量化）
                if lloyd_iter < region_lloyd:
                    # bincount 求每个种子的像素数和坐标总和
                    counts = np.bincount(nearest, minlength=actual_count).astype(np.float64)
                    sum_y = np.bincount(nearest, weights=pixel_ys.astype(np.float64), minlength=actual_count)
                    sum_x = np.bincount(nearest, weights=pixel_xs.astype(np.float64), minlength=actual_count)
                    # 避免除零
                    safe_counts = np.maximum(counts, 1.0)
                    new_sy = np.where(counts > 0, sum_y / safe_counts, seed_ys.astype(np.float64))
                    new_sx = np.where(counts > 0, sum_x / safe_counts, seed_xs.astype(np.float64))
                    seed_ys = new_sy.astype(np.int32)
                    seed_xs = new_sx.astype(np.int32)

            # 向量化 ID 分配
            global_ids = np.arange(next_id, next_id + actual_count, dtype=np.int32)
            province_map[pixel_ys, pixel_xs] = global_ids[nearest]
            next_id += actual_count

    # 后处理：修复 X 型交叉
    from domain.validators.province import fix_x_crossings
    for _ in range(5):
        if fix_x_crossings(province_map) == 0:
            break

    # 后处理：修复不连续省份
    _fix_non_contiguous_fast(province_map)

    # 再修一轮 X-crossings
    for _ in range(5):
        if fix_x_crossings(province_map) == 0:
            break

    # 压实 ID
    province_count = compact_province_ids(province_map)
    return province_map, province_count


def _poisson_disk_sample(
    pixel_ys: np.ndarray,
    pixel_xs: np.ndarray,
    target_count: int,
    n_pixels: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    泊松盘采样：在给定像素集合中均匀间距放置种子。

    近似算法：把像素区域划分成网格，每个格子随机选一个像素作为种子。
    比纯随机均匀得多，比精确泊松盘快得多。
    """
    if target_count >= n_pixels:
        return pixel_ys.copy(), pixel_xs.copy()

    if target_count <= 10:
        # 太少了直接随机
        indices = np.random.choice(n_pixels, size=target_count, replace=False)
        return pixel_ys[indices], pixel_xs[indices]

    # 计算网格间距
    y_min, y_max = pixel_ys.min(), pixel_ys.max()
    x_min, x_max = pixel_xs.min(), pixel_xs.max()
    area = n_pixels
    cell_size = max(1, int(np.sqrt(area / target_count)))

    # 划分网格
    grid_rows = max(1, (y_max - y_min + 1) // cell_size)
    grid_cols = max(1, (x_max - x_min + 1) // cell_size)

    # 把像素分到网格
    cell_y = np.clip((pixel_ys - y_min) // cell_size, 0, grid_rows - 1)
    cell_x = np.clip((pixel_xs - x_min) // cell_size, 0, grid_cols - 1)
    cell_id = cell_y * grid_cols + cell_x

    # 每个有像素的格子随机选一个种子
    unique_cells = np.unique(cell_id)
    seed_ys_list = []
    seed_xs_list = []

    for cid in unique_cells:
        cell_mask = cell_id == cid
        cell_indices = np.where(cell_mask)[0]
        chosen = np.random.choice(cell_indices)
        seed_ys_list.append(pixel_ys[chosen])
        seed_xs_list.append(pixel_xs[chosen])

    result_ys = np.array(seed_ys_list, dtype=np.int32)
    result_xs = np.array(seed_xs_list, dtype=np.int32)

    # 如果网格产生的种子太多，随机裁剪到目标数
    if len(result_ys) > target_count:
        indices = np.random.choice(len(result_ys), size=target_count, replace=False)
        result_ys = result_ys[indices]
        result_xs = result_xs[indices]
    # 如果太少（区域形状不规则），补充随机种子
    elif len(result_ys) < target_count:
        deficit = target_count - len(result_ys)
        extra = np.random.choice(n_pixels, size=min(deficit, n_pixels), replace=False)
        result_ys = np.concatenate([result_ys, pixel_ys[extra[:deficit]]])
        result_xs = np.concatenate([result_xs, pixel_xs[extra[:deficit]]])

    return result_ys, result_xs


def _merge_wrap_regions(labeled: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """合并横向 wrap 连通的区域（左边缘 x=0 与右边缘 x=W-1 同行相连）。"""
    H, W = labeled.shape

    # union-find
    max_label = int(labeled.max())
    parent = list(range(max_label + 1))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # 左右边缘同行都有像素 → 合并它们的 label
    left_col = labeled[:, 0]
    right_col = labeled[:, -1]
    for y in range(H):
        l, r = int(left_col[y]), int(right_col[y])
        if l > 0 and r > 0:
            union(l, r)

    # 重映射到根 label，压实成 1..N
    root_map = np.array([find(i) for i in range(max_label + 1)], dtype=np.int32)
    unique_roots = np.unique(root_map[1:])  # 排除 0
    compact = np.zeros(max_label + 1, dtype=np.int32)
    for new_id, root in enumerate(unique_roots, 1):
        for old_id in range(1, max_label + 1):
            if root_map[old_id] == root:
                compact[old_id] = new_id

    return compact[labeled]


def _fix_non_contiguous_fast(province_map: np.ndarray) -> None:
    """
    修复不连续省份：所有非主体碎片都合并到邻居。

    优化：先用 argsort 一次性分组，bbox+填充率快速跳过连通省份。
    """
    from scipy.ndimage import label

    H, W = province_map.shape

    unique_ids = np.unique(province_map)
    unique_ids = unique_ids[unique_ids > 0]

    # 一次性按省份 ID 分组坐标
    flat = province_map.ravel()
    order = np.argsort(flat, kind='stable')
    sorted_ids = flat[order]
    change = np.where(np.diff(sorted_ids) != 0)[0] + 1
    splits = np.split(order, change)
    split_ids = sorted_ids[np.concatenate([[0], change])]

    pid_to_bbox: dict[int, tuple] = {}
    for sid, group in zip(split_ids, splits):
        if sid <= 0:
            continue
        pys, pxs = np.divmod(group, W)
        pid_to_bbox[int(sid)] = (pys, pxs, int(pys.min()), int(pys.max()) + 1,
                                  int(pxs.min()), int(pxs.max()) + 1, len(group))

    for pid, (ys, xs, y0, y1, x0, x1, pixel_count) in pid_to_bbox.items():
        bbox_area = (y1 - y0) * (x1 - x0)
        # 填充率 > 30% 且 bbox < 10000 → 几乎肯定连通，跳过
        if bbox_area < 10000 or pixel_count > 0.3 * bbox_area:
            continue

        # 只对可疑省份做 label（bbox 子区域内）
        mask = province_map == pid
        sub_mask = mask[y0:y1, x0:x1]
        labeled, num_features = label(sub_mask)
        if num_features <= 1:
            continue

        comp_counts = np.bincount(labeled.ravel())[1:]
        largest = int(np.argmax(comp_counts)) + 1

        for comp_id in range(1, num_features + 1):
            if comp_id == largest:
                continue

            frag_local = labeled == comp_id
            frag_ys, frag_xs = np.where(frag_local)
            frag_ys = frag_ys + y0
            frag_xs = frag_xs + x0

            all_neighbors = set()
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny = np.clip(frag_ys + dy, 0, H - 1)
                nx = np.clip(frag_xs + dx, 0, W - 1)
                neighbor_vals = province_map[ny, nx]
                for nid in np.unique(neighbor_vals):
                    if nid > 0 and nid != pid:
                        all_neighbors.add(int(nid))

            if all_neighbors:
                province_map[frag_ys, frag_xs] = min(all_neighbors)


def auto_classify_water(tile_map: np.ndarray) -> int:
    """
    自动把"被陆地包围的 sea 像素"转换成 lake。
    最大连通分量保留为 sea，其余转为 lake。考虑横向 wrap。
    """
    from scipy.ndimage import label

    sea_mask = tile_map == TILE_SEA
    if not sea_mask.any():
        return 0

    struct = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int32)
    labeled, n_comps = label(sea_mask, structure=struct)
    if n_comps <= 1:
        return 0

    # 横向 wrap union-find
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

    root_map = np.zeros(n_comps + 1, dtype=np.int32)
    for i in range(1, n_comps + 1):
        root_map[i] = find(i)
    merged = root_map[labeled]

    counts = np.bincount(merged.ravel())
    counts[0] = 0
    main_root = int(counts.argmax())

    to_lake = sea_mask & (merged != main_root)
    converted = int(to_lake.sum())
    if converted > 0:
        tile_map[to_lake] = TILE_LAKE
    return converted


def compact_province_ids(province_map: np.ndarray) -> int:
    """将 province_map 中的 ID 压实成 1..N 连续整数。"""
    unique_ids = np.unique(province_map)
    if unique_ids[0] != 0:
        new_ids = np.arange(1, len(unique_ids) + 1, dtype=np.int32)
        mapping = dict(zip(unique_ids.tolist(), new_ids.tolist()))
    else:
        new_ids = np.zeros(len(unique_ids), dtype=np.int32)
        new_ids[1:] = np.arange(1, len(unique_ids), dtype=np.int32)
        mapping = dict(zip(unique_ids.tolist(), new_ids.tolist()))

    if unique_ids.max() < 1_000_000:
        lut = np.zeros(unique_ids.max() + 1, dtype=np.int32)
        for old, new in mapping.items():
            lut[old] = new
        province_map[:] = lut[province_map]
    else:
        sorted_old = unique_ids
        idx = np.searchsorted(sorted_old, province_map.ravel())
        province_map[:] = new_ids[idx].reshape(province_map.shape)

    return int(province_map.max())


def generate_provinces_incremental(
    tile_map: np.ndarray,
    province_map: np.ndarray,
    target_density: float | None = None,
    lloyd_iterations: int = 2,
) -> tuple[np.ndarray, int]:
    """
    增量省份生成：只为未分配省份的新区域生成省份，保留已有省份不变。

    参数:
        tile_map: (H, W) uint8, TILE_LAND/SEA/LAKE
        province_map: (H, W) int32, 已有省份 (>0 的不动)
        target_density: 每个省份的平均像素数（默认 = 总像素 / 12000）
        lloyd_iterations: Lloyd 松弛迭代次数
    返回:
        (更新后的 province_map, 总省份数)
    """
    from scipy.ndimage import label as _label

    H, W = tile_map.shape
    result = province_map.copy()
    next_id = int(result.max()) + 1

    if target_density is None:
        target_density = max(1.0, (H * W) / 12000.0)

    # 找出需要分配省份的像素：有地块类型但没省份
    unassigned_land = (tile_map == TILE_LAND) & (result == 0)
    unassigned_sea = (tile_map == TILE_SEA) & (result == 0)
    unassigned_lake = (tile_map == TILE_LAKE) & (result == 0)

    # 所有类型都用 KDTree（海洋/湖泊不跑 Lloyd）
    incremental_types = [
        (unassigned_land, 1.0, lloyd_iterations),   # 陆地跑 Lloyd
        (unassigned_sea, 4.0, 0),                   # 海洋不跑 Lloyd，密度低
        (unassigned_lake, 3.0, 0),                  # 湖泊不跑 Lloyd
    ]
    for inc_mask, density_scale, inc_lloyd in incremental_types:
        n_total = int(np.sum(inc_mask))
        if n_total == 0:
            continue
        type_target = max(1, int(n_total / (target_density * density_scale)))

        # 拆分成连通分量
        labeled, num_regions = _label(inc_mask)
        if num_regions > 1:
            labeled = _merge_wrap_regions(labeled, inc_mask)
            num_regions = int(labeled.max())

        for region_id in range(1, num_regions + 1):
            region_mask = labeled == region_id
            pixel_ys, pixel_xs = np.where(region_mask)
            n_pixels = len(pixel_ys)
            if n_pixels == 0:
                continue

            region_count = max(1, int(type_target * n_pixels / n_total))
            region_count = min(region_count, n_pixels)

            crosses_wrap = (pixel_xs.min() == 0 and pixel_xs.max() >= W - 1)

            seed_ys, seed_xs = _poisson_disk_sample(
                pixel_ys, pixel_xs, region_count, n_pixels
            )
            actual_count = len(seed_ys)

            for lloyd_iter in range(inc_lloyd + 1):
                if crosses_wrap:
                    seed_coords = np.column_stack([
                        np.tile(seed_ys, 3),
                        np.concatenate([seed_xs, seed_xs - W, seed_xs + W]),
                    ])
                    tree = KDTree(seed_coords)
                    pixel_coords = np.column_stack([pixel_ys, pixel_xs])
                    _, nearest = tree.query(pixel_coords)
                    nearest = nearest % actual_count
                else:
                    seed_coords = np.column_stack([seed_ys, seed_xs])
                    tree = KDTree(seed_coords)
                    pixel_coords = np.column_stack([pixel_ys, pixel_xs])
                    _, nearest = tree.query(pixel_coords)

                if lloyd_iter < inc_lloyd:
                    counts = np.bincount(nearest, minlength=actual_count).astype(np.float64)
                    sum_y = np.bincount(nearest, weights=pixel_ys.astype(np.float64), minlength=actual_count)
                    sum_x = np.bincount(nearest, weights=pixel_xs.astype(np.float64), minlength=actual_count)
                    safe_counts = np.maximum(counts, 1.0)
                    new_sy = np.where(counts > 0, sum_y / safe_counts, seed_ys.astype(np.float64))
                    new_sx = np.where(counts > 0, sum_x / safe_counts, seed_xs.astype(np.float64))
                    seed_ys = new_sy.astype(np.int32)
                    seed_xs = new_sx.astype(np.int32)

            global_ids = np.arange(next_id, next_id + actual_count, dtype=np.int32)
            result[pixel_ys, pixel_xs] = global_ids[nearest]
            next_id += actual_count

    # 后处理：修复 X 型交叉（只处理新区域附近）
    from domain.validators.province import fix_x_crossings
    for _ in range(5):
        if fix_x_crossings(result) == 0:
            break

    # 修复不连续省份
    _fix_non_contiguous_fast(result)

    for _ in range(5):
        if fix_x_crossings(result) == 0:
            break

    # 压实 ID
    province_count = compact_province_ids(result)
    return result, province_count


def generate_province_colors(province_count: int) -> dict[int, tuple[int, int, int]]:
    """为每个省份生成唯一的 RGB 颜色。"""
    rng = np.random.default_rng(42)

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
            while True:
                color = (int(rng.integers(1, 256)), int(rng.integers(0, 256)), int(rng.integers(0, 256)))
                if color not in used:
                    used.add(color)
                    colors[pid] = color
                    break

    return colors
