"""
河流管理器 — 河流数据存储与渲染
严格按原版 HOI4 rivers.bmp 格式：
  - 0:  源头（绿色）
  - 1:  红色标记
  - 2:  入海口（黄色）
  - 3:  河流宽度 1（最窄，浅蓝）
  - 4:  河流宽度 2
  - 5:  河流宽度 3
  - 6:  河流宽度 4（深蓝）
  - 7:  河流宽度 5
  - 8:  河流宽度 6
  - 9:  河流宽度 7
  - 10: 河流宽度 8
  - 11: 河流宽度 9（最宽）
  - 254: 海洋无河流（灰色背景）
  - 255: 陆地无河流（白色背景）
"""
import numpy as np

# 河流调色板索引（与原版一致）
RIVER_SOURCE = 0       # 源头
RIVER_MARKER = 1       # 红色标记
RIVER_MOUTH = 2        # 入海口
RIVER_WIDTH_1 = 3      # 最窄
RIVER_WIDTH_2 = 4
RIVER_WIDTH_3 = 5
RIVER_WIDTH_4 = 6
RIVER_WIDTH_5 = 7
RIVER_WIDTH_6 = 8
RIVER_WIDTH_7 = 9
RIVER_WIDTH_8 = 10
RIVER_WIDTH_9 = 11     # 最宽

# 背景值
RIVER_BG_SEA = 254     # 海洋区域背景
RIVER_BG_LAND = 255    # 陆地区域背景

# 擦除时使用的值（不是0，0是源头！用255=陆地背景）
RIVER_ERASE = RIVER_BG_LAND

# HOI4 rivers.bmp 调色板颜色（严格按原版）
# 格式: index → (R, G, B)
RIVER_PALETTE = {
    0: (0, 255, 0),         # 源头 — 绿色
    1: (255, 0, 0),         # 标记 — 红色
    2: (255, 252, 0),       # 入海口 — 黄色
    3: (0, 225, 255),       # 宽度1 — 浅蓝
    4: (0, 200, 255),       # 宽度2
    5: (0, 150, 255),       # 宽度3
    6: (0, 100, 255),       # 宽度4
    7: (0, 0, 255),         # 宽度5 — 纯蓝
    8: (0, 0, 225),         # 宽度6
    9: (0, 0, 200),         # 宽度7
    10: (0, 0, 150),        # 宽度8
    11: (0, 0, 100),        # 宽度9 — 深蓝
    12: (0, 85, 0),         # 保留
    13: (0, 125, 0),        # 保留
    14: (0, 158, 0),        # 保留
    15: (24, 206, 0),       # 保留
    254: (122, 122, 122),   # 海洋背景 — 灰色
    255: (255, 255, 255),   # 陆地背景 — 白色
}

# 画布显示用 BGRA 颜色
RIVER_DISPLAY_COLORS = {}
for _idx, (_r, _g, _b) in RIVER_PALETTE.items():
    RIVER_DISPLAY_COLORS[_idx] = (_b, _g, _r, 255)

# 可绘制的河流类型（工具面板中显示）
PAINTABLE_RIVER_TYPES = [
    (RIVER_SOURCE, "源头"),
    (RIVER_WIDTH_1, "细流"),
    (RIVER_WIDTH_2, "小河"),
    (RIVER_WIDTH_3, "中河"),
    (RIVER_WIDTH_4, "大河"),
    (RIVER_WIDTH_5, "宽河"),
    (RIVER_WIDTH_6, "巨河"),
    (RIVER_MOUTH, "入海口"),
]

# 有效的河流值（可以画的，不含背景）
VALID_RIVER_VALUES = set(range(0, 12))
