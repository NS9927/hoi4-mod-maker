"""EventBus 单元测试。"""
import pytest

from model.events import EventBus, Event


class TestEventBus:
    """EventBus 基本功能。"""

    def test_subscribe_and_emit(self) -> None:
        """订阅后 emit 能收到事件。"""
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe("test", received.append)
        bus.emit("test", value=42)
        assert len(received) == 1
        assert received[0].type == "test"
        assert received[0].value == 42

    def test_multiple_subscribers(self) -> None:
        """同一事件多个订阅者都能收到。"""
        bus = EventBus()
        results_a: list[Event] = []
        results_b: list[Event] = []
        bus.subscribe("ping", results_a.append)
        bus.subscribe("ping", results_b.append)
        bus.emit("ping", msg="hello")
        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_unsubscribe(self) -> None:
        """取消订阅后不再收到事件。"""
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe("test", received.append)
        bus.unsubscribe("test", received.append)
        bus.emit("test", value=1)
        assert len(received) == 0

    def test_unsubscribe_all(self) -> None:
        """unsubscribe_all 清除所有事件类型的订阅。"""
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe("a", received.append)
        bus.subscribe("b", received.append)
        bus.unsubscribe_all(received.append)
        bus.emit("a")
        bus.emit("b")
        assert len(received) == 0

    def test_emit_no_subscribers(self) -> None:
        """没有订阅者时 emit 不崩溃。"""
        bus = EventBus()
        bus.emit("nonexistent", x=1)  # 不应抛异常

    def test_duplicate_subscribe_ignored(self) -> None:
        """同一个 callback 重复订阅只注册一次。"""
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe("test", received.append)
        bus.subscribe("test", received.append)
        bus.emit("test")
        assert len(received) == 1

    def test_clear(self) -> None:
        """clear 清除所有订阅。"""
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe("test", received.append)
        bus.clear()
        bus.emit("test")
        assert len(received) == 0


class TestEvent:
    """Event 数据访问。"""

    def test_attribute_access(self) -> None:
        """通过属性访问 data 字典的值。"""
        event = Event("test", {"name": "hello", "count": 3})
        assert event.name == "hello"
        assert event.count == 3

    def test_missing_attribute_raises(self) -> None:
        """访问不存在的属性抛 AttributeError。"""
        event = Event("test", {})
        with pytest.raises(AttributeError, match="has no attribute 'missing'"):
            _ = event.missing

    def test_type_field(self) -> None:
        """type 字段正常访问。"""
        event = Event("my_event", {})
        assert event.type == "my_event"
