"""
AssignStateToCountryCommand — 将 State 分配给国家。
"""

from __future__ import annotations

from commands.base import Command


class AssignStateToCountryCommand(Command):
    """将 State 的所有权从一个国家转移到另一个。"""

    label = "分配State到国家"

    def __init__(
        self,
        country_mgr,
        state_id: int,
        old_tag: str,
        new_tag: str,
    ) -> None:
        """
        参数:
            country_mgr: CountryManager 实例
            state_id: State ID
            old_tag: 原国家 TAG（空字符串=未分配）
            new_tag: 新国家 TAG（空字符串=取消分配）
        """
        self._country_mgr = country_mgr
        self._state_id = state_id
        self._old_tag = old_tag
        self._new_tag = new_tag

    def execute(self) -> None:
        """分配 State 给新国家。"""
        self._country_mgr.assign_state(self._state_id, self._new_tag)

    def undo(self) -> None:
        """恢复 State 到旧国家。"""
        self._country_mgr.assign_state(self._state_id, self._old_tag)
