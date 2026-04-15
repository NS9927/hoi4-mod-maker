"""
河流自动生成器 — 基于高度图的汇流模拟

算法参考：
- mapgen4 (redblobgames): downslope BFS + flow accumulation + mini-erosion
- Azgaar Fantasy Map Generator: flux 累积 + 阈值成河

流程：
1. 计算每个省份的平均高度
2. 建省份邻接图
3. BFS 从海洋向内陆建下坡树（每个省份指向最低邻居方向的海洋）
4. 从叶到根累积流量（降水 → 汇入低处）
5. 流量超阈值的省份边界画为河流
6. 根据流量大小分配河流宽度类型
7. 在源头加绿色标记，入海口加黄色标记
"""
import numpy as np
from collections import defaultdict
import heapq


# 河流类型常量（与 domain/managers/river.py 一致）
RIVER_SOURCE = 0       # 源头 (0,255,0)
RIVER_MARKER = 1       # 汇入点 (255,0,0)
RIVER_MOUTH = 2        # 入海口 (255,252,0)
RIVER_BG_SEA = 254     # 海洋背景
RIVER_BG_LAND = 255    # 陆地背景

# 宽度类型：流量越大越宽（索引 3-11）
RIVER_WIDTHS = list(range(3, 12))  # [3,4,5,6,7,8,9,10,11]


def generate_rivers(
    province_map: np.ndarray,
    height_map: np.ndarray,
    tile_map: np.ndarray,
    flow_threshold: float = 3.0,
    rain_per_province: float = 1.0,
) -> np.ndarray:
    """
    从高度图自动生成河流。

    参数:
        province_map: (H, W) int32, 省份 ID
        height_map: (H, W) uint8, 高度图（0=最低, 255=最高）
        tile_map: (H, W) uint8, 地块类型（LAND/SEA/LAKE）
        flow_threshold: 流量超过此值才画河流
        rain_per_province: 每个陆地省份的降水量

    返回:
        river_map: (H, W) uint8, 河流图（与现有格式兼容）
    """
    from data.constants import TILE_LAND, TILE_SEA, TILE_LAKE

    H, W = province_map.shape
    river_map = np.full((H, W), RIVER_BG_LAND, dtype=np.uint8)

    # 海洋区域填充海洋背景色
    sea_mask = (tile_map == TILE_SEA) | (tile_map == TILE_LAKE)
    river_map[sea_mask] = RIVER_BG_SEA

    # ── 1. 计算每个省份的平均高度和类型 ──
    max_pid = int(province_map.max())
    if max_pid <= 0:
        return river_map

    prov_height = np.zeros(max_pid + 1, dtype=np.float64)
    prov_count = np.zeros(max_pid + 1, dtype=np.int64)
    prov_is_land = np.zeros(max_pid + 1, dtype=bool)
    prov_is_water = np.zeros(max_pid + 1, dtype=bool)

    flat_pid = province_map.ravel()
    flat_height = height_map.ravel().astype(np.float64)
    flat_tile = tile_map.ravel()

    np.add.at(prov_height, flat_pid, flat_height)
    np.add.at(prov_count, flat_pid, 1)

    valid = prov_count > 0
    prov_height[valid] /= prov_count[valid]

    # 判断每个省份是陆地还是水域（多数像素决定）
    land_count = np.zeros(max_pid + 1, dtype=np.int64)
    water_count = np.zeros(max_pid + 1, dtype=np.int64)
    land_pixels = flat_tile == TILE_LAND
    water_pixels = (flat_tile == TILE_SEA) | (flat_tile == TILE_LAKE)
    np.add.at(land_count, flat_pid, land_pixels.astype(np.int64))
    np.add.at(water_count, flat_pid, water_pixels.astype(np.int64))
    prov_is_land = land_count > water_count
    prov_is_water = ~prov_is_land
    prov_is_water[0] = True  # ID 0 视为水

    # ── 2. 建省份邻接图 ──
    neighbors = _build_adjacency(province_map)

    # ── 3. BFS 建下坡树（从海洋向内陆） ──
    # 参考 mapgen4 assignDownslope: 优先队列 BFS
    downslope = np.full(max_pid + 1, -1, dtype=np.int32)  # 每个省份的下坡方向
    visited = np.zeros(max_pid + 1, dtype=bool)
    heap = []  # (height, pid)

    # 种子：所有水域省份
    for pid in range(1, max_pid + 1):
        if prov_is_water[pid] and prov_count[pid] > 0:
            visited[pid] = True
            downslope[pid] = -1  # 水域没有下坡
            heapq.heappush(heap, (prov_height[pid], pid))

    # BFS：从低处向高处扩展
    topo_order = []  # 拓扑排序（根在前，叶在后）
    while heap:
        _, current = heapq.heappop(heap)
        topo_order.append(current)
        for nb in neighbors.get(current, []):
            if not visited[nb] and prov_is_land[nb]:
                visited[nb] = True
                downslope[nb] = current  # nb 的水往 current 流
                heapq.heappush(heap, (prov_height[nb], nb))

    # ── 4. 从叶到根累积流量 ──
    flow = np.zeros(max_pid + 1, dtype=np.float64)
    for pid in range(1, max_pid + 1):
        if prov_is_land[pid] and visited[pid]:
            flow[pid] = rain_per_province

    # 反向遍历拓扑序（叶→根）
    for pid in reversed(topo_order):
        ds = downslope[pid]
        if ds > 0 and prov_is_land[pid]:
            flow[ds] += flow[pid]

    # ── 5. 画河流：在流量超阈值的省份边界上画线 ──
    # 找所有需要画河流的省份边界
    river_edges = []  # [(pid_from, pid_to, flow_value)]
    for pid in range(1, max_pid + 1):
        if flow[pid] >= flow_threshold and prov_is_land[pid]:
            ds = downslope[pid]
            if ds > 0:
                river_edges.append((pid, ds, flow[pid]))

    # 在像素级别画河流边界线
    _draw_river_boundaries(
        river_map, province_map, river_edges,
        flow, downslope, prov_is_water, flow_threshold,
    )

    return river_map


def _build_adjacency(province_map: np.ndarray) -> dict[int, set[int]]:
    """建省份邻接图（4-连通）。"""
    H, W = province_map.shape
    neighbors: dict[int, set[int]] = defaultdict(set)

    # 水平相邻
    diff_h = province_map[:, :-1] != province_map[:, 1:]
    ys, xs = np.where(diff_h)
    for y, x in zip(ys, xs):
        a, b = int(province_map[y, x]), int(province_map[y, x + 1])
        if a > 0 and b > 0:
            neighbors[a].add(b)
            neighbors[b].add(a)

    # 垂直相邻
    diff_v = province_map[:-1, :] != province_map[1:, :]
    ys, xs = np.where(diff_v)
    for y, x in zip(ys, xs):
        a, b = int(province_map[y, x]), int(province_map[y + 1, x])
        if a > 0 and b > 0:
            neighbors[a].add(b)
            neighbors[b].add(a)

    return dict(neighbors)


def _draw_river_boundaries(
    river_map: np.ndarray,
    province_map: np.ndarray,
    river_edges: list[tuple[int, int, float]],
    flow: np.ndarray,
    downslope: np.ndarray,
    prov_is_water: np.ndarray,
    flow_threshold: float,
) -> None:
    """在省份边界像素上画河流线。"""
    H, W = province_map.shape

    # 把 river_edges 转成集合快速查找
    edge_set: dict[tuple[int, int], float] = {}
    for pid_from, pid_to, f in river_edges:
        key = (min(pid_from, pid_to), max(pid_from, pid_to))
        edge_set[key] = max(edge_set.get(key, 0), f)

    # 计算最大流量用于归一化宽度
    max_flow = max((f for _, _, f in river_edges), default=1.0)

    # 找所有需要画的边界像素
    # 扫描水平边界
    diff_h = province_map[:, :-1] != province_map[:, 1:]
    ys_h, xs_h = np.where(diff_h)

    # 扫描垂直边界
    diff_v = province_map[:-1, :] != province_map[1:, :]
    ys_v, xs_v = np.where(diff_v)

    # 收集河流源头和入海口的候选位置
    source_candidates: dict[int, list[tuple[int, int]]] = defaultdict(list)
    mouth_candidates: dict[int, list[tuple[int, int]]] = defaultdict(list)

    def _paint_boundary(y: int, x: int, a: int, b: int) -> None:
        """如果 (a,b) 是河流边界，在 (y,x) 画河流像素。"""
        key = (min(a, b), max(a, b))
        f = edge_set.get(key)
        if f is None:
            return

        # 根据流量选择宽度类型
        ratio = min(f / max(max_flow * 0.8, 1.0), 1.0)
        width_idx = int(ratio * (len(RIVER_WIDTHS) - 1))
        river_type = RIVER_WIDTHS[width_idx]
        river_map[y, x] = river_type

        # 检查是否是入海口（一端是水域）
        if prov_is_water[a] or prov_is_water[b]:
            land_pid = b if prov_is_water[a] else a
            mouth_candidates[land_pid].append((y, x))

    # 画水平边界
    for y, x in zip(ys_h, xs_h):
        a, b = int(province_map[y, x]), int(province_map[y, x + 1])
        if a > 0 and b > 0:
            _paint_boundary(y, x, a, b)

    # 画垂直边界
    for y, x in zip(ys_v, xs_v):
        a, b = int(province_map[y, x]), int(province_map[y + 1, x])
        if a > 0 and b > 0:
            _paint_boundary(y, x, a, b)

    # ── 标记源头和入海口 ──
    # 源头：没有上游（没有别的省份流向它）且流量 >= 阈值的陆地省份
    has_upstream = np.zeros(len(flow), dtype=bool)
    for pid in range(1, len(downslope)):
        ds = downslope[pid]
        if ds > 0 and flow[pid] >= flow_threshold:
            has_upstream[ds] = True

    # 找源头省份的边界像素，标记一个绿点
    for pid in range(1, len(flow)):
        if flow[pid] >= flow_threshold and not has_upstream[pid] and not prov_is_water[pid]:
            ds = downslope[pid]
            if ds <= 0:
                continue
            key = (min(pid, ds), max(pid, ds))
            if key not in edge_set:
                continue
            # 找这个省份的一个边界像素作为源头
            _mark_single_pixel(river_map, province_map, pid, ds, RIVER_SOURCE)

    # 入海口：在已收集的候选位置标记黄点
    marked_mouths = set()
    for land_pid, pixels in mouth_candidates.items():
        if land_pid not in marked_mouths and pixels:
            mid = len(pixels) // 2
            y, x = pixels[mid]
            river_map[y, x] = RIVER_MOUTH
            marked_mouths.add(land_pid)


def _mark_single_pixel(
    river_map: np.ndarray,
    province_map: np.ndarray,
    pid_a: int, pid_b: int,
    marker_type: int,
) -> None:
    """在 pid_a 和 pid_b 的边界上标记一个像素。"""
    H, W = province_map.shape
    # 快速扫描找一个边界像素
    # 优化：只在 pid_a 的 bounding box 里找
    ys, xs = np.where(province_map == pid_a)
    if len(ys) == 0:
        return
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()

    for y in range(max(0, y_min), min(H - 1, y_max + 1)):
        for x in range(max(0, x_min), min(W - 1, x_max + 1)):
            if province_map[y, x] != pid_a:
                continue
            # 检查 4 邻居是否有 pid_b
            for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and province_map[ny, nx] == pid_b:
                    river_map[y, x] = marker_type
                    return
