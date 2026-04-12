"""
SetVPCommand — 设置/移除胜利点。
"""

from __future__ import annotations

from commands.base import Command


class SetVPCommand(Command):
    """设置或移除省份的胜利点 (Victory Point)。"""

    label = "设置胜利点"

    def __init__(
        self,
        state_mgr,
        pid: int,
        old_vp: int | None,
        new_vp: int | None,
    ) -> None:
        """
        参数:
            state_mgr: StateManager 实例
            pid: 省份 ID
            old_vp: 旧 VP 值（None=没有 VP）
            new_vp: 新 VP 值（None=移除 VP）
        """
        self._state_mgr = state_mgr
        self._pid = pid
        self._old_vp = old_vp
        self._new_vp = new_vp

    def execute(self) -> None:
        """设置或移除 VP。"""
        if self._new_vp is not None:
            self._state_mgr.set_vp(self._pid, self._new_vp)
        else:
            self._state_mgr.remove_vp(self._pid)

    def undo(self) -> None:
        """恢复旧 VP。"""
        if self._old_vp is not None:
            self._state_mgr.set_vp(self._pid, self._old_vp)
        else:
            self._state_mgr.remove_vp(self._pid)
