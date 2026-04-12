"""LandController — 大陆编辑模式控制器。

处理画笔/橡皮/填充工具绘制 tile_map（陆地/海洋/湖泊）。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controllers.base import BaseController
from commands.map.paint_tile import PaintTileCommand
from commands.map.fill_tile import FillTileCommand

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class LandController(BaseController):
    """大陆编辑模式：画笔/橡皮/填充/变换。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.current_tool: str = "brush"  # brush / eraser / fill / transform
        self.current_tile_type: int = 1  # TILE_LAND=1 default
        self.brush_size: int = 5
        self._stroke_changes: dict[tuple[int, int], int] = {}
        self._is_painting: bool = False

    def activate(self) -> None:
        """进入大陆模式，默认画笔工具。"""
        self.current_tool = "brush"
        self._stroke_changes.clear()
        self._is_painting = False
        self._emit_status("大陆编辑模式")

    def deactivate(self) -> None:
        """离开大陆模式，结束未完成笔触。"""
        if self._is_painting:
            self._commit_stroke()

    def on_press(self, x: int, y: int, pid: int, button: str, modifiers: set) -> bool:
        """鼠标按下开始画笔或填充。"""
        if button != "left":
            return False

        if self.current_tool == "fill":
            self._do_fill(x, y)
            return True

        if self.current_tool in ("brush", "eraser"):
            self._is_painting = True
            self._stroke_changes.clear()
            self._apply_brush(x, y)
            return True

        return False

    def on_drag(self, x: int, y: int) -> bool:
        """鼠标拖拽继续画笔。"""
        if not self._is_painting:
            return False
        self._apply_brush(x, y)
        return True

    def on_release(self, x: int, y: int) -> bool:
        """鼠标释放结束画笔笔触。"""
        if not self._is_painting:
            return False
        self._commit_stroke()
        return True

    def _apply_brush(self, x: int, y: int) -> None:
        """在 (x, y) 处应用画笔/橡皮。"""
        from data.constants import TILE_SEA
        map_data = self.project.map_data
        tile_map = map_data.tile_map
        h, w = tile_map.shape
        r = self.brush_size // 2

        tile_value = self.current_tile_type if self.current_tool == "brush" else TILE_SEA

        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    if int(tile_map[ny, nx]) != tile_value:
                        self._stroke_changes[(ny, nx)] = tile_value

    def _commit_stroke(self) -> None:
        """提交笔触为一个 Command。"""
        self._is_painting = False
        if self._stroke_changes:
            cmd = PaintTileCommand(self.project.map_data, self._stroke_changes)
            self.history.execute(cmd)
            self._stroke_changes = {}
            self.project.mark_dirty()
            self._emit_render(full=True)

    def _do_fill(self, x: int, y: int) -> None:
        """洪水填充。"""
        import numpy as np
        from scipy.ndimage import label

        map_data = self.project.map_data
        tile_map = map_data.tile_map
        h, w = tile_map.shape
        if not (0 <= y < h and 0 <= x < w):
            return

        old_val = int(tile_map[y, x])
        new_val = self.current_tile_type
        if old_val == new_val:
            return

        # 简单洪水填充: 找连通区域
        mask = tile_map == old_val
        labeled, _ = label(mask)
        region_id = labeled[y, x]
        fill_mask = labeled == region_id

        cmd = FillTileCommand(map_data, fill_mask, new_val)
        self.history.execute(cmd)
        self.project.mark_dirty()
        self._emit_render(full=True)
