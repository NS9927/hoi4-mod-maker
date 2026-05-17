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
        strategic_region_mgr=None,
    ) -> None:
        """
        参数:
            map_data: 地图数据对象
            pid_keep: 保留的省份 ID
            pid_remove: 被移除的省份 ID
            state_mgr: StateManager（可选，用于更新 state 引用）
            country_mgr: CountryManager（可选，用于更新 country 引用）
            strategic_region_mgr: StrategicRegionManager（可选, 清理 region 残留 pid）
        """
        self._map_data = map_data
        self._pid_keep = pid_keep
        self._pid_remove = pid_remove
        self._state_mgr = state_mgr
        self._country_mgr = country_mgr
        self._strategic_region_mgr = strategic_region_mgr

        # undo 数据（execute 时填充）
        self._affected_pixels: np.ndarray | None = None  # bool mask
        self._old_state_of_removed: int = 0
        self._old_vp_of_removed: dict[int, int] = {}
        self._compact_mapping: dict[int, int] = {}
        # 被吞并 pid 原属的 strategic_region id（0 = 未分配）
        self._old_region_of_removed: int = 0
        # 若 pid_remove 曾是某国首都, 记录 (tag, old_capital_pid)；否则 ("", 0)
        self._old_capital_of_country: tuple[str, int] = ("", 0)

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

        # 清理 strategic_region: pid_remove 的 ID 会被切割/增量生成复用，
        # 不清掉会导致新 pid 被错误地"继承"到旧的 strategic_region。
        if self._strategic_region_mgr is not None:
            for r in self._strategic_region_mgr.regions.values():
                if self._pid_remove in r.province_ids:
                    self._old_region_of_removed = r.id
                    r.province_ids.remove(self._pid_remove)
                    break

        # country.capital: pid_remove 若是某国首都, capital 会指向死 ID
        # → 启动游戏 set_controller 时崩。把首都迁到 pid_keep (同国) 或该国其他省份。
        if self._country_mgr is not None:
            for tag, country in self._country_mgr.countries.items():
                if country.capital == self._pid_remove:
                    self._old_capital_of_country = (tag, self._pid_remove)
                    country.capital = self._pick_replacement_capital(tag)
                    break  # 首都只能属于一个国家

        # 不压实 ID — 保留空洞，让用户用切割/增量生成补回来
        # 导出时检查 ID 连续性，有空洞则提示
        self._compact_mapping = {}

    def _pick_replacement_capital(self, tag: str) -> int:
        """为国家 tag 选一个新首都. 优先 pid_keep (若同国), 否则该国任一非 pid_remove 省份."""
        # 优先 pid_keep — 它物理上接管了 pid_remove 的像素，最连续
        if self._state_mgr is not None:
            keep_sid = self._state_mgr.get_state_of_province(self._pid_keep)
            if keep_sid > 0:
                owner = self._country_mgr.get_owner_of_state(keep_sid)
                if owner == tag:
                    return self._pid_keep
        # 否则在该国 owned states 里挑一个
        owned = self._country_mgr.get_states_of_country(tag)
        if self._state_mgr is not None:
            for sid in owned:
                s = self._state_mgr.get_state(sid)
                if s is None:
                    continue
                for p in s.provinces:
                    if p != self._pid_remove:
                        return p
        return 0

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

        # 恢复 strategic_region 引用
        if (
            self._strategic_region_mgr is not None
            and self._old_region_of_removed > 0
        ):
            r = self._strategic_region_mgr.get(self._old_region_of_removed)
            if r is not None and self._pid_remove not in r.province_ids:
                r.province_ids.append(self._pid_remove)

        # 恢复 country.capital
        if self._country_mgr is not None and self._old_capital_of_country[0]:
            tag, old_cap = self._old_capital_of_country
            country = self._country_mgr.get_country(tag)
            if country is not None:
                country.capital = old_cap
