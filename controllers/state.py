"""StateController — State 编辑模式控制器。

处理省份分配到 State、State 属性编辑、VP 设置、自动分组。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from controllers.base import BaseController
from commands.state.assign import AssignProvinceToStateCommand
from commands.state.set_property import SetStatePropertyCommand
from commands.state.set_vp import SetVPCommand

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class StateController(BaseController):
    """State 编辑模式。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.selected_state_id: int = 0

    def activate(self) -> None:
        """进入 State 模式，刷新颜色图。"""
        self._emit_status("State 编辑模式")
        self.event_bus.emit("state_changed", state_id=0, action="refresh")

    def deactivate(self) -> None:
        """离开 State 模式。"""
        pass

    def on_province_clicked(self, pid: int) -> None:
        """点击省份分配到当前选中的 State。"""
        if pid <= 0 or self.selected_state_id <= 0:
            return

        state_mgr = self.project.state_mgr
        old_state_id = state_mgr.get_state_of_province(pid)

        if old_state_id == self.selected_state_id:
            return  # 已在此 State

        cmd = AssignProvinceToStateCommand(
            state_mgr, pid, old_state_id, self.selected_state_id,
        )
        self.history.execute(cmd)
        self.project.mark_dirty()

        self.event_bus.emit(
            "state_changed",
            state_id=self.selected_state_id,
            action="modified",
            property="assign",
        )
        self._emit_status(f"省份 {pid} 已分配到 State {self.selected_state_id}")

    def on_province_double_clicked(self, pid: int) -> None:
        """双击省份设置 VP。通过事件通知 UI 弹对话框。"""
        if pid <= 0:
            return

        state_mgr = self.project.state_mgr
        sid = state_mgr.get_state_of_province(pid)
        if sid == 0:
            self._emit_status("该省份未分配到任何 State，请先分组")
            return

        # 通知 UI 弹 VP 对话框（controller 不直接弹 Qt 对话框）
        self.event_bus.emit("vp_dialog_requested", pid=pid, state_id=sid)

    def set_vp(self, pid: int, value: int) -> None:
        """设置省份的 VP 值（由 UI 对话框回调调用）。"""
        state_mgr = self.project.state_mgr

        # 获取旧值
        sid = state_mgr.get_state_of_province(pid)
        state = state_mgr.get_state(sid) if sid > 0 else None
        old_vp = state.victory_points.get(pid) if state else None

        new_vp = value if value > 0 else None

        cmd = SetVPCommand(state_mgr, pid, old_vp, new_vp)
        self.history.execute(cmd)
        self.project.mark_dirty()

        if new_vp:
            self._emit_status(f"省份 {pid} 设为 {value} 分 VP")
        else:
            self._emit_status(f"省份 {pid} VP 已移除")
        self.event_bus.emit("vp_changed", pid=pid, value=value)

    def auto_states(self, per_state: int) -> None:
        """自动分组省份为 State。"""
        state_mgr = self.project.state_mgr
        map_data = self.project.map_data

        state_mgr.auto_split(
            map_data.province_map,
            map_data.tile_map,
            per_state,
        )
        self.project.mark_dirty()

        count = len(state_mgr.states)
        self._emit_status(f"State 分组完成: {count} 个")
        self.event_bus.emit("state_changed", state_id=0, action="refresh")

    def select_state(self, state_id: int) -> None:
        """选中 State。"""
        self.selected_state_id = state_id
        state = self.project.state_mgr.get_state(state_id)
        if state:
            self.event_bus.emit(
                "state_changed",
                state_id=state_id,
                action="selected",
            )

    def change_property(self, state_id: int, prop: str, value: Any) -> None:
        """修改 State 属性（通过 Command 支持撤销）。"""
        state_mgr = self.project.state_mgr
        state = state_mgr.get_state(state_id)
        if not state:
            return

        old_value = getattr(state, prop, None)
        if old_value == value:
            return

        # 类型转换
        if prop == "manpower":
            value = int(value)
        else:
            value = str(value)

        cmd = SetStatePropertyCommand(state_mgr, state_id, prop, old_value, value)
        self.history.execute(cmd)
        self.project.mark_dirty()
        self.event_bus.emit(
            "state_changed", state_id=state_id, action="modified",
        )
