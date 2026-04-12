"""
PaintRiverCommand — 画笔绘制河流像素。

存储变化的像素 delta，支持连续笔触合并。
"""

from __future__ import annotations

from commands.base import Command
from domain.map_data import MapData


class PaintRiverCommand(Command):
    """画笔绘制 river_map 像素。"""

    label = "画河流"

    def __init__(
        self,
        map_data: MapData,
        changes: dict[tuple[int, int], int],
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            changes: {(y, x): new_value} 要写入的新河流像素值
        """
        self._map_data = map_data
        self._changes = dict(changes)
        self._old_values: dict[tuple[int, int], int] = {}

    def execute(self) -> None:
        """保存旧值，写入新值。"""
        river_map = self._map_data.river_map
        old = {}
        for (y, x), new_val in self._changes.items():
            old[(y, x)] = int(river_map[y, x])
            river_map[y, x] = new_val
        self._old_values.update(old)

    def undo(self) -> None:
        """恢复旧值。"""
        river_map = self._map_data.river_map
        for (y, x), old_val in self._old_values.items():
            river_map[y, x] = old_val

    def can_merge_with(self, other: Command) -> bool:
        """连续河流笔触可合并。"""
        return isinstance(other, PaintRiverCommand)

    def merge(self, other: Command) -> None:
        """将 other 的变化合并进来。"""
        if not isinstance(other, PaintRiverCommand):
            raise TypeError("只能合并同类型命令")
        for pos, new_val in other._changes.items():
            if pos not in self._old_values:
                self._old_values[pos] = other._old_values.get(pos, new_val)
            self._changes[pos] = new_val
