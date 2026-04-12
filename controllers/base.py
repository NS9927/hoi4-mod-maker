"""Controller 基类 — 每个编辑模式一个 Controller。"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.project import Project
    from model.events import EventBus
    from commands.history import CommandHistory


class BaseController:
    """编辑模式控制器基类。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        self.project = project
        self.history = command_history
        self.event_bus = project.event_bus

    def activate(self) -> None:
        """进入此模式时调用。重置按钮状态等。"""
        pass

    def deactivate(self) -> None:
        """离开此模式时调用。清理临时状态。"""
        pass

    def on_press(self, x: int, y: int, pid: int, button: str, modifiers: set) -> bool:
        """鼠标按下。pid=点击的省份ID(0=无)。button='left'/'right'/'middle'。返回是否处理了。"""
        return False

    def on_drag(self, x: int, y: int) -> bool:
        """鼠标拖拽。返回是否处理了。"""
        return False

    def on_release(self, x: int, y: int) -> bool:
        """鼠标释放。返回是否处理了。"""
        return False

    def on_province_clicked(self, pid: int) -> None:
        """左键点击省份。"""
        pass

    def on_province_double_clicked(self, pid: int) -> None:
        """双击省份。"""
        pass

    def on_province_right_clicked(self, pid: int, x: int, y: int) -> None:
        """右键点击省份。"""
        pass

    def _emit_status(self, text: str) -> None:
        """发送状态栏消息。"""
        self.event_bus.emit("status_message", text=text)

    def _emit_render(self, full: bool = False, bbox: tuple | None = None) -> None:
        """请求画布刷新。"""
        self.event_bus.emit("request_render", full=full, bbox=bbox)
