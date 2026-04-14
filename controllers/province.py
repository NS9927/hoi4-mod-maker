"""ProvinceController — 省份编辑模式控制器。

处理省份合并、扩张、切割、增量生成操作。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from controllers.base import BaseController
from commands.province.merge import MergeProvincesCommand
from commands.province.split import SplitProvinceCommand

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class ProvinceController(BaseController):
    """省份编辑模式：合并/扩张/切割/增量生成。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.merge_mode: bool = False
        self.merge_first_pid: int = 0
        self.expand_mode: bool = False
        self.selected_province_id: int = 0
        # 增量生成：选中的省份集合
        self.regen_selected_pids: set[int] = set()
        self.regen_mode: bool = False

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
        import numpy as np

        pid = self.selected_province_id
        if pid <= 0:
            self._emit_status("请先点击选中一个省份")
            return False

        map_data = self.project.map_data
        province_map = map_data.province_map

        mask = province_map == pid
        pixels = int(np.sum(mask))
        if pixels < 16:
            self._emit_status("切割失败（省份太小）")
            return False

        # 找省份像素坐标，按中位数分为上下两半
        ys, xs = np.where(mask)
        mid_y = int(np.median(ys))
        new_pid = int(province_map.max()) + 1

        # 构建要分给新省份的像素 mask
        split_mask = np.zeros_like(province_map, dtype=bool)
        upper = ys <= mid_y
        split_mask[ys[upper], xs[upper]] = True

        # 通过 Command 执行（支持撤销）
        cmd = SplitProvinceCommand(map_data, pid, new_pid, split_mask)
        self.history.execute(cmd)

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

    # ── 增量生成 ──

    def set_regen_mode(self, on: bool) -> None:
        """开关增量生成选区模式。"""
        self.regen_mode = on
        if on:
            self.merge_mode = False
            self.expand_mode = False
            self.regen_selected_pids.clear()
            self._emit_status('增量生成：点击省份选择区域（Ctrl+点击多选），选好后点「生成」')
        else:
            self.regen_selected_pids.clear()
            self._emit_status("回到查看模式")

    def toggle_regen_province(self, pid: int) -> None:
        """增量生成模式下切换省份选中状态。"""
        if pid <= 0:
            return
        if pid in self.regen_selected_pids:
            self.regen_selected_pids.discard(pid)
        else:
            self.regen_selected_pids.add(pid)
        n = len(self.regen_selected_pids)
        self._emit_status(f'已选中 {n} 个省份，点「生成」重新生成这些区域的省份')
        self._emit_render(full=True)

    def execute_regen(
        self, density: float | None = None, lloyd_iterations: int = 2
    ) -> tuple[int, int]:
        """执行增量生成。返回 (删除的省份数, 新建的省份数)。"""
        if not self.regen_selected_pids:
            self._emit_status("请先选择要重新生成的省份")
            return 0, 0

        map_data = self.project.map_data
        province_map = map_data.province_map
        tile_map = map_data.tile_map

        # 构建选区 mask：选中省份覆盖的所有像素
        region_mask = np.zeros_like(province_map, dtype=bool)
        for pid in self.regen_selected_pids:
            region_mask |= (province_map == pid)

        from domain.generators.province import generate_provinces_in_region
        removed, new_ids = generate_provinces_in_region(
            province_map, tile_map, region_mask,
            target_density=density,
            lloyd_iterations=lloyd_iterations,
            state_mgr=self.project.state_mgr,
            strategic_region_mgr=self.project.strategic_region_mgr,
            country_mgr=self.project.country_mgr,
        )

        self.project.mark_dirty()
        self.regen_selected_pids.clear()
        self.regen_mode = False
        self._emit_status(f"增量生成完成：删除 {len(removed)} 个旧省份，新建 {len(new_ids)} 个省份")
        self._emit_render(full=True)
        self.event_bus.emit("province_count_changed", count=int(province_map.max()))
        return len(removed), len(new_ids)

    def regen_in_rect(
        self, y1: int, x1: int, y2: int, x2: int,
        density: float | None = None, lloyd_iterations: int = 2
    ) -> tuple[int, int]:
        """在矩形区域内重新生成省份。"""
        map_data = self.project.map_data
        province_map = map_data.province_map
        tile_map = map_data.tile_map
        H, W = province_map.shape

        # 裁剪到地图范围
        y1, y2 = max(0, min(y1, y2)), min(H, max(y1, y2))
        x1, x2 = max(0, min(x1, x2)), min(W, max(x1, x2))

        region_mask = np.zeros((H, W), dtype=bool)
        region_mask[y1:y2, x1:x2] = True

        from domain.generators.province import generate_provinces_in_region
        removed, new_ids = generate_provinces_in_region(
            province_map, tile_map, region_mask,
            target_density=density,
            lloyd_iterations=lloyd_iterations,
            state_mgr=self.project.state_mgr,
            strategic_region_mgr=self.project.strategic_region_mgr,
            country_mgr=self.project.country_mgr,
        )

        self.project.mark_dirty()
        self._emit_status(f"矩形区域增量生成：删除 {len(removed)} 个，新建 {len(new_ids)} 个")
        self._emit_render(full=True)
        self.event_bus.emit("province_count_changed", count=int(province_map.max()))
        return len(removed), len(new_ids)
