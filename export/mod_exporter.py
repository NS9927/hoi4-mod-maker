"""
MOD 完整导出器 — 一键生成完整可用的 HOI4 MOD
参考 KR（Kaiserreich）的文件结构
"""
import os
import struct
import numpy as np

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_LAND, TILE_SEA, TILE_LAKE,
    OCEAN_HEIGHT, LAND_BASE_HEIGHT, SEA_LEVEL,
    DEFAULT_MOD_NAME, DEFAULT_MOD_VERSION, DEFAULT_SUPPORTED_VERSION,
    REPLACE_PATHS,
    VALID_MAIN_IDEOLOGIES, DEFAULT_IDEOLOGY_SUBTYPE, VALID_3D_BUILDING_TYPES,
)
from data.terrain_types import TERRAIN_PALETTE_INDEX, DEFAULT_TERRAIN_FOR_TILE
from core.province_generator import generate_province_colors, compact_province_ids
from core.province_validator import get_coastal_provinces
from export.bmp_writer import (
    write_provinces_bmp, write_heightmap_bmp,
    write_terrain_bmp, write_rivers_bmp, write_trees_bmp,
    write_cities_bmp,
)


def export_full_mod(
    tile_map: np.ndarray,
    province_map: np.ndarray,
    output_dir: str,
    mod_name: str = DEFAULT_MOD_NAME,
    tag: str = "AAA",
    state_mgr=None,
    country_mgr=None,
    river_map: np.ndarray | None = None,
    terrain_map: np.ndarray | None = None,
    height_map: np.ndarray | None = None,
) -> None:
    """一键导出完整 MOD。如果提供 state_mgr/country_mgr，使用用户编辑的数据。"""
    if int(province_map.max()) == 0:
        raise ValueError("没有省份数据，请先生成省份")

    # 安全网：导出前强制压实 ID + 同步所有引用（state.provinces / VP / capital）
    # 这是修复历史 bug：之前只压实 province_map，没更新 state/country 引用，
    # 导致用户编辑过的 state/VP/首都可能指向不存在的省份
    from core.map_data import MapData as _MD
    _tmp = _MD.__new__(_MD)
    _tmp.province_map = province_map
    _tmp.tile_map = tile_map
    # 其他字段不需要，compact_with_references 只用 province_map
    _tmp.compact_with_references(state_mgr=state_mgr, country_mgr=country_mgr)
    province_count = int(province_map.max())

    colors = generate_province_colors(province_count)

    # 向量化分类省份（陆地 / 海洋 / 湖泊），避免逐省份全图扫描
    land_ids, sea_ids, lake_ids = _classify_provinces_fast(
        province_count, province_map, tile_map
    )

    # === BMP 文件 ===
    write_provinces_bmp(province_map, output_dir, colors)

    # 高度图：优先用用户编辑的，否则自动生成
    if height_map is not None and int(height_map.max()) != int(height_map.min()):
        heightmap = height_map
    else:
        heightmap = _gen_heightmap(tile_map)
    write_heightmap_bmp(heightmap, output_dir)

    # 地形图：优先用用户编辑的，否则自动生成
    if terrain_map is not None and int(terrain_map.max()) > 0:
        write_terrain_bmp(terrain_map, output_dir)
    else:
        write_terrain_bmp(_gen_terrain(tile_map), output_dir)

    write_rivers_bmp(output_dir, river_map)
    write_trees_bmp(output_dir)
    write_cities_bmp(output_dir)
    _write_normal_map(heightmap, output_dir)

    # === 地图配置文件 ===
    # 注意：不生成 default.map / seasons.txt / positions.txt / weatherpositions.txt
    # 这些全部用原版（按文件名覆盖机制，我们的BMP自动覆盖原版BMP）
    _write_definition_csv(province_count, colors, province_map, tile_map, output_dir,
                          land_ids, sea_ids, lake_ids)
    _write_continent(output_dir)
    _write_adjacencies(output_dir)

    # === 先 finalize states + 孤儿 land 省份补领养 ===
    # HOI4 要求每个 land province 都属于一个 state，否则 MAP_ERROR "land province has no state"
    if state_mgr and state_mgr.states:
        states = {}
        for sid, s in state_mgr.states.items():
            land_provs = [p for p in s.provinces if _is_land(p, province_map, tile_map)]
            if land_provs:
                states[sid] = land_provs

        # 孤儿领养：把 _classify_provinces_fast 视为 land 但没在任何 state 的省份
        # 分配到地理上最近的 state
        all_in_states = set()
        for provs in states.values():
            all_in_states.update(provs)
        orphans = [p for p in land_ids if p not in all_in_states]
        if orphans:
            # 计算每个 state 的中心
            flat_pm_o = province_map.ravel()
            n_o = int(province_map.max()) + 1
            cnt_o = np.bincount(flat_pm_o, minlength=n_o)
            ys_o, xs_o = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
            sy_o = np.bincount(flat_pm_o, weights=ys_o.ravel().astype(np.float64), minlength=n_o)
            sx_o = np.bincount(flat_pm_o, weights=xs_o.ravel().astype(np.float64), minlength=n_o)
            state_centers = {}
            for sid, provs in states.items():
                tx = ty = tw = 0.0
                for p in provs:
                    if p < n_o and cnt_o[p] > 0:
                        tx += sx_o[p]; ty += sy_o[p]; tw += cnt_o[p]
                if tw > 0:
                    state_centers[sid] = (ty / tw, tx / tw)
            for orphan in orphans:
                if orphan >= n_o or cnt_o[orphan] == 0:
                    continue
                ocy = sy_o[orphan] / cnt_o[orphan]
                ocx = sx_o[orphan] / cnt_o[orphan]
                # 找最近的 state
                best_sid = min(
                    state_centers,
                    key=lambda s: (state_centers[s][0]-ocy)**2 + (state_centers[s][1]-ocx)**2,
                )
                states[best_sid].append(orphan)
                # 同步回 state_mgr，让 _write_states_from_mgr 也写出来
                if state_mgr.get_state(best_sid):
                    state_mgr.get_state(best_sid).provinces.append(orphan)
            print(f"  [orphan adoption] 领养了 {len(orphans)} 个孤儿陆地省份")
    else:
        states = None  # 稍后用 region 拆 state

    # === 战略区域（state-aware 模式：保证每 state 全部省份在同一 region）===
    region_list = _write_strategic_regions(
        province_map, tile_map, output_dir, states_dict=states
    )
    _write_weatherpositions(region_list, province_map, output_dir)

    # === 写 state 文件 ===
    if state_mgr and state_mgr.states:
        _write_states_from_mgr(state_mgr, country_mgr, province_map, output_dir, tile_map)
    else:
        # 按 region 拆分 state：每个 region 内的 land 省份作为一个或多个 state
        states = _split_states_by_region(region_list, set(land_ids))
        _write_states(states, tag, province_map, output_dir)

    # === 补给系统 ===
    _write_supply_nodes(states, province_map, output_dir)
    _write_railways(states, province_map, output_dir)
    _write_buildings(states, province_map, tile_map, output_dir, sea_ids)
    _write_supply_areas(states, output_dir)
    # 覆盖原版 unitstacks.txt（原版引用13000省份坐标，和我们165省份冲突）
    _write_empty_unitstacks(output_dir)

    # === 国家 — 优先用用户数据 ===
    # 国家系统必须完整：country_tags + countries/TAG.txt + history/countries + history/units + gfx/flags
    # 注意：capital 是 STATE ID，不是省份 ID！
    if country_mgr and country_mgr.countries:
        _write_countries_from_mgr(country_mgr, output_dir, states)
    else:
        # 默认国家：首都用第一个 State 的 ID（不是省份ID）
        first_state_id = min(states.keys()) if states else 1
        _write_country(tag, first_state_id, output_dir)
    # 为所有国家生成国旗（避免 "Error loading flag" UI 错误）
    all_tags = list(country_mgr.countries.keys()) if country_mgr and country_mgr.countries else [tag]
    _write_country_flags(all_tags, output_dir, country_mgr)

    # === 本地化 ===
    region_count = len(region_list) if region_list else 24
    _write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir,
                             region_count=region_count)

    # === Bookmark（z_ 前缀，与原版共存）===
    country_tags = list(country_mgr.countries.keys()) if country_mgr and country_mgr.countries else [tag]
    _write_bookmark(mod_name, country_tags, output_dir)

    # === descriptor + replace_path 空目录 ===
    _write_descriptor(mod_name, output_dir)
    _create_replace_dirs(output_dir)

    # === tutorial 屏蔽 ===
    # 必须用 tutorial = { } 覆盖 vanilla tutorial/tutorial.txt，
    # vanilla 文件引用了 vanilla state ID，我们删了 → 加载到 line 40 时 ACCESS_VIOLATION
    # 参考：参考/Troubleshooting.txt:110
    tut_dir = os.path.join(output_dir, "tutorial")
    os.makedirs(tut_dir, exist_ok=True)
    with open(os.path.join(tut_dir, "tutorial.txt"), "w", encoding="utf-8") as f:
        f.write("tutorial = { }\n")

    # === 导出后校验：关键文件必须非空（空文件会让 HOI4 崩溃）===
    _verify_non_empty(output_dir)


def _verify_non_empty(output_dir):
    """校验关键地图/历史文件存在且非空。
    任一缺失或空文件都会导致 HOI4 启动或进图崩溃（柴 TD 经验）。
    """
    critical_files = [
        "map/definition.csv",
        "map/provinces.bmp",
        "map/heightmap.bmp",
        "map/terrain.bmp",
        "map/rivers.bmp",
        "map/trees.bmp",
        "map/continent.txt",
        "map/supply_nodes.txt",
        "map/railways.txt",
        "map/buildings.txt",
    ]
    missing = []
    for rel in critical_files:
        p = os.path.join(output_dir, rel)
        if not os.path.isfile(p) or os.path.getsize(p) == 0:
            missing.append(rel)
    if missing:
        raise RuntimeError(
            "MOD 导出后校验失败：下列关键文件缺失或为空（会导致 HOI4 崩溃）：\n  - "
            + "\n  - ".join(missing)
        )

    # 至少一个 strategicregion 和一个 state
    sr_dir = os.path.join(output_dir, "map", "strategicregions")
    if not os.path.isdir(sr_dir) or not any(
        f.endswith(".txt") for f in os.listdir(sr_dir)
    ):
        raise RuntimeError("map/strategicregions/ 为空 — 至少需要一个战略区域")
    st_dir = os.path.join(output_dir, "history", "states")
    if not os.path.isdir(st_dir) or not any(
        f.endswith(".txt") for f in os.listdir(st_dir)
    ):
        raise RuntimeError("history/states/ 为空 — 至少需要一个 State")


def _compute_coastal_province_level(province_map, land_ids, sea_ids):
    """用省份级邻接计算 coastal land province 集合（与 HOI4 内部一致）。
    任何 land province 只要在像素图上与某个 sea province 像素相邻，即为 coastal。
    """
    n = int(province_map.max()) + 1
    is_land = np.zeros(n, dtype=bool)
    is_sea = np.zeros(n, dtype=bool)
    for lp in land_ids:
        if lp < n:
            is_land[int(lp)] = True
    for sp in sea_ids:
        if sp < n:
            is_sea[int(sp)] = True

    coastal = set()
    # 水平邻接
    left = province_map[:, :-1].ravel()
    right = province_map[:, 1:].ravel()
    m1 = is_land[left] & is_sea[right]
    m2 = is_sea[left] & is_land[right]
    if m1.any():
        coastal.update(int(x) for x in np.unique(left[m1]))
    if m2.any():
        coastal.update(int(x) for x in np.unique(right[m2]))
    # 垂直邻接
    up = province_map[:-1, :].ravel()
    down = province_map[1:, :].ravel()
    m3 = is_land[up] & is_sea[down]
    m4 = is_sea[up] & is_land[down]
    if m3.any():
        coastal.update(int(x) for x in np.unique(up[m3]))
    if m4.any():
        coastal.update(int(x) for x in np.unique(down[m4]))
    return coastal


# ────────────────── definition.csv ──────────────────

def _write_definition_csv(count, colors, pm, tm, output_dir,
                          land_ids=None, sea_ids=None, lake_ids=None):
    """写 definition.csv。
    coastal 字段：根据 `get_coastal_provinces` 判定（仅陆地省份邻接【海洋】时为 true，
    不算邻接湖泊）。buildings.txt 里会为每个 coastal 陆地省份写 naval_base_spawn，
    两者必须一致，否则 HOI4 报 "coastal but has no port" 地图错误并可能崩溃。
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    # 预建类型查找表
    type_map = {}
    if land_ids and sea_ids and lake_ids:
        for pid in land_ids:
            type_map[pid] = "land"
        for pid in sea_ids:
            type_map[pid] = "sea"
        for pid in lake_ids:
            type_map[pid] = "lake"

    # 策略：所有 land province 都标 coastal=true，与 buildings.txt 为每个 land
    # 都写 naval_base_spawn 一致。HOI4 内部 coastal 判定方式不可预测（混合像素邻接、
    # 省份邻接、positions.txt），任何"标 coastal 却没 port"或反之都会触发崩溃。
    # 全标 + 全写 是唯一保证一致的策略。
    coastal_set = set(int(p) for p in (land_ids or []))

    with open(os.path.join(d, "definition.csv"), "w") as f:
        f.write("0;0;0;0;land;false;unknown;0\n")
        for pid in range(1, count + 1):
            r, g, b = colors.get(pid, (1, 1, 1))
            ptype = type_map.get(pid) if type_map else _get_province_type(pid, pm, tm)
            if ptype == "land":
                terrain = "plains"
                cont = 1
                coastal = "true" if pid in coastal_set else "false"
            elif ptype == "lake":
                terrain = "lakes"
                cont = 0
                coastal = "false"
            else:
                terrain = "ocean"
                cont = 0
                coastal = "false"
            f.write(f"{pid};{r};{g};{b};{ptype};{coastal};{terrain};{cont}\n")


# 注意：不再生成 default.map — 用原版的（EaW 验证做法）
# 我们的 BMP/CSV 文件会按文件名自动覆盖原版对应文件


# ────────────────── continent.txt ──────────────────

def _write_continent(output_dir):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "continent.txt"), "w") as f:
        # 用原版名称列表格式
        f.write("continents = {\n\teurope\n}\n")


# ────────────────── adjacencies ──────────────────

def _write_adjacencies(output_dir):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "adjacencies.csv"), "w") as f:
        f.write("From;To;Type;Through;start_x;start_y;stop_x;stop_y;adjacency_rule_name;Comment\n")
        # vanilla 末行格式：-1;-1;;-1;-1;-1;-1;-1;-1
        f.write("-1;-1;;-1;-1;-1;-1;-1;-1\n")


# 注意：不再生成 adjacency_rules/ambient_object/weatherpositions/unitstacks/rocket_sites
# 不再生成 seasons.txt — 全部用原版（EaW 验证做法）


# ────────────────── State 拆分 ──────────────────

def _auto_split_states(land_ids, province_map, per_state=15):
    if not land_ids:
        return {}
    # 向量化计算质心
    flat_pm = province_map.ravel()
    n = int(province_map.max()) + 1
    pid_count = np.bincount(flat_pm, minlength=n)
    ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
    sum_y = np.bincount(flat_pm, weights=ys_grid.ravel().astype(np.float64), minlength=n)
    sum_x = np.bincount(flat_pm, weights=xs_grid.ravel().astype(np.float64), minlength=n)

    centers = {}
    for pid in land_ids:
        if pid_count[pid] > 0:
            centers[pid] = (sum_y[pid] / pid_count[pid], sum_x[pid] / pid_count[pid])
    sorted_ids = sorted(centers.keys(), key=lambda p: (centers[p][0] // 100, centers[p][1]))
    states = {}
    for i in range(0, len(sorted_ids), per_state):
        sid = i // per_state + 1
        states[sid] = sorted_ids[i:i + per_state]
    return states


def _split_states_by_region(region_list, land_id_set, max_per_state=15):
    """
    从 region_list 按地区拆分 State。
    每个 state 的省份必须完全在同一个 strategic region 内（HOI4 强制要求）。

    参数:
        region_list: _write_strategic_regions 返回的 [(region_id, [pid...])] 列表
        land_id_set: 所有陆地省份的集合
        max_per_state: 每个 state 最多多少省份（太大的话拆分）

    返回:
        {state_id: [land_pid, ...]}
    """
    states = {}
    sid = 1
    for region_id, region_provs in region_list:
        # 只取这个 region 里的陆地省份
        region_land = [p for p in region_provs if p in land_id_set]
        if not region_land:
            continue
        # 如果太多则拆成多个 state，都在同一个 region 内
        for i in range(0, len(region_land), max_per_state):
            states[sid] = region_land[i:i + max_per_state]
            sid += 1
    return states


def _write_states(states, tag, province_map, output_dir):
    d = os.path.join(output_dir, "history", "states")
    os.makedirs(d, exist_ok=True)
    for sid, provs in states.items():
        first = provs[0]
        manpower = len(provs) * 50000
        with open(os.path.join(d, f"{sid}-STATE_{sid}.txt"), "w") as f:
            f.write("state = {\n")
            f.write(f"\tid = {sid}\n")
            f.write(f'\tname = "STATE_{sid}"\n')
            f.write(f"\tmanpower = {manpower}\n")
            f.write("\tstate_category = town\n\n")
            f.write("\thistory = {\n")
            f.write(f"\t\towner = {tag}\n")
            f.write(f"\t\tadd_core_of = {tag}\n")
            f.write("\t\tbuildings = {\n")
            f.write("\t\t\tinfrastructure = 1\n")
            f.write("\t\t}\n")
            f.write(f"\t\tvictory_points = {{ {first} 1 }}\n")
            f.write("\t}\n\n")
            f.write("\tprovinces = {\n")
            f.write("\t\t" + " ".join(str(p) for p in provs) + "\n")
            f.write("\t}\n}\n")


# ────────────────── 补给系统 ──────────────────

def _write_supply_nodes(states, province_map, output_dir):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "supply_nodes.txt"), "w") as f:
        # 按索引每5个State放一个补给节点
        state_list = [(sid, provs) for sid, provs in states.items() if provs]
        written = False
        for i, (sid, provs) in enumerate(state_list):
            if i % 5 == 0:
                f.write(f"1 {provs[0]}\n")
                written = True
        if not written and state_list:
            f.write(f"1 {state_list[0][1][0]}\n")
            written = True
        if not written:
            # 文件不能为空也不能写注释，写一个占位节点
            f.write("1 1\n")


def _write_railways(states, province_map, output_dir):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    nodes = [provs[0] for sid, provs in states.items() if provs]
    with open(os.path.join(d, "railways.txt"), "w") as f:
        if len(nodes) >= 2:
            # 取部分节点连铁路
            rail_nodes = nodes[::max(1, len(nodes) // 20)]
            for i in range(len(rail_nodes) - 1):
                f.write(f"1 2 {rail_nodes[i]} {rail_nodes[i+1]}\n")
        elif nodes:
            f.write(f"1 1 {nodes[0]}\n")
        else:
            # 文件不能为空也不能写注释，写占位铁路
            f.write("1 1 1\n")


def _write_buildings(states, province_map, tile_map, output_dir, sea_ids=None):
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

    # HOI4 要求每个 state 至少有这些建筑类型的位置，否则会报 MAP_ERROR
    # 注意：这里只能写【3D建筑】类型，不能写 infrastructure（那是 state 级统计值）
    # 类型必须和 vanilla common/buildings/ 里定义的一致
    required_building_types = [
        "arms_factory", "industrial_complex",
        "air_base", "anti_air_building", "bunker", "supply_node",
        "rocket_site_spawn", "synthetic_refinery", "radar_station",
        "fuel_silo", "dockyard",
    ]
    # 白名单断言：任何非 3D 建筑类型写入 buildings.txt 都会让 HOI4 崩溃
    for _bt in required_building_types:
        assert _bt in VALID_3D_BUILDING_TYPES, (
            f"非法 3D 建筑类型 '{_bt}' — 只能使用 VALID_3D_BUILDING_TYPES 中的类型"
        )

    # 收集所有行后用 "\n".join 一次性写入，确保【没有尾换行】
    # vanilla buildings.txt 不以换行结尾；如果有尾 \n，HOI4 会把空尾行算成
    # "line N+1: invalid arguments count" 错误并崩溃
    lines = []
    for sid, provs in states.items():
        if not provs:
            continue
        pid = provs[0]
        if pid >= n or pid_count[pid] == 0:
            continue
        cx = sum_x[pid] / pid_count[pid]
        cy = sum_y[pid] / pid_count[pid]
        hoi4_y = MAP_HEIGHT - cy
        for i, btype in enumerate(required_building_types):
            offset = i * 0.5
            lines.append(
                f"{sid};{btype};{cx+offset:.2f};11.00;{hoi4_y-offset:.2f};0.00;0"
            )

    # 关键策略：为【每个 land province】都写 naval_base_spawn，无论 def.csv
    # 是否标 coastal。HOI4 内部 coastal 判定无法精确预测（受 positions.txt /
    # 像素邻接 / 省份邻接多个因素影响），任何不一致都触发"is coastal but no port"
    # 警告 + 无限循环崩溃。多写不会崩，少写会崩，所以全部写。
    # 找最近的 sea province 作为出海口
    sea_pids_list = [int(s) for s in sea_set] if sea_set else []
    sea_centroids = {}
    for sp in sea_pids_list:
        if sp < n and pid_count[sp] > 0:
            sea_centroids[sp] = (sum_x[sp] / pid_count[sp], sum_y[sp] / pid_count[sp])

    for land_pid, sid in pid_to_state.items():
        if land_pid >= n or pid_count[land_pid] == 0:
            continue
        cx = sum_x[land_pid] / pid_count[land_pid]
        cy = sum_y[land_pid] / pid_count[land_pid]
        hoi4_y = MAP_HEIGHT - cy
        # 优先用预计算的 land_to_sea 邻接关系；否则用最近的 sea province
        sea_pid = land_to_sea.get(land_pid)
        if sea_pid is None and sea_centroids:
            # 找距离最近的 sea province
            best_sp = min(
                sea_centroids,
                key=lambda sp: (sea_centroids[sp][0] - cx) ** 2
                              + (sea_centroids[sp][1] - cy) ** 2,
            )
            sea_pid = best_sp
        if sea_pid is None:
            continue  # 没有任何海洋省份就跳过
        # 回退：沿海 5 实体方案会导致 Loaded provinces 后立即崩溃（2026-04-08 实测）。
        # vanilla 沿海省份确实有 5 个伙伴实体（naval_base_spawn + coastal_bunker +
        # floating_harbor + naval_headquarters + naval_supply_hub），但它们有
        # 独立坐标 + 不同 sea province 指向 + 可能的 dat 文件依赖，同坐标堆写
        # 会让 buildings.txt 解析失败。保持单 naval_base_spawn（原先能进游戏）。
        lines.append(
            f"{sid};naval_base_spawn;{cx:.2f};11.00;{hoi4_y:.2f};0.00;{sea_pid}"
        )

    if not lines:
        lines.append("1;bunker;100.00;11.00;100.00;0.00;0")

    # 用 binary 模式写入避免 Windows 上 \n → \r\n 自动转换
    with open(os.path.join(d, "buildings.txt"), "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))


def _write_empty_unitstacks(output_dir):
    """写空 map/*.txt 文件覆盖原版，避免 vanilla 的 13000+ 省份 ID 引用崩溃。

    原版 map/ 目录里的这些文件按省份 ID 引用坐标/规则；vanilla IDs 在我们的
    地图里全部无效，会触发 map.cpp:1135 错误。空文件让 HOI4 用默认值。

    【特例 cities.txt】不能为空！它是配置文件（指向 cities.bmp 的元数据），
    第一行 types_source = "map/cities.bmp" 告诉 HOI4 城市 mask 在哪。空文件
    会触发 "Missing cities mask bitmap" → 进图崩溃。写最小配置即可。
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    for name in (
        "unitstacks.txt",
        "airports.txt",
        "rocket_sites.txt",
        "adjacency_rules.txt",
        "ambient_object.txt",
        "positions.txt",
    ):
        open(os.path.join(d, name), "w").close()

    # cities.txt：最小配置，只指向 cities.bmp，不定义任何 city_group
    # → HOI4 找到 mask 文件但不渲染任何 3D 城市模型（地图上无城市建筑）
    with open(os.path.join(d, "cities.txt"), "w", encoding="utf-8") as f:
        f.write('types_source = "map/cities.bmp"\n')
        f.write("pixel_step_x = 2\n")
        f.write("pixel_step_y = 2\n")


def _write_supply_areas(states, output_dir):
    d = os.path.join(output_dir, "map", "supplyareas")
    os.makedirs(d, exist_ok=True)
    state_ids = list(states.keys())
    with open(os.path.join(d, "1-SupplyArea.txt"), "w") as f:
        f.write("supply_area={\n\tid=1\n")
        f.write('\tname="SUPPLYAREA_1"\n\tvalue=5\n')
        f.write("\tstates={\n\t\t" + " ".join(str(s) for s in state_ids) + "\n\t}\n}\n")


# ────────────────── 战略区域（多区域自动拆分）──────────────────

def _write_weatherpositions(region_list, province_map, output_dir):
    """写 map/weatherpositions.txt，每个战略区域一个天气位置点。
    必须覆盖原版文件，否则原版里的 region ID 失效 → MAP_ERROR "invalid region id"。
    格式（vanilla 验证）：`region_id;x;y;z;size`
        - 分号分隔，无空格无括号
        - x/y/z 是 3D 坐标（z 是地图坐标 = MAP_HEIGHT - pixel_y）
        - y 是高度，固定 ~10
        - size: small / medium / large / huge
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    # 向量化算每个省份质心
    flat_pm = province_map.ravel()
    n = int(province_map.max()) + 1
    pid_count = np.bincount(flat_pm, minlength=n)
    ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
    sum_y = np.bincount(flat_pm, weights=ys_grid.ravel().astype(np.float64), minlength=n)
    sum_x = np.bincount(flat_pm, weights=xs_grid.ravel().astype(np.float64), minlength=n)

    with open(os.path.join(d, "weatherpositions.txt"), "w") as f:
        for rid, provs in region_list:
            # 用 region 内所有省份像素加权平均
            total_pix = 0
            sx = 0.0
            sy = 0.0
            for p in provs:
                if p < n and pid_count[p] > 0:
                    sx += sum_x[p]
                    sy += sum_y[p]
                    total_pix += int(pid_count[p])
            if total_pix == 0:
                cx, cy = MAP_WIDTH / 2, MAP_HEIGHT / 2
            else:
                cx = sx / total_pix
                cy = sy / total_pix
            hoi4_z = MAP_HEIGHT - cy
            # vanilla 格式：region_id;x;y;z;size
            f.write(f"{rid};{cx:.2f};10.00;{hoi4_z:.2f};small\n")


def _write_strategic_regions(province_map, tile_map, output_dir,
                             grid_cols=6, grid_rows=4, states_dict=None):
    """
    生成战略区域。两种模式：
    - 不传 states_dict：纯网格拆分（旧行为，TestMOD 用）
    - 传 states_dict {sid: [pids]}：state-aware 模式 — 每个 state 占独立 region，
      sea/未分配省份按网格补充。这样保证每个 state 的所有省份都在同一 region 内
      （否则触发 MAP_ERROR "State has provinces belonging to different strategic areas"）
    """
    d = os.path.join(output_dir, "map", "strategicregions")
    os.makedirs(d, exist_ok=True)

    province_count = int(province_map.max())
    if province_count == 0:
        return []

    # 向量化计算所有省份质心
    flat_pm = province_map.ravel()
    n = province_count + 1
    pid_count = np.bincount(flat_pm, minlength=n)
    ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
    sum_y = np.bincount(flat_pm, weights=ys_grid.ravel().astype(np.float64), minlength=n)
    sum_x = np.bincount(flat_pm, weights=xs_grid.ravel().astype(np.float64), minlength=n)

    centroids = {}
    for pid in range(1, province_count + 1):
        if pid_count[pid] > 0:
            centroids[pid] = (sum_y[pid] / pid_count[pid], sum_x[pid] / pid_count[pid])

    regions: dict[int, list[int]] = {}

    if states_dict:
        # === state-aware 模式：每 state 一个 region ===
        # 先把所有 state 的省份打包成 region
        next_rid = 1
        state_in_region = set()
        for sid in sorted(states_dict.keys()):
            provs = states_dict[sid]
            if not provs:
                continue
            regions[next_rid] = list(provs)
            state_in_region.update(provs)
            next_rid += 1

        # 剩下的省份（海洋/湖泊/孤儿）按网格补充进若干个 region
        cell_h = MAP_HEIGHT / max(1, grid_rows)
        cell_w = MAP_WIDTH / max(1, grid_cols)
        sea_grid_regions: dict[int, list[int]] = {}
        for pid, (cy, cx) in centroids.items():
            if pid in state_in_region:
                continue
            row = min(int(cy / cell_h), grid_rows - 1)
            col = min(int(cx / cell_w), grid_cols - 1)
            cell_id = row * grid_cols + col
            sea_grid_regions.setdefault(cell_id, []).append(pid)
        for cell_id in sorted(sea_grid_regions.keys()):
            regions[next_rid] = sea_grid_regions[cell_id]
            next_rid += 1
    else:
        # === 旧行为：纯网格拆分 ===
        cell_h = MAP_HEIGHT / grid_rows
        cell_w = MAP_WIDTH / grid_cols
        for pid, (cy, cx) in centroids.items():
            row = min(int(cy / cell_h), grid_rows - 1)
            col = min(int(cx / cell_w), grid_cols - 1)
            rid = row * grid_cols + col + 1
            regions.setdefault(rid, []).append(pid)

    # 处理没有质心的省份（理论上不应发生）
    all_assigned = set()
    for provs in regions.values():
        all_assigned.update(provs)
    for pid in range(1, province_count + 1):
        if pid not in all_assigned:
            first_rid = min(regions.keys()) if regions else 1
            regions.setdefault(first_rid, []).append(pid)

    # 重新编号（连续从1开始）
    sorted_rids = sorted(regions.keys())
    region_list = []
    for new_id, old_rid in enumerate(sorted_rids, start=1):
        provs = regions[old_rid]
        if not provs:
            continue
        region_list.append((new_id, provs))

        with open(os.path.join(d, f"{new_id}-strategic_region.txt"), "w") as f:
            f.write("strategic_region={\n")
            f.write(f"\tid={new_id}\n")
            f.write(f'\tname="STRATEGICREGION_{new_id}"\n')
            f.write("\tprovinces={\n\t\t")
            f.write(" ".join(str(p) for p in provs))
            f.write("\n\t}\n")
            f.write("\tweather={\n\t\tperiod={\n")
            # between={ DAY.MONTH DAY.MONTH } — 必须覆盖全年（0.0 到 30.11）
            # 否则 HOI4 警告 "Region temperature doesn't cover the whole year"
            f.write("\t\t\tbetween={ 0.0 30.11 }\n")
            f.write("\t\t\ttemperature={ -5.0 25.0 }\n")
            f.write("\t\t\tno_phenomenon=0.500\n")
            f.write("\t\t\train_light=0.200\n")
            f.write("\t\t\train_heavy=0.100\n")
            f.write("\t\t\tmud=0.050\n")
            f.write("\t\t\tblizzard=0.050\n")
            f.write("\t\t\tsandstorm=0.000\n")
            f.write("\t\t\tsnow=0.100\n")
            f.write("\t\t}\n\t}\n}\n")

    return region_list


# 注意：不再生成 positions.txt — 用原版的（EaW 验证做法）


# ────────────────── 国家 ──────────────────

def _write_country_flags(tags, output_dir, country_mgr=None):
    """为每个国家生成国旗文件。
    HOI4 需要 gfx/flags/TAG.tga 存在，否则UI报错（可能影响交互）。
    格式：82x52 TGA，24位BGR bottom-up。
    """
    import struct
    flag_dir = os.path.join(output_dir, "gfx", "flags")
    os.makedirs(flag_dir, exist_ok=True)
    # 中等、小旗也需要
    med_dir = os.path.join(flag_dir, "medium")
    small_dir = os.path.join(flag_dir, "small")
    os.makedirs(med_dir, exist_ok=True)
    os.makedirs(small_dir, exist_ok=True)

    # 一组默认颜色，按TAG哈希
    default_colors = [
        (200, 80, 80), (80, 80, 200), (80, 200, 80), (200, 200, 80),
        (200, 80, 200), (80, 200, 200), (150, 100, 50), (100, 150, 200),
    ]

    def make_tga(path, w, h, rgb):
        r, g, b = rgb
        # TGA 文件头（18字节） - 32bpp BGRA 格式（HOI4推荐，读取更快）
        header = struct.pack(
            "<BBBHHBHHHHBB",
            0,      # ID length
            0,      # Color map type
            2,      # Image type (uncompressed true color)
            0, 0, 0,    # Color map spec
            0, 0,       # X, Y origin
            w, h,       # Width, Height
            32,         # Pixel depth (32bpp)
            8,          # Image descriptor: 8 = 8bit alpha + bottom-up
        )
        # 像素数据：BGRA 顺序，A=255（不透明）
        pixel = bytes([b, g, r, 255]) * (w * h)
        with open(path, "wb") as f:
            f.write(header)
            f.write(pixel)

    ideologies = ["neutrality", "democratic", "fascism", "communism"]

    for i, tag in enumerate(tags):
        # 获取国家颜色
        if country_mgr and tag in country_mgr.countries:
            rgb = country_mgr.countries[tag].color
        else:
            rgb = default_colors[i % len(default_colors)]

        # 主国旗 82x52
        make_tga(os.path.join(flag_dir, f"{tag}.tga"), 82, 52, rgb)
        # 意识形态变体（HOI4 需要 TAG_ideology.tga）
        for ideo in ideologies:
            make_tga(os.path.join(flag_dir, f"{tag}_{ideo}.tga"), 82, 52, rgb)
        # 中等国旗 41x26
        make_tga(os.path.join(med_dir, f"{tag}.tga"), 41, 26, rgb)
        for ideo in ideologies:
            make_tga(os.path.join(med_dir, f"{tag}_{ideo}.tga"), 41, 26, rgb)
        # 小国旗 10x7
        make_tga(os.path.join(small_dir, f"{tag}.tga"), 10, 7, rgb)
        for ideo in ideologies:
            make_tga(os.path.join(small_dir, f"{tag}_{ideo}.tga"), 10, 7, rgb)


def _write_country_portraits(tag, output_dir):
    """生成 portraits/<TAG>.txt — HOI4 顶级 portraits 目录

    【崩溃根因】HOI4 在启动游戏时为每个国家自动生成缺失的 scientist，
    它从 portraits/<TAG>.txt 或 portraits/continent_xxx.txt 里的 scientist 池
    随机选择肖像。如果国家没有这个文件，自动生成失败 → 崩溃。

    文件必须放在 MOD 根目录下的 portraits/ 文件夹（不是 common/portraits）。
    """
    d = os.path.join(output_dir, "portraits")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{tag}.txt"), "w", encoding="utf-8") as f:
        f.write(f"{tag} = {{\n")

        # scientist（关键，否则崩溃）
        f.write("\tscientist = {\n")
        f.write("\t\tmale = {\n")
        for i in range(1, 17):
            f.write(f'\t\t\t"GFX_portrait_generic_europe_male_{i:02d}"\n')
        f.write("\t\t}\n")
        f.write("\t\tfemale = {\n")
        for i in range(1, 17):
            f.write(f'\t\t\t"GFX_portrait_generic_europe_female_{i:02d}"\n')
        f.write("\t\t}\n")
        f.write("\t}\n")

        # army（将领）
        f.write("\tarmy = {\n")
        f.write("\t\tmale = {\n")
        for i in range(1, 6):
            f.write(f'\t\t\t"GFX_Portrait_Europe_Generic_land_{i}"\n')
        f.write("\t\t}\n")
        f.write("\t}\n")

        # navy（海军）
        f.write("\tnavy = {\n")
        f.write("\t\tmale = {\n")
        for i in range(1, 4):
            f.write(f'\t\t\t"GFX_Portrait_Europe_Generic_navy_{i}"\n')
        f.write("\t\t}\n")
        f.write("\t}\n")

        # political（领袖，按意识形态）
        f.write("\tpolitical = {\n")
        for i, ideo in enumerate(["communism", "democratic", "fascism", "neutrality"], 1):
            f.write(f"\t\t{ideo} = {{\n")
            f.write("\t\t\tmale = {\n")
            f.write(f'\t\t\t\t"GFX_Portrait_Europe_Generic_{i}"\n')
            f.write("\t\t\t}\n")
            f.write("\t\t}\n")
        f.write("\t}\n")

        # operative（特工）
        f.write("\toperative = {\n")
        f.write("\t\tmale = { \"GFX_portrait_operative_unknown\" }\n")
        f.write("\t\tfemale = { \"GFX_portrait_operative_unknown\" }\n")
        f.write("\t}\n")

        # fallback male/female
        f.write("\tmale = { \"GFX_portrait_unknown\" }\n")
        f.write("\tfemale = { \"GFX_portrait_unknown_female\" }\n")

        f.write("}\n")


def _write_country_colors(tag, rgb, output_dir):
    """生成 common/countries/colors.txt — 地图上国家的颜色

    HOI4 用这个文件定义国家在地图上的边框/填充颜色。
    如果缺失，国家颜色可能异常或默认为灰色。
    """
    d = os.path.join(output_dir, "common", "countries")
    os.makedirs(d, exist_ok=True)
    r, g, b = rgb
    # 追加模式：如果 colors.txt 已存在（多国家情况），累加
    path = os.path.join(d, "colors.txt")
    mode = "a" if os.path.exists(path) else "w"
    with open(path, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("#reload countrycolors\n\n")
        f.write(f"{tag} = {{\n")
        f.write(f"\tcolor = rgb {{ {r} {g} {b} }}\n")
        f.write(f"\tcolor_ui = rgb {{ {r} {g} {b} }}\n")
        f.write("}\n\n")


def _write_country_names(tag, output_dir, country_name="Fantasy"):
    """生成 common/names/<TAG>_names.txt

    HOI4 的人物自动生成器（character_manager）会从这个文件里拉取
    姓名和姓氏。如果国家没有对应的 names 条目，游戏会用国家的本地化
    名字作为 origins 去查找，查找失败则导致崩溃。

    不 replace_path common/names（保留原版名字），只【添加】我们的文件。
    """
    d = os.path.join(output_dir, "common", "names")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{tag}_names.txt"), "w", encoding="utf-8") as f:
        f.write(f"{tag} = {{\n")
        f.write("\tmale = {\n")
        f.write('\t\tnames = { "Alex" "Benjamin" "Charles" "David" "Edward" "Frank" "George" "Henry" "James" "John" "Kevin" "Louis" "Michael" "Nathan" "Oliver" "Peter" }\n')
        f.write("\t}\n")
        f.write("\tfemale = {\n")
        f.write('\t\tnames = { "Alice" "Beatrice" "Catherine" "Diana" "Emma" "Fiona" "Grace" "Helen" "Isabel" "Julia" "Kate" "Laura" "Maria" "Nora" "Olivia" "Patricia" }\n')
        f.write("\t}\n")
        f.write('\tsurnames = { "Smith" "Jones" "Taylor" "Brown" "Williams" "Wilson" "Evans" "Walker" "White" "Roberts" "Lewis" "Harris" "Clark" "Young" "King" "Hill" }\n')
        f.write("\tcallsigns = { }\n")
        f.write("}\n")


def _write_country_characters(tag, output_dir, country_name="Fantasy"):
    """生成国家人物文件 common/characters/<TAG>.txt

    HOI4 引擎会为每个国家自动生成 country_leader/scientist/field_marshal 等人物。
    如果国家没有这些角色定义，自动生成会因为找不到 origins 而失败，
    进而导致游戏在启动时崩溃（character_manager.cpp 报错）。

    解决：至少提供 country_leader + field_marshal + general + scientist，
    覆盖游戏的自动生成路径。
    注意：这里不 replace_path common/characters，而是【添加】文件，
    和原版 characters 共存。
    """
    d = os.path.join(output_dir, "common", "characters")
    os.makedirs(d, exist_ok=True)
    # 用 TAG.txt 命名避免和原版文件冲突
    with open(os.path.join(d, f"{tag}.txt"), "w") as f:
        f.write("characters = {\n\n")

        # 1. 国家领袖（4种意识形态子类型各一个，对齐 vanilla 最小格式，
        #    去掉 id=-1 和 expire — 1.17 这俩字段会让 AI 初始化校验失败）
        for ideo in ("despotism", "conservatism", "nazism", "marxism"):
            f.write(f"\t{tag}_leader_{ideo} = {{\n")
            f.write(f'\t\tname = "{country_name} Leader"\n')
            f.write("\t\tportraits = {\n")
            f.write("\t\t\tcivilian = { large = GFX_Portrait_Europe_Generic_1 }\n")
            f.write("\t\t}\n")
            f.write("\t\tcountry_leader = {\n")
            f.write(f"\t\t\tideology = {ideo}\n")
            f.write("\t\t\ttraits = { }\n")
            f.write("\t\t}\n")
            f.write("\t}\n\n")

        # 2. 元帅
        f.write(f"\t{tag}_field_marshal_1 = {{\n")
        f.write(f'\t\tname = "{country_name} Marshal"\n')
        f.write("\t\tportraits = {\n")
        f.write("\t\t\tarmy = { large = GFX_Portrait_Europe_Generic_land_1 }\n")
        f.write("\t\t}\n")
        f.write("\t\tfield_marshal = {\n")
        f.write("\t\t\ttraits = { }\n")
        f.write("\t\t\tskill = 3\n")
        f.write("\t\t\tattack_skill = 3\n")
        f.write("\t\t\tdefense_skill = 3\n")
        f.write("\t\t\tplanning_skill = 3\n")
        f.write("\t\t\tlogistics_skill = 3\n")
        f.write("\t\t}\n")
        f.write("\t}\n\n")

        # 3. 将军
        f.write(f"\t{tag}_general_1 = {{\n")
        f.write(f'\t\tname = "{country_name} General"\n')
        f.write("\t\tportraits = {\n")
        f.write("\t\t\tarmy = { large = GFX_Portrait_Europe_Generic_land_2 }\n")
        f.write("\t\t}\n")
        f.write("\t\tcorps_commander = {\n")
        f.write("\t\t\ttraits = { }\n")
        f.write("\t\t\tskill = 2\n")
        f.write("\t\t\tattack_skill = 2\n")
        f.write("\t\t\tdefense_skill = 2\n")
        f.write("\t\t\tplanning_skill = 2\n")
        f.write("\t\t\tlogistics_skill = 2\n")
        f.write("\t\t}\n")
        f.write("\t}\n\n")

        # 4. 海军将领
        f.write(f"\t{tag}_admiral_1 = {{\n")
        f.write(f'\t\tname = "{country_name} Admiral"\n')
        f.write("\t\tportraits = {\n")
        f.write("\t\t\tarmy = { large = GFX_Portrait_Europe_Generic_navy_1 }\n")
        f.write("\t\t}\n")
        f.write("\t\tnavy_leader = {\n")
        f.write("\t\t\ttraits = { }\n")
        f.write("\t\t\tskill = 2\n")
        f.write("\t\t\tattack_skill = 2\n")
        f.write("\t\t\tdefense_skill = 2\n")
        f.write("\t\t\tmaneuvering_skill = 2\n")
        f.write("\t\t\tcoordination_skill = 2\n")
        f.write("\t\t}\n")
        f.write("\t}\n\n")

        # 5. 科学家（4种专业，避免自动生成失败）
        specializations = ["air", "industry", "naval", "army"]
        for i, spec in enumerate(specializations, 1):
            f.write(f"\t{tag}_scientist_{i} = {{\n")
            f.write(f'\t\tname = "{country_name} Scientist {i}"\n')
            f.write("\t\tportraits = {\n")
            f.write("\t\t\tcivilian = { large = GFX_Portrait_Europe_Generic_1 }\n")
            f.write("\t\t}\n")
            f.write("\t\tscientist = {\n")
            f.write("\t\t\tskills = {\n")
            f.write(f"\t\t\t\tspecialization_{spec} = 2\n")
            f.write("\t\t\t}\n")
            f.write("\t\t\ttraits = { }\n")
            f.write("\t\t}\n")
            f.write("\t}\n\n")

        f.write("}\n")


def _write_dynamic_countries(output_dir, count=75):
    """生成 dynamic countries 用于内战、傀儡等系统占位。

    HOI4 wiki: "If the mod doesn't have enough dynamic countries defined, the game
    will crash if there is a sufficient amount of non-dynamic countries..."

    【EaW 验证做法】每个 dynamic tag 必须有【独立】的 country file（D01.txt～D75.txt），
    不能所有 tag 共享一个 Dynamic.txt —— 那会让引擎在 AI/划分命名组时把 80 个 tag
    视为同一国家，触发 "Multiple name groups for D69" 和 naval goal 重复添加循环，
    最终 ACCESS_VIOLATION 崩溃。EaW 用 75 个，我们对齐。
    """
    ct_dir = os.path.join(output_dir, "common", "country_tags")
    co_dir = os.path.join(output_dir, "common", "countries")
    os.makedirs(ct_dir, exist_ok=True)
    os.makedirs(co_dir, exist_ok=True)

    # 每个 dynamic tag 一个独立文件（EaW 格式：仅 2 行）
    # 用简单哈希生成不同颜色，避免所有 D 国颜色一样
    for i in range(1, count + 1):
        tag = f"D{i:02d}"
        r = (i * 37) % 200 + 40
        g = (i * 73) % 200 + 40
        b = (i * 113) % 200 + 40
        with open(os.path.join(co_dir, f"{tag}.txt"), "w") as f:
            f.write("use_legacy_ai_pp_spend = yes\n")
            f.write(f"color = {{ {r} {g} {b} }}\n")

    # dynamic_tags = yes 标记后的 tag 都是临时内战国
    with open(os.path.join(ct_dir, "zz_dynamic_countries.txt"), "w") as f:
        f.write("dynamic_tags = yes\n\n")
        for i in range(1, count + 1):
            tag = f"D{i:02d}"
            f.write(f'{tag} = "countries/{tag}.txt"\n')


def _write_country(tag, capital_state_id, output_dir):
    """写一个默认国家。capital_state_id 必须是有效的 State ID，不是省份ID！"""
    os.makedirs(os.path.join(output_dir, "common", "country_tags"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "common", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "units"), exist_ok=True)

    # 生成 80 个 dynamic countries（HOI4 强制要求，否则崩溃）
    _write_dynamic_countries(output_dir)

    with open(os.path.join(output_dir, "common", "country_tags", "00_countries.txt"), "w") as f:
        f.write(f'{tag} = "countries/{tag}.txt"\n')

    with open(os.path.join(output_dir, "common", "countries", f"{tag}.txt"), "w") as f:
        f.write("graphical_culture = western_european_gfx\n")
        f.write("graphical_culture_2d = western_european_2d\n")
        f.write("color = { 100 100 200 }\n")

    # 生成国家人物（country_leader/将领/科学家）
    _write_country_characters(tag, output_dir)
    # 生成国家名字数组（避免 character_manager 找不到名字崩溃）
    _write_country_names(tag, output_dir)
    # 生成国家肖像池（避免 scientist 自动生成崩溃）★崩溃根因★
    _write_country_portraits(tag, output_dir)
    # 生成国家颜色（地图上显示）
    _write_country_colors(tag, (100, 100, 200), output_dir)

    with open(os.path.join(output_dir, "history", "countries", f"{tag} - Fantasy.txt"), "w") as f:
        f.write(f"capital = {capital_state_id}\n")
        f.write(f'oob = "{tag}_1936"\n')
        f.write("set_research_slots = 3\n")
        # 不 recruit_character — 让 HOI4 自动从 common/characters 生成 leader。
        # 显式 recruit 在 1.17 可能引用格式不对的字段导致 AI 启动校验失败崩溃
        f.write("set_politics = {\n\truling_party = neutrality\n")
        f.write('\tlast_election = "1932.1.1"\n\telection_frequency = 48\n')
        f.write("\telections_allowed = no\n}\n")
        f.write("set_popularities = {\n\tdemocratic = 10\n\tfascism = 5\n")
        f.write("\tcommunism = 5\n\tneutrality = 80\n}\n")
        # Wiki: 文件不能以 recruit_character 结尾，最后必须有非 recruit 行
        # 这里 set_popularities 已经是最后一个，所以本身就符合要求
        f.write("\n# end of country history\n")

    with open(os.path.join(output_dir, "history", "units", f"{tag}_1936.txt"), "w") as f:
        f.write("units = { }\n\n")


# ────────────────── 本地化 ──────────────────

def _write_localisation(mod_name, tag, states, output_dir, region_count=24):
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")
    with open(os.path.join(d, f"{safe}_l_english.yml"), "w", encoding="utf-8-sig") as f:
        f.write("l_english:\n")
        for sid in states:
            f.write(f' STATE_{sid}:0 "State {sid}"\n')
        for rid in range(1, region_count + 1):
            f.write(f' STRATEGICREGION_{rid}:0 "Region {rid}"\n')
        f.write(f' SUPPLYAREA_1:0 "Fantasy Supply"\n')
        f.write(f' FANTASY_BOOKMARK:0 "Fantasy World"\n')
        f.write(f' FANTASY_BOOKMARK_DESC:0 "A fantasy world awaits."\n')
        f.write(f' {tag}:0 "Fantasy Country"\n')
        f.write(f' {tag}_DEF:0 "Fantasy Country"\n')
        f.write(f' {tag}_ADJ:0 "Fantasy"\n')
        f.write(f' {tag}_BOOKMARK_DESC:0 "Play as Fantasy Country"\n')
        f.write(f' OTHER_BOOKMARK_DESC:0 "Other nations"\n')


# ────────────────── descriptor.mod + 空目录 ──────────────────

def _write_descriptor(mod_name, output_dir):
    rp = "\n".join(f'replace_path="{p}"' for p in REPLACE_PATHS)

    # 内部 descriptor.mod（MOD目录内）
    with open(os.path.join(output_dir, "descriptor.mod"), "w") as f:
        f.write(f'version="{DEFAULT_MOD_VERSION}"\n')
        f.write('tags={\n\t"Alternative History"\n\t"Map"\n\t"Total Conversion"\n}\n')
        f.write(f'name="{mod_name}"\n')
        f.write(f'supported_version="{DEFAULT_SUPPORTED_VERSION}"\n')
        f.write(rp + "\n")

    # 外层 .mod 文件（MOD目录旁边，启动器需要）
    mod_dir_name = os.path.basename(output_dir)
    outer_mod = os.path.join(os.path.dirname(output_dir), f"{mod_dir_name}.mod")
    with open(outer_mod, "w") as f:
        f.write(f'version="{DEFAULT_MOD_VERSION}"\n')
        f.write('tags={\n\t"Alternative History"\n\t"Map"\n\t"Total Conversion"\n}\n')
        f.write(f'name="{mod_name}"\n')
        f.write(f'supported_version="{DEFAULT_SUPPORTED_VERSION}"\n')
        # path 用正斜杠
        abs_path = os.path.abspath(output_dir).replace("\\", "/")
        f.write(f'path="{abs_path}"\n')
        f.write(rp + "\n")


def _build_division_names_with_phantoms():
    """生成 names_divisions 文件内容：generic fallback + 28 个 vanilla scripted_effects
    引用的幽灵 name groups（ENG_MAR_01/ITA_INF_01 等）。
    防止 vanilla 创建 division template 时找不到 name group → 坏 template → AI 崩。
    """
    out = (
        "GENERIC_INF_DIVISION = {\n"
        '\tname = "Infantry Division"\n'
        "\tcan_use = { always = yes }\n"
        '\tdivision_types = { "infantry" }\n'
        '\tfallback_name = "%d Infantry Division"\n'
        "}\n\n"
    )
    PHANTOM_GROUPS = [
        "AFG_INF_01", "BUL_INF_04", "BUL_INF_06", "ENG_MAR_01", "ETH_ARB",
        "GER_SS_01", "ITA_CAM_01", "ITA_CAM_02", "ITA_CAV_03", "ITA_INF_01",
        "ITA_INF_02", "JAP_CAV_01", "JAP_INF_01", "JAP_MIL_02", "NOR_INF_01",
        "NOR_MIL_01", "POL_INF_01", "PRC_GAR_01", "PRC_INF_01", "SOV_CAV_01",
        "SOV_INF_01", "SOV_INF_03", "SOV_INF_04", "SOV_JAP_INF", "SOV_MEC_01",
        "SOV_MOT_01", "SPD_INF_02", "USA_INF_01",
    ]
    for g in PHANTOM_GROUPS:
        out += (
            f"{g} = {{\n"
            f'\tname = "{g}"\n'
            "\tcan_use = { always = yes }\n"
            '\tdivision_types = { "infantry" }\n'
            f'\tfallback_name = "%d {g}"\n'
            "}\n\n"
        )
    return out


def _create_replace_dirs(output_dir):
    """为所有 replace_path 创建目录。

    精简策略：所有 REPLACE_PATHS 里的目录我们都自己生成了内容
    （history/*, common/country_tags, common/countries, common/characters,
    common/names, map/strategicregions, map/supplyareas）。
    history/general 里没有内容，放一个空占位文件避免空目录。
    """
    for p in REPLACE_PATHS:
        os.makedirs(os.path.join(output_dir, p), exist_ok=True)

    # history/general 没有自动生成的内容，放空占位
    hg = os.path.join(output_dir, "history", "general")
    if os.path.isdir(hg) and not os.listdir(hg):
        with open(os.path.join(hg, "00_placeholder.txt"), "w") as f:
            f.write("# Empty - no generals defined\n")

    # common/ai_* 必须 replace 掉 vanilla 但不能完全空 —— AI 5x 速度多线程
    # 评估时找不到模板/策略/焦点会 null deref → client_ping 崩溃。
    # 策略：从 vanilla 完整复制 ai_templates/ai_strategy/ai_focuses/ai_equipment/
    #       ai_strategy_plans/ai_navy/fleet|taskforce，让 AI 系统完整在场。
    # 例外：ai_navy/goals 必须保持单个 generic 文件（vanilla 的 goals_ENG.txt
    #      等用 available_for={ENG} 引用已删国家，过滤器失败 → 全 naval goal
    #      落到唯一国家头上重复添加溢出崩溃，已实测验证）
    from data.constants import DEFAULT_HOI4_PATH
    import shutil as _sh

    ai_full_copy_dirs = (
        "common/ai_strategy",
        "common/ai_focuses",
        "common/ai_equipment",
        "common/ai_strategy_plans",
        "common/ai_navy/fleet",
        "common/ai_navy/taskforce",
        # 注意：common/ai_templates 不在这里 —— 改为阶段 4 自建无 allowed 过滤的 template
        # 注意：common/scripted_effects 不在这里 —— vanilla 文件名"看起来 generic"
        #       的 6 个文件（00_/NORDIC_/SP_/SS_/operation_strat_/zzz_play_speech_）
        #       内容硬编码 FRA/GER/SOV/MEX 等已删 TAG → 解析失败 404 errors →
        #       AI tick 撞 null → 5x 多线程 race → 崩
    )
    # 关键：只复制 generic / default / documentation 等"通用"文件，
    # 跳过所有 TAG-specific 的：
    #   ENG.txt, GER_naval.txt          (3 大写字母开头)
    #   templates_CHI.txt, AFG_default  (3 大写字母 token，前后用 _ 或 . 分隔)
    #   GUAY.txt                        (4 大写字母开头)
    # 这些文件用 allowed={original_tag=ENG} 等过滤器引用我们删除的国家，
    # 5x 速度 AI 多线程评估时撞 null → client_ping 崩
    import re as _re
    # 匹配文件名中任何"3-4 大写字母的独立 token"，前后是开头/结尾或 _ 或 .
    TAG_TOKEN = _re.compile(r"(?:^|[_.])[A-Z]{3,4}(?:[_.]|$)")
    # 显式黑名单：即使文件名没有 TAG token，但内容引用已删国家/TAG 的文件
    FILENAME_BLACKLIST = {
        "zz_debug_effects.txt",       # 含 ITA_INF_01/Cavalleria 等破 division template
    }
    def _is_generic(filename):
        if filename in FILENAME_BLACKLIST:
            return False  # 强制跳过
        if filename.startswith("_") or "documentation" in filename.lower():
            return True  # 文档复制 OK
        return not TAG_TOKEN.search(filename)
    # 关键：复制后必须 scrub 所有 blocked_for = {...} 块
    # vanilla 的 generic_naval/planes/tank 等"看似 generic"文件内部都含
    # `blocked_for = { ENG FRA GER ... }` → AI tick null deref → 崩
    _BLOCKED_FOR_RE = _re.compile(r"blocked_for\s*=\s*\{[^{}]*\}", _re.DOTALL)
    _DEAD_TAG_RE = _re.compile(
        r"\b(ENG|FRA|GER|ITA|JAP|SOV|USA|CHI|POL|HUN|ROM|YUG|BUL|TUR|GRE|"
        r"MEX|CAN|FIN|NOR|SWE|DEN|CZE|SIA|RAJ|AST|NZL|SAF)\b"
    )
    _AVAILABLE_FOR_RE = _re.compile(r"available_for\s*=\s*\{[^{}]*\}", _re.DOTALL)
    def _scrub_file(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
        except Exception:
            return
        new = _BLOCKED_FOR_RE.sub("blocked_for = {}", txt)
        def _av_sub(m):
            return "available_for = {}" if _DEAD_TAG_RE.search(m.group(0)) else m.group(0)
        new = _AVAILABLE_FOR_RE.sub(_av_sub, new)
        if new != txt:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)

    for sub in ai_full_copy_dirs:
        dst = os.path.join(output_dir, *sub.split("/"))
        src = os.path.join(DEFAULT_HOI4_PATH, *sub.split("/"))
        os.makedirs(dst, exist_ok=True)
        if os.path.isdir(src):
            for fn in os.listdir(src):
                if not _is_generic(fn):
                    continue  # 跳过 TAG-specific
                sp = os.path.join(src, fn)
                if os.path.isfile(sp):
                    dp = os.path.join(dst, fn)
                    _sh.copy2(sp, dp)
                    _scrub_file(dp)  # 清掉内含的 vanilla dead TAG
        if not os.listdir(dst):
            with open(os.path.join(dst, "00_placeholder.txt"), "w") as f:
                f.write(f"# Empty — no vanilla generic files for {sub}\n")

    # === 阶段 1：scripted_effects 完全空（不复制任何 vanilla 文件）===
    se_dir = os.path.join(output_dir, "common", "scripted_effects")
    os.makedirs(se_dir, exist_ok=True)
    with open(os.path.join(se_dir, "00_placeholder.txt"), "w", encoding="utf-8") as f:
        f.write("# Empty — TC MOD doesn't need vanilla scripted_effects\n")
        f.write("# Placeholder effect to keep file non-empty\n")
        f.write("placeholder_effect = { }\n")

    # === 阶段 3：scripted_triggers + dynamic_modifiers 也 replace 成空 ===
    # vanilla 这两个目录的文件大量引用 FRA/GER/SOV 等已删 TAG，原理同 scripted_effects
    for sub in ("common/scripted_triggers", "common/dynamic_modifiers"):
        d2 = os.path.join(output_dir, *sub.split("/"))
        os.makedirs(d2, exist_ok=True)
        with open(os.path.join(d2, "00_placeholder.txt"), "w", encoding="utf-8") as f:
            f.write(f"# Empty — TC MOD replaces vanilla {sub}\n")

    # === common/achievements.txt（顶级单文件覆盖）===
    # vanilla 7726 行含 651 个硬编码 state ID（owns_state/controls_state），
    # 成就系统每 tick 查 state → "State 361 not found" 刷几万次 → 5x 崩。
    ach_path = os.path.join(output_dir, "common", "achievements.txt")
    os.makedirs(os.path.dirname(ach_path), exist_ok=True)
    with open(ach_path, "w", encoding="utf-8") as f:
        f.write("# Empty — TC MOD disables vanilla achievements\n")

    # === common/decisions（replace 空）===
    # vanilla decisions/GER.txt/ENG.txt/CHL.txt 硬编码 state 361 等 vanilla ID
    # 即便 allowed={tag=GER} 过滤，scope block 仍被全局评估 → State not found 狂刷
    dec_dir = os.path.join(output_dir, "common", "decisions")
    os.makedirs(dec_dir, exist_ok=True)
    with open(os.path.join(dec_dir, "00_placeholder.txt"), "w", encoding="utf-8") as f:
        f.write("# Empty — TC MOD replaces vanilla decisions\n")
    dcat_dir = os.path.join(dec_dir, "categories")
    os.makedirs(dcat_dir, exist_ok=True)
    with open(os.path.join(dcat_dir, "00_categories.txt"), "w", encoding="utf-8") as f:
        f.write("# Empty\n")

    # === 同名空文件覆盖 3 个 DLC on_actions（硬编码 vanilla state ID）===
    # 14_sea_on_actions.txt — SEA DLC，on_startup 初始化 global.great_wall_state
    #                        数组，硬编码 CHI state 621/615/1046/608/614/... ×10+
    # 12_wuw_on_actions.txt — WUW DLC，GER_navy_democratic_modifier 等
    # 13_goe_on_actions.txt — GOE DLC，AFG/RAJ/PER/PAL 相关
    # 不是 replace_path（会破坏 vanilla 核心 on_actions），是文件级同名覆盖
    oa_dir = os.path.join(output_dir, "common", "on_actions")
    os.makedirs(oa_dir, exist_ok=True)
    for fn in ("12_wuw_on_actions.txt", "13_goe_on_actions.txt",
               "14_sea_on_actions.txt"):
        with open(os.path.join(oa_dir, fn), "w", encoding="utf-8") as f:
            f.write(f"# Empty — TC MOD overrides vanilla {fn}\n")

    # === common/raids（2026-04-08 走时间崩溃根因）===
    # vanilla land_infiltration_custom.txt 用 global.great_wall_state 未初始化
    # 变量 → scope None → 每 AI tick 刷几万错误 → tbb worker race → 崩。
    # 完全 replace 为空（TC MOD 不需要空袭/伞降/核袭系统）。
    raids_dir = os.path.join(output_dir, "common", "raids")
    os.makedirs(raids_dir, exist_ok=True)
    with open(os.path.join(raids_dir, "00_placeholder.txt"), "w", encoding="utf-8") as f:
        f.write("# Empty — TC MOD disables vanilla raids system\n")
    cat_dir = os.path.join(raids_dir, "categories")
    os.makedirs(cat_dir, exist_ok=True)
    with open(os.path.join(cat_dir, "00_categories.txt"), "w", encoding="utf-8") as f:
        f.write("categories = {\n}\n")

    # === 阶段 5 "Nuke AI" 已回退（2026-04-08）===
    # 加这 7 个 replace_path + 空占位会让 vanilla on_actions 的 country_event /
    # add_ideas / dynamic_modifier 调用全部指向 null → 9000+ 行错误 → 崩。
    # 见 memory/ai_tick_crash_rootcauses.md

    # === 阶段 4：自建 ai_templates，无 allowed 过滤 ===
    at_dir = os.path.join(output_dir, "common", "ai_templates")
    os.makedirs(at_dir, exist_ok=True)
    # 删除可能存在的 vanilla 复制
    for fn in os.listdir(at_dir):
        os.remove(os.path.join(at_dir, fn))
    with open(os.path.join(at_dir, "00_generic_templates.txt"), "w", encoding="utf-8") as f:
        f.write("""# Generic AI templates — no allowed filter, matches all countries
infantry_generic = {
\trole = infantry
\tupgrade_prio = { base = 2 }
\tinfantry_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tinfantry = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
garrison_generic = {
\trole = garrison
\tupgrade_prio = { base = 1 }
\tgarrison_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tinfantry = 4
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
cavalry_generic = {
\trole = cavalry
\tupgrade_prio = { base = 1 }
\tcavalry_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tcavalry = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
motorized_generic = {
\trole = motorized
\tupgrade_prio = { base = 1 }
\tmotorized_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tmotorized = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
mechanized_generic = {
\trole = mechanized
\tupgrade_prio = { base = 1 }
\tmechanized_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tmechanized = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
armor_generic = {
\trole = armor
\tupgrade_prio = { base = 2 }
\tarmor_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tlight_armor = 4
\t\t\t\tmotorized = 4
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
""")
    # ai_navy/goals/goals_generic.txt — 关键崩溃根因！
    # vanilla 的 goals_generic.txt 含 `blocked_for = { ENG FRA GER ITA JAP SOV USA }`
    # 10 处硬编码已删 TAG → AI tick 评估 naval goal 时 null deref → tbb worker 崩。
    # 必须【自建】不带 blocked_for 的干净版本，不能复制 vanilla。
    ang_dst_dir = os.path.join(output_dir, "common", "ai_navy", "goals")
    os.makedirs(ang_dst_dir, exist_ok=True)
    with open(os.path.join(ang_dst_dir, "goals_generic.txt"), "w", encoding="utf-8") as f:
        f.write("""# Self-built generic naval goals — NO blocked_for TAG references
# (vanilla lists ENG/FRA/GER/ITA/JAP/SOV/USA which crash our TC MOD)
generic_naval_invasion_support = { objective_type = naval_invasion_support
\tmin_priority = 4  max_priority = 14 }
generic_mine_sweeping = { objective_type = mines_sweeping
\tmin_priority = 2  max_priority = 8 }
generic_invasion_defense = { objective_type = naval_invasion_defense
\tmin_priority = 15 max_priority = 25 }
generic_coast_defense = { objective_type = coast_defense
\tmin_priority = 1  max_priority = 16 }
generic_convoy_protection = { objective_type = convoy_protection
\tmin_priority = 1  max_priority = 5 }
generic_convoy_raiding = { objective_type = convoy_raiding
\tmin_priority = 3  max_priority = 7 }
generic_naval_dominance = { objective_type = naval_dominance
\tmin_priority = 1  max_priority = 13 }
generic_mine_laying = { objective_type = mines_planting
\tmin_priority = 2  max_priority = 8 }
generic_training = { objective_type = training
\tmin_priority = 10 max_priority = 20 }
generic_naval_blockade = { objective_type = naval_blockade
\tmin_priority = 10 max_priority = 20 }
generic_strike_force = { objective_type = strike_force_objective
\tmin_priority = 10 max_priority = 20 }
""")

    # ai_peace 无 generic 文件，写占位
    apd = os.path.join(output_dir, "common", "ai_peace")
    os.makedirs(apd, exist_ok=True)
    if not os.listdir(apd):
        with open(os.path.join(apd, "00_placeholder.txt"), "w") as f:
            f.write("# Empty — vanilla has no generic ai_peace\n")

    # common/units/names* 必须 replace 掉 vanilla — vanilla 的 fallback 名字组
    # 会匹配我们 75 个 dynamic tag (D01..D75)，触发 "Multiple name groups for Dxx"
    # 错误，初始化 division/ship/operative 命名时崩。
    # 但不能完全空：HOI4 要求每种单位类型至少有一个 fallback 命名组，否则
    # 报 "No fallback name group found for X" 同样崩。
    # 解决：提供单一全局 fallback 组（无 for_countries 即匹配所有国家）
    _UNITS_FALLBACK_FILES = {
        "names_railway_guns": (
            "RG_COMMON_FALLBACK = {\n"
            "\ttype = railway_gun\n"
            '\tfallback_name = "Railway Gun %d"\n'
            "}\n"
        ),
        "names_divisions": _build_division_names_with_phantoms(),
        "names_ships": (
            "GENERIC_SHIPS = {\n"
            "\tname = NAME_THEME_GENERIC\n"
            "\ttype = ship\n"
            '\tprefix = ""\n'
            '\tfallback_name = "Ship %d"\n'
            "}\n"
        ),
        "codenames_operatives": (
            "GENERIC_OPERATIVE_CODENAMES = {\n"
            "\tname = GENERIC_OPERATIVE_CODENAME\n"
            "\ttype = codename\n"
            '\tfallback_name = "Agent %d"\n'
            "}\n"
        ),
        # common/units/names = 团/营级单位名（regiment_names），可空
        "names": "# Empty — regiment-level unit names (optional)\n",
    }
    for sub, content in _UNITS_FALLBACK_FILES.items():
        d2 = os.path.join(output_dir, "common", "units", sub)
        os.makedirs(d2, exist_ok=True)
        if not os.listdir(d2):
            with open(os.path.join(d2, "00_generic_fallback.txt"), "w",
                      encoding="utf-8") as f:
                f.write(content)


def _write_bookmark(mod_name, country_tags, output_dir):
    """生成 bookmark 文件。
    策略：
    1. 用同名文件 the_gathering_storm.txt / blitzkrieg.txt 覆盖原版为【空 bookmarks 块】
       - 原因：原版 bookmark 引用 GER/ENG/JAP 等我们已移除的国家，选中会崩溃
       - 覆盖为空让玩家在菜单里看不到原版 bookmark
    2. 用 z_fantasy.txt 写我们自己的 bookmark（z_ 前缀确保排序在后，不会和原版冲突）
    """
    d = os.path.join(output_dir, "common", "bookmarks")
    os.makedirs(d, exist_ok=True)

    # --- 1. 屏蔽原版 bookmark ---
    # 原版有两个 bookmark 文件：the_gathering_storm.txt 和 blitzkrieg.txt
    # 写一个空的 bookmarks 块覆盖它们
    empty_bookmarks = "bookmarks = {\n}\n"
    with open(os.path.join(d, "the_gathering_storm.txt"), "w") as f:
        f.write(empty_bookmarks)
    with open(os.path.join(d, "blitzkrieg.txt"), "w") as f:
        f.write(empty_bookmarks)

    # --- 2. 写我们自己的 bookmark ---
    with open(os.path.join(d, "z_fantasy.txt"), "w") as f:
        f.write("bookmarks = {\n")
        f.write("\tbookmark = {\n")
        f.write(f'\t\tname = FANTASY_BOOKMARK\n')
        f.write(f'\t\tdesc = FANTASY_BOOKMARK_DESC\n')
        f.write('\t\tdate = 1936.1.1.12\n')
        f.write('\t\tpicture = GFX_select_date_1936\n')
        if country_tags:
            f.write(f'\t\tdefault_country = "{country_tags[0]}"\n')
        f.write("\t\tdefault = yes\n\n")
        # 第一个国家作为主要国家
        for i, tag in enumerate(country_tags):
            f.write(f'\t\t"{tag}" = {{\n')
            f.write(f'\t\t\thistory = "{tag}_BOOKMARK_DESC"\n')
            f.write(f'\t\t\tideology = neutrality\n')
            if i > 0:
                f.write(f'\t\t\tminor = yes\n')
            f.write(f'\t\t}}\n')
        # 其他国家占位
        f.write('\t\t"---" = {\n')
        f.write('\t\t\thistory = OTHER_BOOKMARK_DESC\n')
        f.write('\t\t}\n')
        # effect — randomize_weather 是必须的
        f.write('\t\teffect = {\n')
        f.write('\t\t\trandomize_weather = 22345\n')
        f.write('\t\t}\n')
        f.write("\t}\n")
        f.write("}\n")


# 注意：不再生成 ideologies 和 state_category — 用原版的（EaW 验证做法）
# 原版的 common/ideologies 和 common/state_category 已经足够完整


# ────────────────── 使用管理器数据导出 ──────────────────

def _write_states_from_mgr(state_mgr, country_mgr, province_map, output_dir, tile_map=None):
    """用 StateManager + CountryManager 的数据写 State 文件"""
    d = os.path.join(output_dir, "history", "states")
    os.makedirs(d, exist_ok=True)

    # 预计算沿海省份集合（用于 state 级 naval_base 分配）
    coastal_set = set()
    if tile_map is not None and province_map is not None:
        coastal_set = set(int(p) for p in get_coastal_provinces(tile_map, province_map))

    # state_category → 建筑等级映射（vanilla 风格，中等发展水平）
    # 顺序：infrastructure / arms_factory / industrial_complex / dockyard / air_base
    _CAT_BUILDINGS = {
        "wasteland":    (0, 0, 0, 0, 0),
        "enclave":      (1, 0, 0, 0, 0),
        "tiny_island":  (1, 0, 0, 0, 0),
        "small_island": (1, 0, 0, 0, 0),
        "pastoral":     (2, 0, 1, 0, 0),
        "rural":        (2, 0, 1, 0, 0),
        "town":         (3, 1, 2, 0, 1),
        "large_town":   (4, 1, 3, 0, 1),
        "city":         (4, 2, 4, 0, 2),
        "large_city":   (5, 3, 5, 0, 2),
        "metropolis":   (6, 4, 6, 0, 3),
        "megalopolis":  (6, 5, 7, 0, 3),
    }
    # 沿海 state 的额外 dockyard（覆盖上面 0）
    _COASTAL_DOCKYARDS = {
        "pastoral": 1, "rural": 1,
        "town": 1, "large_town": 2,
        "city": 2, "large_city": 3,
        "metropolis": 3, "megalopolis": 4,
    }

    for sid, state in state_mgr.states.items():
        if not state.provinces:
            continue

        # 过滤掉海洋/湖泊省份（State 只能包含陆地省份）
        if tile_map is not None:
            land_provs = [p for p in state.provinces if _is_land(p, province_map, tile_map)]
        else:
            land_provs = list(state.provinces)
        if not land_provs:
            continue

        owner = ""
        if country_mgr:
            owner = country_mgr.get_owner_of_state(sid)
        if not owner and country_mgr and country_mgr.countries:
            owner = list(country_mgr.countries.keys())[0]

        # 确保文件名安全
        safe_name = state.name.replace("/", "_").replace("\\", "_").replace(":", "_")

        with open(os.path.join(d, f"{sid}-{safe_name}.txt"), "w") as f:
            f.write("state = {\n")
            f.write(f"\tid = {sid}\n")
            f.write(f'\tname = "STATE_{sid}"\n')
            f.write(f"\tmanpower = {state.manpower}\n")
            f.write(f"\tstate_category = {state.category}\n\n")
            f.write("\thistory = {\n")
            if owner:
                f.write(f"\t\towner = {owner}\n")
                f.write(f"\t\tadd_core_of = {owner}\n")
            # 根据 state_category 写建筑等级
            infra, arms, indu, dock, air = _CAT_BUILDINGS.get(
                state.category, (2, 1, 1, 0, 0)
            )
            # 沿海 state 升级 dockyard 并分配 naval_base
            state_coastal_provs = [p for p in land_provs if p in coastal_set]
            is_coastal_state = bool(state_coastal_provs)
            if is_coastal_state:
                dock = max(dock, _COASTAL_DOCKYARDS.get(state.category, 1))

            f.write("\t\tbuildings = {\n")
            f.write(f"\t\t\tinfrastructure = {max(infra, 1)}\n")
            if arms > 0:
                f.write(f"\t\t\tarms_factory = {arms}\n")
            if indu > 0:
                f.write(f"\t\t\tindustrial_complex = {indu}\n")
            if dock > 0 and is_coastal_state:
                f.write(f"\t\t\tdockyard = {dock}\n")
            if air > 0:
                f.write(f"\t\t\tair_base = {air}\n")
            # naval_base 必须按【沿海省份ID】分配，格式是嵌套块
            if is_coastal_state:
                nb_level = 3 if state.category in (
                    "city", "large_city", "metropolis", "megalopolis"
                ) else 2
                nb_prov = state_coastal_provs[0]
                f.write(f"\t\t\t{nb_prov} = {{\n")
                f.write(f"\t\t\t\tnaval_base = {nb_level}\n")
                f.write(f"\t\t\t}}\n")
            f.write("\t\t}\n")
            # VP（只用陆地省份的VP）
            vp_written = False
            for vpid, vpval in state.victory_points.items():
                if vpid in land_provs:
                    f.write(f"\t\tvictory_points = {{ {vpid} {vpval} }}\n")
                    vp_written = True
            if not vp_written and land_provs:
                f.write(f"\t\tvictory_points = {{ {land_provs[0]} 1 }}\n")
            f.write("\t}\n\n")
            f.write("\tprovinces = {\n")
            f.write("\t\t" + " ".join(str(p) for p in land_provs) + "\n")
            f.write("\t}\n}\n")


def _write_countries_from_mgr(country_mgr, output_dir, states):
    """用 CountryManager 的数据写国家文件。
    注意：country_mgr.capital 存的是【省份ID】，但 HOI4 的 capital 字段要求【State ID】。
    这里会自动把省份ID转换成包含该省份的State ID。
    """
    os.makedirs(os.path.join(output_dir, "common", "country_tags"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "common", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "units"), exist_ok=True)

    # 构建 省份ID -> State ID 反查表
    prov_to_state = {}
    for sid, provs in states.items():
        for p in provs:
            prov_to_state[p] = sid
    if not states:
        raise ValueError(
            "无法导出国家：没有生成任何 State。请先生成省份和 State 数据。"
        )
    fallback_state = min(states.keys())

    # 生成 80 个 dynamic countries（HOI4 强制要求，否则崩溃）
    _write_dynamic_countries(output_dir)

    # country_tags
    with open(os.path.join(output_dir, "common", "country_tags", "00_countries.txt"), "w") as f:
        for tag in country_mgr.countries:
            f.write(f'{tag} = "countries/{tag}.txt"\n')

    for tag, c in country_mgr.countries.items():
        r, g, b = c.color
        with open(os.path.join(output_dir, "common", "countries", f"{tag}.txt"), "w") as f:
            f.write("graphical_culture = western_european_gfx\n")
            f.write("graphical_culture_2d = western_european_2d\n")
            f.write(f"color = {{ {r} {g} {b} }}\n")

        # 生成国家人物（country_leader/将领/科学家）
        _write_country_characters(tag, output_dir, country_name=c.name)
        # 生成国家名字数组
        _write_country_names(tag, output_dir, country_name=c.name)
        # 生成国家肖像池（避免 scientist 自动生成崩溃）★崩溃根因★
        _write_country_portraits(tag, output_dir)
        # 生成国家颜色
        _write_country_colors(tag, c.color, output_dir)

        # 省份ID → State ID 转换
        capital_state = prov_to_state.get(c.capital, fallback_state)

        # 意识形态白名单校验：非法的 ruling_party 降级为 neutrality，
        # 非法的 popularities 键会被丢弃，缺失的键补 0，总和归一化到 100
        ruling = c.ruling_party if c.ruling_party in VALID_MAIN_IDEOLOGIES else "neutrality"
        pops = {k: max(0, int(v)) for k, v in (c.popularities or {}).items()
                if k in VALID_MAIN_IDEOLOGIES}
        for k in VALID_MAIN_IDEOLOGIES:
            pops.setdefault(k, 0)
        total = sum(pops.values())
        if total <= 0:
            # 全空 → ruling_party 100%
            pops = {k: (100 if k == ruling else 0) for k in VALID_MAIN_IDEOLOGIES}
        elif total != 100:
            # 按比例归一化，四舍五入后再用 ruling_party 补余数
            scaled = {k: round(v * 100 / total) for k, v in pops.items()}
            diff = 100 - sum(scaled.values())
            scaled[ruling] = scaled.get(ruling, 0) + diff
            pops = scaled

        # 安全文件名
        safe_name = c.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace('"', "")
        with open(os.path.join(output_dir, "history", "countries", f"{tag} - {safe_name}.txt"), "w") as f:
            f.write(f"capital = {capital_state}\n")
            f.write(f'oob = "{tag}_1936"\n')
            f.write("set_research_slots = 3\n")
            # 强制加载 vanilla generic_focus 通用国策树，避免引擎尝试匹配
            # FRA/GER/ENG 等特定国策树（触发条件引用 vanilla idea/trigger 会错）
            f.write("load_focus_tree = generic_focus\n")
            # 不 recruit_character — 让 HOI4 自动从 common/characters 生成 leader。
            # 显式 recruit 在 1.17 可能引用格式不对（id/expire 废弃字段）导致 AI
            # 启动时校验失败崩溃
            f.write(f"set_politics = {{\n\truling_party = {ruling}\n")
            f.write('\tlast_election = "1932.1.1"\n\telection_frequency = 48\n')
            f.write("\telections_allowed = no\n}\n")
            f.write("set_popularities = {\n")
            for party in VALID_MAIN_IDEOLOGIES:
                f.write(f"\t{party} = {pops[party]}\n")
            f.write("}\n")
            # 注意：不再在 country history 写 add_ideas —— 引用未定义 idea 会触发
            # AI 每 tick 评估时崩。national_spirits 数据保留在 country_mgr 但不
            # 写入 history（以后真要做 spirits 必须先把所有 ideas 完整定义）
            f.write("\n# end of country history\n")

        # OOB：必须有至少一个 division template + 一个部署的 division，
        # 否则 5x 速度时 AI 多线程评估空军队 → null deref → client_ping 崩
        # location 用国家首都所在的 land province
        capital_prov = c.capital if c.capital else 1
        # 如果 capital 是 0 或不在该国土地，找一个 fallback
        country_states = country_mgr.get_states_of_country(tag)
        any_land_prov = capital_prov
        if country_states:
            first_state = states.get(country_states[0]) if isinstance(states, dict) else None
            if first_state:
                any_land_prov = first_state[0]
        with open(os.path.join(output_dir, "history", "units", f"{tag}_1936.txt"), "w") as f:
            f.write("division_template = {\n")
            f.write(f'\tname = "Infantry Division"\n')
            f.write("\tregiments = {\n")
            f.write("\t\tinfantry = { x = 0 y = 0 }\n")
            f.write("\t\tinfantry = { x = 0 y = 1 }\n")
            f.write("\t\tinfantry = { x = 0 y = 2 }\n")
            f.write("\t}\n")
            f.write("}\n\n")
            f.write("units = {\n")
            f.write("\tdivision = {\n")
            f.write(f'\t\tname = "1st Infantry Division"\n')
            f.write(f"\t\tlocation = {any_land_prov}\n")
            f.write(f'\t\tdivision_template = "Infantry Division"\n')
            f.write("\t\tstart_experience_factor = 0.3\n")
            f.write("\t}\n")
            f.write("}\n")

    # 不再生成 country ideas 文件 —— 阶段 2 已禁止 country history add_ideas
    # _write_country_ideas(country_mgr, output_dir)

    # 为所有 dynamic countries 写空 OOB 文件
    # （D01-D75 在 country_tags/zz_dynamic_countries.txt 里注册但没有 history/units/Dxx_1936.txt
    #  → AI 5x 多线程评估它们的军队时 null → tbb race → 崩）
    _write_dynamic_country_oobs(output_dir)


def _write_dynamic_country_oobs(output_dir, count=75):
    """为 D01..D75 写空 OOB。HOI4 对每个注册的 country 都会尝试读 history/units/<TAG>_1936.txt"""
    d = os.path.join(output_dir, "history", "units")
    os.makedirs(d, exist_ok=True)
    for i in range(1, count + 1):
        tag = f"D{i:02d}"
        with open(os.path.join(d, f"{tag}_1936.txt"), "w", encoding="utf-8") as f:
            f.write("units = { }\n")


def _write_country_ideas(country_mgr, output_dir):
    """生成 common/ideas/<MOD>_country_ideas.txt 包含所有国家的 national spirits。
    不 replace_path common/ideas（vanilla idea 都保留），只【添加】我们的文件。
    """
    all_spirits = []
    for tag, c in country_mgr.countries.items():
        for spirit in c.national_spirits:
            all_spirits.append(spirit)
    if not all_spirits:
        return

    d = os.path.join(output_dir, "common", "ideas")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "zz_fantasy_country_ideas.txt"), "w", encoding="utf-8") as f:
        f.write("ideas = {\n")
        f.write("\tcountry = {\n")
        for spirit in all_spirits:
            f.write(f"\t\t{spirit.id} = {{\n")
            f.write("\t\t\tallowed = { always = yes }\n")
            f.write("\t\t\tallowed_civil_war = { always = yes }\n")
            f.write("\t\t\tremoval_cost = -1\n")
            f.write(f"\t\t\tpicture = {spirit.picture}\n")
            f.write("\t\t\tmodifier = {\n")
            for k, v in spirit.modifiers.items():
                f.write(f"\t\t\t\t{k} = {v}\n")
            f.write("\t\t\t}\n")
            f.write("\t\t}\n")
        f.write("\t}\n")
        f.write("}\n")


def _write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir,
                             region_count=24):
    """完整本地化。同时生成英文和简体中文版本（HOI4 按语言加载对应yml）。"""
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")

    def _write_yml(lang):
        """lang: 'english' or 'simp_chinese'"""
        with open(os.path.join(d, f"{safe}_l_{lang}.yml"), "w", encoding="utf-8-sig") as f:
            f.write(f"l_{lang}:\n")
            # State 名称
            if state_mgr and state_mgr.states:
                for sid, s in state_mgr.states.items():
                    f.write(f' STATE_{sid}:0 "{s.name}"\n')
            else:
                for sid in states:
                    f.write(f' STATE_{sid}:0 "State {sid}"\n')
            # 国家名称（完整：TAG、TAG_DEF、TAG_ADJ、TAG_leader_despotism等）
            if country_mgr and country_mgr.countries:
                for tag, c in country_mgr.countries.items():
                    f.write(f' {tag}:0 "{c.name}"\n')
                    f.write(f' {tag}_DEF:0 "{c.name}"\n')
                    f.write(f' {tag}_ADJ:0 "{c.name}"\n')
                    f.write(f' {tag}_BOOKMARK_DESC:0 "Play as {c.name}"\n')
                    f.write(f' {tag}_leader_despotism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_leader_conservatism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_leader_nazism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_leader_marxism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_field_marshal_1:0 "{c.name} Marshal"\n')
                    f.write(f' {tag}_general_1:0 "{c.name} General"\n')
                    f.write(f' {tag}_admiral_1:0 "{c.name} Admiral"\n')
                    # 民族精神本地化
                    for spirit in c.national_spirits:
                        nm = spirit.name.replace('"', "'")
                        ds = (spirit.desc or spirit.name).replace('"', "'")
                        f.write(f' {spirit.id}:0 "{nm}"\n')
                        f.write(f' {spirit.id}_desc:0 "{ds}"\n')
            else:
                # 默认国家（无 country_mgr）
                tag = "AAA"
                f.write(f' {tag}:0 "Fantasy Country"\n')
                f.write(f' {tag}_DEF:0 "Fantasy Country"\n')
                f.write(f' {tag}_ADJ:0 "Fantasy"\n')
                f.write(f' {tag}_BOOKMARK_DESC:0 "Play as Fantasy Country"\n')
                f.write(f' {tag}_leader_despotism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_leader_conservatism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_leader_nazism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_leader_marxism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_field_marshal_1:0 "Fantasy Marshal"\n')
                f.write(f' {tag}_general_1:0 "Fantasy General"\n')
                f.write(f' {tag}_admiral_1:0 "Fantasy Admiral"\n')
            for rid in range(1, region_count + 1):
                f.write(f' STRATEGICREGION_{rid}:0 "Region {rid}"\n')
            f.write(f' SUPPLYAREA_1:0 "Fantasy Supply"\n')
            f.write(f' FANTASY_BOOKMARK:0 "Fantasy World"\n')
            f.write(f' FANTASY_BOOKMARK_DESC:0 "A fantasy world awaits."\n')
            f.write(f' OTHER_BOOKMARK_DESC:0 "Other nations"\n')

    # 同时生成英文和简中两个版本
    _write_yml("english")
    _write_yml("simp_chinese")


# ────────────────── 辅助函数 ──────────────────

def _is_land(pid, pm, tm):
    """与 _classify_provinces_fast 保持一致：land_n >= sea_n AND land_n >= lake_n"""
    mask = pm == pid
    if not np.any(mask):
        return False
    tiles = tm[mask]
    l = int(np.sum(tiles == TILE_LAND))
    s = int(np.sum(tiles == TILE_SEA))
    k = int(np.sum(tiles == TILE_LAKE))
    return l >= s and l >= k


def _get_province_type(pid, pm, tm):
    """返回省份类型: 'land', 'sea', 'lake'"""
    mask = pm == pid
    if not np.any(mask):
        return "sea"
    tiles = tm[mask]
    land_n = int(np.sum(tiles == TILE_LAND))
    sea_n = int(np.sum(tiles == TILE_SEA))
    lake_n = int(np.sum(tiles == TILE_LAKE))
    if land_n >= sea_n and land_n >= lake_n:
        return "land"
    elif lake_n > sea_n:
        return "lake"
    return "sea"


def _classify_provinces_fast(province_count, province_map, tile_map):
    """向量化批量分类所有省份，避免逐省份全图扫描"""
    flat_pm = province_map.ravel()
    flat_tm = tile_map.ravel()

    # 用 bincount 一次性统计每个省份中各地块类型的像素数
    n = province_count + 1
    land_counts = np.bincount(flat_pm, weights=(flat_tm == TILE_LAND), minlength=n)
    sea_counts = np.bincount(flat_pm, weights=(flat_tm == TILE_SEA), minlength=n)
    lake_counts = np.bincount(flat_pm, weights=(flat_tm == TILE_LAKE), minlength=n)

    land_ids = []
    sea_ids = []
    lake_ids = []
    total_counts = land_counts + sea_counts + lake_counts
    for pid in range(1, province_count + 1):
        if total_counts[pid] == 0:
            # 0像素的幽灵省份 — 归入海洋（不需要State/战略区域）
            sea_ids.append(pid)
            continue
        l, s, k = land_counts[pid], sea_counts[pid], lake_counts[pid]
        if l >= s and l >= k:
            land_ids.append(pid)
        elif k > s:
            lake_ids.append(pid)
        else:
            sea_ids.append(pid)

    return land_ids, sea_ids, lake_ids


def _gen_heightmap(tm):
    from scipy.ndimage import gaussian_filter
    hm = np.full((MAP_HEIGHT, MAP_WIDTH), OCEAN_HEIGHT, dtype=np.float32)
    hm[tm == TILE_LAND] = LAND_BASE_HEIGHT
    hm[tm == TILE_LAKE] = SEA_LEVEL - 5
    hm = gaussian_filter(hm, sigma=8)
    hm[tm == TILE_SEA] = np.minimum(hm[tm == TILE_SEA], SEA_LEVEL - 1)
    hm[tm == TILE_LAND] = np.maximum(hm[tm == TILE_LAND], SEA_LEVEL + 1)
    return np.clip(hm, 0, 255).astype(np.uint8)


def _gen_terrain(tm):
    t = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8)
    for tile_type, name in DEFAULT_TERRAIN_FOR_TILE.items():
        t[tm == tile_type] = TERRAIN_PALETTE_INDEX[name]
    return t


def _write_normal_map(hm, output_dir):
    """写 world_normal.bmp 光照法线图。
    注意：原版是 2816x1024（地图尺寸的一半），因为 HOI4 有 MAX_TEXTURE_SIZE 限制。
    如果写成 5632x2048 会导致 "Failed to load texture larger than MAX_TEXTURE_SIZE"。
    """
    from scipy.ndimage import sobel, zoom
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    # 先在全尺寸上计算 normal，然后下采样到半尺寸
    h = hm.astype(np.float32) / 255.0
    dx = sobel(h, axis=1)
    dy = -sobel(h, axis=0)
    nx, ny, nz = -dx, -dy, np.ones_like(h)
    L = np.sqrt(nx**2 + ny**2 + nz**2); L[L == 0] = 1
    nx /= L; ny /= L; nz /= L

    # 下采样到半尺寸（原版格式）
    NW, NH = MAP_WIDTH // 2, MAP_HEIGHT // 2
    r_full = ((nx + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
    g_full = ((ny + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
    b_full = ((nz + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
    # 每2x2像素块取平均
    r = r_full.reshape(NH, 2, NW, 2).mean(axis=(1, 3)).astype(np.uint8)
    g = g_full.reshape(NH, 2, NW, 2).mean(axis=(1, 3)).astype(np.uint8)
    b = b_full.reshape(NH, 2, NW, 2).mean(axis=(1, 3)).astype(np.uint8)

    row = NW * 3
    pad = (4 - (row % 4)) % 4
    pix = (row + pad) * NH
    with open(os.path.join(d, "world_normal.bmp"), "wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<I", 54 + pix))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", 54))
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<ii", NW, NH))
        f.write(struct.pack("<HH", 1, 24))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pix))
        f.write(struct.pack("<ii", 2835, 2835))
        f.write(struct.pack("<II", 0, 0))
        pb = b"\x00" * pad
        for y in range(NH - 1, -1, -1):
            f.write(np.stack([b[y], g[y], r[y]], axis=1).tobytes())
            if pad:
                f.write(pb)
