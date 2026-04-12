"""CommandHistory 单元测试。"""
from commands.base import Command
from commands.history import CommandHistory
from model.events import EventBus


class FakeCommand(Command):
    """测试用的假命令。"""

    label = "fake"

    def __init__(self) -> None:
        self.executed = 0
        self.undone = 0

    def execute(self) -> None:
        self.executed += 1

    def undo(self) -> None:
        self.undone += 1


class MergeableCommand(Command):
    """可合并的假命令。"""

    label = "mergeable"

    def __init__(self, value: int = 0) -> None:
        self.value = value
        self.merged_values: list[int] = [value]

    def execute(self) -> None:
        pass

    def undo(self) -> None:
        pass

    def can_merge_with(self, other: Command) -> bool:
        return isinstance(other, MergeableCommand)

    def merge(self, other: Command) -> None:
        if isinstance(other, MergeableCommand):
            self.merged_values.extend(other.merged_values)


class TestCommandHistory:
    """CommandHistory 基本功能。"""

    def test_execute_pushes_to_undo_stack(self) -> None:
        """execute 后命令进入 undo 栈。"""
        history = CommandHistory()
        cmd = FakeCommand()
        history.execute(cmd)
        assert cmd.executed == 1
        assert history.can_undo
        assert not history.can_redo

    def test_undo_pops_and_calls_undo(self) -> None:
        """undo 弹出命令并调用 cmd.undo()。"""
        history = CommandHistory()
        cmd = FakeCommand()
        history.execute(cmd)
        result = history.undo()
        assert result is True
        assert cmd.undone == 1
        assert not history.can_undo
        assert history.can_redo

    def test_redo_pops_and_calls_execute(self) -> None:
        """redo 弹出命令并调用 cmd.execute()。"""
        history = CommandHistory()
        cmd = FakeCommand()
        history.execute(cmd)
        history.undo()
        result = history.redo()
        assert result is True
        assert cmd.executed == 2  # execute called twice (initial + redo)
        assert history.can_undo
        assert not history.can_redo

    def test_undo_on_empty_returns_false(self) -> None:
        """空栈 undo 返回 False。"""
        history = CommandHistory()
        assert history.undo() is False

    def test_redo_on_empty_returns_false(self) -> None:
        """空栈 redo 返回 False。"""
        history = CommandHistory()
        assert history.redo() is False

    def test_new_execute_clears_redo_stack(self) -> None:
        """新命令执行后 redo 栈被清空。"""
        history = CommandHistory()
        history.execute(FakeCommand())
        history.undo()
        assert history.can_redo
        history.execute(FakeCommand())
        assert not history.can_redo

    def test_max_size_enforced(self) -> None:
        """超过 max_size 时最早的命令被丢弃。"""
        history = CommandHistory(max_size=3)
        for _ in range(5):
            history.execute(FakeCommand())
        # 只保留最近 3 个
        count = 0
        while history.undo():
            count += 1
        assert count == 3

    def test_event_bus_notified(self) -> None:
        """每次操作后 event_bus 收到 undo_state_changed。"""
        bus = EventBus()
        notifications: list[dict] = []

        def on_state_changed(event) -> None:
            notifications.append({"can_undo": event.can_undo, "can_redo": event.can_redo})

        bus.subscribe("undo_state_changed", on_state_changed)
        history = CommandHistory(event_bus=bus)

        history.execute(FakeCommand())
        assert notifications[-1] == {"can_undo": True, "can_redo": False}

        history.undo()
        assert notifications[-1] == {"can_undo": False, "can_redo": True}

        history.redo()
        assert notifications[-1] == {"can_undo": True, "can_redo": False}

    def test_clear_empties_both_stacks(self) -> None:
        """clear 清空 undo 和 redo 栈。"""
        history = CommandHistory()
        history.execute(FakeCommand())
        history.execute(FakeCommand())
        history.undo()
        assert history.can_undo
        assert history.can_redo
        history.clear()
        assert not history.can_undo
        assert not history.can_redo

    def test_merge_commands(self) -> None:
        """可合并的命令不会增加栈深度。"""
        history = CommandHistory()
        history.execute(MergeableCommand(1))
        history.execute(MergeableCommand(2))
        history.execute(MergeableCommand(3))
        # 全部合并到第一个命令
        count = 0
        while history.undo():
            count += 1
        assert count == 1  # 只有一个命令在栈里
