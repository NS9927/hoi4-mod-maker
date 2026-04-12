"""
PaintTileCommand — 画笔绘制陆地/海洋/湖泊瓦片。

存储变化的像素 delta: {(y, x): new_value}，execute 时记录旧值，undo 时恢复。
支持连续笔触合并 (can_merge_with / merge)。
"""

from __future__ import annotations

from commands.base import Command
from domain.map_data import MapData


class PaintTileCommand(Command):
    """画笔绘制 tile_map 像素。"""

    label = "画地块"

    def __init__(
        self,
        map_data: MapData,
        changes: dict[tuple[int, int], int],
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            changes: {(y, x): new_value} 要写入的新像素值
        """
        self._map_data = map_data
        self._changes = dict(changes)  # 防御性复制
        self._old_values: dict[tuple[int, int], int] = {}

    def execute(self) -> None:
        """保存旧值，写入新值。"""
        tile_map = self._map_data.tile_map
        old = {}
        for (y, x), new_val in self._changes.items():
            old[(y, x)] = int(tile_map[y, x])
            tile_map[y, x] = new_val
        self._old_values.update(old)

    def undo(self) -> None:
        """恢复旧值。"""
        tile_map = self._map_data.tile_map
        for (y, x), old_val in self._old_values.items():
            tile_map[y, x] = old_val

    def can_merge_with(self, other: Command) -> bool:
        """连续画笔笔触可合并。"""
        return isinstance(other, PaintTileCommand)

    def merge(self, other: Command) -> None:
        """将 other 的变化合并进来。

        对于重叠像素，保留 self 的 old_value（最早的旧值），
        用 other 的 new_value（最新的新值）。
        """
        if not isinstance(other, PaintTileCommand):
            raise TypeError("只能合并同类型命令")
        for pos, new_val in other._changes.items():
            if pos not in self._old_values:
                # self 没碰过这个像素，从 other 取旧值
                self._old_values[pos] = other._old_values.get(pos, new_val)
            # 新值始终取最新的
            self._changes[pos] = new_val
