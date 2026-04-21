"""
DowngradeMountainCommand — 一键把"太多山"降级。

做两件事:
1. 视觉层 (terrain.bmp): 雪山→山地, 山地→丘陵, 丘陵→平原
   + 形态学 opening 去掉小于 N 像素的孤立山地斑块(下沉到丘陵)
2. 属性层 (provincial_terrain dict): 同步降级 per-province 类型

支持 undo (保存旧 terrain_map + 旧 provincial_terrain dict)。
"""
from __future__ import annotations

import numpy as np

from commands.base import Command
from data.terrain_types import PALETTE_TO_TYPE, TERRAIN_PALETTE_INDEX
from domain.map_data import MapData


# 视觉层(terrain.bmp) 的 palette 降级映射
# 保持大生态（沙漠山地→沙漠丘陵），其他山地→通用丘陵
_PALETTE_DOWNGRADE: dict[int, int] = {
    # 雪山 → 山地
    16: 6,       # snow_16 → terrain_6 (mountain)
    31: 6,       # desert_mountain_tops → mountain
    19: 0,       # plains_snow → plains
    # 山地 → 丘陵 (保留沙漠生态)
    6: 17,       # terrain_6 (mountain) → hills_blend
    10: 17,      # terrain_10 → hills_blend
    11: 8,       # desert_mountain_11 → desert_hills (沙漠丘陵)
    18: 17,      # sand mountain variation → hills_blend
    20: 17,      # grass mountain variation → hills_blend
    27: 1,       # jungle_mountain → forest(丛林里降级成森林/丘陵争议,用森林)
    # 丘陵 → 平原 (保留沙漠)
    17: 0,       # hills_blend → terrain_0 (plains)
    2: 3,        # desert_mountain(hills type) → desert
    8: 3,        # desert_hills → desert
}


# 属性层(provincial_terrain dict) 的类型名降级
_TYPE_DOWNGRADE: dict[str, str] = {
    "mountain": "hills",
    "hills": "plains",
}


# 降级后，小于此像素数的孤立"丘陵"斑块（原本是散落的山地碎点）
# 被清理成平原。直接修复"平原区域散落橙色碎点"的问题。
_MIN_PATCH_PIXELS = 50

# 丘陵类的 palette 索引（降级后要清理的）
_HILLS_PALETTES = (17, 2, 8)


class DowngradeMountainCommand(Command):
    """一键降级山脉。"""

    label = "一键降级山脉"

    def __init__(self, map_data: MapData) -> None:
        self._map_data = map_data
        self._old_terrain: np.ndarray | None = None
        self._old_prov_terrain: dict | None = None

    def execute(self) -> None:
        tm = self._map_data.terrain_map
        self._old_terrain = tm.copy()
        self._old_prov_terrain = dict(self._map_data.provincial_terrain)

        # —— Step 1: 应用 palette 降级 LUT (雪→山, 山→丘, 丘→平) ——
        lut = np.arange(256, dtype=np.uint8)
        for old_idx, new_idx in _PALETTE_DOWNGRADE.items():
            lut[old_idx] = new_idx
        new_tm = lut[tm]

        # —— Step 2: 清理降级后的"小丘陵斑块"（原本是散落山地碎点）——
        # 降级后, 原来的小山地变成小丘陵斑块, 我们再把 <50 像素的丘陵斑块降为平原
        hills_mask = np.isin(new_tm, _HILLS_PALETTES)
        if np.any(hills_mask):
            from scipy.ndimage import label as _label
            labels, n = _label(hills_mask, structure=np.ones((3, 3), dtype=bool))
            if n > 0:
                sizes = np.bincount(labels.ravel())
                small_labels = np.where(sizes < _MIN_PATCH_PIXELS)[0]
                small_labels = small_labels[small_labels > 0]  # 排除背景
                if len(small_labels) > 0:
                    small_mask = np.isin(labels, small_labels)
                    new_tm[small_mask] = 0  # 降为平原

        self._map_data.terrain_map[:] = new_tm

        # —— Step 3: 重算 provincial_terrain (从新 terrain_map 反推) ——
        # 直接降级 dict 里的类型比重算简单, 因为现有 dict 已经是按省份多数票决定
        new_prov: dict = {}
        for pid, typ in self._old_prov_terrain.items():
            new_prov[pid] = _TYPE_DOWNGRADE.get(typ, typ)
        self._map_data.provincial_terrain.clear()
        self._map_data.provincial_terrain.update(new_prov)

    def undo(self) -> None:
        if self._old_terrain is not None:
            self._map_data.terrain_map[:] = self._old_terrain
        if self._old_prov_terrain is not None:
            self._map_data.provincial_terrain.clear()
            self._map_data.provincial_terrain.update(self._old_prov_terrain)
