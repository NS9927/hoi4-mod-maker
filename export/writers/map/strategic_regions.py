"""strategicregions/*.txt + weatherpositions.txt."""
import os
import numpy as np
from data.constants import MAP_WIDTH, MAP_HEIGHT, TILE_LAND, TILE_SEA


def write_strategic_regions(province_map, tile_map, output_dir,
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

        with open(os.path.join(d, f"{new_id}-strategic_region.txt"), "w", encoding="utf-8") as f:
            f.write("strategic_region={\n")
            f.write(f"\tid={new_id}\n")
            f.write(f'\tname="STRATEGICREGION_WT_{new_id}"\n')
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


def write_strategic_regions_from_mgr(region_mgr, output_dir):
    """从 StrategicRegionManager 写 strategicregions/*.txt.

    使用 manager 里的 weather_preset + naval_terrain 数据, 而非硬编码占位.
    返回 region_list 用于 weatherpositions.
    """
    from domain.managers.strategic_region import WEATHER_PRESETS

    d = os.path.join(output_dir, "map", "strategicregions")
    os.makedirs(d, exist_ok=True)

    region_list = []
    # 重编号 (连续从 1, HOI4 要求)
    sorted_regions = sorted(region_mgr.regions.values(), key=lambda r: r.id)
    for new_id, region in enumerate(sorted_regions, start=1):
        provs = region.province_ids
        if not provs:
            continue
        region_list.append((new_id, provs))

        preset = region.weather_preset or "temperate"
        periods = WEATHER_PRESETS.get(preset, WEATHER_PRESETS["temperate"])

        with open(os.path.join(d, f"{new_id}-strategic_region.txt"), "w", encoding="utf-8") as f:
            f.write("strategic_region={\n")
            f.write(f"\tid={new_id}\n")
            # 永远写 key，绝不写 region.name — 用户可能输入中文，HOI4 parser 遇
            # 到非 ASCII 直接崩游戏。显示名走 localisation yml。
            f.write(f'\tname="STRATEGICREGION_WT_{new_id}"\n')
            if region.naval_terrain:
                f.write(f"\tnaval_terrain={region.naval_terrain}\n")
            f.write("\tprovinces={\n\t\t")
            f.write(" ".join(str(p) for p in provs))
            f.write("\n\t}\n")
            f.write("\tweather={\n")
            for period in periods:
                f.write("\t\tperiod={\n")
                f.write(f"\t\t\tbetween={{ {period['between']} }}\n")
                f.write(f"\t\t\ttemperature={{ {period['temp']} }}\n")
                f.write(f"\t\t\tno_phenomenon={period['no']:.3f}\n")
                f.write(f"\t\t\train_light={period['rain_light']:.3f}\n")
                f.write(f"\t\t\train_heavy={period['rain_heavy']:.3f}\n")
                f.write(f"\t\t\tsnow={period['snow']:.3f}\n")
                f.write(f"\t\t\tblizzard={period['blizzard']:.3f}\n")
                f.write(f"\t\t\tmud={period['mud']:.3f}\n")
                f.write(f"\t\t\tsandstorm={period['sandstorm']:.3f}\n")
                if period.get("min_snow", 0) > 0:
                    f.write(f"\t\t\tmin_snow_level={period['min_snow']:.2f}\n")
                f.write("\t\t}\n")
            f.write("\t}\n}\n")

    return region_list


def write_weatherpositions(region_list, province_map, output_dir):
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

    with open(os.path.join(d, "weatherpositions.txt"), "w", encoding="utf-8") as f:
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

