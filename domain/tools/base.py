"""
Tool 基类 + ToolContext + CleanupLevel 枚举
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.map_data import MapData
    from domain.undo_manager import UndoManager


class CleanupLevel(Enum):
    """工具完成一次操作后要做的清理级别。

    - NONE: 不做任何清理（拖动中实时操作）
    - FAST: 仅在受影响 bbox 内做轻量修复（X-crossing 局部修）
    - FULL: 全图清理（X-crossing 修复 + 不连通修复 + ID 压实）

    一般规则：
    - 拖动中（drag）→ NONE
    - 单步操作末尾（release）→ FAST
    - 导出前 / 手动触发 → FULL
    """
    NONE = "none"
    FAST = "fast"
    FULL = "full"


@dataclass
class ToolContext:
    """工具操作时的共享上下文。

    工具不直接访问 canvas / main_window，所有需要的对象通过 ctx 拿。
    canvas 在调用工具时构造 ctx 并传入。
    """
    map_data: "MapData"
    undo_mgr: "UndoManager"

    # 引用更新需要的管理器（压实 ID 时同步 state/country 的省份引用）
    state_mgr: object = None
    country_mgr: object = None

    # 当前选中状态（被多个工具共享）
    selected_province_id: int = 0
    selected_state_id: int = 0
    selected_country_tag: str = ""

    # 当前操作的元数据
    brush_size: int = 10
    display_mode: str = "land"

    # 工具状态机用的临时数据（每个工具自己 push/pop）
    state: dict[str, Any] = field(default_factory=dict)

    # 标记本次操作影响的 bbox（用于 FAST 清理）
    dirty_bbox: tuple[int, int, int, int] | None = None  # (x0, y0, x1, y1)

    def expand_dirty(self, x: int, y: int) -> None:
        """把 (x, y) 加入受影响范围。"""
        if self.dirty_bbox is None:
            self.dirty_bbox = (x, y, x + 1, y + 1)
        else:
            x0, y0, x1, y1 = self.dirty_bbox
            self.dirty_bbox = (
                min(x0, x), min(y0, y),
                max(x1, x + 1), max(y1, y + 1),
            )


class Tool:
    """所有编辑工具的基类。

    子类必须设置类属性：
        name: 唯一标识符（"lasso_province", "land_brush"...）
        display_modes: 在哪些 display_mode 下激活（["province"]）
        cleanup_level: 操作完成后清理级别

    可选实现：
        on_press / on_drag / on_release
        get_undo_array_names: 这个工具影响哪些 numpy 数组
    """

    name: str = ""
    display_modes: tuple[str, ...] = ()
    cleanup_level: CleanupLevel = CleanupLevel.NONE
    cursor: str = "cross"
    label: str = ""  # 按钮显示文字
    description: str = ""  # 状态栏提示

    def get_undo_array_names(self, ctx: ToolContext) -> list[str]:
        """这个工具影响哪些数组。默认空——必须由子类指定。"""
        return []

    def on_press(self, ctx: ToolContext, x: int, y: int) -> None:
        """鼠标按下。"""
        pass

    def on_drag(self, ctx: ToolContext, x: int, y: int) -> None:
        """鼠标拖动（按下后移动）。"""
        pass

    def on_release(self, ctx: ToolContext, x: int, y: int) -> None:
        """鼠标松开。子类不需要调清理函数——框架会根据 cleanup_level 自动调。"""
        pass

    def on_cancel(self, ctx: ToolContext) -> None:
        """操作被取消（ESC 或切换工具）。"""
        ctx.state.clear()
        ctx.dirty_bbox = None

    # ───── 框架辅助方法 ─────

    def begin_undo(self, ctx: ToolContext) -> None:
        """开始记录撤销快照。框架会在 on_press 前调用。"""
        names = self.get_undo_array_names(ctx)
        if not names:
            return
        arrays = {n: getattr(ctx.map_data, n) for n in names}
        ctx.undo_mgr.begin_stroke(self.name, arrays)

    def end_undo(self, ctx: ToolContext) -> None:
        """结束撤销快照并入栈。框架会在清理后调用。"""
        names = self.get_undo_array_names(ctx)
        if not names:
            return
        arrays = {n: getattr(ctx.map_data, n) for n in names}
        ctx.undo_mgr.end_stroke(arrays)

    def run_cleanup(self, ctx: ToolContext) -> None:
        """根据 cleanup_level 执行清理。框架在 on_release 后自动调。"""
        if self.cleanup_level == CleanupLevel.NONE:
            return
        if self.cleanup_level == CleanupLevel.FULL:
            from domain.generators.province import (
                _fix_non_contiguous_fast, compact_province_ids,
            )
            from domain.validators.province import fix_x_crossings
            for _ in range(5):
                if fix_x_crossings(ctx.map_data.province_map) == 0:
                    break
            _fix_non_contiguous_fast(ctx.map_data.province_map)
            compact_province_ids(ctx.map_data.province_map)
        elif self.cleanup_level == CleanupLevel.FAST:
            # 仅在 dirty_bbox 内修 X-crossing
            from domain.validators.province import fix_x_crossings
            if ctx.dirty_bbox is None:
                return
            x0, y0, x1, y1 = ctx.dirty_bbox
            # 留 2 像素 margin 防止边缘漏检
            from data.constants import MAP_WIDTH, MAP_HEIGHT
            x0 = max(0, x0 - 2); y0 = max(0, y0 - 2)
            x1 = min(MAP_WIDTH, x1 + 2); y1 = min(MAP_HEIGHT, y1 + 2)
            sub = ctx.map_data.province_map[y0:y1, x0:x1]
            for _ in range(3):
                if fix_x_crossings(sub) == 0:
                    break
