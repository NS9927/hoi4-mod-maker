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
    DEFAULT_MOD_NAME,
)
from data.terrain_types import TERRAIN_PALETTE_INDEX, DEFAULT_TERRAIN_FOR_TILE
from domain.generators.province import generate_province_colors
from export.bmp_writer import (
    write_provinces_bmp, write_heightmap_bmp,
    write_terrain_bmp, write_rivers_bmp,
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
    continent_mgr=None,
    adjacency_mgr=None,
    railway_mgr=None,
    supply_mgr=None,
    colormap_settings=None,
    default_map_settings=None,
    adjacency_rule_mgr=None,
    strategic_region_mgr=None,
    provincial_terrain: dict[int, str] | None = None,
) -> None:
    """一键导出完整 MOD。如果提供 state_mgr/country_mgr，使用用户编辑的数据。"""
    if int(province_map.max()) == 0:
        raise ValueError("没有省份数据，请先生成省份")

    # 安全网：导出前强制压实 ID + 同步所有引用（state.provinces / VP / capital）
    # 这是修复历史 bug：之前只压实 province_map，没更新 state/country 引用，
    # 导致用户编辑过的 state/VP/首都可能指向不存在的省份
    from domain.map_data import MapData as _MD
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
    # trees.bmp: 从 terrain_map 自动生成树木分布 (A8)
    from export.writers.map.trees_bmp import (
        write_trees_bmp as _write_trees_new,
        auto_generate_tree_map,
    )
    _tm_for_trees = terrain_map if terrain_map is not None else _gen_terrain(tile_map)
    _tree_map = auto_generate_tree_map(_tm_for_trees)
    _write_trees_new(output_dir, tree_map=_tree_map)
    # cities.bmp: 从 urban terrain 生成城市标记 (Feature 11)
    from export.writers.map.cities_bmp import write_cities_bmp as _write_cities_new
    _write_cities_new(output_dir, terrain_map=terrain_map)
    _write_normal_map(heightmap, output_dir)

    # colormap_rgb_cityemissivemask_a.dds 战略视角总览贴图
    # (不覆盖会看到 vanilla 地球大陆)
    from export.writers.map.colormap_dds import write_colormap_dds
    write_colormap_dds(tile_map, output_dir, settings=colormap_settings,
                       terrain_map=terrain_map)

    # colormap_water_0/1/2.dds 海洋着色贴图
    from export.writers.map.colormap_dds import write_water_colormap_dds
    write_water_colormap_dds(tile_map, output_dir)

    # ambient_object.txt — 地图边框 (frame_border_top/bottom 挡住上下空白)
    from export.writers.map.ambient_object import write_ambient_object_txt
    write_ambient_object_txt(output_dir)

    # default.map 引擎配置文件 (A3, 用户可通过菜单调整 tree palette / river_max_level)
    from export.writers.map.default_map import write_default_map
    write_default_map(
        output_dir,
        settings=default_map_settings,
        province_count=int(province_map.max()),
    )

    # === 同步 terrain_map 与 tile_map ===
    # 用户可能扩张/缩小陆地后没重新生成地形，导致 terrain_map 与 tile_map 不一致。
    # 修正：陆地上的 ocean 地形→plains，海洋上的陆地地形→ocean
    # （与 gen_from_project.py 相同的修正逻辑）
    if terrain_map is not None:
        _sync_terrain_with_tile(terrain_map, tile_map)

    # === 地图配置文件 ===
    _write_definition_csv(province_count, colors, province_map, tile_map, output_dir,
                          land_ids, sea_ids, lake_ids, continent_mgr=continent_mgr,
                          terrain_map=terrain_map,
                          provincial_terrain=provincial_terrain)
    _write_continent(output_dir, continent_mgr=continent_mgr)
    # Adjacencies: 有用户数据用新 writer, 否则写仅含 header+sentinel
    if adjacency_mgr is not None and adjacency_mgr.count() > 0:
        from export.writers.map.adjacencies import write_adjacencies_csv
        write_adjacencies_csv(output_dir, adjacency_mgr=adjacency_mgr)
    else:
        _write_adjacencies(output_dir)

    # adjacency_rules.txt (A6, 海峡通行规则)
    from export.writers.map.adjacency_rules import write_adjacency_rules_txt
    write_adjacency_rules_txt(output_dir, rule_mgr=adjacency_rule_mgr)

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

    # === 战略区域 ===
    if strategic_region_mgr is not None and strategic_region_mgr.count() > 0:
        # 用户编辑的 region (带 weather 预设 + naval_terrain)
        from export.writers.map.strategic_regions import (
            write_strategic_regions_from_mgr, write_weatherpositions,
        )
        region_list = write_strategic_regions_from_mgr(strategic_region_mgr, output_dir)
        write_weatherpositions(region_list, province_map, output_dir)
    else:
        # 自动生成 (旧行为, state-aware)
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
    # Supply nodes: 有用户数据用新 writer, 否则用老的自动生成
    if supply_mgr is not None and supply_mgr.count() > 0:
        from export.writers.map.supply_nodes import write_supply_nodes_txt
        write_supply_nodes_txt(output_dir, supply_mgr=supply_mgr)
    else:
        _write_supply_nodes(states, province_map, output_dir)

    # Railways: 同上
    if railway_mgr is not None and railway_mgr.count() > 0:
        from export.writers.map.railways import write_railways_txt
        write_railways_txt(output_dir, railway_mgr=railway_mgr)
    else:
        _write_railways(states, province_map, output_dir)
    _write_buildings(states, province_map, tile_map, output_dir, sea_ids)
    _write_supply_areas(states, output_dir)
    # 覆盖原版 unitstacks.txt（原版引用13000省份坐标，和我们165省份冲突）
    _write_empty_unitstacks(output_dir)
    # positions.txt: 每个省份的单位/文字/城市/港口 3D 坐标
    _write_positions(province_map, tile_map, output_dir)

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
    from export.writers.replace_path.scrubber import write_replace_path_dirs
    write_replace_path_dirs(output_dir)

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
                          land_ids=None, sea_ids=None, lake_ids=None,
                          continent_mgr=None, terrain_map=None,
                          provincial_terrain=None):
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

    # 策略 (2026-04-09 修): 只把真正邻海的陆地省份标 coastal=true.
    # 之前全标策略触发 Troubleshooting.txt 行 117 "Province is coastal but no port"
    # 无限循环崩溃. buildings.txt 里 naval_base_spawn 也只为真沿海省份写,
    # 两者必须完全对齐.
    # 用省份级邻接 (land_pid 邻 sea_pid), 和 buildings.py 里的 land_to_sea 算法一致.
    coastal_set: set[int] = set()
    if land_ids and sea_ids:
        sea_set_local = set(int(x) for x in sea_ids)
        land_set_local = set(int(x) for x in land_ids)
        max_pid = int(pm.max()) + 1
        is_sea_arr = np.zeros(max_pid, dtype=bool)
        for sp in sea_set_local:
            if sp < max_pid:
                is_sea_arr[sp] = True
        is_land_arr = np.zeros(max_pid, dtype=bool)
        for lp in land_set_local:
            if lp < max_pid:
                is_land_arr[lp] = True
        # 水平邻接
        left_arr = pm[:, :-1].ravel()
        right_arr = pm[:, 1:].ravel()
        m1 = is_land_arr[left_arr] & is_sea_arr[right_arr]
        m2 = is_sea_arr[left_arr] & is_land_arr[right_arr]
        coastal_set.update(int(x) for x in left_arr[m1])
        coastal_set.update(int(x) for x in right_arr[m2])
        # 垂直邻接
        up_arr = pm[:-1, :].ravel()
        down_arr = pm[1:, :].ravel()
        m3 = is_land_arr[up_arr] & is_sea_arr[down_arr]
        m4 = is_sea_arr[up_arr] & is_land_arr[down_arr]
        coastal_set.update(int(x) for x in up_arr[m3])
        coastal_set.update(int(x) for x in down_arr[m4])

    with open(os.path.join(d, "definition.csv"), "w") as f:
        f.write("0;0;0;0;land;false;unknown;0\n")
        for pid in range(1, count + 1):
            r, g, b = colors.get(pid, (1, 1, 1))
            ptype = type_map.get(pid) if type_map else _get_province_type(pid, pm, tm)
            if ptype == "land":
                terrain = _resolve_provincial_terrain(pid, pm, terrain_map,
                                                     provincial_terrain=provincial_terrain)
                if continent_mgr is not None:
                    cont = continent_mgr.get_province_continent_hoi4_id(pid, True)
                    if cont <= 0:
                        cont = 1
                else:
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


def _resolve_provincial_terrain(pid, province_map, terrain_map,
                                provincial_terrain=None):
    """解析陆地省份的 provincial terrain type.
    优先使用 provincial_terrain 字典 (Feature A)，
    回退到从 terrain_map 多数投票推算。"""
    # 优先使用显式设定的省份级地形
    if provincial_terrain and pid in provincial_terrain:
        return provincial_terrain[pid]

    if terrain_map is None:
        return "plains"

    from data.terrain_types import PALETTE_TO_TYPE

    mask = province_map == pid
    indices = terrain_map[mask]
    if indices.size == 0:
        return "plains"

    counts = np.bincount(indices)
    dominant_index = int(counts.argmax())
    return PALETTE_TO_TYPE.get(dominant_index, "plains")


# 注意：不再生成 default.map — 用原版的（EaW 验证做法）
# 我们的 BMP/CSV 文件会按文件名自动覆盖原版对应文件


# ────────────────── continent.txt ──────────────────

def _write_continent(output_dir, continent_mgr=None):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    # 用 continent_mgr 的名字列表; 没有就回退到单一 default_continent
    if continent_mgr is not None and continent_mgr.count() > 0:
        names = continent_mgr.names
    else:
        names = ["default_continent"]
    with open(os.path.join(d, "continent.txt"), "w") as f:
        f.write("continents = {\n")
        for n in names:
            f.write(f"\t{n}\n")
        f.write("}\n")


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
    from export.writers.history.states import write_states_fallback
    write_states_fallback(states, tag, province_map, output_dir)


# ────────────────── 补给系统 ──────────────────

def _write_supply_nodes(states, province_map, output_dir):
    from export.writers.map.supply import write_supply_nodes
    return write_supply_nodes(states, province_map, output_dir)


def _write_railways(states, province_map, output_dir):
    from export.writers.map.supply import write_railways
    return write_railways(states, province_map, output_dir)


def _write_buildings(states, province_map, tile_map, output_dir, sea_ids=None):
    from export.writers.map.buildings import write_buildings
    return write_buildings(states, province_map, tile_map, output_dir, sea_ids)


def _write_empty_unitstacks(output_dir):
    from export.writers.map.buildings import write_empty_unitstacks
    return write_empty_unitstacks(output_dir)


def _write_supply_areas(states, output_dir):
    from export.writers.map.supply import write_supply_areas
    return write_supply_areas(states, output_dir)


# ────────────────── 战略区域（多区域自动拆分）──────────────────

def _write_weatherpositions(region_list, province_map, output_dir):
    from export.writers.map.strategic_regions import write_weatherpositions
    return write_weatherpositions(region_list, province_map, output_dir)


def _write_strategic_regions(province_map, tile_map, output_dir,
                             grid_cols=6, grid_rows=4, states_dict=None):
    from export.writers.map.strategic_regions import write_strategic_regions
    return write_strategic_regions(province_map, tile_map, output_dir, grid_cols, grid_rows, states_dict)


def _write_positions(province_map, tile_map, output_dir):
    from export.writers.map.positions import write_positions_txt
    return write_positions_txt(province_map, tile_map, output_dir)


# ────────────────── 国家 ──────────────────

def _write_country_flags(tags, output_dir, country_mgr=None):
    from export.writers.gfx.flags import write_country_flags
    return write_country_flags(tags, output_dir, country_mgr)


def _write_country_portraits(tag, output_dir):
    from export.writers.gfx.portraits import write_country_portraits
    return write_country_portraits(tag, output_dir)


def _write_country_colors(tag, rgb, output_dir):
    from export.writers.common.countries import write_country_colors
    return write_country_colors(tag, rgb, output_dir)


def _write_country_names(tag, output_dir, country_name="Fantasy"):
    from export.writers.common.countries import write_country_names
    return write_country_names(tag, output_dir, country_name)


def _write_country_characters(tag, output_dir, country_name="Fantasy"):
    from export.writers.common.countries import write_country_characters
    return write_country_characters(tag, output_dir, country_name)


def _write_dynamic_countries(output_dir, count=75):
    from export.writers.common.countries import write_dynamic_countries
    return write_dynamic_countries(output_dir, count)


def _write_country(tag, capital_state_id, output_dir):
    from export.writers.common.countries import write_country
    return write_country(tag, capital_state_id, output_dir)


# ────────────────── 本地化 ──────────────────

def _write_localisation(mod_name, tag, states, output_dir, region_count=24):
    from export.writers.localisation.yml import write_localisation_simple
    return write_localisation_simple(mod_name, tag, states, output_dir, region_count)


# ────────────────── descriptor.mod + 空目录 ──────────────────

def _write_descriptor(mod_name, output_dir):
    from export.writers.map.descriptor import write_descriptor
    return write_descriptor(mod_name, output_dir)



def _write_bookmark(mod_name, country_tags, output_dir):
    from export.writers.common.countries import write_bookmark
    return write_bookmark(mod_name, country_tags, output_dir)


# 注意：不再生成 ideologies 和 state_category — 用原版的（EaW 验证做法）
# 原版的 common/ideologies 和 common/state_category 已经足够完整


# ────────────────── 使用管理器数据导出 ──────────────────

def _write_states_from_mgr(state_mgr, country_mgr, province_map, output_dir, tile_map=None):
    from export.writers.history.states import write_states_from_mgr
    write_states_from_mgr(state_mgr, country_mgr, province_map, output_dir, tile_map)


def _write_countries_from_mgr(country_mgr, output_dir, states):
    from export.writers.common.countries import write_countries_from_mgr
    return write_countries_from_mgr(country_mgr, output_dir, states)


def _write_dynamic_country_oobs(output_dir, count=75):
    from export.writers.common.countries import write_dynamic_country_oobs
    return write_dynamic_country_oobs(output_dir, count)


def _write_country_ideas(country_mgr, output_dir):
    from export.writers.common.countries import write_country_ideas
    return write_country_ideas(country_mgr, output_dir)


def _write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir,
                             region_count=24):
    from export.writers.localisation.yml import write_localisation_full
    return write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir, region_count)


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


def _sync_terrain_with_tile(terrain_map: np.ndarray, tile_map: np.ndarray) -> None:
    """同步 terrain_map 与 tile_map，就地修改 terrain_map。

    - 陆地像素上 terrain==ocean(15) → 改为 plains(0)
    - 海洋像素上 terrain!=ocean(15) → 改为 ocean(15)
    - 湖泊像素上 terrain!=lakes(14) → 改为 lakes(14)

    注意：这里直接修改 terrain_map（mutation），因为是导出前的一次性修正，
    不影响用户编辑器里的数据（导出器拿到的是独立 array）。
    """
    ocean_idx = TERRAIN_PALETTE_INDEX["ocean"]   # 15
    plains_idx = TERRAIN_PALETTE_INDEX["plains"]  # 0
    lakes_idx = TERRAIN_PALETTE_INDEX["lakes"]    # 14

    # 陆地上不应有 ocean 地形
    land_bad = (tile_map == TILE_LAND) & (terrain_map == ocean_idx)
    count_land = int(np.sum(land_bad))
    if count_land > 0:
        terrain_map[land_bad] = plains_idx
        print(f"  [terrain sync] {count_land:,} 个陆地像素的地形从 ocean 改为 plains")

    # 海洋上不应有陆地地形
    sea_bad = (tile_map == TILE_SEA) & (terrain_map != ocean_idx)
    count_sea = int(np.sum(sea_bad))
    if count_sea > 0:
        terrain_map[sea_bad] = ocean_idx
        print(f"  [terrain sync] {count_sea:,} 个海洋像素的地形改为 ocean")

    # 湖泊上地形应为 lakes
    lake_bad = (tile_map == TILE_LAKE) & (terrain_map != lakes_idx)
    count_lake = int(np.sum(lake_bad))
    if count_lake > 0:
        terrain_map[lake_bad] = lakes_idx
        print(f"  [terrain sync] {count_lake:,} 个湖泊像素的地形改为 lakes")


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
    full_h, full_w = hm.shape
    NW, NH = full_w // 2, full_h // 2
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
