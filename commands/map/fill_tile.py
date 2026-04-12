"""
FillTileCommand — 洪水填充 tile_map。

使用 numpy bool mask 标记受影响区域，存储旧值 delta。
"""

from __future__ import annotations

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class FillTileCommand(Command):
    """洪水填充 tile_map。"""

    label = "填充地块"

    def __init__(
        self,
        map_data: MapData,
        fill_mask: np.ndarray,
        fill_value: int,
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            fill_mask: bool 数组，True 的像素会被填充
            fill_value: 填充值
        """
        self._map_data = map_data
        self._fill_mask = fill_mask.copy()
        self._fill_value = fill_value
        # 只存被改变的旧值（压缩存储）
        self._old_values: np.ndarray | None = None

    def execute(self) -> None:
        """保存 mask 区域旧值，写入填充值。"""
        tile_map = self._map_data.tile_map
        self._old_values = tile_map[self._fill_mask].copy()
        tile_map[self._fill_mask] = self._fill_value

    def undo(self) -> None:
        """恢复 mask 区域的旧值。"""
        if self._old_values is not None:
            self._map_data.tile_map[self._fill_mask] = self._old_values
