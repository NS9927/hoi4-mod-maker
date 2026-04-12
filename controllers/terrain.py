"""TerrainController — 地形编辑模式控制器。

处理省份级地形指定和画笔模式地形绘制。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from controllers.base import BaseController
from commands.map.paint_terrain import PaintTerrainCommand

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class TerrainController(BaseController):
    """地形编辑模式：省份指定 / 画笔绘制。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.current_terrain_index: int = 0
        self.brush_mode: bool = False
        self.brush_size: int = 5
        self._stroke_changes: dict[tuple[int, int], int] = {}
        self._is_painting: bool = False

    def activate(self) -> None:
        """进入地形模式。"""
        self._stroke_changes.clear()
        self._is_painting = False
        self._emit_status("地形编辑模式")

    def deactivate(self) -> None:
        """离开地形模式，结束未完成笔触。"""
        if self._is_painting:
            self._commit_stroke()

    def on_province_clicked(self, pid: int) -> None:
        """省份模式下点击省份设置地形。"""
        if self.brush_mode or pid <= 0:
            return

        map_data = self.project.map_data
        province_map = map_data.province_map
        tile_map = map_data.tile_map
        mask = province_map == pid
        ys, xs = np.where(mask)
        if len(ys) == 0:
            return

        # 海洋/湖泊省份不可改地形
        from data.constants import TILE_SEA, TILE_LAKE
        tile_val = int(tile_map[ys[0], xs[0]])
        if tile_val in (TILE_SEA, TILE_LAKE):
            return

        # 收集地形变化
        terrain_map = map_data.terrain_map
        terrain_changes = {}
        for i in range(len(ys)):
            y, x = int(ys[i]), int(xs[i])
            if int(terrain_map[y, x]) != self.current_terrain_index:
                terrain_changes[(y, x)] = self.current_terrain_index

        if not terrain_changes:
            return

        # 查 provincial terrain type
        from data.terrain_types import PALETTE_TO_TYPE, TERRAIN_TYPES
        ptype = PALETTE_TO_TYPE.get(self.current_terrain_index)
        prov_changes = {pid: ptype} if ptype else {}

        # 高度联动
        height_changes = {}
        if ptype and ptype in TERRAIN_TYPES:
            target_h = TERRAIN_TYPES[ptype].height_base
            height_map = map_data.height_map
            for i in range(len(ys)):
                y, x = int(ys[i]), int(xs[i])
                if int(height_map[y, x]) != target_h:
                    height_changes[(y, x)] = target_h

        cmd = PaintTerrainCommand(
            map_data, terrain_changes,
            provincial_terrain_changes=prov_changes,
            height_changes=height_changes,
        )
        self.history.execute(cmd)
        self.project.mark_dirty()
        self._emit_render(full=True)
        self._emit_status(f"省份 {pid} 地形已设为 {ptype or '未知'}")

    def on_press(self, x: int, y: int, pid: int, button: str, modifiers: set) -> bool:
        """画笔模式下鼠标按下。"""
        if not self.brush_mode or button != "left":
            return False
        self._is_painting = True
        self._stroke_changes.clear()
        self._apply_brush(x, y)
        return True

    def on_drag(self, x: int, y: int) -> bool:
        """画笔模式下鼠标拖拽。"""
        if not self._is_painting:
            return False
        self._apply_brush(x, y)
        return True

    def on_release(self, x: int, y: int) -> bool:
        """画笔模式下鼠标释放。"""
        if not self._is_painting:
            return False
        self._commit_stroke()
        return True

    def _apply_brush(self, x: int, y: int) -> None:
        """在 (x, y) 处应用地形画笔。"""
        terrain_map = self.project.map_data.terrain_map
        h, w = terrain_map.shape
        r = self.brush_size // 2

        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    if int(terrain_map[ny, nx]) != self.current_terrain_index:
                        self._stroke_changes[(ny, nx)] = self.current_terrain_index

    def _commit_stroke(self) -> None:
        """提交地形笔触。"""
        self._is_painting = False
        if self._stroke_changes:
            cmd = PaintTerrainCommand(
                self.project.map_data, self._stroke_changes,
            )
            self.history.execute(cmd)
            self._stroke_changes = {}
            self.project.mark_dirty()
            self._emit_render(full=True)
