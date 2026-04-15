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
    lake_scale: float = 0.3,
    lloyd_iterations: int = 2,
    density_map: np.ndarray | None = None,
) -> tuple[np.ndarray, int]:
    """
    基于泊松盘 + Lloyd 松弛生成省份。

    参数:
        tile_map: (H, W) uint8, TILE_LAND/SEA/LAKE
        target_count: 目标省份总数
        land_density_ratio: 陆地密度权重（vs 海洋 1.0）
        sea_scale: 海洋省份密度系数（0.15 = 海洋只生成 15% 的省份密度）
        lake_scale: 湖泊省份密度系数（0.3 = 湖泊是陆地的 30% 密度）
        lloyd_iterations: Lloyd 松弛迭代次数（0=不松弛，2=推荐）
        density_map: (H, W) float32, 0.0~1.0 密度图（1=密集，0=稀疏），None=均匀
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
    lake_weight = lake_pixels * lake_scale
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

            # 泊松盘采样种子（支持密度图）
            seed_ys, seed_xs = _poisson_disk_sample(
                pixel_ys, pixel_xs, region_count, n_pixels,
                density_map=density_map,
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

    # 清理过小省份（< 8 像素）→ 合并到最大邻居，循环直到全部清除
    for _ in range(10):
        merged = _merge_tiny_provinces(province_map, min_pixels=MIN_PROVINCE_PIXELS)
        if merged == 0:
            break

    # 压实 ID
    province_count = compact_province_ids(province_map)
    return province_map, province_count


def _poisson_disk_sample(
    pixel_ys: np.ndarray,
    pixel_xs: np.ndarray,
    target_count: int,
    n_pixels: int,
    density_map: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    泊松盘采样：在给定像素集合中放置种子。

    近似算法：把像素区域划分成网格，每个格子根据密度决定是否放种子。
    density_map 为 None 时退化为均匀采样。

    density_map: (H, W) float32, 0.0=稀疏 ~ 1.0=密集
    """
    if target_count >= n_pixels:
        return pixel_ys.copy(), pixel_xs.copy()

    if target_count <= 10:
        indices = np.random.choice(n_pixels, size=target_count, replace=False)
        return pixel_ys[indices], pixel_xs[indices]

    # 计算基础网格间距（用最密的间距，密度图控制跳过）
    y_min, y_max = pixel_ys.min(), pixel_ys.max()
    x_min, x_max = pixel_xs.min(), pixel_xs.max()
    area = n_pixels

    if density_map is not None:
        # 用更细的网格（按最大密度），然后概率跳过低密度格子
        # 基础 cell_size 按 target_count * 1.5 估算（多撒一些，后面裁）
        cell_size = max(1, int(np.sqrt(area / (target_count * 1.5))))
    else:
        cell_size = max(1, int(np.sqrt(area / target_count)))

    # 划分网格
    grid_rows = max(1, (y_max - y_min + 1) // cell_size)
    grid_cols = max(1, (x_max - x_min + 1) // cell_size)

    # 把像素分到网格
    cell_y = np.clip((pixel_ys - y_min) // cell_size, 0, grid_rows - 1)
    cell_x = np.clip((pixel_xs - x_min) // cell_size, 0, grid_cols - 1)
    cell_id = cell_y * grid_cols + cell_x

    # 每个有像素的格子决定是否放种子
    unique_cells = np.unique(cell_id)
    seed_ys_list = []
    seed_xs_list = []

    for cid in unique_cells:
        cell_mask = cell_id == cid
        cell_indices = np.where(cell_mask)[0]
        chosen = np.random.choice(cell_indices)
        cy, cx = pixel_ys[chosen], pixel_xs[chosen]

        if density_map is not None:
            # 采样该位置的密度值，概率决定是否放种子
            # density=1.0 → 100% 放，density=0.0 → 基础概率（不完全跳过）
            d = float(density_map[cy, cx])
            prob = 0.1 + 0.9 * d  # 最低 10% 概率，保证不会完全空白
            if np.random.random() > prob:
                continue

        seed_ys_list.append(cy)
        seed_xs_list.append(cx)

    result_ys = np.array(seed_ys_list, dtype=np.int32)
    result_xs = np.array(seed_xs_list, dtype=np.int32)

    # 如果种子太多，随机裁剪到目标数
    if len(result_ys) > target_count:
        indices = np.random.choice(len(result_ys), size=target_count, replace=False)
        result_ys = result_ys[indices]
        result_xs = result_xs[indices]
    # 如果太少，补充随机种子（优先高密度区域）
    elif len(result_ys) < target_count:
        deficit = target_count - len(result_ys)
        if density_map is not None:
            # 按密度值做加权随机采样
            densities = density_map[pixel_ys, pixel_xs].astype(np.float64)
            densities = np.maximum(densities, 0.01)
            probs = densities / densities.sum()
            extra = np.random.choice(n_pixels, size=min(deficit, n_pixels),
                                     replace=False, p=probs)
        else:
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

    # 清理过小省份（< 8 像素）→ 合并到最大邻居，循环直到全部清除
    for _ in range(10):
        merged = _merge_tiny_provinces(result, min_pixels=8)
        if merged == 0:
            break

    # 压实 ID
    province_count = compact_province_ids(result)
    return result, province_count


def _merge_tiny_provinces(province_map: np.ndarray, min_pixels: int = 8) -> int:
    """将像素数 < min_pixels 的省份合并到相邻最大省份。返回合并数量。"""
    flat = province_map.ravel()
    max_pid = int(province_map.max())
    counts = np.bincount(flat, minlength=max_pid + 1)

    tiny_pids = [pid for pid in range(1, max_pid + 1) if 0 < counts[pid] < min_pixels]
    if not tiny_pids:
        return 0

    H, W = province_map.shape
    merged = 0
    for pid in tiny_pids:
        ys, xs = np.where(province_map == pid)
        if len(ys) == 0:
            continue
        # 找所有邻居省份
        neighbors: dict[int, int] = {}
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny = np.clip(ys + dy, 0, H - 1)
            nx = np.clip(xs + dx, 0, W - 1)
            adj_ids = province_map[ny, nx]
            for aid in np.unique(adj_ids):
                aid = int(aid)
                if aid != pid and aid > 0:
                    neighbors[aid] = neighbors.get(aid, 0) + int(np.sum(adj_ids == aid))
        if not neighbors:
            continue
        # 合并到接触面积最大的邻居
        best = max(neighbors, key=neighbors.get)
        province_map[ys, xs] = best
        merged += 1

    return merged


def generate_provinces_in_region(
    province_map: np.ndarray,
    tile_map: np.ndarray,
    region_mask: np.ndarray,
    target_density: float | None = None,
    lloyd_iterations: int = 2,
    state_mgr=None,
    strategic_region_mgr=None,
    country_mgr=None,
) -> tuple[set[int], set[int]]:
    """在 region_mask 区域内重新生成省份，选区外完全不动。

    参数:
        province_map: (H, W) int32, 就地修改
        tile_map: (H, W) uint8
        region_mask: (H, W) bool, True = 选区内需重新生成
        target_density: 每万像素多少省份, None=自动
        lloyd_iterations: Lloyd 松弛迭代次数
        state_mgr/strategic_region_mgr/country_mgr: 可选, 用于清理旧引用

    返回:
        (removed_ids, new_ids) — 被删除的旧省份 ID 集合, 新创建的省份 ID 集合
    """
    H, W = province_map.shape

    if target_density is None:
        # 默认密度：基于当前地图的省份密度
        total_provinces = int(province_map.max())
        total_pixels = H * W
        if total_provinces > 0 and total_pixels > 0:
            target_density = total_provinces / (total_pixels / 10000.0)
        else:
            target_density = 1.3  # ~13000 省份 / 1000万像素

    # 1. 记录选区内被删除的旧省份 ID
    region_pids = np.unique(province_map[region_mask])
    removed_ids = set(int(p) for p in region_pids if p > 0)

    # 检查哪些旧省份被完全删除（选区外没有残留像素）
    fully_removed: set[int] = set()
    for pid in removed_ids:
        outside_pixels = int(np.sum((province_map == pid) & ~region_mask))
        if outside_pixels == 0:
            fully_removed.add(pid)

    # 2. 清除选区内的旧 ID
    province_map[region_mask] = 0

    # 3. 新 ID 从当前最大值 +1 开始
    next_id = int(province_map.max()) + 1

    # 4. 按地块类型分别生成（陆地/海洋/湖泊密度不同）
    from scipy.ndimage import label as _label

    gen_types = [
        (TILE_LAND, 1.0, lloyd_iterations),
        (TILE_SEA, 4.0, 0),
        (TILE_LAKE, 3.0, 0),
    ]

    new_ids: set[int] = set()

    for tile_type, density_scale, n_lloyd in gen_types:
        type_mask = region_mask & (tile_map == tile_type)
        n_pixels = int(np.sum(type_mask))
        if n_pixels == 0:
            continue

        target_count = max(1, int(n_pixels * target_density / (10000.0 * density_scale)))

        # 拆成连通分量（避免跨海生成）
        labeled, num_regions = _label(type_mask)
        for rid in range(1, num_regions + 1):
            comp_mask = labeled == rid
            pys, pxs = np.where(comp_mask)
            n_comp = len(pys)
            if n_comp == 0:
                continue

            comp_count = max(1, int(target_count * n_comp / n_pixels))
            comp_count = min(comp_count, n_comp)

            # 泊松盘采样
            seed_ys, seed_xs = _poisson_disk_sample(pys, pxs, comp_count, n_comp)
            actual = len(seed_ys)

            # KDTree 分配 + Lloyd 松弛
            for lloyd_i in range(n_lloyd + 1):
                seed_coords = np.column_stack([seed_ys, seed_xs])
                tree = KDTree(seed_coords)
                pixel_coords = np.column_stack([pys, pxs])
                _, nearest = tree.query(pixel_coords)

                if lloyd_i < n_lloyd:
                    counts = np.bincount(nearest, minlength=actual).astype(np.float64)
                    sy = np.bincount(nearest, weights=pys.astype(np.float64), minlength=actual)
                    sx = np.bincount(nearest, weights=pxs.astype(np.float64), minlength=actual)
                    safe = np.maximum(counts, 1.0)
                    seed_ys = np.where(counts > 0, sy / safe, seed_ys).astype(np.int32)
                    seed_xs = np.where(counts > 0, sx / safe, seed_xs).astype(np.int32)

            # 写入 province_map
            ids = np.arange(next_id, next_id + actual, dtype=np.int32)
            province_map[pys, pxs] = ids[nearest]
            new_ids.update(int(i) for i in ids)
            next_id += actual

    # 5. 后处理：X-crossing 修复
    from domain.validators.province import fix_x_crossings
    for _ in range(5):
        if fix_x_crossings(province_map) == 0:
            break

    # 6. 合并碎片省份
    for _ in range(10):
        merged = _merge_tiny_provinces(province_map, min_pixels=MIN_PROVINCE_PIXELS)
        if merged == 0:
            break

    # 7. 清理旧数据引用（只清完全被删的省份）
    if fully_removed:
        if state_mgr:
            for sid, state in list(state_mgr.states.items()):
                state.provinces = [p for p in state.provinces if p not in fully_removed]
                # 清空后的 state 也删掉
                if not state.provinces:
                    state_mgr.states.pop(sid, None)
        if strategic_region_mgr:
            for r in strategic_region_mgr.regions.values():
                r.province_ids = [p for p in r.province_ids if p not in fully_removed]
        if country_mgr:
            for tag, country in country_mgr.countries.items():
                if country.capital in fully_removed:
                    # 找该国其他省份作为新首都
                    owned_states = country_mgr.get_states_of_country(tag)
                    new_cap = 0
                    if state_mgr and owned_states:
                        for osid in owned_states:
                            s = state_mgr.get_state(osid)
                            if s and s.provinces:
                                new_cap = s.provinces[0]
                                break
                    country.capital = new_cap

    return fully_removed, new_ids


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
