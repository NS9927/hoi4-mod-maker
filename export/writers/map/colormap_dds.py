"""
map/terrain/colormap_rgb_cityemissivemask_a.dds 生成.

HOI4 zoom out 到战略视角时, 引擎用这张 2816x1024 的 DDS 作为"全球总览"背景纹理.
vanilla 文件画的是地球大陆 (北美/欧洲/非洲), 架空 MOD 不覆盖 → 用户缩远就看到地球.

格式: DDS, 2816x1024, 无压缩 BGRA8, 128 字节头.
RGB channel 存颜色, Alpha channel 存城市夜间灯光 mask (0 = 无灯, 255 = 亮城市).
我们架空 MOD 不做城市灯光, alpha 全部给 0.

生成逻辑: 把 tile_map 从 5632x2048 降采样到 2816x1024, 陆地涂土色 / 海洋涂深蓝.
"""

from __future__ import annotations

import os
import struct

import numpy as np

from data.constants import MAP_WIDTH, MAP_HEIGHT, TILE_LAND, TILE_SEA, TILE_LAKE


_DDS_WIDTH = MAP_WIDTH // 2   # 我们地图 2048 → DDS 1024
_DDS_HEIGHT = MAP_HEIGHT // 2  # 我们地图 1024 → DDS 512

# 默认颜色 (B, G, R, A) — DDS 字节顺序. 用户通过 ColormapSettings 覆盖.
_DEFAULT_COLOR_LAND = (60, 90, 95, 0)
_DEFAULT_COLOR_SEA  = (90, 55, 30, 0)
_DEFAULT_COLOR_LAKE = (140, 110, 70, 0)

# 按 terrain type 的战略视图着色 (B, G, R, A)
_TERRAIN_TYPE_COLORS: dict[str, tuple[int, int, int, int]] = {
    "plains":   (55, 100, 90, 0),    # 土绿
    "forest":   (45, 80, 55, 0),     # 深绿
    "hills":    (55, 95, 110, 0),    # 黄褐
    "mountain": (70, 80, 90, 0),     # 灰褐
    "desert":   (60, 130, 170, 0),   # 沙黄
    "marsh":    (65, 90, 60, 0),     # 暗绿
    "jungle":   (35, 75, 45, 0),     # 深绿
    "urban":    (75, 85, 95, 0),     # 灰色
    "ocean":    (90, 55, 30, 0),     # 深蓝
    "lakes":    (140, 110, 70, 0),   # 浅蓝
}


def _build_dds_header(width: int, height: int) -> bytes:
    """构造 128 字节 DDS 文件头 (无压缩 BGRA8, 单 mipmap)."""
    # 匹配 vanilla 参数: flags=0x100f, pitch=width*4, pf_flags=0x41 (ALPHAPIXELS|RGB)
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<I", header, 4, 124)           # dwSize
    struct.pack_into("<I", header, 8, 0x100f)        # dwFlags (CAPS+HEIGHT+WIDTH+PITCH+PIXELFORMAT)
    struct.pack_into("<I", header, 12, height)       # dwHeight
    struct.pack_into("<I", header, 16, width)        # dwWidth
    struct.pack_into("<I", header, 20, width * 4)    # dwPitchOrLinearSize
    struct.pack_into("<I", header, 24, 0)            # dwDepth
    struct.pack_into("<I", header, 28, 1)            # dwMipMapCount
    # dwReserved1[11] — 44 字节 0
    # ddspf at offset 76
    struct.pack_into("<I", header, 76, 32)           # dwSize
    struct.pack_into("<I", header, 80, 0x41)         # dwFlags (ALPHAPIXELS | RGB)
    struct.pack_into("<I", header, 84, 0)            # dwFourCC
    struct.pack_into("<I", header, 88, 32)           # dwRGBBitCount
    struct.pack_into("<I", header, 92, 0x00FF0000)   # R mask
    struct.pack_into("<I", header, 96, 0x0000FF00)   # G mask
    struct.pack_into("<I", header, 100, 0x000000FF)  # B mask
    struct.pack_into("<I", header, 104, 0xFF000000)  # A mask
    struct.pack_into("<I", header, 108, 0x1000)      # dwCaps (TEXTURE)
    return bytes(header)


def write_water_colormap_dds(
    tile_map: np.ndarray,
    output_dir: str,
) -> None:
    """生成 map/terrain/colormap_water_0.dds (及 1, 2 mip 级别).

    HOI4 用这些 DDS 决定海洋颜色。
    - colormap_water_0.dds: 半地图尺寸 (MAP_WIDTH//2 x MAP_HEIGHT//2)
    - colormap_water_1.dds: 四分之一尺寸
    - colormap_water_2.dds: 八分之一尺寸

    格式: 无压缩 BGRA8, 128 字节 DDS 头。
    海洋像素: 深蓝色; 陆地像素: 同色（只有水面被引擎使用）。
    """
    # 水面颜色 (B, G, R, A)
    water_color = np.array([150, 100, 50, 255], dtype=np.uint8)

    out_dir = os.path.join(output_dir, "map", "terrain")
    os.makedirs(out_dir, exist_ok=True)

    for level, divisor in enumerate([2, 4, 8]):
        dds_w = MAP_WIDTH // divisor
        dds_h = MAP_HEIGHT // divisor
        if dds_w < 1 or dds_h < 1:
            break

        # 降采样 tile_map
        downsampled = tile_map[::divisor, ::divisor]
        # 裁剪到目标尺寸（避免不整除的余数行列）
        downsampled = downsampled[:dds_h, :dds_w]
        h, w = downsampled.shape

        pixels = np.empty((h, w, 4), dtype=np.uint8)
        pixels[:] = water_color  # 全部填水色（陆地部分引擎不用）

        header = _build_dds_header(w, h)
        out_path = os.path.join(out_dir, f"colormap_water_{level}.dds")
        with open(out_path, "wb") as f:
            f.write(header)
            f.write(pixels.tobytes())


def write_colormap_dds(
    tile_map: np.ndarray,
    output_dir: str,
    settings=None,
    terrain_map: np.ndarray | None = None,
) -> None:
    """从 tile_map + terrain_map 生成 map/terrain/colormap_rgb_cityemissivemask_a.dds.

    - tile_map: (MAP_HEIGHT, MAP_WIDTH) uint8, TILE_LAND/SEA/LAKE
    - terrain_map: (MAP_HEIGHT, MAP_WIDTH) uint8, 可选, 有则按地形着色
    - settings: ColormapSettings 实例, None 用默认色
    - 输出: 降采样 BGRA8 DDS
    """
    if tile_map.shape != (MAP_HEIGHT, MAP_WIDTH):
        raise ValueError(
            f"tile_map 尺寸应为 ({MAP_HEIGHT}, {MAP_WIDTH}), 实际 {tile_map.shape}"
        )

    # 决定三色
    if settings is not None:
        color_land = settings.land.to_bgra()
        color_sea = settings.sea.to_bgra()
        color_lake = settings.lake.to_bgra()
    else:
        color_land = _DEFAULT_COLOR_LAND
        color_sea = _DEFAULT_COLOR_SEA
        color_lake = _DEFAULT_COLOR_LAKE

    downsampled = tile_map[::2, ::2]
    h, w = downsampled.shape
    pixels = np.empty((h, w, 4), dtype=np.uint8)
    pixels[:] = color_sea
    land_mask = downsampled == TILE_LAND
    lake_mask = downsampled == TILE_LAKE

    if terrain_map is not None and terrain_map.shape == (MAP_HEIGHT, MAP_WIDTH):
        # 按地形类型着色陆地
        from data.terrain_types import PALETTE_TO_TYPE
        ds_terrain = terrain_map[::2, ::2]
        # 先填默认陆地色
        pixels[land_mask] = color_land
        # 再按地形类型覆盖
        for idx in np.unique(ds_terrain[land_mask]):
            ttype = PALETTE_TO_TYPE.get(int(idx))
            if ttype and ttype in _TERRAIN_TYPE_COLORS:
                tmask = land_mask & (ds_terrain == idx)
                pixels[tmask] = _TERRAIN_TYPE_COLORS[ttype]
    else:
        pixels[land_mask] = color_land

    pixels[lake_mask] = color_lake

    # ── 消除"拼贴"硬边：给陆地加噪声 + gaussian 模糊 ──
    # 为什么：vanilla colormap 是画家手绘 + 噪声，几千种颜色；
    # 我们按地形类型填纯色只有 7 种颜色，atlas 材质叠上去就是硬边块。
    # 加噪声 + 轻度模糊后，相邻地形之间有渐变带，肉眼看不到"拼贴"。
    try:
        from scipy.ndimage import gaussian_filter
        rng = np.random.default_rng(42)
        # 只对陆地 BGR 三通道做抖动 + 模糊（alpha 保持 0）
        rgb = pixels[..., :3].astype(np.float32)
        noise = rng.integers(-12, 13, size=rgb.shape, dtype=np.int16).astype(np.float32)
        rgb = rgb + noise
        for c in range(3):
            rgb[..., c] = gaussian_filter(rgb[..., c], sigma=2.5)
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
        pixels[..., :3] = rgb
        # 模糊会让颜色渗进海洋/湖泊，重新覆盖回纯海色/湖色（海面另有 colormap_water 渲染）
        pixels[downsampled == TILE_SEA] = color_sea
        pixels[lake_mask] = color_lake
    except ImportError:
        pass  # scipy 不在时退回硬边版本

    # 写文件
    out_dir = os.path.join(output_dir, "map", "terrain")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "colormap_rgb_cityemissivemask_a.dds")
    header = _build_dds_header(_DDS_WIDTH, _DDS_HEIGHT)
    with open(out_path, "wb") as f:
        f.write(header)
        f.write(pixels.tobytes())
