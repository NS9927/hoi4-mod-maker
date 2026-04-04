"""
撤销/重做管理器 — 基于压缩快照的命令历史
支持对 numpy 数组的局部差异存储
"""
import zlib
import numpy as np


class UndoStep:
    """一个撤销步骤，存储操作前的压缩数据"""
    __slots__ = ("description", "snapshots")

    def __init__(self, description: str, snapshots: list[tuple[str, bytes, tuple]]):
        """
        snapshots: [(array_name, compressed_data, shape_and_dtype), ...]
        """
        self.description = description
        self.snapshots = snapshots


class UndoManager:
    """管理撤销/重做栈"""

    def __init__(self, max_steps: int = 30):
        self._max_steps = max_steps
        self._undo_stack: list[UndoStep] = []
        self._redo_stack: list[UndoStep] = []
        # 当前正在记录的操作（mousePress 到 mouseRelease）
        self._pending: dict[str, tuple[bytes, tuple]] | None = None
        self._pending_desc: str = ""

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def begin_stroke(self, description: str, arrays: dict[str, np.ndarray]) -> None:
        """开始一次画笔操作，记录操作前的快照"""
        self._pending_desc = description
        self._pending = {}
        for name, arr in arrays.items():
            compressed = zlib.compress(arr.tobytes(), level=1)
            self._pending[name] = (compressed, (arr.shape, arr.dtype))

    def end_stroke(self, arrays: dict[str, np.ndarray]) -> None:
        """结束画笔操作，比较并保存差异"""
        if self._pending is None:
            return

        # 检查是否有实际变化
        changed = False
        for name, arr in arrays.items():
            if name in self._pending:
                old_data = zlib.decompress(self._pending[name][0])
                shape, dtype = self._pending[name][1]
                old_arr = np.frombuffer(old_data, dtype=dtype).reshape(shape)
                if not np.array_equal(old_arr, arr):
                    changed = True
                    break

        if changed:
            snapshots = [
                (name, data, info)
                for name, (data, info) in self._pending.items()
            ]
            step = UndoStep(self._pending_desc, snapshots)
            self._undo_stack.append(step)
            if len(self._undo_stack) > self._max_steps:
                self._undo_stack.pop(0)
            self._redo_stack.clear()

        self._pending = None

    def push_snapshot(self, description: str, arrays: dict[str, np.ndarray]) -> None:
        """直接压入一个完整快照（用于非画笔操作，如合并/切割/填充）"""
        snapshots = []
        for name, arr in arrays.items():
            compressed = zlib.compress(arr.tobytes(), level=1)
            snapshots.append((name, compressed, (arr.shape, arr.dtype)))

        step = UndoStep(description, snapshots)
        self._undo_stack.append(step)
        if len(self._undo_stack) > self._max_steps:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self, current_arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray] | None:
        """
        撤销一步。
        current_arrays: 当前各数组的引用（用于保存到 redo 栈）
        返回恢复后的数组字典，或 None（无可撤销）
        """
        if not self._undo_stack:
            return None

        step = self._undo_stack.pop()

        # 保存当前状态到 redo 栈
        redo_snapshots = []
        for name, _, _ in step.snapshots:
            if name in current_arrays:
                arr = current_arrays[name]
                compressed = zlib.compress(arr.tobytes(), level=1)
                redo_snapshots.append((name, compressed, (arr.shape, arr.dtype)))
        self._redo_stack.append(UndoStep(step.description, redo_snapshots))

        # 恢复旧数据
        result = {}
        for name, compressed, (shape, dtype) in step.snapshots:
            data = zlib.decompress(compressed)
            result[name] = np.frombuffer(data, dtype=dtype).reshape(shape).copy()
        return result

    def redo(self, current_arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray] | None:
        """
        重做一步。
        返回恢复后的数组字典，或 None（无可重做）
        """
        if not self._redo_stack:
            return None

        step = self._redo_stack.pop()

        # 保存当前状态到 undo 栈
        undo_snapshots = []
        for name, _, _ in step.snapshots:
            if name in current_arrays:
                arr = current_arrays[name]
                compressed = zlib.compress(arr.tobytes(), level=1)
                undo_snapshots.append((name, compressed, (arr.shape, arr.dtype)))
        self._undo_stack.append(UndoStep(step.description, undo_snapshots))

        # 恢复数据
        result = {}
        for name, compressed, (shape, dtype) in step.snapshots:
            data = zlib.decompress(compressed)
            result[name] = np.frombuffer(data, dtype=dtype).reshape(shape).copy()
        return result

    def clear(self) -> None:
        """清空所有历史"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._pending = None
