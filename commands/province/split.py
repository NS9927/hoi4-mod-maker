"""
SplitProvinceCommand — 拆分省份。

将指定像素从原省份分配给新省份 ID。
"""

from __future__ import annotations

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class SplitProvinceCommand(Command):
    """拆分省份：将 split_pixels 从 pid 分配给 new_pid。"""

    label = "拆分省份"

    def __init__(
        self,
        map_data: MapData,
        pid: int,
        new_pid: int,
        split_pixels: np.ndarray,
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            pid: 原始省份 ID
            new_pid: 新省份 ID
            split_pixels: bool mask，True 的像素分配给 new_pid
        """
        self._map_data = map_data
        self._pid = pid
        self._new_pid = new_pid
        self._split_pixels = split_pixels.copy()

    def execute(self) -> None:
        """将 split_pixels 标记的像素分配给 new_pid。"""
        self._map_data.province_map[self._split_pixels] = self._new_pid

    def undo(self) -> None:
        """将像素恢复回原 pid。"""
        self._map_data.province_map[self._split_pixels] = self._pid
