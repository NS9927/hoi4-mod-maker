"""
MergeProvincesCommand 单元测试。
"""

import numpy as np
import pytest

from domain.map_data import MapData
from commands.province.merge import MergeProvincesCommand


def _make_map_data(h: int = 4, w: int = 4) -> MapData:
    """创建小尺寸 MapData 用于测试。"""
    md = MapData.__new__(MapData)
    md.tile_map = np.ones((h, w), dtype=np.uint8)  # 全陆地
    md.province_map = np.zeros((h, w), dtype=np.int32)
    md.terrain_map = np.zeros((h, w), dtype=np.uint8)
    md.height_map = np.full((h, w), 40, dtype=np.uint8)
    md.river_map = np.full((h, w), 255, dtype=np.uint8)
    md.provincial_terrain = {}
    return md


class TestMergeProvincesCommand:
    """MergeProvincesCommand 测试。"""

    def test_merge_changes_pixels(self) -> None:
        """execute 应将被移除省份的像素改为保留省份 ID。"""
        md = _make_map_data()
        # 设置两个省份: pid=1 占左半，pid=2 占右半
        md.province_map[:, :2] = 1
        md.province_map[:, 2:] = 2

        cmd = MergeProvincesCommand(md, pid_keep=1, pid_remove=2)
        cmd.execute()

        # 所有像素应变为 pid=1
        assert (md.province_map[:, 2:] == 1).all()
        assert (md.province_map[:, :2] == 1).all()

    def test_undo_restores_pixels(self) -> None:
        """undo 应恢复被合并省份的像素。"""
        md = _make_map_data()
        md.province_map[:, :2] = 1
        md.province_map[:, 2:] = 2

        original = md.province_map.copy()

        cmd = MergeProvincesCommand(md, pid_keep=1, pid_remove=2)
        cmd.execute()

        # 合并后 pid=2 消失
        assert not (md.province_map == 2).any()

        cmd.undo()

        # 恢复后右半应回到 pid=2
        assert (md.province_map[:, 2:] == 2).all()
        assert (md.province_map[:, :2] == 1).all()
