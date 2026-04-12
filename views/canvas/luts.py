"""
颜色查找表 (LUT) — 地块/地形/河流/省份的 BGRA 颜色映射
从 canvas_widget.py 拆分而来，供 renderer 和 widget 共用
"""
import numpy as np

from data.constants import TILE_UNDEFINED, TILE_LAND, TILE_SEA, TILE_LAKE
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX, GRAPHICAL_TERRAINS, PALETTE_TO_TYPE
from domain.managers.river import (
    RIVER_DISPLAY_COLORS, RIVER_SOURCE, RIVER_BG_LAND, RIVER_BG_SEA,
    RIVER_ERASE, VALID_RIVER_VALUES,
)

# 地块类型对应的 BGRA 值（QImage Format_RGB32）
_TILE_BGRA = {
    TILE_UNDEFINED: (30, 20, 20, 255),
    TILE_LAND:      (101, 172, 139, 255),
    TILE_SEA:       (156, 105, 68, 255),
    TILE_LAKE:      (210, 160, 100, 255),
}

# 构建 terrain 索引 → BGRA 颜色查找表 (覆盖全部 graphical terrain)
# 每个变体用独立的高饱和色，确保 canvas 上一眼能分辨
_TERRAIN_COLOR_LUT = np.zeros((256, 4), dtype=np.uint8)
_TERRAIN_DISPLAY_COLORS: dict[int, tuple[int, int, int]] = {
    # plains 组: 绿色系
    0:  (120, 180, 60),   # 平原
    5:  (100, 160, 40),   # 平原(变体)
    19: (180, 200, 220),  # 雪原 (偏白蓝)
    # forest 组: 深绿
    1:  (30, 130, 30),    # 森林
    4:  (50, 150, 70),    # 森林(变体)
    # hills 组: 黄橙
    2:  (210, 180, 80),   # 沙漠丘陵
    17: (230, 200, 60),   # 丘陵
    # mountain 组: 灰棕分明
    6:  (140, 130, 120),  # 山地
    10: (160, 140, 100),  # 山地(变体)
    11: (180, 150, 100),  # 沙漠山地
    16: (200, 210, 230),  # 雪山 (偏白蓝)
    18: (190, 170, 110),  # 沙色山地
    20: (130, 150, 100),  # 草地山地
    27: (80, 120, 70),    # 丛林山地
    31: (110, 90, 60),    # 沙漠山顶 (深褐)
    # desert 组: 黄沙系
    3:  (220, 190, 100),  # 沙漠
    7:  (200, 170, 80),   # 沙漠(变体)
    8:  (210, 160, 90),   # 沙漠丘陵
    12: (230, 210, 130),  # 沙漠(岩地)
    # marsh: 暗青绿
    9:  (70, 120, 90),    # 沼泽
    # urban: 紫灰
    13: (160, 130, 170),  # 城市
    # jungle: 黄绿
    21: (60, 140, 20),    # 丛林
    22: (80, 160, 40),    # 丛林(变体)
    # water (不可画但需要显示)
    14: (60, 130, 200),   # 湖泊
    15: (30, 80, 180),    # 海洋
}
for _idx, (_r, _g, _b) in _TERRAIN_DISPLAY_COLORS.items():
    _TERRAIN_COLOR_LUT[_idx] = (_b, _g, _r, 255)  # BGRA

# 河流颜色 LUT (索引 → BGRA)
_RIVER_COLOR_LUT = np.zeros((256, 4), dtype=np.uint8)
for _ridx, _rbgra in RIVER_DISPLAY_COLORS.items():
    _RIVER_COLOR_LUT[_ridx] = _rbgra
# 背景色不需要在画布上显示（用底图）

# 省份随机颜色 LUT (确定性, 基于省份ID)
_PROVINCE_COLOR_LUT_SIZE = 65536
_rng = np.random.RandomState(42)
_PROVINCE_COLOR_LUT = np.zeros((_PROVINCE_COLOR_LUT_SIZE, 4), dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 0] = _rng.randint(40, 220, _PROVINCE_COLOR_LUT_SIZE, dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 1] = _rng.randint(40, 220, _PROVINCE_COLOR_LUT_SIZE, dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 2] = _rng.randint(40, 220, _PROVINCE_COLOR_LUT_SIZE, dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 3] = 255
# ID 0 = 未分配，用深色
_PROVINCE_COLOR_LUT[0] = (30, 20, 20, 255)
