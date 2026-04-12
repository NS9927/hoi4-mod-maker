"""
PaintTerrainCommand — 画笔绘制地形 + 可选高度自动联动。

支持两种模式:
1. 画笔模式: 直接修改 terrain_map 像素
2. 省份模式: 同时更新 provincial_terrain 字典
"""

from __future__ import annotations

from commands.base import Command
from domain.map_data import MapData


class PaintTerrainCommand(Command):
    """画笔绘制 terrain_map 像素，可联动 height_map。"""

    label = "画地形"

    def __init__(
        self,
        map_data: MapData,
        terrain_changes: dict[tuple[int, int], int],
        height_changes: dict[tuple[int, int], int] | None = None,
        provincial_terrain_changes: dict[int, str] | None = None,
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            terrain_changes: {(y, x): new_terrain_index}
            height_changes: {(y, x): new_height_value} 高度联动（可选）
            provincial_terrain_changes: {province_id: new_terrain_type} 省份级地形（可选）
        """
        self._map_data = map_data
        self._terrain_changes = dict(terrain_changes)
        self._height_changes = dict(height_changes) if height_changes else {}
        self._prov_terrain_changes = (
            dict(provincial_terrain_changes) if provincial_terrain_changes else {}
        )
        # 旧值存储
        self._old_terrain: dict[tuple[int, int], int] = {}
        self._old_height: dict[tuple[int, int], int] = {}
        self._old_prov_terrain: dict[int, str | None] = {}

    def execute(self) -> None:
        """保存旧值，写入新地形/高度。"""
        terrain_map = self._map_data.terrain_map
        height_map = self._map_data.height_map

        for (y, x), new_val in self._terrain_changes.items():
            self._old_terrain[(y, x)] = int(terrain_map[y, x])
            terrain_map[y, x] = new_val

        for (y, x), new_val in self._height_changes.items():
            self._old_height[(y, x)] = int(height_map[y, x])
            height_map[y, x] = new_val

        prov_terrain = self._map_data.provincial_terrain
        for pid, new_type in self._prov_terrain_changes.items():
            self._old_prov_terrain[pid] = prov_terrain.get(pid)
            prov_terrain[pid] = new_type

    def undo(self) -> None:
        """恢复旧地形/高度。"""
        terrain_map = self._map_data.terrain_map
        height_map = self._map_data.height_map

        for (y, x), old_val in self._old_terrain.items():
            terrain_map[y, x] = old_val

        for (y, x), old_val in self._old_height.items():
            height_map[y, x] = old_val

        prov_terrain = self._map_data.provincial_terrain
        for pid, old_type in self._old_prov_terrain.items():
            if old_type is None:
                prov_terrain.pop(pid, None)
            else:
                prov_terrain[pid] = old_type
