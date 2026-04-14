"""
GenerateTerrainCommand — 智能地形生成的 undo/redo。

支持全图生成和局部重塑 (mask)。
"""

from __future__ import annotations

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class GenerateTerrainCommand(Command):
    """智能地形生成 — 快照整个 terrain_map 或 mask 区域。"""

    label = "智能地形生成"

    def __init__(
        self,
        map_data: MapData,
        new_terrain: np.ndarray,
        mask: np.ndarray | None = None,
    ) -> None:
        """
        Parameters
        ----------
        map_data : 地图数据对象
        new_terrain : 生成的新 terrain_map (完整尺寸)
        mask : bool 数组，只影响 mask==True 区域 (局部重塑用)
        """
        self._map_data = map_data
        self._mask = mask

        if mask is not None:
            # 局部重塑: 只存 mask 区域的像素
            coords = np.argwhere(mask)
            self._coords = coords
            self._new_values = new_terrain[mask].copy()
            self._old_values = map_data.terrain_map[mask].copy()
        else:
            # 全图: 存整个旧 terrain_map
            self._coords = None
            self._new_terrain = new_terrain.copy()
            self._old_terrain = map_data.terrain_map.copy()

    def execute(self) -> None:
        if self._coords is not None:
            # 局部
            for i, (y, x) in enumerate(self._coords):
                self._map_data.terrain_map[y, x] = self._new_values[i]
        else:
            # 全图
            self._map_data.terrain_map[:] = self._new_terrain

    def undo(self) -> None:
        if self._coords is not None:
            for i, (y, x) in enumerate(self._coords):
                self._map_data.terrain_map[y, x] = self._old_values[i]
        else:
            self._map_data.terrain_map[:] = self._old_terrain
