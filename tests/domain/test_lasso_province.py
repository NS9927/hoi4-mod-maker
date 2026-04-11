"""
LassoProvinceTool (省份扩张) 行为测试.

验证 2026-04-09 修正:
- 松开鼠标后 active 必须变 False
- 下次点击同一省份应重新走 Case 2 (激活 + 画第一笔)
- 单次 stroke 不能跨越当前 allowed_mask
"""

import numpy as np
import pytest


def _make_ctx_with_map():
    """构造一个最小 MapData + ToolContext, 用来驱动 LassoProvinceTool."""
    from domain.map_data import MapData
    from domain.tools.base import ToolContext
    from data.constants import TILE_LAND

    # 10x10 全陆地, 3 省份: 1 占左半, 2 占右半, 3 在角落
    pm = np.zeros((10, 10), dtype=np.int32)
    pm[:, :5] = 1
    pm[:, 5:] = 2
    pm[0:2, 0:2] = 3  # 角落一小块
    tm = np.full((10, 10), TILE_LAND, dtype=np.uint8)

    md = MapData.__new__(MapData)
    md.province_map = pm
    md.tile_map = tm

    class _FakeUndo:
        def push_snapshot(self, *a, **k): pass

    ctx = ToolContext(map_data=md, undo_mgr=_FakeUndo())
    return ctx


def test_release_deactivates_expand_mode():
    """松开鼠标后 active 应为 False, 防止继续扩张到新邻居."""
    from domain.tools.lasso_province import LassoProvinceTool
    tool = LassoProvinceTool()
    ctx = _make_ctx_with_map()

    # 第一次点击省份 1 (位置 5, 5 是 2 号省, 我们点 3,3 应该是 1 号省)
    tool.on_press(ctx, 3, 3)
    assert ctx.state.get("pid") == 1
    assert ctx.state.get("active") is False

    # 第二次点击同省进入扩张
    tool.on_press(ctx, 3, 3)
    assert ctx.state.get("active") is True
    assert ctx.state.get("painting") is True

    # 拖动几下
    tool.on_drag(ctx, 4, 4)

    # 松开 → active 必须变 False
    tool.on_release(ctx, 4, 4)
    assert ctx.state.get("painting") is False
    assert ctx.state.get("active") is False, (
        "松开后 active 必须 False, 否则一次拖拽能吃整条大陆"
    )


def test_next_press_on_same_province_reactivates():
    """松开后再次点击同一省份, 应走 Case 2 重新激活 (而非 Case 3 继续画)."""
    from domain.tools.lasso_province import LassoProvinceTool
    tool = LassoProvinceTool()
    ctx = _make_ctx_with_map()

    tool.on_press(ctx, 3, 3)   # Case 1: 选中
    tool.on_press(ctx, 3, 3)   # Case 2: 激活
    tool.on_release(ctx, 3, 3)
    assert not ctx.state.get("active")

    # 下一次点击同一省份应该再次激活 (Case 2), 不是继续 (Case 3)
    tool.on_press(ctx, 3, 3)
    assert ctx.state.get("active") is True
    assert ctx.state.get("painting") is True
