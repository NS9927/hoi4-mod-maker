"""
AssignProvinceToStateCommand — 将省份分配到指定 State。
"""

from __future__ import annotations

from commands.base import Command


class AssignProvinceToStateCommand(Command):
    """将省份从一个 State 移动到另一个 State。"""

    label = "分配省份到State"

    def __init__(
        self,
        state_mgr,
        pid: int,
        old_state_id: int,
        new_state_id: int,
    ) -> None:
        """
        参数:
            state_mgr: StateManager 实例
            pid: 省份 ID
            old_state_id: 原 State ID（0=未分配）
            new_state_id: 新 State ID
        """
        self._state_mgr = state_mgr
        self._pid = pid
        self._old_state_id = old_state_id
        self._new_state_id = new_state_id

    def execute(self) -> None:
        """将省份移动到新 State。"""
        self._state_mgr.assign_province(self._pid, self._new_state_id)

    def undo(self) -> None:
        """将省份移回旧 State。"""
        self._state_mgr.assign_province(self._pid, self._old_state_id)
