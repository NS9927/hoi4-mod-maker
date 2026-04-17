"""
SetRailwayLevelCommand — 设置省份铁路等级（支持撤销）。
"""

from __future__ import annotations

from commands.base import Command


class SetRailwayLevelCommand(Command):
    """设置单个省份的铁路等级。"""

    label = "设置铁路等级"

    def __init__(self, railway_mgr, pid: int, old_level: int, new_level: int) -> None:
        self._mgr = railway_mgr
        self._pid = pid
        self._old = old_level
        self._new = new_level

    def execute(self) -> None:
        self._mgr.set_province_level(self._pid, self._new)

    def undo(self) -> None:
        self._mgr.set_province_level(self._pid, self._old)
