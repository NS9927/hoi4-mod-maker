"""
CompositeCommand — 把多个子命令打包成一个原子撤销单元。

用法：一次操作影响多个数据源（如局部重生改 province_map + state_mgr + sr_mgr + country_mgr），
将各自的子 Command 装入一个 CompositeCommand。撤销时反序撤销，重做时正序执行。
"""

from __future__ import annotations

from commands.base import Command


class CompositeCommand(Command):
    """复合命令 — 按顺序 execute 子命令，按反序 undo。"""

    def __init__(self, children: list[Command], label: str = "复合操作") -> None:
        if not children:
            raise ValueError("CompositeCommand 至少需要一个子命令")
        self.label = label
        self._children = list(children)

    def execute(self) -> None:
        for cmd in self._children:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self._children):
            cmd.undo()

    @property
    def children(self) -> list[Command]:
        return self._children
