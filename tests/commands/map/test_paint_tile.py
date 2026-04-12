"""
PaintTileCommand 单元测试。
"""

import numpy as np
import pytest

from domain.map_data import MapData
from commands.map.paint_tile import PaintTileCommand


def _make_map_data(h: int = 4, w: int = 4) -> MapData:
    """创建小尺寸 MapData 用于测试。"""
    md = MapData.__new__(MapData)
    md.tile_map = np.zeros((h, w), dtype=np.uint8)
    md.province_map = np.zeros((h, w), dtype=np.int32)
    md.terrain_map = np.zeros((h, w), dtype=np.uint8)
    md.height_map = np.full((h, w), 40, dtype=np.uint8)
    md.river_map = np.full((h, w), 255, dtype=np.uint8)
    md.provincial_terrain = {}
    return md


class TestPaintTileCommand:
    """PaintTileCommand 测试。"""

    def test_execute_changes_pixels(self) -> None:
        """execute 应该修改 tile_map 对应像素。"""
        md = _make_map_data()
        changes = {(0, 0): 1, (1, 2): 2, (3, 3): 1}
        cmd = PaintTileCommand(md, changes)
        cmd.execute()

        assert md.tile_map[0, 0] == 1
        assert md.tile_map[1, 2] == 2
        assert md.tile_map[3, 3] == 1
        # 未修改的像素保持不变
        assert md.tile_map[0, 1] == 0

    def test_undo_restores_old_values(self) -> None:
        """undo 应该恢复修改前的值。"""
        md = _make_map_data()
        md.tile_map[0, 0] = 5
        md.tile_map[1, 1] = 7

        changes = {(0, 0): 1, (1, 1): 2}
        cmd = PaintTileCommand(md, changes)
        cmd.execute()

        assert md.tile_map[0, 0] == 1
        assert md.tile_map[1, 1] == 2

        cmd.undo()

        assert md.tile_map[0, 0] == 5
        assert md.tile_map[1, 1] == 7

    def test_can_merge_with_same_type(self) -> None:
        """can_merge_with 对同类型应返回 True。"""
        md = _make_map_data()
        cmd1 = PaintTileCommand(md, {(0, 0): 1})
        cmd2 = PaintTileCommand(md, {(1, 1): 2})

        assert cmd1.can_merge_with(cmd2) is True

    def test_can_merge_with_different_type(self) -> None:
        """can_merge_with 对不同类型应返回 False。"""
        from commands.base import Command

        md = _make_map_data()
        cmd1 = PaintTileCommand(md, {(0, 0): 1})

        class DummyCommand(Command):
            def execute(self) -> None: ...
            def undo(self) -> None: ...

        cmd2 = DummyCommand()
        assert cmd1.can_merge_with(cmd2) is False

    def test_merge_combines_changes(self) -> None:
        """merge 应合并两个命令的 changes，保留最早旧值。"""
        md = _make_map_data()
        md.tile_map[0, 0] = 10
        md.tile_map[1, 1] = 20

        cmd1 = PaintTileCommand(md, {(0, 0): 1})
        cmd1.execute()

        cmd2 = PaintTileCommand(md, {(0, 0): 3, (1, 1): 4})
        cmd2.execute()

        cmd1.merge(cmd2)

        # 合并后 undo 应恢复到最初始值
        cmd1.undo()
        assert md.tile_map[0, 0] == 10  # 最早的旧值
        assert md.tile_map[1, 1] == 20  # cmd2 记录的旧值

    def test_execute_is_reentrant(self) -> None:
        """execute 可重入（redo 再调一次不出错）。"""
        md = _make_map_data()
        changes = {(0, 0): 1}
        cmd = PaintTileCommand(md, changes)

        cmd.execute()
        assert md.tile_map[0, 0] == 1
        cmd.undo()
        assert md.tile_map[0, 0] == 0
        cmd.execute()
        assert md.tile_map[0, 0] == 1
