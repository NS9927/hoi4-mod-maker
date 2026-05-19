"""
QuickInitCommand — 一键初始化（自动生成 state/strategic_region/country）的 undo/redo。

用 deepcopy 快照三个 manager 的关键内部状态，撤销时整体还原。
"""

from __future__ import annotations

import copy
from typing import Any

from commands.base import Command


class QuickInitCommand(Command):
    """一键初始化命令 — 整体快照三个 manager。

    流程：
    1. 构造时拍 before 快照
    2. 在 handler 中执行实际 auto_complete_project
    3. 调 capture_after() 拍 after 快照
    4. 将命令推入 CommandHistory（不再调 execute()）
    5. undo() 还原到 before；redo (execute) 还原到 after
    """

    label = "一键初始化"

    def __init__(self, state_mgr: Any, country_mgr: Any, sr_mgr: Any) -> None:
        self._state_mgr = state_mgr
        self._country_mgr = country_mgr
        self._sr_mgr = sr_mgr
        # before snapshot — 三个 manager 的关键内部状态
        self._before = self._snapshot()
        self._after: dict[str, Any] | None = None

    def _snapshot(self) -> dict[str, Any]:
        snap = {
            "states": copy.deepcopy(getattr(self._state_mgr, "_states", {})),
            "countries": copy.deepcopy(getattr(self._country_mgr, "_countries", {})),
            "state_owner": copy.deepcopy(getattr(self._country_mgr, "_state_owner", {})),
            "regions": copy.deepcopy(getattr(self._sr_mgr, "_regions", {})),
            "sr_next_id": getattr(self._sr_mgr, "_next_id", 1),
        }
        # state_mgr 可能也有 _next_id（看实现）
        if hasattr(self._state_mgr, "_next_id"):
            snap["state_next_id"] = self._state_mgr._next_id
        return snap

    def capture_after(self) -> None:
        """handler 执行完 auto_complete_project 后调用此方法。"""
        self._after = self._snapshot()

    def _restore(self, snap: dict[str, Any]) -> None:
        if hasattr(self._state_mgr, "_states"):
            self._state_mgr._states = copy.deepcopy(snap["states"])
        if hasattr(self._state_mgr, "_next_id") and "state_next_id" in snap:
            self._state_mgr._next_id = snap["state_next_id"]
        if hasattr(self._country_mgr, "_countries"):
            self._country_mgr._countries = copy.deepcopy(snap["countries"])
        if hasattr(self._country_mgr, "_state_owner"):
            self._country_mgr._state_owner = copy.deepcopy(snap["state_owner"])
        if hasattr(self._sr_mgr, "_regions"):
            self._sr_mgr._regions = copy.deepcopy(snap["regions"])
        if hasattr(self._sr_mgr, "_next_id"):
            self._sr_mgr._next_id = snap["sr_next_id"]

    def execute(self) -> None:
        """重做时还原到 after。首次执行由 handler 完成，此处只处理 redo。"""
        if self._after is None:
            return  # capture_after 还没调，首次执行路径
        self._restore(self._after)

    def undo(self) -> None:
        self._restore(self._before)
