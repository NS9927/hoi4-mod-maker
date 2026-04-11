"""
工具框架 — 所有编辑工具按统一模板组织.

每种工具是一个 Tool 子类, 注册到 ToolRegistry.
canvas 在收到鼠标事件时查找对应工具, 调用 on_press / on_drag / on_release.
"""

from domain.tools.base import Tool, ToolContext, CleanupLevel
from domain.tools.registry import ToolRegistry, register_tool, get_tool, list_tools

__all__ = [
    "Tool",
    "ToolContext",
    "CleanupLevel",
    "ToolRegistry",
    "register_tool",
    "get_tool",
    "list_tools",
]
