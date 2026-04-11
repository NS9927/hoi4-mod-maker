"""
Command 模式基类 — 封装一次"可撤销编辑动作".

每个 Command 实现 execute() 和 undo(). CommandBus 负责执行、推入 undo 栈、广播信号.
Phase 5 会把旧 undo_manager 的快照式 undo 切换到命令式 undo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Command(ABC):
    """命令基类. 子类必须实现 execute() 和 undo()."""

    #: 命令的人类可读描述, 用于 UI 显示 "撤销: 画陆地"
    label: str = ""

    @abstractmethod
    def execute(self) -> None:
        """执行命令. 必须可重入 (redo 会再调一次)."""
        ...

    @abstractmethod
    def undo(self) -> None:
        """撤销命令. 必须把状态恢复到 execute 前."""
        ...

    def can_merge_with(self, other: "Command") -> bool:
        """是否可以合并相邻同类命令 (例如连续画笔笔触)."""
        return False

    def merge(self, other: "Command") -> None:
        """将 other 合并到 self, 只在 can_merge_with 返回 True 时被调用."""
        raise NotImplementedError
