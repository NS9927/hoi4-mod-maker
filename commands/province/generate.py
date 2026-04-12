"""
GenerateProvincesCommand — 生成省份（存储旧 province_map 的 zlib 压缩快照）。

由于 province_map 很大 (5632x2048 int32 = ~44MB)，用 zlib 压缩存储旧值。
"""

from __future__ import annotations

import zlib

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class GenerateProvincesCommand(Command):
    """生成省份，存储完整旧 province_map（zlib 压缩）。"""

    label = "生成省份"

    def __init__(
        self,
        map_data: MapData,
        new_province_map: np.ndarray,
        new_count: int,
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            new_province_map: 新的省份图（int32 数组）
            new_count: 新的省份总数
        """
        self._map_data = map_data
        self._new_map = new_province_map.copy()
        self._new_count = new_count
        # 延迟保存旧值（execute 时压缩）
        self._old_map_compressed: bytes = b""
        self._old_shape: tuple[int, ...] = ()
        self._old_dtype: np.dtype = np.dtype(np.int32)

    def execute(self) -> None:
        """压缩保存旧 province_map，写入新值。"""
        old_map = self._map_data.province_map
        self._old_shape = old_map.shape
        self._old_dtype = old_map.dtype
        self._old_map_compressed = zlib.compress(old_map.tobytes(), level=1)
        self._map_data.province_map[:] = self._new_map

    def undo(self) -> None:
        """解压恢复旧 province_map。"""
        raw = zlib.decompress(self._old_map_compressed)
        old_map = np.frombuffer(raw, dtype=self._old_dtype).reshape(self._old_shape)
        self._map_data.province_map[:] = old_map
