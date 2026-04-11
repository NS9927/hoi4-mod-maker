"""
history/states/ — State 历史文件生成器.

一个 state 对应一个 {sid}-{name}.txt, 包含:
- 基础字段: id / name / manpower / state_category / impassable / local_supplies / resources
- 历史块: owner / add_core_of / add_claim_by / controller / buildings / victory_points
- 省份列表
"""

import os

from domain.validators.province import get_coastal_provinces


# state_category → 建筑默认等级 (infra, arms, indu, dock, air)
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

_COASTAL_DOCKYARDS = {
    "pastoral": 1, "rural": 1,
    "town": 1, "large_town": 2,
    "city": 2, "large_city": 3,
    "metropolis": 3, "megalopolis": 4,
}


def _is_land(pid: int, province_map, tile_map) -> bool:
    """判断省份是否主要是陆地."""
    import numpy as np
    from data.constants import TILE_LAND
    mask = province_map == pid
    if not np.any(mask):
        return False
    return int(np.sum(tile_map[mask] == TILE_LAND)) > 0


def write_states_from_mgr(
    state_mgr, country_mgr, province_map, output_dir, tile_map=None
) -> None:
    """用 StateManager + CountryManager 的数据写 State 文件."""
    d = os.path.join(output_dir, "history", "states")
    os.makedirs(d, exist_ok=True)

    coastal_set = set()
    if tile_map is not None and province_map is not None:
        coastal_set = set(int(p) for p in get_coastal_provinces(tile_map, province_map))

    for sid, state in state_mgr.states.items():
        if not state.provinces:
            continue

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

        safe_name = state.name.replace("/", "_").replace("\\", "_").replace(":", "_")

        impassable = bool(getattr(state, "impassable", False))
        controller_tag = getattr(state, "controller_tag", "") or ""
        local_supplies = float(getattr(state, "local_supplies", 0.0) or 0.0)
        user_resources = getattr(state, "resources", {}) or {}
        user_buildings = getattr(state, "buildings", {}) or {}
        user_prov_buildings = getattr(state, "province_buildings", {}) or {}
        extra_cores = list(getattr(state, "extra_cores", []) or [])
        claims = list(getattr(state, "claims", []) or [])

        with open(os.path.join(d, f"{sid}-{safe_name}.txt"), "w") as f:
            f.write("state = {\n")
            f.write(f"\tid = {sid}\n")
            f.write(f'\tname = "STATE_{sid}"\n')
            f.write(f"\tmanpower = {state.manpower}\n")
            f.write(f"\tstate_category = {state.category}\n")
            if impassable:
                f.write("\timpassable = yes\n")
            if local_supplies > 0:
                f.write(f"\tlocal_supplies = {local_supplies:.2f}\n")
            active_resources = {k: int(v) for k, v in user_resources.items() if int(v or 0) > 0}
            if active_resources:
                f.write("\tresources = {\n")
                for k, v in active_resources.items():
                    f.write(f"\t\t{k} = {v}\n")
                f.write("\t}\n")
            f.write("\n\thistory = {\n")
            if owner:
                f.write(f"\t\towner = {owner}\n")
                f.write(f"\t\tadd_core_of = {owner}\n")
            for core_tag in extra_cores:
                if core_tag and core_tag != owner:
                    f.write(f"\t\tadd_core_of = {core_tag}\n")
            for claim_tag in claims:
                if claim_tag:
                    f.write(f"\t\tadd_claim_by = {claim_tag}\n")
            if controller_tag and controller_tag != owner:
                f.write(f"\t\tcontroller = {controller_tag}\n")

            infra, arms, indu, dock, air = _CAT_BUILDINGS.get(
                state.category, (2, 1, 1, 0, 0)
            )
            state_coastal_provs = [p for p in land_provs if p in coastal_set]
            is_coastal_state = bool(state_coastal_provs)
            if is_coastal_state:
                dock = max(dock, _COASTAL_DOCKYARDS.get(state.category, 1))

            final_buildings: dict[str, int] = {
                "infrastructure": max(infra, 1),
            }
            if arms > 0:
                final_buildings["arms_factory"] = arms
            if indu > 0:
                final_buildings["industrial_complex"] = indu
            if dock > 0 and is_coastal_state:
                final_buildings["dockyard"] = dock
            if air > 0:
                final_buildings["air_base"] = air
            for bname, bval in user_buildings.items():
                bv = int(bval or 0)
                if bv > 0:
                    final_buildings[bname] = bv
                elif bname in final_buildings:
                    final_buildings.pop(bname)

            if impassable or state.category == "wasteland":
                final_buildings = {}

            f.write("\t\tbuildings = {\n")
            for bname, bval in final_buildings.items():
                f.write(f"\t\t\t{bname} = {bval}\n")

            prov_blocks: dict[int, dict[str, int]] = {}
            for pid, bmap in user_prov_buildings.items():
                if pid in land_provs:
                    prov_blocks[pid] = {k: int(v) for k, v in bmap.items() if int(v or 0) > 0}
            has_user_nb = any(
                "naval_base" in bmap for bmap in prov_blocks.values()
            )
            if is_coastal_state and not has_user_nb and not impassable:
                nb_level = 3 if state.category in (
                    "city", "large_city", "metropolis", "megalopolis"
                ) else 2
                nb_prov = state_coastal_provs[0]
                prov_blocks.setdefault(nb_prov, {})["naval_base"] = nb_level
            for pid, bmap in prov_blocks.items():
                if not bmap:
                    continue
                f.write(f"\t\t\t{pid} = {{\n")
                for bname, bval in bmap.items():
                    f.write(f"\t\t\t\t{bname} = {bval}\n")
                f.write("\t\t\t}\n")
            f.write("\t\t}\n")

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


def write_states_fallback(states: dict, tag: str, province_map, output_dir: str) -> None:
    """无 StateManager 时的 fallback 写法 (硬编码 town + infra=1)."""
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
