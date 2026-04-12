"""
SetHeightCommand — 按省份 mask 设置高度值。
"""

from __future__ import annotations

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class SetHeightCommand(Command):
    """按省份 mask 批量设置 height_map。"""

    label = "设置高度"

    def __init__(
        self,
        map_data: MapData,
        province_mask: np.ndarray,
        new_height_value: int,
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            province_mask: bool 数组，True 的像素会被修改
            new_height_value: 新高度值 (0-255)
        """
        self._map_data = map_data
        self._mask = province_mask.copy()
        self._new_height = new_height_value
        self._old_heights: np.ndarray | None = None

    def execute(self) -> None:
        """保存旧高度，写入新值。"""
        height_map = self._map_data.height_map
        self._old_heights = height_map[self._mask].copy()
        height_map[self._mask] = self._new_height

    def undo(self) -> None:
        """恢复旧高度。"""
        if self._old_heights is not None:
            self._map_data.height_map[self._mask] = self._old_heights
