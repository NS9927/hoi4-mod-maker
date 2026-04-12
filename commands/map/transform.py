"""
TransformCommand — 区域变换（移动/旋转/缩放等）。

存储受影响区域的 bbox + 旧/新数据快照。
"""

from __future__ import annotations

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class TransformCommand(Command):
    """区域变换 tile_map。"""

    label = "变换区域"

    def __init__(
        self,
        map_data: MapData,
        old_region: tuple[tuple[int, int, int, int], np.ndarray],
        new_region: tuple[tuple[int, int, int, int], np.ndarray],
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            old_region: ((y_min, x_min, y_max, x_max), data) 变换前的区域数据
            new_region: ((y_min, x_min, y_max, x_max), data) 变换后的区域数据
        """
        self._map_data = map_data
        self._old_bbox, self._old_data = old_region
        self._new_bbox, self._new_data = new_region
        # 防御性复制
        self._old_data = self._old_data.copy()
        self._new_data = self._new_data.copy()

    def _apply_region(
        self, bbox: tuple[int, int, int, int], data: np.ndarray
    ) -> None:
        """将数据写入 tile_map 的指定 bbox 区域。"""
        y_min, x_min, y_max, x_max = bbox
        self._map_data.tile_map[y_min:y_max, x_min:x_max] = data

    def execute(self) -> None:
        """应用新区域数据。"""
        self._apply_region(self._new_bbox, self._new_data)

    def undo(self) -> None:
        """恢复旧区域数据。"""
        self._apply_region(self._old_bbox, self._old_data)
