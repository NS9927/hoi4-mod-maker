"""ContinentController — 大陆分区编辑控制器。

处理大陆的添加/重命名/删除/省份指派。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controllers.base import BaseController

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class ContinentController(BaseController):
    """大陆分区编辑。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.pick_on: bool = False
        self.pick_index: int = -1

    def activate(self) -> None:
        """进入大陆模式。"""
        self.pick_on = False
        self.pick_index = -1
        self._emit_status("大陆分区编辑模式")

    def deactivate(self) -> None:
        """离开大陆模式。"""
        self.pick_on = False
        self.pick_index = -1

    def toggle_pick(self, on: bool, index: int = -1) -> None:
        """开关大陆指派拾取模式。"""
        self.pick_on = on
        self.pick_index = index if on else -1
        if on and index >= 0:
            self._emit_status(f"大洲指派: 点击陆地省份")
        else:
            self._emit_status("大洲指派关闭")

    def on_province_clicked(self, pid: int) -> None:
        """拾取模式下点击省份指派大陆。"""
        if not self.pick_on or self.pick_index < 0 or pid <= 0:
            return

        import numpy as np
        from data.constants import TILE_LAND

        map_data = self.project.map_data
        province_map = map_data.province_map
        tile_map = map_data.tile_map

        ys, xs = np.where(province_map == pid)
        if len(ys) == 0:
            return

        # 只允许陆地省份
        if int(tile_map[ys[0], xs[0]]) != TILE_LAND:
            self._emit_status(f"省份 {pid} 不是陆地，跳过")
            return

        continent_mgr = self.project.continent_mgr
        continent_mgr.assign_province(pid, self.pick_index)
        self.project.mark_dirty()
        self._emit_status(f"省份 {pid} 已指派到大陆 #{self.pick_index + 1}")

    def add_continent(self, name: str) -> bool:
        """添加大陆。返回是否成功。"""
        try:
            self.project.continent_mgr.add_continent(name)
            self.project.mark_dirty()
            return True
        except ValueError as e:
            self._emit_status(f"添加大陆失败: {e}")
            return False

    def rename_continent(self, index: int, name: str) -> bool:
        """重命名大陆。"""
        try:
            self.project.continent_mgr.rename_continent(index, name)
            self.project.mark_dirty()
            return True
        except (ValueError, IndexError) as e:
            self._emit_status(f"重命名失败: {e}")
            return False

    def remove_continent(self, index: int) -> bool:
        """删除大陆。"""
        try:
            self.project.continent_mgr.remove_continent(index)
            self.project.mark_dirty()
            return True
        except (ValueError, IndexError) as e:
            self._emit_status(f"删除失败: {e}")
            return False
