"""
ExpandProvinceTool — 省份扩张工具（两步激活 + 画笔扩张）。

工作流程（2026-04-09 修正: 一次只扩张一圈）：
1. 第一次点击省份 A → 选中（黄色边框 + 半透明 allowed 区域 overlay）
2. 第二次点击同一省份 A → 进入扩张模式，开始绘制
3. 按住拖动 → 光标经过的像素归给省份 A（限当前 allowed_mask 内）
4. 松开鼠标 → **退出扩张模式**，allowed_mask 不再生效
5. 想继续扩张（吃下一圈邻居）→ 重新点击省份 A 两次, 新的 allowed_mask
   会包含"吃掉第一圈后暴露出来的第二圈邻居"

约束：
- 单次 stroke 只能扩张到**当前**的直接邻居（neighborhood mask）
- 松开后必须重新激活才能扩张下一圈, 防止一次拖拽吃掉整条大陆
- 只能影响相同地块类型（陆地省份不会吃海洋像素）
- 邻居被吃掉的像素自动减少；邻居完全消失会触发 ID 压实（导出时）

为了向后兼容，工具名仍叫 lasso_province（注册名）。
"""
from __future__ import annotations

import numpy as np

from domain.tools.base import Tool, ToolContext, CleanupLevel


# 扩张笔刷半径（像素）。固定值，不依赖全局 brush_size 滑块以避免歧义。
EXPAND_RADIUS = 4


class LassoProvinceTool(Tool):
    name = "lasso_province"
    display_modes = ("province",)
    cleanup_level = CleanupLevel.FAST
    label = "省份扩张"
    description = "点选省份 → 再点同一省份进入扩张 → 拖动画笔扩张边界"
    cursor = "cross"

    def get_undo_array_names(self, ctx: ToolContext) -> list[str]:
        return ["province_map"]

    def on_press(self, ctx: ToolContext, x: int, y: int) -> None:
        md = ctx.map_data
        pid_under = int(md.province_map[y, x])
        if pid_under <= 0:
            return

        sel = ctx.state.get("pid", 0)

        # Case 1: 没选过 / 选了别的省份 → 首次选中
        if pid_under != sel:
            ctx.state["pid"] = pid_under
            ctx.state["tile"] = md.get_province_tile_type(pid_under)
            ctx.state["allowed_mask"] = md.get_neighborhood_mask(pid_under)
            ctx.state["active"] = False  # 还没进入扩张模式
            ctx.state["painting"] = False
            ctx.selected_province_id = pid_under
            return

        # Case 2: 已选中同一省份 → 进入扩张模式 + 立刻画第一笔
        if not ctx.state.get("active"):
            ctx.state["active"] = True
            ctx.state["painting"] = True
            self._paint_at(ctx, x, y)
            return

        # Case 3: 已在扩张模式 → 继续画
        ctx.state["painting"] = True
        self._paint_at(ctx, x, y)

    def on_drag(self, ctx: ToolContext, x: int, y: int) -> None:
        if not ctx.state.get("painting"):
            return
        self._paint_at(ctx, x, y)
        ctx.expand_dirty(x, y)

    def on_release(self, ctx: ToolContext, x: int, y: int) -> None:
        ctx.state["painting"] = False
        # 松开就退出扩张模式 (2026-04-09 修正):
        # 用户必须重新点击才能扩张下一圈, 避免一次拖拽把整片大陆吃掉.
        # pid 保留, 下次同省份点击时走 Case 2 重新激活, 并拿到新的 allowed_mask.
        ctx.state["active"] = False

    def on_cancel(self, ctx: ToolContext) -> None:
        ctx.state.clear()
        ctx.dirty_bbox = None
        ctx.selected_province_id = 0

    def run_cleanup(self, ctx: ToolContext) -> None:
        """覆盖默认清理：在 FAST 清理之外，额外做"压实 + 同步引用"。
        防止扩张吃光邻居导致 ID gap。"""
        # 先做基类的 FAST 清理（局部 X-crossing 修复）
        super().run_cleanup(ctx)
        # 然后压实 + 同步引用
        sel = ctx.state.get("pid", 0)
        mapping = ctx.map_data.compact_with_references(
            state_mgr=ctx.state_mgr,
            country_mgr=ctx.country_mgr,
        )
        # 选中的省份可能被改了 ID，跟踪
        if sel in mapping:
            new_sel = mapping[sel]
            ctx.state["pid"] = new_sel
            ctx.selected_province_id = new_sel
            # 重算 allowed_mask（可能因为压实而需要更新）
            if ctx.state.get("active") and new_sel > 0:
                ctx.state["allowed_mask"] = ctx.map_data.get_neighborhood_mask(new_sel)

    # ────── 笔刷 ──────

    def _paint_at(self, ctx: ToolContext, cx: int, cy: int) -> None:
        """在 (cx, cy) 周围画一个笔刷印章，把符合条件的像素归给选中省份。"""
        md = ctx.map_data
        sel_pid = ctx.state.get("pid", 0)
        if sel_pid <= 0:
            return
        allowed: np.ndarray = ctx.state.get("allowed_mask")
        sel_tile = ctx.state.get("tile", 0)
        if allowed is None:
            return

        h, w = md.province_map.shape
        x0 = max(0, cx - EXPAND_RADIUS)
        y0 = max(0, cy - EXPAND_RADIUS)
        x1 = min(w, cx + EXPAND_RADIUS + 1)
        y1 = min(h, cy + EXPAND_RADIUS + 1)
        if x0 >= x1 or y0 >= y1:
            return

        sub_pm = md.province_map[y0:y1, x0:x1]
        sub_tm = md.tile_map[y0:y1, x0:x1]
        sub_allowed = allowed[y0:y1, x0:x1]

        mask = (
            sub_allowed
            & (sub_tm == sel_tile)
            & (sub_pm != sel_pid)
            & (sub_pm != 0)
        )
        sub_pm[mask] = sel_pid


from domain.tools.registry import register_tool
register_tool(LassoProvinceTool())
