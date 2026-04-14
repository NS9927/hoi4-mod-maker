"""buildings.txt / unitstacks.txt 等 entity 文件."""
import os
import numpy as np
from data.constants import (
    MAP_WIDTH, MAP_HEIGHT, TILE_LAND, TILE_SEA,
    VALID_3D_BUILDING_TYPES,
)
from domain.validators.province import get_coastal_provinces


def _safe_coord(pid, province_map, pid_count, sum_x, sum_y):
    """返回保证在该省份像素内部（非边缘）的坐标 (cx, cy)。
    先试质心，如果质心飘到隔壁省份就回退到省份的几何中心像素。
    HOI4 对边缘像素的坐标匹配不稳定，必须用内部像素。"""
    cx = sum_x[pid] / pid_count[pid]
    cy = sum_y[pid] / pid_count[pid]
    icy, icx = int(round(cy)), int(round(cx))
    h, w = province_map.shape
    if 0 <= icy < h and 0 <= icx < w and province_map[icy, icx] == pid:
        return cx, cy
    # 质心不在省份内 → 找几何中心（median of y, median of x）
    ys, xs = np.where(province_map == pid)
    if len(ys) == 0:
        return cx, cy
    # 用中位数而不是中间索引，得到的点更靠近省份中心
    my = float(np.median(ys))
    mx = float(np.median(xs))
    # 确保这个点真的在省份内
    imy, imx = int(round(my)), int(round(mx))
    if 0 <= imy < h and 0 <= imx < w and province_map[imy, imx] == pid:
        return mx, my
    # 中位数也不行（非凸省份），取最靠近质心的省份内像素
    dist = (ys.astype(float) - cy)**2 + (xs.astype(float) - cx)**2
    best = np.argmin(dist)
    return float(xs[best]), float(ys[best])


def write_buildings(states, province_map, tile_map, output_dir, sea_ids=None,
                    land_to_sea=None,
                    pid_count=None, sum_x=None, sum_y=None):
    """写 buildings.txt。
    如果传入预计算的 land_to_sea/pid_count/sum_x/sum_y，直接使用；否则自行计算。
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    n = int(province_map.max()) + 1

    # 使用预计算数据，或自行计算质心
    if pid_count is None:
        flat_pm = province_map.ravel()
        pid_count = np.bincount(flat_pm, minlength=n)
        ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
        sum_y = np.bincount(flat_pm, weights=ys_grid.ravel().astype(np.float64), minlength=n)
        sum_x = np.bincount(flat_pm, weights=xs_grid.ravel().astype(np.float64), minlength=n)

    # 使用预计算的 land_to_sea，或自行计算
    if land_to_sea is None:
        land_to_sea = {}
        land_mask = (tile_map == TILE_LAND)
        sea_mask = (tile_map == TILE_SEA)
        is_land_arr = np.zeros(n, dtype=bool)
        is_sea_arr = np.zeros(n, dtype=bool)
        is_land_arr[province_map[land_mask].ravel()] = True
        is_sea_arr[province_map[sea_mask].ravel()] = True
        for land_pm, sea_pm in [
            (province_map[:, :-1], province_map[:, 1:]),
            (province_map[:, 1:], province_map[:, :-1]),
            (province_map[:-1, :], province_map[1:, :]),
            (province_map[1:, :], province_map[:-1, :]),
        ]:
            la = land_pm.ravel()
            sa = sea_pm.ravel()
            m = is_land_arr[la] & is_sea_arr[sa]
            if m.any():
                lp_hits = la[m]
                sp_hits = sa[m]
                _, first_idx = np.unique(lp_hits, return_index=True)
                for i in first_idx:
                    lp = int(lp_hits[i])
                    if lp not in land_to_sea:
                        land_to_sea[lp] = int(sp_hits[i])

    pid_to_state = {}
    for sid, provs in states.items():
        for p in provs:
            pid_to_state[int(p)] = sid

    # 每个 state 写最小必需 entity 集合
    lines = []
    REQUIRED_STATE_ENTITIES = ("air_base", "rocket_site_spawn")
    for sid, provs in states.items():
        if not provs:
            continue
        pid = provs[0]
        if pid >= n or pid_count[pid] == 0:
            continue
        cx, cy = _safe_coord(pid, province_map, pid_count, sum_x, sum_y)
        hoi4_y = MAP_HEIGHT - cy
        for btype in REQUIRED_STATE_ENTITIES:
            lines.append(
                f"{sid};{btype};{cx:.2f};11.00;{hoi4_y:.2f};0.00;0"
            )

    # 只给真正沿海的省份写 naval_base_spawn
    # 验证坐标确实在该省份像素上，否则 HOI4 无限循环崩溃
    h_map, w_map = province_map.shape
    failed_coastal: set[int] = set()
    for land_pid, sea_pid in land_to_sea.items():
        sid = pid_to_state.get(land_pid)
        if sid is None:
            continue
        if land_pid >= n or pid_count[land_pid] == 0:
            continue
        cx, cy = _safe_coord(land_pid, province_map, pid_count, sum_x, sum_y)
        # 验证坐标在该省份的陆地像素上
        iy, ix = round(cy), round(cx)
        ok = (0 <= iy < h_map and 0 <= ix < w_map
              and province_map[iy, ix] == land_pid
              and tile_map[iy, ix] == TILE_LAND)
        if ok:
            hoi4_y = MAP_HEIGHT - cy
            lines.append(
                f"{sid};naval_base_spawn;{cx:.2f};11.00;{hoi4_y:.2f};0.00;{sea_pid}"
            )
        else:
            failed_coastal.add(land_pid)

    if not lines:
        lines.append("1;bunker;100.00;11.00;100.00;0.00;0")

    with open(os.path.join(d, "buildings.txt"), "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))

    return failed_coastal


def write_empty_unitstacks(output_dir):
    """写空 map/*.txt 文件覆盖原版，避免 vanilla 的 13000+ 省份 ID 引用崩溃。

    原版 map/ 目录里的这些文件按省份 ID 引用坐标/规则；vanilla IDs 在我们的
    地图里全部无效，会触发 map.cpp:1135 错误。空文件让 HOI4 用默认值。

    【特例 cities.txt】不能为空！它是配置文件（指向 cities.bmp 的元数据），
    第一行 types_source = "map/cities.bmp" 告诉 HOI4 城市 mask 在哪。空文件
    会触发 "Missing cities mask bitmap" → 进图崩溃。写最小配置即可。
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    # adjacency_rules.txt 由 writers/map/adjacency_rules.py 单独写, 这里不再创建空文件
    for name in (
        "unitstacks.txt",
        "airports.txt",
        "rocket_sites.txt",
    ):
        open(os.path.join(d, name), "w").close()

    # cities.txt：最小配置，只指向 cities.bmp，不定义任何 city_group
    # → HOI4 找到 mask 文件但不渲染任何 3D 城市模型（地图上无城市建筑）
    with open(os.path.join(d, "cities.txt"), "w", encoding="utf-8") as f:
        f.write('types_source = "map/cities.bmp"\n')
        f.write("pixel_step_x = 2\n")
        f.write("pixel_step_y = 2\n")

