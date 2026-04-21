"""
DowngradeMountainCommand — 一键把"太多山"降级。

做三件事:
1. 视觉层 (terrain.bmp): 雪山→山地, 山地→丘陵, 丘陵→平原
   + 连通分量清理<50px 的小丘陵斑块→平原
2. 高度图 (height_map): 同步降一级 (雪-45, 山-35, 丘-30)
   这保证游戏内 3D 效果和贴图一致, 不会出现"平原贴图但还是高山"的割裂
3. 属性层 (provincial_terrain dict): 同步降级 per-province 类型

支持 undo (保存旧 terrain_map + 旧 height_map + 旧 provincial_terrain dict)。
"""
from __future__ import annotations

import numpy as np

from commands.base import Command
from data.constants import SEA_LEVEL
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

# 高度图降级量（按原像素所在的 palette 类别）
# HOI4 高度 band 中心间隔约 40，降一个 band ≈ 减 30-45
_SNOW_PALETTES = (16, 19, 31)
_MOUNTAIN_PALETTES = (6, 10, 11, 18, 20, 27)
_HEIGHT_DROP_SNOW = 45      # 雪山 -45 → 山地高度
_HEIGHT_DROP_MOUNTAIN = 35  # 山地 -35 → 丘陵高度
_HEIGHT_DROP_HILLS = 30     # 丘陵 -30 → 平原高度


class DowngradeMountainCommand(Command):
    """一键降级山脉。"""

    label = "一键降级山脉"

    def __init__(
        self,
        map_data: MapData,
        mask: np.ndarray | None = None,
    ) -> None:
        """
        mask: None = 对整张地图降级
              (H,W) bool 数组 = 仅对 mask==True 的像素降级
        """
        self._map_data = map_data
        self._mask = mask.copy() if mask is not None else None
        self._old_terrain: np.ndarray | None = None
        self._old_height: np.ndarray | None = None
        self._old_prov_terrain: dict | None = None

    def execute(self) -> None:
        # 注意: terrain_map 是 ref, 改回去会污染. 必须先 copy 原始值
        tm_orig = self._map_data.terrain_map.copy()  # 原始 palette 给高度降级用
        hm = self._map_data.height_map
        self._old_terrain = tm_orig
        self._old_height = hm.copy()
        self._old_prov_terrain = dict(self._map_data.provincial_terrain)

        # —— Step 1: 应用 palette 降级 LUT (雪→山, 山→丘, 丘→平) ——
        lut = np.arange(256, dtype=np.uint8)
        for old_idx, new_idx in _PALETTE_DOWNGRADE.items():
            lut[old_idx] = new_idx
        new_tm = lut[tm_orig]

        # —— Step 2: 清理降级后的"小丘陵斑块"（原本是散落山地碎点）——
        # 降级后, 原来的小山地变成小丘陵斑块, 我们再把 <50 像素的丘陵斑块降为平原
        hills_mask = np.isin(new_tm, _HILLS_PALETTES)
        small_patch_mask = np.zeros_like(hills_mask)
        if np.any(hills_mask):
            from scipy.ndimage import label as _label
            labels, n = _label(hills_mask, structure=np.ones((3, 3), dtype=bool))
            if n > 0:
                sizes = np.bincount(labels.ravel())
                small_labels = np.where(sizes < _MIN_PATCH_PIXELS)[0]
                small_labels = small_labels[small_labels > 0]  # 排除背景
                if len(small_labels) > 0:
                    small_patch_mask = np.isin(labels, small_labels)
                    new_tm[small_patch_mask] = 0  # 降为平原

        # —— 如果指定了选区 mask, 把 mask 外的 terrain 恢复为原值 ——
        if self._mask is not None:
            new_tm[~self._mask] = tm_orig[~self._mask]

        self._map_data.terrain_map[:] = new_tm

        # —— Step 3: 高度图降级 (基于原 terrain 的 palette 类别) ——
        # 这一步至关重要: 只改视觉不改高度, 游戏内 3D 和贴图会割裂。
        # 用 tm_orig (原始 copy), 不要用 tm (已经被覆盖)
        new_hm = hm.astype(np.int16)  # 用 int16 避免下溢
        was_snow = np.isin(tm_orig, _SNOW_PALETTES)
        was_mountain = np.isin(tm_orig, _MOUNTAIN_PALETTES)
        was_hills = np.isin(tm_orig, _HILLS_PALETTES)
        # 如果有 mask, 高度降级也限制在选区内
        if self._mask is not None:
            was_snow &= self._mask
            was_mountain &= self._mask
            was_hills &= self._mask
            small_patch_mask_in = small_patch_mask & self._mask
        else:
            small_patch_mask_in = small_patch_mask
        new_hm[was_snow] -= _HEIGHT_DROP_SNOW
        new_hm[was_mountain] -= _HEIGHT_DROP_MOUNTAIN
        new_hm[was_hills] -= _HEIGHT_DROP_HILLS
        # 小斑点(原山地碎点)被清理成平原, 高度也要降到平原级
        # 注意: 这些像素已经在上面 was_mountain/was_hills 里被降了, 再多降一点推到平原
        extra_drop = small_patch_mask_in & (~was_snow)  # 小斑点额外降 15
        new_hm[extra_drop] -= 15
        # 守底线: 陆地不能低于 SEA_LEVEL+1
        land_mask = self._map_data.tile_map == 1  # TILE_LAND
        np.clip(new_hm, 0, 255, out=new_hm)
        new_hm_u8 = new_hm.astype(np.uint8)
        # 陆地像素至少 SEA_LEVEL+1
        np.maximum(
            new_hm_u8, SEA_LEVEL + 1, out=new_hm_u8, where=land_mask
        )
        self._map_data.height_map[:] = new_hm_u8

        # —— Step 4: 降级 provincial_terrain dict (属性层) ——
        # 有 mask 时只降级选区内"多数像素在选区里"的省份
        if self._mask is not None:
            in_sel_pids = self._find_provinces_in_mask()
        else:
            in_sel_pids = None
        new_prov: dict = {}
        for pid, typ in self._old_prov_terrain.items():
            if in_sel_pids is None or pid in in_sel_pids:
                new_prov[pid] = _TYPE_DOWNGRADE.get(typ, typ)
            else:
                new_prov[pid] = typ
        self._map_data.provincial_terrain.clear()
        self._map_data.provincial_terrain.update(new_prov)

    def _find_provinces_in_mask(self) -> set[int]:
        """返回 province_map 里 >50% 像素落在 mask 内的 province id 集合。"""
        pm = self._map_data.province_map
        mask = self._mask
        # 数每个 pid 在 mask 内/外的像素数
        in_pids = pm[mask]
        all_pids = pm.ravel()
        if in_pids.size == 0:
            return set()
        max_pid = int(all_pids.max())
        total = np.bincount(all_pids, minlength=max_pid + 1)
        in_cnt = np.bincount(in_pids, minlength=max_pid + 1)
        # 只取总像素数 >0 且选区内占比 >50% 的 pid
        ratio = np.zeros_like(total, dtype=np.float32)
        nonzero = total > 0
        ratio[nonzero] = in_cnt[nonzero] / total[nonzero]
        pids = np.where(ratio > 0.5)[0]
        return set(int(p) for p in pids if p > 0)

    def undo(self) -> None:
        if self._old_terrain is not None:
            self._map_data.terrain_map[:] = self._old_terrain
        if self._old_height is not None:
            self._map_data.height_map[:] = self._old_height
        if self._old_prov_terrain is not None:
            self._map_data.provincial_terrain.clear()
            self._map_data.provincial_terrain.update(self._old_prov_terrain)
