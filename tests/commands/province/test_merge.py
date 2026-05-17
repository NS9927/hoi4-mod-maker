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


class TestMergeStrategicRegionCleanup:
    """merge 后 pid_remove 必须从 strategic_region 移除, 否则切割复用 ID 时新省份会继承旧 region."""

    def test_pid_remove_cleared_from_region_on_execute(self) -> None:
        from domain.managers.strategic_region import StrategicRegionManager

        md = _make_map_data()
        md.province_map[:, :2] = 1
        md.province_map[:, 2:] = 2

        sr = StrategicRegionManager()
        r = sr.create_region(name="region_A")
        r.province_ids = [1, 2]

        cmd = MergeProvincesCommand(
            md, pid_keep=1, pid_remove=2, strategic_region_mgr=sr
        )
        cmd.execute()

        assert 2 not in sr.get(r.id).province_ids
        assert 1 in sr.get(r.id).province_ids

    def test_undo_restores_pid_to_region(self) -> None:
        from domain.managers.strategic_region import StrategicRegionManager

        md = _make_map_data()
        md.province_map[:, :2] = 1
        md.province_map[:, 2:] = 2

        sr = StrategicRegionManager()
        r = sr.create_region(name="region_A")
        r.province_ids = [1, 2]

        cmd = MergeProvincesCommand(
            md, pid_keep=1, pid_remove=2, strategic_region_mgr=sr
        )
        cmd.execute()
        cmd.undo()

        assert 2 in sr.get(r.id).province_ids


class TestMergeCapitalMigration:
    """merge 若吞掉某国首都, capital 必须迁移, 否则 capital 指向死 ID → 启动游戏崩."""

    def test_capital_migrates_to_pid_keep_when_same_country(self) -> None:
        from domain.managers.state import StateManager
        from domain.managers.country import CountryManager

        md = _make_map_data()
        md.province_map[:, :2] = 1
        md.province_map[:, 2:] = 2

        state_mgr = StateManager()
        s = state_mgr.create_state()
        state_mgr.assign_province(1, s.id)
        state_mgr.assign_province(2, s.id)

        country_mgr = CountryManager()
        country_mgr.create_country("AAA", name="A", color=(1, 2, 3))
        country_mgr.assign_state(s.id, "AAA")
        country_mgr.set_capital("AAA", 2)  # 首都 = pid_remove

        cmd = MergeProvincesCommand(
            md, pid_keep=1, pid_remove=2,
            state_mgr=state_mgr, country_mgr=country_mgr,
        )
        cmd.execute()

        # 首都迁到 pid_keep (同国, 物理上接管了 pid_remove 的像素)
        assert country_mgr.get_country("AAA").capital == 1

    def test_undo_restores_capital(self) -> None:
        from domain.managers.state import StateManager
        from domain.managers.country import CountryManager

        md = _make_map_data()
        md.province_map[:, :2] = 1
        md.province_map[:, 2:] = 2

        state_mgr = StateManager()
        s = state_mgr.create_state()
        state_mgr.assign_province(1, s.id)
        state_mgr.assign_province(2, s.id)

        country_mgr = CountryManager()
        country_mgr.create_country("AAA", name="A", color=(1, 2, 3))
        country_mgr.assign_state(s.id, "AAA")
        country_mgr.set_capital("AAA", 2)

        cmd = MergeProvincesCommand(
            md, pid_keep=1, pid_remove=2,
            state_mgr=state_mgr, country_mgr=country_mgr,
        )
        cmd.execute()
        cmd.undo()

        assert country_mgr.get_country("AAA").capital == 2

    def test_no_capital_change_when_pid_remove_not_capital(self) -> None:
        from domain.managers.state import StateManager
        from domain.managers.country import CountryManager

        md = _make_map_data()
        md.province_map[:, :2] = 1
        md.province_map[:, 2:] = 2

        state_mgr = StateManager()
        s = state_mgr.create_state()
        state_mgr.assign_province(1, s.id)
        state_mgr.assign_province(2, s.id)

        country_mgr = CountryManager()
        country_mgr.create_country("AAA", name="A", color=(1, 2, 3))
        country_mgr.assign_state(s.id, "AAA")
        country_mgr.set_capital("AAA", 1)  # 首都 = pid_keep, 不是 pid_remove

        cmd = MergeProvincesCommand(
            md, pid_keep=1, pid_remove=2,
            state_mgr=state_mgr, country_mgr=country_mgr,
        )
        cmd.execute()

        assert country_mgr.get_country("AAA").capital == 1
