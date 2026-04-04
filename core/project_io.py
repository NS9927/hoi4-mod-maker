"""
项目保存/加载 — 将所有数据序列化到 .hoi4proj 文件
使用 numpy 压缩存储大数组，JSON 存储元数据
"""
import os
import json
import numpy as np
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED


def save_project(
    path: str,
    tile_map: np.ndarray,
    province_map: np.ndarray,
    terrain_map: np.ndarray,
    height_map: np.ndarray,
    state_mgr,   # StateManager
    country_mgr, # CountryManager
    river_map: np.ndarray | None = None,
) -> None:
    """保存项目到 .hoi4proj 文件（zip 格式）"""
    with ZipFile(path, "w", ZIP_DEFLATED) as zf:
        # 保存 numpy 数组
        arrays_to_save = [
            ("tile_map.npy", tile_map),
            ("province_map.npy", province_map),
            ("terrain_map.npy", terrain_map),
            ("height_map.npy", height_map),
        ]
        if river_map is not None:
            arrays_to_save.append(("river_map.npy", river_map))
        for name, arr in arrays_to_save:
            buf = BytesIO()
            np.save(buf, arr)
            zf.writestr(name, buf.getvalue())

        # 保存 State 数据
        states_data = {}
        for sid, s in state_mgr.states.items():
            states_data[str(sid)] = {
                "id": s.id,
                "name": s.name,
                "provinces": s.provinces,
                "manpower": s.manpower,
                "category": s.category,
                "owner_tag": s.owner_tag,
                "victory_points": {str(k): v for k, v in s.victory_points.items()},
            }
        zf.writestr("states.json", json.dumps(states_data, ensure_ascii=False, indent=2))

        # 保存国家数据
        countries_data = {}
        for tag, c in country_mgr.countries.items():
            countries_data[tag] = {
                "tag": c.tag,
                "name": c.name,
                "color": list(c.color),
                "capital": c.capital,
                "ruling_party": c.ruling_party,
                "popularities": c.popularities,
            }
        # 保存 state_owner 映射
        state_owners = {str(k): v for k, v in country_mgr._state_owner.items()}

        zf.writestr("countries.json", json.dumps({
            "countries": countries_data,
            "state_owners": state_owners,
        }, ensure_ascii=False, indent=2))


def load_project(
    path: str,
    state_mgr,
    country_mgr,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """
    加载项目文件。

    返回 (tile_map, province_map, terrain_map, height_map, river_map)
    同时填充 state_mgr 和 country_mgr
    river_map 可能为 None（旧版项目文件没有）
    """
    with ZipFile(path, "r") as zf:
        # 加载 numpy 数组
        tile_map = np.load(BytesIO(zf.read("tile_map.npy")))
        province_map = np.load(BytesIO(zf.read("province_map.npy")))
        terrain_map = np.load(BytesIO(zf.read("terrain_map.npy")))
        height_map = np.load(BytesIO(zf.read("height_map.npy")))

        # 河流数据（兼容旧版本）
        river_map = None
        if "river_map.npy" in zf.namelist():
            river_map = np.load(BytesIO(zf.read("river_map.npy")))

        # 加载 State 数据
        state_mgr.clear()
        states_raw = json.loads(zf.read("states.json"))
        from core.state_manager import StateData
        for sid_str, data in states_raw.items():
            sid = int(sid_str)
            state = StateData(
                id=data["id"],
                name=data["name"],
                provinces=data["provinces"],
                manpower=data["manpower"],
                category=data["category"],
                owner_tag=data.get("owner_tag", ""),
                victory_points={int(k): v for k, v in data.get("victory_points", {}).items()},
            )
            state_mgr._states[sid] = state
            for pid in state.provinces:
                state_mgr._province_to_state[pid] = sid
            state_mgr._next_id = max(state_mgr._next_id, sid + 1)

        # 加载国家数据
        country_mgr.clear()
        countries_raw = json.loads(zf.read("countries.json"))
        from core.country_manager import CountryData
        for tag, data in countries_raw.get("countries", {}).items():
            country = CountryData(
                tag=data["tag"],
                name=data["name"],
                color=tuple(data["color"]),
                capital=data.get("capital", 0),
                ruling_party=data.get("ruling_party", "neutrality"),
                popularities=data.get("popularities", {
                    "democratic": 10, "fascism": 5, "communism": 5, "neutrality": 80,
                }),
            )
            country_mgr._countries[tag] = country

        for sid_str, tag in countries_raw.get("state_owners", {}).items():
            country_mgr._state_owner[int(sid_str)] = tag

    return tile_map, province_map, terrain_map, height_map, river_map
