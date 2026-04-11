"""
map/cities.bmp 写入器.

HOI4 用 cities.bmp 决定城市 3D 模型分布. 8-bit indexed BMP.
扫描 terrain_map 中 urban terrain (palette index 13, spawn_city=yes),
在对应位置标记城市. 无 terrain_map 时生成全黑 (无城市).

参考: Map modding.txt §Cities
"""

from __future__ import annotations

import os
import struct

import numpy as np

from data.constants import MAP_WIDTH, MAP_HEIGHT


_CITIES_W = MAP_WIDTH // 4
_CITIES_H = MAP_HEIGHT // 4

# terrain.bmp 中 spawn_city=yes 的调色板索引
_URBAN_PALETTE_INDEX = 13


def write_cities_bmp(output_dir: str,
                     terrain_map: np.ndarray | None = None) -> None:
    """生成 map/cities.bmp.
    如果提供 terrain_map，从 urban terrain 区域生成城市标记;
    否则生成全黑占位。"""
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "cities.bmp")

    w, h = _CITIES_W, _CITIES_H

    if terrain_map is not None:
        data = _generate_from_terrain(terrain_map, w, h)
    else:
        data = np.zeros((h, w), dtype=np.uint8)

    _write_8bit_bmp(path, data, w, h)


def _generate_from_terrain(terrain_map: np.ndarray,
                           out_w: int, out_h: int) -> np.ndarray:
    """从 terrain_map 提取 urban 区域，缩放到 1/4 尺寸。
    非零像素值 = 城市存在 (用 15 作为城市标记值)。"""
    # 标记 urban 像素
    urban_mask = (terrain_map == _URBAN_PALETTE_INDEX).astype(np.float32)

    # 用 4x4 block 平均池化缩放到 1/4 尺寸
    src_h, src_w = terrain_map.shape
    # 裁剪到 4 的整数倍
    crop_h = (src_h // 4) * 4
    crop_w = (src_w // 4) * 4
    cropped = urban_mask[:crop_h, :crop_w]
    # reshape 成 4x4 block 然后取均值
    blocks = cropped.reshape(crop_h // 4, 4, crop_w // 4, 4)
    density = blocks.mean(axis=(1, 3))

    # 任何 block 中有 urban 像素 → 标记为城市 (阈值 > 0)
    result = np.zeros((out_h, out_w), dtype=np.uint8)
    rh = min(out_h, density.shape[0])
    rw = min(out_w, density.shape[1])
    result[:rh, :rw] = (density[:rh, :rw] > 0).astype(np.uint8) * 15

    return result


def _write_8bit_bmp(path: str, data: np.ndarray,
                    w: int, h: int) -> None:
    """写 8-bit indexed BMP 文件 (bottom-up)."""
    row_pad = (4 - w % 4) % 4
    padded_row = w + row_pad

    palette_size = 256 * 4
    pixel_size = padded_row * h
    header_size = 14 + 40 + palette_size
    file_size = header_size + pixel_size

    with open(path, "wb") as f:
        # BMP header
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", header_size))

        # DIB header
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<i", w))
        f.write(struct.pack("<i", h))  # positive = bottom-up
        f.write(struct.pack("<HH", 1, 8))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pixel_size))
        f.write(struct.pack("<ii", 2835, 2835))
        f.write(struct.pack("<II", 256, 0))

        # Palette (grayscale)
        for i in range(256):
            f.write(struct.pack("BBBB", i, i, i, 0))

        # Pixel data (bottom-up)
        pad = b"\x00" * row_pad
        for row_idx in range(h - 1, -1, -1):
            f.write(data[row_idx].tobytes())
            if row_pad:
                f.write(pad)
