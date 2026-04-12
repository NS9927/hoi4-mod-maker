"""
SetVPCommand 单元测试。
"""

import pytest

from domain.managers.state import StateManager
from commands.state.set_vp import SetVPCommand


class TestSetVPCommand:
    """SetVPCommand 测试。"""

    def _make_state_mgr(self) -> StateManager:
        """创建带一个 State 的 StateManager。"""
        mgr = StateManager()
        state = mgr.create_state(provinces=[1, 2, 3])
        return mgr

    def test_execute_sets_vp(self) -> None:
        """execute 应设置 VP。"""
        mgr = self._make_state_mgr()
        cmd = SetVPCommand(mgr, pid=1, old_vp=None, new_vp=10)
        cmd.execute()

        state = mgr.get_state(1)
        assert state is not None
        assert state.victory_points[1] == 10

    def test_undo_restores_no_vp(self) -> None:
        """undo 应移除之前不存在的 VP。"""
        mgr = self._make_state_mgr()
        cmd = SetVPCommand(mgr, pid=1, old_vp=None, new_vp=10)
        cmd.execute()
        cmd.undo()

        state = mgr.get_state(1)
        assert state is not None
        assert 1 not in state.victory_points

    def test_undo_restores_old_vp(self) -> None:
        """undo 应恢复旧的 VP 值。"""
        mgr = self._make_state_mgr()
        # 先设一个初始 VP
        mgr.set_vp(2, 5)

        cmd = SetVPCommand(mgr, pid=2, old_vp=5, new_vp=20)
        cmd.execute()

        state = mgr.get_state(1)
        assert state is not None
        assert state.victory_points[2] == 20

        cmd.undo()
        assert state.victory_points[2] == 5

    def test_execute_remove_vp(self) -> None:
        """new_vp=None 时 execute 应移除 VP。"""
        mgr = self._make_state_mgr()
        mgr.set_vp(1, 10)

        cmd = SetVPCommand(mgr, pid=1, old_vp=10, new_vp=None)
        cmd.execute()

        state = mgr.get_state(1)
        assert state is not None
        assert 1 not in state.victory_points
