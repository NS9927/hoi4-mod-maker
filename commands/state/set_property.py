"""
SetStatePropertyCommand — 修改 State 的任意属性。
"""

from __future__ import annotations

from typing import Any

from commands.base import Command


class SetStatePropertyCommand(Command):
    """修改 State 的某个属性值。"""

    label = "修改State属性"

    def __init__(
        self,
        state_mgr,
        state_id: int,
        prop_name: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """
        参数:
            state_mgr: StateManager 实例
            state_id: State ID
            prop_name: 属性名（如 'name', 'manpower', 'category'）
            old_value: 旧值
            new_value: 新值
        """
        self._state_mgr = state_mgr
        self._state_id = state_id
        self._prop_name = prop_name
        self._old_value = old_value
        self._new_value = new_value

    def _set_value(self, value: Any) -> None:
        """设置 State 属性值。"""
        state = self._state_mgr.get_state(self._state_id)
        if state is not None:
            setattr(state, self._prop_name, value)

    def execute(self) -> None:
        """设置新值。"""
        self._set_value(self._new_value)

    def undo(self) -> None:
        """恢复旧值。"""
        self._set_value(self._old_value)
