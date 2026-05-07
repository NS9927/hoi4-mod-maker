"""
GenerateTerrainCommand — 智能地形生成的 undo/redo。

支持全图生成和局部重塑 (mask)。
"""

from __future__ import annotations

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class GenerateTerrainCommand(Command):
    """智能地形生成 — 快照整个 terrain_map 或 mask 区域。

    同时同步 provincial_terrain dict (BUG-4): 自动生成 terrain.bmp 后,
    属性层的 dict 也会跟着填充, 避免用户报告 "attribute 没生成".
    策略: 只填补 dict 里没有的 province, 已有的不覆盖 (保护用户手动编辑).
    """

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

        # 同步 provincial_terrain (BUG-4): 反推新 terrain 对应的 dict, 只填补空的
        self._old_provincial = dict(map_data.provincial_terrain)
        self._new_provincial = self._compute_merged_provincial(
            map_data, new_terrain
        )

    def _compute_merged_provincial(
        self, map_data: MapData, new_terrain: np.ndarray,
    ) -> dict[int, str]:
        """从 new_terrain 反推 provincial_terrain, 与现有 dict 合并 (现有的优先)."""
        try:
            from services.terrain_service import compute_provincial_terrain_from_bmp
            inferred = compute_provincial_terrain_from_bmp(
                new_terrain, map_data.province_map, map_data.tile_map,
            )
        except Exception:
            return dict(map_data.provincial_terrain)
        merged = dict(map_data.provincial_terrain)
        # 只填补 dict 里没有的 province, 不覆盖用户已设定的
        for pid, terr in inferred.items():
            if pid not in merged:
                merged[pid] = terr
        return merged

    def execute(self) -> None:
        if self._coords is not None:
            # 局部
            for i, (y, x) in enumerate(self._coords):
                self._map_data.terrain_map[y, x] = self._new_values[i]
        else:
            # 全图
            self._map_data.terrain_map[:] = self._new_terrain
        # 同步 dict
        self._map_data.provincial_terrain.clear()
        self._map_data.provincial_terrain.update(self._new_provincial)

    def undo(self) -> None:
        if self._coords is not None:
            for i, (y, x) in enumerate(self._coords):
                self._map_data.terrain_map[y, x] = self._old_values[i]
        else:
            self._map_data.terrain_map[:] = self._old_terrain
        # 恢复 dict
        self._map_data.provincial_terrain.clear()
        self._map_data.provincial_terrain.update(self._old_provincial)
