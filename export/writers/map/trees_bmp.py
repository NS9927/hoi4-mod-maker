"""
map/trees.bmp 写入器.

8-bit indexed BMP, bottom-up, vanilla palette (256 色).
尺寸 = 地图 ÷ 4 (HOI4 按比例缩放到实际地图).

参考: Map modding.txt §Trees (行 419-470).
"""

from __future__ import annotations

import os
import struct

import numpy as np

from data.constants import MAP_WIDTH, MAP_HEIGHT
from data.trees_palette import TREES_PALETTE_BYTES


_TREES_W = MAP_WIDTH // 4
_TREES_H = MAP_HEIGHT // 4


def write_trees_bmp(
    output_dir: str,
    tree_map: np.ndarray | None = None,
    map_width: int | None = None,
    map_height: int | None = None,
) -> None:
    """生成 map/trees.bmp.

    tree_map: uint8 数组 (H//4, W//4), 每像素一个 palette 索引.
              None → 全黑 (无树).
    map_width/map_height: 实际地图尺寸, 用于 tree_map=None 时计算尺寸.
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "trees.bmp")

    if tree_map is not None:
        data = tree_map.astype(np.uint8)
        h, w = data.shape[:2]
    else:
        mw = map_width if map_width else MAP_WIDTH
        mh = map_height if map_height else MAP_HEIGHT
        w = mw // 4
        h = mh // 4
        data = np.zeros((h, w), dtype=np.uint8)

    # BMP row padding (each row must be multiple of 4 bytes)
    row_bytes = w
    row_pad = (4 - row_bytes % 4) % 4
    padded_row = row_bytes + row_pad

    # BMP is bottom-up: flip vertically
    data_flipped = data[::-1, :]

    # 写 BMP
    palette_size = 256 * 4  # 1024
    pixel_size = padded_row * h
    header_size = 14 + 40 + palette_size
    file_size = header_size + pixel_size

    with open(path, "wb") as f:
        # BMP file header (14 bytes)
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", header_size))

        # DIB header (40 bytes)
        f.write(struct.pack("<I", 40))       # header size
        f.write(struct.pack("<i", w))        # width
        f.write(struct.pack("<i", h))        # height (positive = bottom-up)
        f.write(struct.pack("<HH", 1, 8))   # planes, bpp
        f.write(struct.pack("<I", 0))        # compression (none)
        f.write(struct.pack("<I", pixel_size))
        f.write(struct.pack("<ii", 2835, 2835))  # ppm
        f.write(struct.pack("<II", 256, 0))       # colors used, important

        # Palette (256 × BGRA)
        f.write(TREES_PALETTE_BYTES)

        # Pixel data (bottom-up, padded rows)
        pad = b"\x00" * row_pad
        for row in range(h):
            f.write(data_flipped[row, :].tobytes())
            if row_pad:
                f.write(pad)


def auto_generate_tree_map(terrain_map: np.ndarray) -> np.ndarray:
    """从 terrain_map 自动生成 tree_map (降采样到 trees 分辨率).

    terrain_map: (H, W) uint8, palette index.
    返回: (H//4, W//4) uint8, trees palette index.
    """
    from data.terrain_types import TERRAIN_PALETTE_INDEX
    from data.trees_palette import TERRAIN_TO_TREE_INDEX

    full_h, full_w = terrain_map.shape[:2]
    h = full_h // 4
    w = full_w // 4

    # 降采样 terrain_map
    step_y = max(1, full_h // h)
    step_x = max(1, full_w // w)
    small_terrain = terrain_map[::step_y, ::step_x][:h, :w]

    # 建反查表: terrain_palette_index → terrain_name
    idx_to_name: dict[int, str] = {}
    for tname, tidx in TERRAIN_PALETTE_INDEX.items():
        idx_to_name[tidx] = tname

    tree_map = np.zeros((h, w), dtype=np.uint8)
    for terrain_idx, terrain_name in idx_to_name.items():
        tree_idx = TERRAIN_TO_TREE_INDEX.get(terrain_name, 0)
        if tree_idx > 0:
            tree_map[small_terrain == terrain_idx] = tree_idx

    return tree_map
