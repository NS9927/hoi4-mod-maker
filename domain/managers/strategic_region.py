"""
Strategic Region 管理器 — 战略区域数据.

参考: 参考/Strategic region modding .txt

每个 region:
- id: 连续整数 (跳号崩)
- name: 本地化 key
- province_ids: 所属省份 (每个省份只能属一个 region)
- weather_preset: 'polar'/'cold'/'temperate'/'tropical'/'desert' — 自动填天气
- naval_terrain: 仅海洋 region, 下拉选
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np


WeatherPreset = Literal["polar", "cold", "temperate", "tropical", "desert"]

# 天气预设 → 4 季 period 块参数
# between 格式: DAY.MONTH, 0-indexed (0.0 = 1月1日, 30.11 = 12月31日)
WEATHER_PRESETS: dict[str, list[dict]] = {
    "polar": [
        {"between": "0.0 30.11", "temp": "-30.0 -5.0", "no": 0.2, "snow": 0.4,
         "blizzard": 0.3, "rain_light": 0.05, "rain_heavy": 0.0, "mud": 0.0,
         "sandstorm": 0.0, "min_snow": 0.5},
    ],
    "cold": [
        {"between": "0.0 29.1", "temp": "-15.0 0.0", "no": 0.3, "snow": 0.3,
         "blizzard": 0.15, "rain_light": 0.1, "rain_heavy": 0.05, "mud": 0.05,
         "sandstorm": 0.0, "min_snow": 0.2},
        {"between": "0.2 30.4", "temp": "0.0 15.0", "no": 0.4, "snow": 0.1,
         "blizzard": 0.0, "rain_light": 0.2, "rain_heavy": 0.1, "mud": 0.15,
         "sandstorm": 0.0, "min_snow": 0.0},
        {"between": "0.5 30.7", "temp": "10.0 25.0", "no": 0.5, "snow": 0.0,
         "blizzard": 0.0, "rain_light": 0.2, "rain_heavy": 0.1, "mud": 0.1,
         "sandstorm": 0.0, "min_snow": 0.0},
        {"between": "0.8 30.11", "temp": "-10.0 5.0", "no": 0.3, "snow": 0.25,
         "blizzard": 0.1, "rain_light": 0.15, "rain_heavy": 0.05, "mud": 0.1,
         "sandstorm": 0.0, "min_snow": 0.1},
    ],
    "temperate": [
        {"between": "0.0 30.11", "temp": "-5.0 25.0", "no": 0.5, "snow": 0.1,
         "blizzard": 0.05, "rain_light": 0.15, "rain_heavy": 0.05, "mud": 0.1,
         "sandstorm": 0.0, "min_snow": 0.0},
    ],
    "tropical": [
        {"between": "0.0 30.11", "temp": "20.0 35.0", "no": 0.3, "snow": 0.0,
         "blizzard": 0.0, "rain_light": 0.25, "rain_heavy": 0.2, "mud": 0.15,
         "sandstorm": 0.0, "min_snow": 0.0},
    ],
    "desert": [
        {"between": "0.0 30.11", "temp": "10.0 45.0", "no": 0.6, "snow": 0.0,
         "blizzard": 0.0, "rain_light": 0.05, "rain_heavy": 0.0, "mud": 0.0,
         "sandstorm": 0.25, "min_snow": 0.0},
    ],
}

PRESET_LABELS = {
    "polar": "极地", "cold": "寒带", "temperate": "温带",
    "tropical": "热带", "desert": "沙漠",
}


@dataclass
class StrategicRegion:
    id: int
    name: str = ""
    province_ids: list[int] = field(default_factory=list)
    weather_preset: str = "temperate"
    naval_terrain: str = ""  # ocean_terrain / deep_ocean / shallow_sea 等

    def __post_init__(self):
        if not self.name:
            self.name = f"STRATEGICREGION_{self.id}"


class StrategicRegionManager:
    """管理所有战略区域. ID 必须连续从 1 开始."""

    def __init__(self) -> None:
        self._regions: dict[int, StrategicRegion] = {}
        self._next_id = 1

    @property
    def regions(self) -> dict[int, StrategicRegion]:
        return dict(self._regions)

    def count(self) -> int:
        return len(self._regions)

    def get(self, rid: int) -> StrategicRegion | None:
        return self._regions.get(rid)

    def create_region(self, name: str = "") -> StrategicRegion:
        """新建空 region, 返回它."""
        r = StrategicRegion(id=self._next_id, name=name)
        self._regions[self._next_id] = r
        self._next_id += 1
        return r

    def remove_region(self, rid: int) -> bool:
        if rid in self._regions:
            del self._regions[rid]
            return True
        return False

    def assign_province(self, pid: int, rid: int) -> None:
        """把省份分配给 region. 自动从旧 region 移除."""
        for r in self._regions.values():
            if pid in r.province_ids:
                r.province_ids.remove(pid)
        if rid in self._regions:
            self._regions[rid].province_ids.append(pid)

    def get_region_of_province(self, pid: int) -> int:
        """查省份属于哪个 region. 0 = 未分配."""
        for r in self._regions.values():
            if pid in r.province_ids:
                return r.id
        return 0

    def auto_generate(
        self,
        province_map: np.ndarray,
        tile_map: np.ndarray,
        state_mgr=None,
        grid_cols: int = 6,
        grid_rows: int = 4,
    ) -> None:
        """自动生成战略区域 (覆盖现有数据).

        如果有 state_mgr, 每个 state 的省份归到同一 region (避免跨区错误).
        否则用网格拆分.
        """
        from data.constants import MAP_WIDTH, MAP_HEIGHT, TILE_LAND

        self._regions = {}
        self._next_id = 1

        province_count = int(province_map.max())
        if province_count == 0:
            return

        # 质心计算
        flat_pm = province_map.ravel()
        n = province_count + 1
        pid_count = np.bincount(flat_pm, minlength=n)
        ys, xs = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
        sum_y = np.bincount(flat_pm, weights=ys.ravel().astype(np.float64), minlength=n)
        sum_x = np.bincount(flat_pm, weights=xs.ravel().astype(np.float64), minlength=n)

        if state_mgr is not None and state_mgr.states:
            # state-aware: 每 state 一个 region
            assigned = set()
            for sid in sorted(state_mgr.states.keys()):
                s = state_mgr.states[sid]
                provs = [p for p in s.provinces if pid_count[p] > 0]
                if not provs:
                    continue
                r = self.create_region()
                r.province_ids = list(provs)
                assigned.update(provs)

            # 剩余省份 (海/湖/孤儿) 按网格
            cell_h = MAP_HEIGHT / max(1, grid_rows)
            cell_w = MAP_WIDTH / max(1, grid_cols)
            sea_buckets: dict[int, list[int]] = {}
            for pid in range(1, province_count + 1):
                if pid in assigned or pid_count[pid] == 0:
                    continue
                cy = sum_y[pid] / pid_count[pid]
                cx = sum_x[pid] / pid_count[pid]
                row = min(int(cy / cell_h), grid_rows - 1)
                col = min(int(cx / cell_w), grid_cols - 1)
                key = row * grid_cols + col
                sea_buckets.setdefault(key, []).append(pid)
            for provs in sea_buckets.values():
                r = self.create_region()
                r.province_ids = list(provs)
        else:
            # 纯网格
            cell_h = MAP_HEIGHT / grid_rows
            cell_w = MAP_WIDTH / grid_cols
            buckets: dict[int, list[int]] = {}
            for pid in range(1, province_count + 1):
                if pid_count[pid] == 0:
                    continue
                cy = sum_y[pid] / pid_count[pid]
                cx = sum_x[pid] / pid_count[pid]
                row = min(int(cy / cell_h), grid_rows - 1)
                col = min(int(cx / cell_w), grid_cols - 1)
                key = row * grid_cols + col
                buckets.setdefault(key, []).append(pid)
            for provs in buckets.values():
                r = self.create_region()
                r.province_ids = list(provs)

        # 自动分配 weather preset (按质心纬度)
        for r in self._regions.values():
            if not r.province_ids:
                continue
            total_y = sum(float(sum_y[p]) / max(pid_count[p], 1) for p in r.province_ids)
            avg_y = total_y / len(r.province_ids)
            # 纬度映射: y=0 北极, y=MAP_HEIGHT 南极, 中间赤道
            lat_fraction = avg_y / MAP_HEIGHT  # 0=北极, 0.5=赤道, 1=南极
            dist_from_equator = abs(lat_fraction - 0.5) * 2  # 0=赤道, 1=极地
            if dist_from_equator > 0.8:
                r.weather_preset = "polar"
            elif dist_from_equator > 0.6:
                r.weather_preset = "cold"
            elif dist_from_equator > 0.3:
                r.weather_preset = "temperate"
            else:
                # 赤道附近: 检查是否沙漠 (如果大部分省份是沙漠地形)
                r.weather_preset = "tropical"

    def clear(self) -> None:
        self._regions = {}
        self._next_id = 1

    # ─────────── 序列化 ───────────

    def to_dict(self) -> dict:
        return {
            "next_id": self._next_id,
            "regions": [
                {
                    "id": r.id,
                    "name": r.name,
                    "province_ids": list(r.province_ids),
                    "weather_preset": r.weather_preset,
                    "naval_terrain": r.naval_terrain,
                }
                for r in self._regions.values()
            ],
        }

    def from_dict(self, data: dict) -> None:
        self._regions = {}
        self._next_id = int(data.get("next_id", 1))
        for d in data.get("regions", []):
            r = StrategicRegion(
                id=int(d["id"]),
                name=d.get("name", ""),
                province_ids=[int(p) for p in d.get("province_ids", [])],
                weather_preset=d.get("weather_preset", "temperate"),
                naval_terrain=d.get("naval_terrain", ""),
            )
            self._regions[r.id] = r
            self._next_id = max(self._next_id, r.id + 1)
