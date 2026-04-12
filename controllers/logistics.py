"""LogisticsController — 后勤编辑控制器。

处理铁路画笔、补给节点拾取、adjacency/adjacency_rule 对话框拾取。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controllers.base import BaseController

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class LogisticsController(BaseController):
    """后勤编辑：铁路/补给/adjacency/adjacency_rule。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)
        # 拾取目标: 'adj_from'/'adj_to'/'adj_through'/'supply'/'rule_required'/'rule_icon'
        self.pick_target: str | None = None
        # 铁路画笔状态
        self.railway_draw_on: bool = False
        self.railway_level: int = 3
        self.railway_draft: list[int] = []

    def activate(self) -> None:
        """进入后勤模式。"""
        self.pick_target = None
        self.railway_draw_on = False
        self.railway_draft.clear()
        self._emit_status("后勤编辑模式")

    def deactivate(self) -> None:
        """离开后勤模式，清理所有临时状态。"""
        self.pick_target = None
        self.railway_draw_on = False
        self.railway_draft.clear()

    def on_province_clicked(self, pid: int) -> None:
        """省份点击分发：补给/铁路/adjacency 拾取。"""
        if pid <= 0:
            return

        # 铁路画笔进行中
        if self.railway_draw_on:
            if pid not in self.railway_draft:
                self.railway_draft.append(pid)
                trail = " → ".join(str(p) for p in self.railway_draft[-5:])
                self._emit_status(
                    f"铁路草稿 ({len(self.railway_draft)} 省): {trail}"
                )
            return

        # 拾取模式
        if self.pick_target is not None:
            self._handle_pick(pid)
            return

    def toggle_railway_draw(self, on: bool) -> None:
        """开始/结束铁路画笔。结束时把草稿变成一条 railway entry。"""
        if on:
            self.railway_draw_on = True
            self.railway_draft = []
            self._emit_status(
                f"铁路画笔已启用 (等级 {self.railway_level}): "
                "依次点击省份, 再次点击按钮结束"
            )
        else:
            self.railway_draw_on = False
            draft = list(self.railway_draft)
            self.railway_draft = []
            if len(draft) >= 2:
                try:
                    self.project.railway_mgr.add(
                        level=self.railway_level,
                        province_ids=draft,
                    )
                    self.project.mark_dirty()
                    self._emit_status(
                        f"铁路已保存: level {self.railway_level}, {len(draft)} 省"
                    )
                except ValueError as e:
                    self._emit_status(f"铁路保存失败: {e}")
            else:
                self._emit_status("铁路画笔已取消 (至少需要 2 个省份)")

    def set_railway_level(self, level: int) -> None:
        """设置铁路等级。"""
        self.railway_level = level

    def toggle_supply_pick(self, on: bool) -> None:
        """开关补给节点拾取模式。"""
        if on:
            self.pick_target = "supply"
            self._emit_status("点击陆地省份切换补给节点")
        else:
            if self.pick_target == "supply":
                self.pick_target = None
            self._emit_status("补给拾取已关闭")

    def set_adjacency_pick(self, on: bool, target: str = "") -> None:
        """设置 adjacency 对话框拾取模式。"""
        if on and target:
            self.pick_target = f"adj_{target}"
            self._emit_status(f"点击画布省份填入 adjacency {target}")
        else:
            self.pick_target = None
            self._emit_status("拾取模式关闭")

    def set_rule_pick(self, on: bool, target: str = "") -> None:
        """设置 adjacency_rule 对话框拾取模式。"""
        if on and target:
            self.pick_target = target  # 'rule_required' or 'rule_icon'
            self._emit_status(f"点击画布省份 → 加入 {target}")
        else:
            self.pick_target = None
            self._emit_status("拾取模式关闭")

    def _handle_pick(self, pid: int) -> None:
        """统一的拾取分发。"""
        target = self.pick_target

        if target == "supply":
            self._pick_supply(pid)
            # supply 模式是持续的，不重置 target
        elif target in ("adj_from", "adj_to", "adj_through"):
            # 通知 UI 回填省份 ID
            self.event_bus.emit(
                "logistics_province_picked",
                pid=pid,
                target=target,
            )
            self.pick_target = None
        elif target in ("rule_required", "rule_icon"):
            self.event_bus.emit(
                "logistics_province_picked",
                pid=pid,
                target=target,
            )
            self.pick_target = None
        else:
            self.pick_target = None

    def _pick_supply(self, pid: int) -> None:
        """补给节点拾取：切换陆地省份的补给节点状态。"""
        import numpy as np
        from data.constants import TILE_LAND

        map_data = self.project.map_data
        province_map = map_data.province_map
        tile_map = map_data.tile_map

        ys, xs = np.where(province_map == pid)
        if len(ys) == 0:
            return

        if int(tile_map[ys[0], xs[0]]) != TILE_LAND:
            self._emit_status(f"省份 {pid} 不是陆地, 跳过")
            return

        added = self.project.supply_mgr.toggle(pid)
        self.project.mark_dirty()
        self._emit_status(
            f"补给节点 {'已添加' if added else '已删除'}: 省份 {pid}"
        )
