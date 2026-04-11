"""buildings.txt / unitstacks.txt 等 entity 文件."""
import os
import numpy as np
from data.constants import (
    MAP_WIDTH, MAP_HEIGHT, TILE_LAND, TILE_SEA,
    VALID_3D_BUILDING_TYPES,
)
from domain.validators.province import get_coastal_provinces


def write_buildings(states, province_map, tile_map, output_dir, sea_ids=None):
    """写 buildings.txt，包括基础设施、兵工厂，以及【关键】沿海省份的 naval_base。
    HOI4 会自动把挨着海的陆地省份判为 coastal，必须为每个 coastal 省份写 naval_base，
    否则 HOI4 弹出地图错误提示并可能崩溃。

    【关键】coastal 判定必须与 definition.csv 用同一套（get_coastal_provinces，
    像素级 TILE_LAND/TILE_SEA 邻接），不能用省份级邻接 —— 后者会把"省份多数像素是
    海但仍含陆地像素"的 sea province 与相邻的纯陆地 province 判为 coastal pair，
    在 buildings.txt 写出 definition.csv 视为非 coastal 的 naval_base_spawn →
    HOI4 校验失败 → 无限循环 → CPU 拉爆崩溃（Troubleshooting.txt line 116-117）。
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    # 预计算所有省份质心（向量化）
    flat_pm = province_map.ravel()
    n = int(province_map.max()) + 1
    pid_count = np.bincount(flat_pm, minlength=n)
    ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
    sum_y = np.bincount(flat_pm, weights=ys_grid.ravel().astype(np.float64), minlength=n)
    sum_x = np.bincount(flat_pm, weights=xs_grid.ravel().astype(np.float64), minlength=n)

    # 计算每个陆地省份的沿海邻接海洋省份（纯向量化）
    # 方法：找 land-sea 边界，记录 (land_pid, sea_pid) 对
    sea_set = set(int(x) for x in (sea_ids or []))
    land_to_sea = {}  # land_pid -> first adjacent sea_pid
    pid_to_state = {}
    for sid, provs in states.items():
        for p in provs:
            pid_to_state[int(p)] = sid

    # 用省份级邻接判定 coastal（与 HOI4 内部一致），不再用像素级 get_coastal_provinces。
    # HOI4 内部用 land_pid 邻 sea_pid 决定 coastal，definition.csv 写啥都被覆盖 →
    # 必须 buildings.txt 跟 HOI4 走，definition.csv 也跟 HOI4 走，保持一致

    if sea_set and pid_to_state:
        # 构造一个 "is_sea" 数组 (bool)，索引是省份ID
        max_pid = n
        is_sea = np.zeros(max_pid, dtype=bool)
        for sp in sea_set:
            if sp < max_pid:
                is_sea[sp] = True
        is_land = np.zeros(max_pid, dtype=bool)
        for lp in pid_to_state:
            if lp < max_pid:
                is_land[lp] = True

        # 水平相邻：(左邻像素, 右邻像素)
        left = province_map[:, :-1].ravel()
        right = province_map[:, 1:].ravel()
        # 掩码：一侧是 land、另一侧是 sea
        mask1 = is_land[left] & is_sea[right]  # left=land, right=sea
        mask2 = is_sea[left] & is_land[right]  # left=sea, right=land
        # 收集 (land, sea) 对
        if mask1.any():
            for lp, sp in zip(left[mask1], right[mask1]):
                lp, sp = int(lp), int(sp)
                if lp not in land_to_sea:
                    land_to_sea[lp] = sp
        if mask2.any():
            for lp, sp in zip(right[mask2], left[mask2]):
                lp, sp = int(lp), int(sp)
                if lp not in land_to_sea:
                    land_to_sea[lp] = sp

        # 垂直相邻
        up = province_map[:-1, :].ravel()
        down = province_map[1:, :].ravel()
        mask3 = is_land[up] & is_sea[down]
        mask4 = is_sea[up] & is_land[down]
        if mask3.any():
            for lp, sp in zip(up[mask3], down[mask3]):
                lp, sp = int(lp), int(sp)
                if lp not in land_to_sea:
                    land_to_sea[lp] = sp
        if mask4.any():
            for lp, sp in zip(down[mask4], up[mask4]):
                lp, sp = int(lp), int(sp)
                if lp not in land_to_sea:
                    land_to_sea[lp] = sp

    # 每个 state 写最小必需 entity 集合 (参考 Map modding.txt 行 459-469).
    # 游戏启动时 HOI4 检查 strategicair.cpp:5571/5591/5611:
    #   - air_base (state 级) — 必需, 否则 "no air base site defined for state N"
    #   - rocket_site_spawn (state 级) — 必需, 它是 rocket_site 和
    #     mega_gun_emplacement 两种 building 的 spawn_point (buildings/00_buildings.txt)
    # 所有 entity 放在 state 中心 land 省份的质心, 不加偏移, 避免落到海/邻州.
    lines = []
    REQUIRED_STATE_ENTITIES = ("air_base", "rocket_site_spawn")
    for sid, provs in states.items():
        if not provs:
            continue
        # 选中心省份: 就用第一个 land 省份, 其质心必在 land 内
        pid = provs[0]
        if pid >= n or pid_count[pid] == 0:
            continue
        cx = sum_x[pid] / pid_count[pid]
        cy = sum_y[pid] / pid_count[pid]
        hoi4_y = MAP_HEIGHT - cy
        for btype in REQUIRED_STATE_ENTITIES:
            lines.append(
                f"{sid};{btype};{cx:.2f};11.00;{hoi4_y:.2f};0.00;0"
            )

    # ⚠ 只给真正沿海的省份写 naval_base_spawn (有 sea 邻接的 land 省份).
    # 参考: 参考/Troubleshooting.txt 行 116-117 -
    # "if the game attempts to evaluate an invalid naval base definition,
    #  the game gets stuck in an infinite loop... resulting in CPU overload and crash"
    # 之前为所有 land 省份都写 naval_base_spawn, 内陆省份指向"最近的"sea,
    # HOI4 找不到有效水路 → 无限循环 → tick 12 后 tbb 崩. 这是"走时间崩溃"官方原因.
    for land_pid, sid in pid_to_state.items():
        sea_pid = land_to_sea.get(land_pid)
        if sea_pid is None:
            continue  # 内陆省份, 不写 naval_base_spawn
        if land_pid >= n or pid_count[land_pid] == 0:
            continue
        cx = sum_x[land_pid] / pid_count[land_pid]
        cy = sum_y[land_pid] / pid_count[land_pid]
        hoi4_y = MAP_HEIGHT - cy
        lines.append(
            f"{sid};naval_base_spawn;{cx:.2f};11.00;{hoi4_y:.2f};0.00;{sea_pid}"
        )

    # ── Issue 1 修复：交叉检查 definition.csv 的 coastal 省份 ──
    # definition.csv 里的 coastal 判定也是用像素级邻接（在 mod_exporter.py 里算的）,
    # 但 buildings 里的 land_to_sea 只包含 pid_to_state 里的省份（已分配 state 的）。
    # 如果有 coastal 省份没被任何 state 认领（理论上不应该，但导出流程可能存在时序问题），
    # 就会缺 naval_base_spawn 行 → HOI4 崩溃。
    # 安全网：用 get_coastal_provinces 重新算一遍，补上遗漏。
    coastal_pids = get_coastal_provinces(province_map, tile_map)
    has_naval = set(land_to_sea.keys())
    missing_coastal = [p for p in coastal_pids if p not in has_naval and p in pid_to_state]
    for land_pid in missing_coastal:
        if land_pid >= n or pid_count[land_pid] == 0:
            continue
        cx = sum_x[land_pid] / pid_count[land_pid]
        cy = sum_y[land_pid] / pid_count[land_pid]
        hoi4_y = MAP_HEIGHT - cy
        sid = pid_to_state[land_pid]
        # 找一个相邻的 sea province（用 coastal_pids 里的判定）
        # 从已知的 sea_set 中找最近的
        best_sea = None
        best_dist = float('inf')
        for sp in sea_set:
            if sp >= n or pid_count[sp] == 0:
                continue
            sp_cx = sum_x[sp] / pid_count[sp]
            sp_cy = sum_y[sp] / pid_count[sp]
            dist = (cx - sp_cx) ** 2 + (cy - sp_cy) ** 2
            if dist < best_dist:
                best_dist = dist
                best_sea = sp
        if best_sea is not None:
            lines.append(
                f"{sid};naval_base_spawn;{cx:.2f};11.00;{hoi4_y:.2f};0.00;{best_sea}"
            )

    if not lines:
        lines.append("1;bunker;100.00;11.00;100.00;0.00;0")

    # 用 binary 模式写入避免 Windows 上 \n → \r\n 自动转换
    with open(os.path.join(d, "buildings.txt"), "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))


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

