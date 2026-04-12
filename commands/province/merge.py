"""
MergeProvincesCommand — 合并两个省份。

存储受影响像素位置、旧省份 ID、旧 state/country 引用，
以便完整撤销。
"""

from __future__ import annotations

import numpy as np

from commands.base import Command
from domain.map_data import MapData


class MergeProvincesCommand(Command):
    """合并省份：将 pid_remove 的所有像素并入 pid_keep。"""

    label = "合并省份"

    def __init__(
        self,
        map_data: MapData,
        pid_keep: int,
        pid_remove: int,
        state_mgr=None,
        country_mgr=None,
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            pid_keep: 保留的省份 ID
            pid_remove: 被移除的省份 ID
            state_mgr: StateManager（可选，用于更新 state 引用）
            country_mgr: CountryManager（可选，用于更新 country 引用）
        """
        self._map_data = map_data
        self._pid_keep = pid_keep
        self._pid_remove = pid_remove
        self._state_mgr = state_mgr
        self._country_mgr = country_mgr

        # undo 数据（execute 时填充）
        self._affected_pixels: np.ndarray | None = None  # bool mask
        self._old_state_of_removed: int = 0
        self._old_vp_of_removed: dict[int, int] = {}
        self._compact_mapping: dict[int, int] = {}

    def execute(self) -> None:
        """合并省份像素，更新 state/country 引用，压实 ID。"""
        province_map = self._map_data.province_map

        # 记录被移除省份的像素位置
        self._affected_pixels = (province_map == self._pid_remove)

        # 保存 state 引用
        if self._state_mgr is not None:
            self._old_state_of_removed = (
                self._state_mgr.get_state_of_province(self._pid_remove)
            )
            old_state = self._state_mgr.get_state(self._old_state_of_removed)
            if old_state is not None:
                # 保存被移除省份的 VP
                if self._pid_remove in old_state.victory_points:
                    self._old_vp_of_removed = dict(old_state.victory_points)

        # 执行合并：像素改为 pid_keep
        province_map[self._affected_pixels] = self._pid_keep

        # 更新 state: 从旧 state 移除 pid_remove
        if self._state_mgr is not None:
            sid = self._old_state_of_removed
            state = self._state_mgr.get_state(sid) if sid > 0 else None
            if state is not None:
                if self._pid_remove in state.provinces:
                    state.provinces.remove(self._pid_remove)
                state.victory_points.pop(self._pid_remove, None)

        # 压实 ID
        self._compact_mapping = self._map_data.compact_with_references(
            state_mgr=self._state_mgr,
            country_mgr=self._country_mgr,
        )

    def undo(self) -> None:
        """恢复被合并省份的像素和引用。"""
        if self._affected_pixels is None:
            return

        province_map = self._map_data.province_map

        # 反向压实: 找到 pid_keep 和 pid_remove 的当前映射
        # 需要先恢复像素，再处理引用
        # 由于压实可能改变了 ID，我们需要反向映射
        reverse_map = {v: k for k, v in self._compact_mapping.items()}

        # 恢复像素
        province_map[self._affected_pixels] = self._pid_remove

        # 恢复 state 引用
        if self._state_mgr is not None and self._old_state_of_removed > 0:
            state = self._state_mgr.get_state(self._old_state_of_removed)
            if state is not None:
                if self._pid_remove not in state.provinces:
                    state.provinces.append(self._pid_remove)
                if self._old_vp_of_removed:
                    state.victory_points.update(self._old_vp_of_removed)
            # 重建索引
            self._state_mgr._province_to_state[self._pid_remove] = (
                self._old_state_of_removed
            )
