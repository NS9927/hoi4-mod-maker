"""
工具框架 — 所有编辑工具按统一模板组织。

每种工具是一个 Tool 子类，注册到 ToolRegistry。
canvas 在收到鼠标事件时查找对应工具，调用 on_press / on_drag / on_release。

设计目标：
- 加新工具 = 新建一个文件 + 注册一行
- 撤销/清理/键位/UI 都自动接入
- 工具不直接访问 canvas 内部，全部通过 ToolContext

迁移策略：
- 新工具（套索、未来的工具）按这套框架写
- 现有工具暂时保持原状，不强制迁移
- 现有工具有空闲时再迁，逐个验证
"""

from core.tools.base import Tool, ToolContext, CleanupLevel
from core.tools.registry import ToolRegistry, register_tool, get_tool, list_tools

__all__ = [
    "Tool",
    "ToolContext",
    "CleanupLevel",
    "ToolRegistry",
    "register_tool",
    "get_tool",
    "list_tools",
]
