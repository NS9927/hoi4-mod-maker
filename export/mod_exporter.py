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
    DEFAULT_HOI4_PATH, REPLACE_PATHS,
)
from data.terrain_types import TERRAIN_PALETTE_INDEX, DEFAULT_TERRAIN_FOR_TILE
from core.province_generator import generate_province_colors
from core.province_validator import get_coastal_provinces
from export.bmp_writer import (
    write_provinces_bmp, write_heightmap_bmp,
    write_terrain_bmp, write_rivers_bmp, write_trees_bmp,
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
    province_count = int(province_map.max())
    if province_count == 0:
        raise ValueError("没有省份数据，请先生成省份")

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
    _write_normal_map(heightmap, output_dir)

    # === 地图配置文件 ===
    _write_definition_csv(province_count, colors, province_map, tile_map, output_dir,
                          land_ids, sea_ids, lake_ids)
    _write_default_map(output_dir, sea_ids, lake_ids)
    _write_continent(output_dir)
    _write_adjacencies(output_dir)
    _write_empty_map_files(output_dir)

    # === State — 优先用用户数据，否则自动拆分 ===
    if state_mgr and state_mgr.states:
        # 使用用户编辑的 State 数据（过滤海洋/湖泊省份）
        states = {}
        for sid, s in state_mgr.states.items():
            land_provs = [p for p in s.provinces if _is_land(p, province_map, tile_map)]
            if land_provs:
                states[sid] = land_provs
        _write_states_from_mgr(state_mgr, country_mgr, province_map, output_dir, tile_map)
    else:
        states = _auto_split_states(land_ids, province_map)
        _write_states(states, tag, province_map, output_dir)

    # === 补给系统 ===
    _write_supply_nodes(states, province_map, output_dir)
    _write_railways(states, province_map, output_dir)
    _write_buildings(states, province_map, output_dir)
    _write_supply_areas(states, output_dir)

    # === 战略区域（多区域自动拆分）===
    region_list = _write_strategic_regions(province_map, tile_map, output_dir)

    # === 省份坐标 ===
    _write_positions(province_map, output_dir)

    # === 国家 — 优先用用户数据 ===
    if country_mgr and country_mgr.countries:
        _write_countries_from_mgr(country_mgr, output_dir)
    else:
        first_land = land_ids[0] if land_ids else 1
        _write_country(tag, first_land, output_dir)

    # === 本地化 ===
    _write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir)

    # 意识形态和State类别（在replace_path中，必须生成）
    _write_ideologies(output_dir)
    _write_state_categories(output_dir)

    # === Bookmark（选国家界面必须有）===
    country_tags = list(country_mgr.countries.keys()) if country_mgr and country_mgr.countries else [tag]
    _write_bookmark(mod_name, country_tags, output_dir)

    # === descriptor + replace_path 空目录 ===
    _write_descriptor(mod_name, output_dir)
    _create_replace_dirs(output_dir)


# ────────────────── definition.csv ──────────────────

def _write_definition_csv(count, colors, pm, tm, output_dir,
                          land_ids=None, sea_ids=None, lake_ids=None):
    coastal = get_coastal_provinces(tm, pm)
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

    with open(os.path.join(d, "definition.csv"), "w") as f:
        f.write("0;0;0;0;land;false;unknown;0\n")
        for pid in range(1, count + 1):
            r, g, b = colors.get(pid, (1, 1, 1))
            ptype = type_map.get(pid) if type_map else _get_province_type(pid, pm, tm)
            if ptype == "land":
                terrain = "plains"
                cont = 1
                c = "true" if pid in coastal else "false"
            elif ptype == "lake":
                terrain = "lakes"
                cont = 0
                c = "false"
            else:
                terrain = "ocean"
                cont = 0
                c = "false"
            f.write(f"{pid};{r};{g};{b};{ptype};{c};{terrain};{cont}\n")


# ────────────────── default.map ──────────────────

def _write_default_map(output_dir, sea_ids=None, lake_ids=None):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "default.map"), "w") as f:
        # 严格按原版格式（原版没有 max_provinces 字段）
        f.write('definitions = "definition.csv"\n')
        f.write('provinces = "provinces.bmp"\n')
        f.write('positions = "positions.txt"\n')
        f.write('terrain = "terrain.bmp"\n')
        f.write('rivers = "rivers.bmp"\n')
        f.write('heightmap = "heightmap.bmp"\n')
        f.write('tree_definition = "trees.bmp"\n')
        f.write('continent = "continent.txt"\n')
        f.write('adjacency_rules = "adjacency_rules.txt"\n')
        f.write('adjacencies = "adjacencies.csv"\n')
        f.write('ambient_object = "ambient_object.txt"\n')
        f.write('seasons = "seasons.txt"\n\n')
        f.write('tree = { 3 4 7 10 }\n\n')

        # 注意：原版1.17的default.map没有sea_starts/lakes字段
        # 海洋/湖泊省份通过definition.csv的type字段标识即可


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
        f.write(";;;;;;;;;\n")


# ────────────────── 空文件 ──────────────────

def _write_empty_map_files(output_dir):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    # 这些文件必须存在但可以为空
    for name in ["adjacency_rules.txt", "ambient_object.txt",
                 "weatherpositions.txt", "unitstacks.txt", "rocket_sites.txt",
                 "positions.txt"]:
        open(os.path.join(d, name), "w").close()
    # seasons.txt — default.map 引用了它，必须存在且有内容
    with open(os.path.join(d, "seasons.txt"), "w") as f:
        f.write("# Seasons definition\n")
        for season, start, end in [
            ("winter", "00.12.01", "00.02.10"),
            ("spring", "00.03.10", "00.04.22"),
            ("summer", "00.05.20", "00.09.10"),
            ("autumn", "00.10.10", "00.10.31"),
        ]:
            f.write(f'{season} = {{\n')
            f.write(f'\tstart_date={start} end_date={end}\n')
            f.write(f'\thsv_north={{ 0 0.1 1 }} colorbalance_north={{ 0.9 0.9 1 }}\n')
            f.write(f'\thsv_center={{ 0.0 1.0 1.0 }} colorbalance_center={{ 1.0 1.0 1.0 }}\n')
            f.write(f'\thsv_south={{ 0.0 1.0 1.0 }} colorbalance_south={{ 1.0 1.0 1.0 }}\n')
            f.write(f'}}\n')


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
            f.write("# No supply nodes\n")


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
            f.write("# No railways\n")


def _write_buildings(states, province_map, output_dir):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    # 预计算所有省份质心（向量化）
    flat_pm = province_map.ravel()
    n = int(province_map.max()) + 1
    pid_count = np.bincount(flat_pm, minlength=n)
    ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
    sum_y = np.bincount(flat_pm, weights=ys_grid.ravel().astype(np.float64), minlength=n)
    sum_x = np.bincount(flat_pm, weights=xs_grid.ravel().astype(np.float64), minlength=n)

    with open(os.path.join(d, "buildings.txt"), "w") as f:
        written = False
        for sid, provs in states.items():
            if not provs:
                continue
            pid = provs[0]
            if pid >= n or pid_count[pid] == 0:
                continue
            cx = sum_x[pid] / pid_count[pid]
            cy = sum_y[pid] / pid_count[pid]
            f.write(f"{sid};infrastructure;{cx:.2f};11.00;{cy:.2f};0.00;0\n")
            f.write(f"{sid};arms_factory;{cx+2:.2f};11.00;{cy+2:.2f};0.00;0\n")
            written = True
        if not written:
            f.write("# No buildings\n")


def _write_supply_areas(states, output_dir):
    d = os.path.join(output_dir, "map", "supplyareas")
    os.makedirs(d, exist_ok=True)
    state_ids = list(states.keys())
    with open(os.path.join(d, "1-SupplyArea.txt"), "w") as f:
        f.write("supply_area={\n\tid=1\n")
        f.write('\tname="SUPPLYAREA_1"\n\tvalue=5\n')
        f.write("\tstates={\n\t\t" + " ".join(str(s) for s in state_ids) + "\n\t}\n}\n")


# ────────────────── 战略区域（多区域自动拆分）──────────────────

def _write_strategic_regions(province_map, tile_map, output_dir, grid_cols=6, grid_rows=4):
    """
    按地理网格自动拆分多个战略区域。
    grid_cols x grid_rows 个格子，每个格子内的省份归入同一个战略区域。
    确保所有省份都被分配（包括海洋）。
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

    # 按网格分组
    cell_h = MAP_HEIGHT / grid_rows
    cell_w = MAP_WIDTH / grid_cols
    regions: dict[int, list[int]] = {}

    for pid, (cy, cx) in centroids.items():
        row = min(int(cy / cell_h), grid_rows - 1)
        col = min(int(cx / cell_w), grid_cols - 1)
        rid = row * grid_cols + col + 1  # 从1开始
        if rid not in regions:
            regions[rid] = []
        regions[rid].append(pid)

    # 处理没有质心的省份（理论上不应发生）
    all_assigned = set()
    for provs in regions.values():
        all_assigned.update(provs)
    for pid in range(1, province_count + 1):
        if pid not in all_assigned:
            # 归入第1个区域
            first_rid = min(regions.keys()) if regions else 1
            if first_rid not in regions:
                regions[first_rid] = []
            regions[first_rid].append(pid)

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
            f.write("\t\t\tbetween={ 0.0 30.0 }\n")
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


# ────────────────── positions.txt（省份坐标）──────────────────

def _write_positions(province_map, output_dir):
    """
    生成 positions.txt — 每个省份的中心坐标。
    HOI4 用这个定位城市名、单位图标、建筑位置等。

    格式（每个省份一条）:
    ID;X;height;Y;rotation;X;height;Y;rotation;... (重复多组，分别对应不同用途)

    HOI4 positions.txt 有多种位置：
    1. unit position (部队)
    2. text position (省份名)
    3. city position (城市图标)
    4. port position (港口)
    5. building/factory position
    每组 4 个值: x, height(11.0), y, rotation(0.0)
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    province_count = int(province_map.max())
    if province_count == 0:
        with open(os.path.join(d, "positions.txt"), "w") as f:
            f.write("")
        return

    # 向量化计算所有省份质心
    flat_pm = province_map.ravel()
    ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
    flat_ys = ys_grid.ravel().astype(np.float64)
    flat_xs = xs_grid.ravel().astype(np.float64)
    n = province_count + 1
    pid_count = np.bincount(flat_pm, minlength=n)
    sum_y = np.bincount(flat_pm, weights=flat_ys, minlength=n)
    sum_x = np.bincount(flat_pm, weights=flat_xs, minlength=n)

    with open(os.path.join(d, "positions.txt"), "w") as f:
        for pid in range(1, province_count + 1):
            if pid_count[pid] == 0:
                continue
            cx = sum_x[pid] / pid_count[pid]
            cy = sum_y[pid] / pid_count[pid]

            # HOI4 坐标系：X = 像素X，Y = MAP_HEIGHT - 像素Y（翻转）
            hoi4_x = cx
            hoi4_y = MAP_HEIGHT - cy

            # 8组位置数据（unit, text, city, port, building, factory, 额外2组）
            # 每组: x, height, y, rotation
            pos = f"{hoi4_x:.2f};11.00;{hoi4_y:.2f};0.00"
            # 文本位置略偏上
            text_pos = f"{hoi4_x:.2f};11.00;{hoi4_y + 1:.2f};0.00"

            f.write(f"{pid};{pos};{text_pos};{pos};{pos};{pos};{pos};{pos};{pos}\n")


# ────────────────── 国家 ──────────────────

def _write_country(tag, capital, output_dir):
    os.makedirs(os.path.join(output_dir, "common", "country_tags"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "common", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "units"), exist_ok=True)

    with open(os.path.join(output_dir, "common", "country_tags", "00_countries.txt"), "w") as f:
        f.write(f'{tag} = "countries/{tag}.txt"\n')

    with open(os.path.join(output_dir, "common", "countries", f"{tag}.txt"), "w") as f:
        f.write("graphical_culture = western_european_gfx\n")
        f.write("graphical_culture_2d = western_european_2d\n")
        f.write("color = { 100 100 200 }\n")

    with open(os.path.join(output_dir, "history", "countries", f"{tag} - Fantasy.txt"), "w") as f:
        f.write(f"capital = {capital}\n")
        f.write(f'oob = "{tag}_1936"\n')
        f.write("set_research_slots = 3\n")
        f.write("set_politics = {\n\truling_party = neutrality\n")
        f.write('\tlast_election = "1932.1.1"\n\telection_frequency = 48\n')
        f.write("\telections_allowed = no\n}\n")
        f.write("set_popularities = {\n\tdemocratic = 10\n\tfascism = 5\n")
        f.write("\tcommunism = 5\n\tneutrality = 80\n}\n")

    with open(os.path.join(output_dir, "history", "units", f"{tag}_1936.txt"), "w") as f:
        f.write("units = { }\n")


# ────────────────── 本地化 ──────────────────

def _write_localisation(mod_name, tag, states, output_dir):
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")
    with open(os.path.join(d, f"{safe}_l_english.yml"), "w", encoding="utf-8-sig") as f:
        f.write("l_english:\n")
        for sid in states:
            f.write(f' STATE_{sid}:0 "State {sid}"\n')
        for rid in range(1, 25):
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
        f.write(rp + "\n")
        f.write(f'supported_version="{DEFAULT_SUPPORTED_VERSION}"\n')
        # path 用正斜杠
        abs_path = os.path.abspath(output_dir).replace("\\", "/")
        f.write(f'path="{abs_path}"\n')


def _create_replace_dirs(output_dir):
    """为所有 replace_path 创建空目录"""
    for p in REPLACE_PATHS:
        os.makedirs(os.path.join(output_dir, p), exist_ok=True)


def _write_bookmark(mod_name, country_tags, output_dir):
    """生成 bookmark 文件 — 严格按原版格式，包含所有必需字段"""
    d = os.path.join(output_dir, "common", "bookmarks")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "the_gathering_storm.txt"), "w") as f:
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


def _write_ideologies(output_dir):
    """生成意识形态定义文件 — 必须包含 types 子块，否则崩溃"""
    d = os.path.join(output_dir, "common", "ideologies")
    os.makedirs(d, exist_ok=True)

    # 严格按原版格式，只用原版有的字段
    ideologies = [
        ("democratic", "{ 0 0 200 }", [
            "conservatism", "liberalism", "socialism",
        ], "ai_democratic", "0.25", "0.1"),
        ("fascism", "{ 169 68 66 }", [
            "fascism_ideology", "nazism", "falangism",
        ], "ai_fascist", "0.8", "0.5"),
        ("communism", "{ 200 0 0 }", [
            "marxism", "leninism", "stalinism",
        ], "ai_communist", "0.8", "0.5"),
        ("neutrality", "{ 125 127 126 }", [
            "despotism", "oligarchism", "moderatism", "centrism",
        ], "ai_neutral", "1.0", "0.5"),
    ]

    with open(os.path.join(d, "00_ideologies.txt"), "w") as f:
        f.write("ideologies = {\n\n")
        for name, color, subtypes, ai_flag, war_tension, faction_tension in ideologies:
            f.write(f"\t{name} = {{\n\n")
            # types 子块（必须存在）
            f.write(f"\t\ttypes = {{\n")
            for st in subtypes:
                f.write(f"\t\t\t{st} = {{\n\t\t\t}}\n")
            f.write(f"\t\t}}\n\n")
            f.write(f"\t\tcolor = {color}\n\n")
            f.write(f"\t\trules = {{\n")
            f.write(f"\t\t\tcan_create_factions = yes\n")
            f.write(f"\t\t}}\n\n")
            f.write(f"\t\twar_impact_on_world_tension = {war_tension}\n")
            f.write(f"\t\tfaction_impact_on_world_tension = {faction_tension}\n\n")
            f.write(f"\t\tmodifiers = {{\n\t\t}}\n\n")
            # 用原版的 ai_xxx = yes 格式
            f.write(f"\t\t{ai_flag} = yes\n")
            f.write(f"\t\tcan_be_boosted = yes\n")
            f.write(f"\t}}\n\n")
        f.write("}\n")


def _write_state_categories(output_dir):
    """生成 state_category 定义文件 — 严格按原版格式，每个类别用 state_categories 包裹"""
    d = os.path.join(output_dir, "common", "state_category")
    os.makedirs(d, exist_ok=True)

    # (名称, 建筑槽, 颜色RGB)  — 与原版一致
    categories = [
        ("wasteland", 0, (40, 40, 40)),
        ("pastoral", 1, (160, 160, 0)),
        ("tiny", 1, (180, 180, 0)),
        ("small", 2, (190, 190, 0)),
        ("town", 4, (200, 200, 0)),
        ("large_town", 5, (150, 200, 0)),
        ("city", 6, (0, 200, 0)),
        ("large_city", 8, (0, 150, 0)),
        ("megalopolis", 10, (0, 100, 0)),
    ]
    for name, slots, (cr, cg, cb) in categories:
        with open(os.path.join(d, f"{name}.txt"), "w") as f:
            f.write("state_categories={\n")
            f.write(f"\t{name} = {{\n")
            f.write(f"\t\tlocal_building_slots = {slots}\n")
            f.write(f"\t\tcolor = {{ {cr} {cg} {cb} }}\n")
            f.write(f"\t}}\n")
            f.write("}\n")


# ────────────────── 使用管理器数据导出 ──────────────────

def _write_states_from_mgr(state_mgr, country_mgr, province_map, output_dir, tile_map=None):
    """用 StateManager + CountryManager 的数据写 State 文件"""
    d = os.path.join(output_dir, "history", "states")
    os.makedirs(d, exist_ok=True)
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
            f.write("\t\tbuildings = {\n")
            f.write("\t\t\tinfrastructure = 1\n")
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


def _write_countries_from_mgr(country_mgr, output_dir):
    """用 CountryManager 的数据写国家文件"""
    os.makedirs(os.path.join(output_dir, "common", "country_tags"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "common", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "countries"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "history", "units"), exist_ok=True)

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

        # 确保首都有效：必须是已有省份
        capital = c.capital if c.capital > 0 else 1
        # 安全文件名
        safe_name = c.name.replace("/", "_").replace("\\", "_").replace(":", "_").replace('"', "")
        with open(os.path.join(output_dir, "history", "countries", f"{tag} - {safe_name}.txt"), "w") as f:
            f.write(f"capital = {capital}\n")
            f.write(f'oob = "{tag}_1936"\n')
            f.write("set_research_slots = 3\n")
            f.write(f"set_politics = {{\n\truling_party = {c.ruling_party}\n")
            f.write('\tlast_election = "1932.1.1"\n\telection_frequency = 48\n')
            f.write("\telections_allowed = no\n}\n")
            f.write("set_popularities = {\n")
            for party, val in c.popularities.items():
                f.write(f"\t{party} = {val}\n")
            f.write("}\n")

        with open(os.path.join(output_dir, "history", "units", f"{tag}_1936.txt"), "w") as f:
            f.write("units = { }\n")


def _write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir):
    """完整本地化"""
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")
    with open(os.path.join(d, f"{safe}_l_english.yml"), "w", encoding="utf-8-sig") as f:
        f.write("l_english:\n")
        # State 名称
        if state_mgr and state_mgr.states:
            for sid, s in state_mgr.states.items():
                f.write(f' STATE_{sid}:0 "{s.name}"\n')
        else:
            for sid in states:
                f.write(f' STATE_{sid}:0 "State {sid}"\n')
        # 国家名称
        if country_mgr and country_mgr.countries:
            for tag, c in country_mgr.countries.items():
                f.write(f' {tag}:0 "{c.name}"\n')
                f.write(f' {tag}_DEF:0 "{c.name}"\n')
                f.write(f' {tag}_ADJ:0 "{c.name}"\n')
                f.write(f' {tag}_BOOKMARK_DESC:0 "Play as {c.name}"\n')
        for rid in range(1, 25):
            f.write(f' STRATEGICREGION_{rid}:0 "Region {rid}"\n')
        f.write(f' SUPPLYAREA_1:0 "Fantasy Supply"\n')
        f.write(f' FANTASY_BOOKMARK:0 "Fantasy World"\n')
        f.write(f' FANTASY_BOOKMARK_DESC:0 "A fantasy world awaits."\n')
        f.write(f' OTHER_BOOKMARK_DESC:0 "Other nations"\n')


# ────────────────── 辅助函数 ──────────────────

def _is_land(pid, pm, tm):
    mask = pm == pid
    if not np.any(mask):
        return False
    return int(np.sum(tm[mask] == TILE_LAND)) > int(np.sum(tm[mask] != TILE_LAND))


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
    for pid in range(1, province_count + 1):
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
    from scipy.ndimage import sobel
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    h = hm.astype(np.float32) / 255.0
    dx = sobel(h, axis=1)
    dy = -sobel(h, axis=0)
    nx, ny, nz = -dx, -dy, np.ones_like(h)
    L = np.sqrt(nx**2 + ny**2 + nz**2); L[L == 0] = 1
    nx /= L; ny /= L; nz /= L
    r = ((nx + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
    g = ((ny + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
    b = ((nz + 1) / 2 * 255).clip(0, 255).astype(np.uint8)

    row = MAP_WIDTH * 3
    pad = (4 - (row % 4)) % 4
    pix = (row + pad) * MAP_HEIGHT
    with open(os.path.join(d, "world_normal.bmp"), "wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<I", 54 + pix))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", 54))
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<ii", MAP_WIDTH, MAP_HEIGHT))
        f.write(struct.pack("<HH", 1, 24))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pix))
        f.write(struct.pack("<ii", 2835, 2835))
        f.write(struct.pack("<II", 0, 0))
        pb = b"\x00" * pad
        for y in range(MAP_HEIGHT - 1, -1, -1):
            f.write(np.stack([b[y], g[y], r[y]], axis=1).tobytes())
            if pad:
                f.write(pb)
