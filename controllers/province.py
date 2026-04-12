"""ProvinceController — 省份编辑模式控制器。

处理省份合并、扩张、切割操作。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controllers.base import BaseController
from commands.province.merge import MergeProvincesCommand

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class ProvinceController(BaseController):
    """省份编辑模式：合并/扩张/切割。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.merge_mode: bool = False
        self.merge_first_pid: int = 0
        self.expand_mode: bool = False
        self.selected_province_id: int = 0

    def activate(self) -> None:
        """进入省份模式。"""
        self.merge_mode = False
        self.merge_first_pid = 0
        self.expand_mode = False
        self._emit_status("省份编辑模式")

    def deactivate(self) -> None:
        """离开省份模式，清理状态。"""
        self.merge_mode = False
        self.merge_first_pid = 0
        self.expand_mode = False

    def on_province_clicked(self, pid: int) -> None:
        """左键点击省份：选择或合并。"""
        if pid <= 0:
            return

        if self.merge_mode:
            self._handle_merge_click(pid)
            return

        # 普通选择
        self.selected_province_id = pid

    def set_merge_mode(self, on: bool) -> None:
        """开关合并模式。"""
        self.merge_mode = on
        self.merge_first_pid = 0
        if on:
            self.expand_mode = False
            self._emit_status("合并模式：点第一个省份，再点第二个")
        else:
            self._emit_status("回到查看模式")

    def set_expand_mode(self, on: bool) -> None:
        """开关扩张模式。"""
        self.expand_mode = on
        if on:
            self.merge_mode = False
            self.merge_first_pid = 0
            self._emit_status("扩张模式：点击省份后拖动扩张")
        else:
            self._emit_status("回到查看模式")

    def split_selected(self) -> bool:
        """切割当前选中的省份。返回是否成功。"""
        pid = self.selected_province_id
        if pid <= 0:
            self._emit_status("请先点击选中一个省份")
            return False

        # 切割逻辑委托给 map_data（实际切割需要操作 province_map）
        map_data = self.project.map_data
        province_map = map_data.province_map

        import numpy as np
        mask = province_map == pid
        pixels = int(np.sum(mask))
        if pixels < 16:
            self._emit_status("切割失败（省份太小）")
            return False

        # 找省份像素坐标
        ys, xs = np.where(mask)
        mid_y = int(np.median(ys))

        # 分为上下两半
        new_pid = int(province_map.max()) + 1
        upper = ys <= mid_y
        province_map[ys[upper], xs[upper]] = new_pid

        self.project.mark_dirty()
        self._emit_status(f"省份 {pid} 已切割，新省份 ID: {new_pid}")
        self._emit_render(full=True)
        self.event_bus.emit("province_count_changed", count=int(province_map.max()))
        return True

    def _handle_merge_click(self, pid: int) -> None:
        """合并模式下点击省份。"""
        if self.merge_first_pid == 0:
            self.merge_first_pid = pid
            self._emit_status(f"已选中省份 {pid}，点击要合并的目标省份")
        elif self.merge_first_pid == pid:
            self.merge_first_pid = 0
            self._emit_status("取消选择，仍在合并模式")
        else:
            # 执行合并
            cmd = MergeProvincesCommand(
                self.project.map_data,
                pid_keep=self.merge_first_pid,
                pid_remove=pid,
                state_mgr=self.project.state_mgr,
                country_mgr=self.project.country_mgr,
            )
            self.history.execute(cmd)
            self.project.mark_dirty()
            self._emit_status(f"省份 {pid} 已合并到 {self.merge_first_pid}")
            self._emit_render(full=True)

            province_map = self.project.map_data.province_map
            self.event_bus.emit(
                "province_count_changed", count=int(province_map.max())
            )

            self.merge_first_pid = 0
            self.merge_mode = False
