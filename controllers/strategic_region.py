"""StrategicRegionController — 战略区域编辑控制器。

处理战略区域的自动生成、创建/删除、省份拾取。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controllers.base import BaseController

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class StrategicRegionController(BaseController):
    """战略区域编辑。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.pick_on: bool = False
        self.pick_rid: int = 0
        # 始终监听省份重新生成
        self.event_bus.subscribe("province_map_regenerated", self._on_province_regen)

    def _on_province_regen(self, event) -> None:
        """省份全量重新生成 → 清除战略区域。"""
        if not event.data.get("incremental"):
            self.project.strategic_region_mgr.clear()

    def activate(self) -> None:
        """进入战略区域模式。"""
        self.pick_on = False
        self.pick_rid = 0
        self._emit_status("战略区域编辑模式")

    def deactivate(self) -> None:
        """离开战略区域模式。"""
        self.pick_on = False
        self.pick_rid = 0

    def on_province_clicked(self, pid: int) -> None:
        """拾取模式下点击省份分配到战略区域。"""
        if not self.pick_on or self.pick_rid <= 0 or pid <= 0:
            return

        sr_mgr = self.project.strategic_region_mgr
        sr_mgr.assign_province(pid, self.pick_rid)
        self.project.mark_dirty()
        self._emit_status(f"省份 {pid} 已加入战略区域 #{self.pick_rid}")

    def toggle_pick(self, on: bool, rid: int = 0) -> None:
        """开关拾取模式。"""
        self.pick_on = on
        self.pick_rid = rid if on else 0
        if on:
            self._emit_status(f"战略区拾取: 点击省份 → 加入 Region #{rid}")
        else:
            self._emit_status("战略区拾取关闭")

    def auto_generate(self) -> None:
        """自动生成战略区域。"""
        map_data = self.project.map_data
        province_map = map_data.province_map

        if int(province_map.max()) == 0:
            self._emit_status("请先生成省份")
            return

        sr_mgr = self.project.strategic_region_mgr
        sr_mgr.auto_generate(
            province_map,
            map_data.tile_map,
            state_mgr=self.project.state_mgr,
        )
        self.project.mark_dirty()
        self._emit_status(f"已生成 {sr_mgr.count()} 个战略区域")

    def auto_assign_weather(self) -> None:
        """按纬度自动分配所有战略区域的天气预设."""
        sr_mgr = self.project.strategic_region_mgr
        if sr_mgr.count() == 0:
            self._emit_status("没有战略区域，请先生成")
            return

        province_map = self.project.map_data.province_map
        changed = sr_mgr.auto_assign_weather_by_latitude(province_map)
        self.project.mark_dirty()
        self._emit_status(f"已按纬度分配 {changed} 个战略区域的天气预设")

    def select_region(self, rid: int) -> None:
        """选中战略区域（UI 刷新由事件驱动）。"""
        self.pick_rid = rid

    def create_region(self) -> None:
        """创建新战略区域。"""
        self.project.strategic_region_mgr.create_region()
        self.project.mark_dirty()

    def delete_region(self, rid: int) -> None:
        """删除战略区域。"""
        if rid > 0:
            self.project.strategic_region_mgr.remove_region(rid)
            self.project.mark_dirty()

    def set_name(self, rid: int, name: str) -> None:
        """设置战略区域名称。"""
        r = self.project.strategic_region_mgr.get(rid)
        if r:
            r.name = name.strip() or f"STRATEGICREGION_{rid}"
            self.project.mark_dirty()

    def set_weather(self, rid: int, preset: str) -> None:
        """设置战略区域天气预设。"""
        r = self.project.strategic_region_mgr.get(rid)
        if r:
            r.weather_preset = preset
            self.project.mark_dirty()

    def set_naval(self, rid: int, naval: str) -> None:
        """设置战略区域海军地形。"""
        r = self.project.strategic_region_mgr.get(rid)
        if r:
            r.naval_terrain = naval
            self.project.mark_dirty()

    def create_from_states(self, state_ids: list[int]) -> int:
        """把选中的州合并成一个战略区域。返回新 region ID。"""
        if not state_ids:
            return 0

        sr_mgr = self.project.strategic_region_mgr
        state_mgr = self.project.state_mgr

        # 收集选中州的所有省份
        province_ids: list[int] = []
        for sid in state_ids:
            state = state_mgr.get_state(sid)
            if state:
                province_ids.extend(state.provinces)

        if not province_ids:
            self._emit_status("选中的州没有省份")
            return 0

        # 从旧战略区域移除这些省份
        for pid in province_ids:
            old_rid = sr_mgr.get_region_of_province(pid)
            if old_rid > 0:
                old_r = sr_mgr.get(old_rid)
                if old_r and pid in old_r.province_ids:
                    old_r.province_ids.remove(pid)

        # 创建新战略区域
        r = sr_mgr.create_region()
        r.province_ids = province_ids
        self.project.mark_dirty()

        state_names = ", ".join(str(s) for s in state_ids[:5])
        if len(state_ids) > 5:
            state_names += f"... (+{len(state_ids)-5})"
        self._emit_status(f"创建战略区域 #{r.id}（包含州 {state_names}，{len(province_ids)} 个省份）")
        return r.id
