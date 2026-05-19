"""
ManagerSnapshotCommand — 通用 manager 字段快照 undo/redo。

用于自动分组州、自动战略区、其他批量改 manager 内部字段的命令。
保留 dict 对象身份（clear + update），不替换引用，避免外部持有旧引用失效。
"""

from __future__ import annotations

import copy
from typing import Any

from commands.base import Command


class ManagerSnapshotCommand(Command):
    """通用 manager 状态快照命令。

    用法：
    1. cmd = ManagerSnapshotCommand("自动分组州", mgr, ["_states", "_next_id"])
    2. handler 执行实际操作（修改 mgr）
    3. cmd.capture_after()
    4. history._undo_stack.append(cmd)
    """

    def __init__(self, label: str, manager: Any, field_names: list[str]) -> None:
        self.label = label
        self._manager = manager
        self._fields = field_names
        self._before = self._snapshot()
        self._after: dict[str, Any] | None = None

    def _snapshot(self) -> dict[str, Any]:
        return {f: copy.deepcopy(getattr(self._manager, f)) for f in self._fields}

    def capture_after(self) -> None:
        self._after = self._snapshot()

    def _restore(self, snap: dict[str, Any]) -> None:
        for field, val in snap.items():
            current = getattr(self._manager, field, None)
            new_val = copy.deepcopy(val)
            # dict 保持对象身份（clear + update），其他直接 setattr
            if isinstance(current, dict) and isinstance(new_val, dict):
                current.clear()
                current.update(new_val)
            elif isinstance(current, set) and isinstance(new_val, set):
                current.clear()
                current.update(new_val)
            elif isinstance(current, list) and isinstance(new_val, list):
                current.clear()
                current.extend(new_val)
            else:
                setattr(self._manager, field, new_val)

    def execute(self) -> None:
        """redo — 还原到 after。首次执行由 handler 完成。"""
        if self._after is None:
            return
        self._restore(self._after)

    def undo(self) -> None:
        self._restore(self._before)
