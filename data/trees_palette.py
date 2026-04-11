"""
trees.bmp 调色板 — 从 vanilla 提取的 256 色 BGRA palette.

前 16 色有意义:
  0 = 无树 (黑)
  1 = 未使用 (红)
  2-4 = 热带树 (shallow forest / medium / dense)
  5-7 = 温带树 (sparse / medium / dense)
  8-10 = 棕榈树 (sparse / medium / dense)
  11-15 = 其他 (丛林等)

default.map 的 `tree = { 3 4 7 10 }` 定义哪些索引被 HOI4 算作"有树".
"""

# (R, G, B) — 从 vanilla trees.bmp 抽出
TREES_PALETTE_RGB: list[tuple[int, int, int]] = [
    (  0,   0,   0),  #  0: 无树
    (255,   0,   0),  #  1: unused
    ( 30, 139, 109),  #  2: tropical sparse
    ( 18, 100,  78),  #  3: tropical medium  ← tree
    (  8,  58,  44),  #  4: tropical dense   ← tree
    ( 76, 156,  51),  #  5: temperate sparse
    ( 47, 120,  24),  #  6: temperate medium
    ( 20,  85,   0),  #  7: temperate dense  ← tree
    (154, 156,  51),  #  8: palm sparse
    (118, 120,  24),  #  9: palm medium
    ( 83,  85,   0),  # 10: palm dense       ← tree
    (255, 255,   0),  # 11: misc yellow
    (213, 160,   0),  # 12: misc gold
    (  0, 183,   0),  # 13: jungle sparse
    (  0, 128,   0),  # 14: jungle medium
    (  0,  60,   0),  # 15: jungle dense
]

# 补齐到 256 色 (全黑)
while len(TREES_PALETTE_RGB) < 256:
    TREES_PALETTE_RGB.append((0, 0, 0))

# BMP palette 是 BGRA 格式
TREES_PALETTE_BGRA: list[bytes] = []
for r, g, b in TREES_PALETTE_RGB:
    TREES_PALETTE_BGRA.append(bytes([b, g, r, 0]))

TREES_PALETTE_BYTES = b"".join(TREES_PALETTE_BGRA)  # 1024 bytes


# 地形类型 → trees.bmp 索引 映射 (自动生成用)
# 参考 Map modding.txt §Trees (行 419-470)
TERRAIN_TO_TREE_INDEX: dict[str, int] = {
    "forest":   7,   # temperate dense
    "hills":    5,   # temperate sparse (有些丘陵有树)
    "jungle":  14,   # jungle medium
    "marsh":    6,   # temperate medium
    "mountain": 0,   # 无树
    "plains":   0,   # 无树 (平原默认不放树)
    "desert":   0,
    "urban":    0,
    "ocean":    0,
    "lakes":    0,
}
