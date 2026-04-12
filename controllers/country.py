"""CountryController — 国家编辑模式控制器。

处理国家创建、领土分配、首都设置、属性编辑。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controllers.base import BaseController
from commands.country.assign import AssignStateToCountryCommand
from commands.country.create import CreateCountryCommand

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class CountryController(BaseController):
    """国家编辑模式。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        self.selected_country_tag: str = ""

    def activate(self) -> None:
        """进入国家模式，刷新颜色图。"""
        self._emit_status("国家编辑模式")
        self.event_bus.emit("country_changed", tag="", action="refresh")

    def deactivate(self) -> None:
        """离开国家模式。"""
        pass

    def on_province_clicked(self, pid: int) -> None:
        """点击省份：将所在 State 分配给当前选中国家。"""
        if pid <= 0 or not self.selected_country_tag:
            return

        state_mgr = self.project.state_mgr
        country_mgr = self.project.country_mgr

        state_id = state_mgr.get_state_of_province(pid)
        if state_id <= 0:
            self._emit_status("该省份未分配到任何 State")
            return

        # 获取旧的所有者
        old_tag = ""
        for tag, country in country_mgr.countries.items():
            if state_id in getattr(country, "states", []):
                old_tag = tag
                break

        if old_tag == self.selected_country_tag:
            return  # 已属于此国家

        cmd = AssignStateToCountryCommand(
            country_mgr, state_id, old_tag, self.selected_country_tag,
        )
        self.history.execute(cmd)
        self.project.mark_dirty()

        self.event_bus.emit(
            "country_changed",
            tag=self.selected_country_tag,
            action="modified",
        )
        self._emit_status(
            f"State {state_id} 已分配给 {self.selected_country_tag}"
        )

    def on_province_right_clicked(self, pid: int, x: int, y: int) -> None:
        """右键省份：设为当前国家的首都。"""
        if pid <= 0 or not self.selected_country_tag:
            if not self.selected_country_tag:
                self._emit_status("请先在国家模式下选中一个国家")
            return

        tag = self.selected_country_tag
        country_mgr = self.project.country_mgr
        country_mgr.set_capital(tag, pid)
        self.project.mark_dirty()

        self.event_bus.emit("country_changed", tag=tag, action="modified")
        self._emit_status(f"{tag} 的首都已设为省份 {pid}")

    def create_country(
        self,
        tag: str,
        name: str,
        color: tuple[int, int, int],
        party: str = "neutrality",
    ) -> bool:
        """创建新国家。返回是否成功。"""
        tag = tag.upper().strip()[:3]
        if len(tag) != 3 or not tag.isalpha():
            self._emit_status("TAG 必须是 3 个英文字母")
            return False

        cmd = CreateCountryCommand(
            self.project.country_mgr,
            tag, name or tag, color, party,
        )
        try:
            self.history.execute(cmd)
        except ValueError as e:
            self._emit_status(f"创建国家失败: {e}")
            return False

        self.project.mark_dirty()
        self.selected_country_tag = tag
        self.event_bus.emit("country_changed", tag=tag, action="created")
        self._emit_status(f"国家 {tag} ({name}) 已创建")
        return True

    def select_country(self, tag: str) -> None:
        """选中国家。"""
        self.selected_country_tag = tag
        country = self.project.country_mgr.get_country(tag)
        if country:
            self.event_bus.emit(
                "country_changed", tag=tag, action="selected",
            )

    def change_property(self, tag: str, prop: str, value: str) -> None:
        """修改国家属性。"""
        country_mgr = self.project.country_mgr
        country = country_mgr.get_country(tag)
        if not country:
            return

        if prop == "name":
            country.name = str(value)
        elif prop == "ruling_party":
            country_mgr.set_ruling_party(tag, str(value))

        self.project.mark_dirty()
        self.event_bus.emit("country_changed", tag=tag, action="modified")

    def change_color(self, tag: str, color: tuple[int, int, int]) -> None:
        """修改国家颜色。"""
        country = self.project.country_mgr.get_country(tag)
        if not country:
            return
        country.color = color
        self.project.mark_dirty()
        self.event_bus.emit("country_changed", tag=tag, action="modified")
        self._emit_status(f"{tag} 颜色已修改")
