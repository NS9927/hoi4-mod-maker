"""CommandHistory — 增量撤销/重做栈。

替代旧的 UndoManager（快照式）和 CommandBus。
每个 Command 只记录改了什么（delta），不存整张地图。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from commands.base import Command

if TYPE_CHECKING:
    from model.events import EventBus


class CommandHistory:
    """命令历史栈，支持撤销/重做。"""

    def __init__(self, event_bus: "EventBus | None" = None, max_size: int = 200) -> None:
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []
        self._max_size = max_size
        self._event_bus = event_bus

    def execute(self, cmd: Command) -> None:
        """执行命令并压入撤销栈。"""
        cmd.execute()

        # Try to merge with last command (for continuous brush strokes)
        if (
            self._undo_stack
            and hasattr(cmd, "can_merge_with")
            and cmd.can_merge_with(self._undo_stack[-1])
        ):
            merged = self._undo_stack[-1]
            merged.merge(cmd)
        else:
            self._undo_stack.append(cmd)

        # Clear redo stack (new action invalidates redo history)
        self._redo_stack.clear()

        # Enforce max size
        while len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)

        self._notify()

    def undo(self) -> bool:
        """撤销最后一个命令。返回是否成功。"""
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        self._notify()
        return True

    def redo(self) -> bool:
        """重做。返回是否成功。"""
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        self._notify()
        return True

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def clear(self) -> None:
        """清空所有历史。"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify()

    def _notify(self) -> None:
        """通知 UI 撤销/重做状态变化。"""
        if self._event_bus:
            self._event_bus.emit(
                "undo_state_changed",
                can_undo=self.can_undo,
                can_redo=self.can_redo,
            )
