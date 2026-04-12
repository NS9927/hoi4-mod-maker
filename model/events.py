"""事件总线 — 模块间解耦通信的核心。

所有跨模块通信通过 EventBus 发布/订阅，不直接调用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from collections import defaultdict


class EventBus:
    """简单的发布/订阅事件总线。"""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """订阅事件。callback 接收 event 数据对象。"""
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """取消订阅。"""
        subs = self._subscribers[event_type]
        if callback in subs:
            subs.remove(callback)

    def unsubscribe_all(self, callback: Callable) -> None:
        """取消某个回调的所有订阅（用于清理）。"""
        for subs in self._subscribers.values():
            if callback in subs:
                subs.remove(callback)

    def emit(self, event_type: str, **data: Any) -> None:
        """发布事件，所有订阅者按注册顺序收到。"""
        event = Event(event_type, data)
        for callback in self._subscribers[event_type][:]:  # copy to allow modify during iteration
            callback(event)

    def clear(self) -> None:
        """清除所有订阅。"""
        self._subscribers.clear()


@dataclass
class Event:
    """事件数据载体。"""

    type: str
    data: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        if name in ("type", "data") or name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.data[name]
        except KeyError:
            raise AttributeError(f"Event '{self.type}' has no attribute '{name}'")


# ── 事件类型常量 ──

# 图层变化
LAYER_CHANGED = "layer_changed"  # layer_name, bbox=(x0,y0,x1,y1) or None
PROVINCE_MAP_CHANGED = "province_map_changed"

# 用户交互
PROVINCE_CLICKED = "province_clicked"  # pid, x, y
PROVINCE_RIGHT_CLICKED = "province_right_clicked"  # pid, x, y
PROVINCE_DOUBLE_CLICKED = "province_double_clicked"  # pid

# 模式
MODE_CHANGED = "mode_changed"  # old_mode, new_mode

# 数据变化
STATE_CHANGED = "state_changed"  # state_id, action ("created"/"deleted"/"modified")
COUNTRY_CHANGED = "country_changed"  # tag, action
VP_CHANGED = "vp_changed"  # pid, value

# 撤销/重做
UNDO_STATE_CHANGED = "undo_state_changed"  # can_undo, can_redo

# UI
STATUS_MESSAGE = "status_message"  # text
PROVINCE_COUNT_CHANGED = "province_count_changed"  # count
REQUEST_RENDER = "request_render"  # full=True/False, bbox=(x0,y0,x1,y1)
