"""
BMP 文件写入器 — 严格按 HOI4 要求的格式生成 BMP 文件
"""
import struct
import os
import numpy as np

from data.constants import MAP_WIDTH, MAP_HEIGHT
from core.province_generator import generate_province_colors


def write_provinces_bmp(
    province_map: np.ndarray,
    output_dir: str,
    colors: dict[int, tuple[int, int, int]] | None = None,
) -> dict[int, tuple[int, int, int]]:
    """
    将省份地图写入 24 位 BMP 文件。

    格式要求：
    - Windows BITMAPINFOHEADER 格式
    - 24 位 RGB
    - 像素数据 bottom-up（从下到上）
    - 每行需要 4 字节对齐（padding）
    - 不能有抗锯齿

    参数:
        province_map: 省份ID数组 (H, W), int32
        output_dir: 输出目录
        colors: 省份颜色映射 {ID: (R, G, B)}，如果为 None 则自动生成

    返回:
        实际使用的颜色映射
    """
    province_count = int(province_map.max())
    if colors is None:
        colors = generate_province_colors(province_count)

    # 确保输出目录存在
    map_dir = os.path.join(output_dir, "map")
    os.makedirs(map_dir, exist_ok=True)

    file_path = os.path.join(map_dir, "provinces.bmp")

    # 构建像素数据
    # BMP 24位格式：每像素 3 字节 (B, G, R)，注意是 BGR 顺序
    row_bytes = MAP_WIDTH * 3
    # 每行需要 4 字节对齐
    padding = (4 - (row_bytes % 4)) % 4
    padded_row_bytes = row_bytes + padding

    # 像素数据大小
    pixel_data_size = padded_row_bytes * MAP_HEIGHT

    # 文件总大小
    file_size = 14 + 40 + pixel_data_size  # BITMAPFILEHEADER + BITMAPINFOHEADER + 像素

    with open(file_path, "wb") as f:
        # === BITMAPFILEHEADER (14 bytes) ===
        f.write(b"BM")                          # 签名
        f.write(struct.pack("<I", file_size))    # 文件大小
        f.write(struct.pack("<HH", 0, 0))        # 保留字段
        f.write(struct.pack("<I", 14 + 40))      # 像素数据偏移

        # === BITMAPINFOHEADER (40 bytes) ===
        f.write(struct.pack("<I", 40))           # header 大小
        f.write(struct.pack("<i", MAP_WIDTH))    # 宽度
        f.write(struct.pack("<i", MAP_HEIGHT))   # 高度（正值 = bottom-up）
        f.write(struct.pack("<HH", 1, 24))       # 色彩平面数=1, 位深=24
        f.write(struct.pack("<I", 0))            # 压缩方式=0 (BI_RGB)
        f.write(struct.pack("<I", pixel_data_size))  # 像素数据大小
        f.write(struct.pack("<i", 2835))         # 水平分辨率 (72 DPI)
        f.write(struct.pack("<i", 2835))         # 垂直分辨率
        f.write(struct.pack("<I", 0))            # 调色板颜色数=0
        f.write(struct.pack("<I", 0))            # 重要颜色数=0

        # === 像素数据 (bottom-up) ===
        pad_bytes = b"\x00" * padding

        # 构建颜色查找表（向量化，避免逐像素 Python 循环）
        max_pid = int(province_map.max())
        # 查找表：index=省份ID → (B, G, R)
        lut = np.ones((max_pid + 1, 3), dtype=np.uint8)  # 默认(1,1,1)避免(0,0,0)
        for pid, (r, g, b) in colors.items():
            if pid <= max_pid:
                lut[pid] = [b, g, r]  # BMP 是 BGR 顺序

        # 从最后一行开始写（bottom-up）
        for y in range(MAP_HEIGHT - 1, -1, -1):
            row_ids = province_map[y, :]
            # 将ID为0的像素映射为0（lut[0]=(1,1,1)，不是黑色）
            row_bgr = lut[row_ids]  # (W, 3)
            f.write(row_bgr.tobytes())
            if padding:
                f.write(pad_bytes)

    return colors


def write_heightmap_bmp(
    heightmap: np.ndarray,
    output_dir: str,
) -> None:
    """
    写入 8 位灰度 BMP 高度图。

    格式要求：
    - 8 位索引色 BMP
    - 256 色灰度调色板
    - bottom-up
    """
    map_dir = os.path.join(output_dir, "map")
    os.makedirs(map_dir, exist_ok=True)

    file_path = os.path.join(map_dir, "heightmap.bmp")

    row_bytes = MAP_WIDTH
    padding = (4 - (row_bytes % 4)) % 4
    padded_row_bytes = row_bytes + padding

    # 调色板大小：256 个 RGBQUAD (4 bytes each)
    palette_size = 256 * 4
    pixel_data_size = padded_row_bytes * MAP_HEIGHT
    pixel_offset = 14 + 40 + palette_size
    file_size = pixel_offset + pixel_data_size

    with open(file_path, "wb") as f:
        # === BITMAPFILEHEADER ===
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", pixel_offset))

        # === BITMAPINFOHEADER ===
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<i", MAP_WIDTH))
        f.write(struct.pack("<i", MAP_HEIGHT))
        f.write(struct.pack("<HH", 1, 8))       # 8位
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pixel_data_size))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<I", 0))            # ncolors=0（原版格式，表示默认256色）
        f.write(struct.pack("<I", 0))

        # === 灰度调色板 ===
        for i in range(256):
            f.write(struct.pack("BBBB", i, i, i, 0))  # B, G, R, Reserved

        # === 像素数据 ===
        pad_bytes = b"\x00" * padding
        for y in range(MAP_HEIGHT - 1, -1, -1):
            f.write(heightmap[y, :].tobytes())
            if padding:
                f.write(pad_bytes)


def write_terrain_bmp(
    terrain_map: np.ndarray,
    output_dir: str,
) -> None:
    """
    写入 8 位索引色 terrain.bmp。
    直接从原版复制文件头+调色板，确保格式完全一致（255色, offset=1074）。
    """
    from data.constants import DEFAULT_HOI4_PATH

    map_dir = os.path.join(output_dir, "map")
    os.makedirs(map_dir, exist_ok=True)
    file_path = os.path.join(map_dir, "terrain.bmp")

    row_bytes = MAP_WIDTH
    padding = (4 - (row_bytes % 4)) % 4

    # 原版 terrain.bmp: ncolors=255, offset=1074
    # 策略：从原版只读调色板，自己生成正确的文件头（避免文件大小不匹配）
    n_colors = 255
    palette_size = n_colors * 4
    pixel_data_size = (row_bytes + padding) * MAP_HEIGHT
    pixel_offset = 14 + 40 + palette_size
    file_size = pixel_offset + pixel_data_size

    # 尝试从原版读调色板
    vanilla_terrain = os.path.join(DEFAULT_HOI4_PATH, "map", "terrain.bmp")
    vanilla_palette = None
    if os.path.exists(vanilla_terrain):
        with open(vanilla_terrain, "rb") as vf:
            vf.read(10)
            v_offset = struct.unpack("<I", vf.read(4))[0]
            vf.seek(14 + 40)  # 跳过文件头和信息头，直接读调色板
            vanilla_palette = vf.read(n_colors * 4)

    with open(file_path, "wb") as f:
        # 自己生成正确的文件头（文件大小精确匹配）
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", pixel_offset))
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<i", MAP_WIDTH))
        f.write(struct.pack("<i", MAP_HEIGHT))
        f.write(struct.pack("<HH", 1, 8))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pixel_data_size))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<I", n_colors))
        f.write(struct.pack("<I", n_colors))

        # 调色板：优先用原版，否则自己生成
        if vanilla_palette and len(vanilla_palette) == n_colors * 4:
            f.write(vanilla_palette)
        else:
            from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX
            palette = [(0, 0, 0)] * n_colors
            for terrain_name, index in TERRAIN_PALETTE_INDEX.items():
                if index < n_colors:
                    t = TERRAIN_TYPES[terrain_name]
                    palette[index] = t.color
            for r, g, b in palette:
                f.write(struct.pack("BBBB", b, g, r, 0))

        # 像素数据
        pad_bytes = b"\x00" * padding
        for y in range(MAP_HEIGHT - 1, -1, -1):
            f.write(terrain_map[y, :].tobytes())
            if padding:
                f.write(pad_bytes)


def write_rivers_bmp(output_dir: str, river_map: np.ndarray | None = None) -> None:
    """
    写入 rivers.bmp — 8 位索引色 BMP。
    如果 river_map 不为 None，使用实际河流数据；否则生成全白空白文件。
    """
    from core.river_manager import RIVER_PALETTE

    map_dir = os.path.join(output_dir, "map")
    os.makedirs(map_dir, exist_ok=True)
    file_path = os.path.join(map_dir, "rivers.bmp")

    row_bytes = MAP_WIDTH
    padding = (4 - (row_bytes % 4)) % 4
    padded_row_bytes = row_bytes + padding
    palette_size = 256 * 4
    pixel_data_size = padded_row_bytes * MAP_HEIGHT
    pixel_offset = 14 + 40 + palette_size
    file_size = pixel_offset + pixel_data_size

    with open(file_path, "wb") as f:
        # BMP 文件头
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", pixel_offset))

        # BITMAPINFOHEADER
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<i", MAP_WIDTH))
        f.write(struct.pack("<i", MAP_HEIGHT))
        f.write(struct.pack("<HH", 1, 8))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pixel_data_size))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<I", 0))  # ncolors=0（原版格式）
        f.write(struct.pack("<I", 0))

        # 调色板（256 entries, BGRA）
        for i in range(256):
            if i in RIVER_PALETTE:
                r, g, b = RIVER_PALETTE[i]
                f.write(struct.pack("BBBB", b, g, r, 0))
            else:
                # 未定义的索引用白色
                f.write(struct.pack("BBBB", 255, 255, 255, 0))

        # 像素数据（bottom-up）
        pad_bytes = b"\x00" * padding
        if river_map is not None:
            for y in range(MAP_HEIGHT - 1, -1, -1):
                f.write(river_map[y].tobytes())
                if padding:
                    f.write(pad_bytes)
        else:
            # 索引 255 = 陆地无河流背景（白色）
            empty_row = b"\xff" * MAP_WIDTH
            for _ in range(MAP_HEIGHT):
                f.write(empty_row)
                if padding:
                    f.write(pad_bytes)


def write_trees_bmp(output_dir: str) -> None:
    """
    写入空白 trees.bmp。
    原版 trees.bmp 尺寸是 1650×600（不是地图尺寸 5632×2048！）
    8 位调色板 BMP，像素值 = 树模型索引（0 = 无树，255 = 未定义）。
    【关键】必须填 0（无树），不能填 255 —— 否则 HOI4 为每个像素查找
    mapobject_255 模型失败，graphics.log 刷屏 "mapobject_255 failed to load"
    并在进入游戏时崩溃。
    """
    # 原版实测: trees.bmp = 1650x600, 8bit, ncolors=0, offset=1078
    TREE_W = 1650
    TREE_H = 600

    map_dir = os.path.join(output_dir, "map")
    os.makedirs(map_dir, exist_ok=True)
    file_path = os.path.join(map_dir, "trees.bmp")

    row_bytes = TREE_W
    padding = (4 - (row_bytes % 4)) % 4
    padded_row_bytes = row_bytes + padding
    palette_size = 256 * 4
    pixel_data_size = padded_row_bytes * TREE_H
    pixel_offset = 14 + 40 + palette_size
    file_size = pixel_offset + pixel_data_size

    with open(file_path, "wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", pixel_offset))

        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<i", TREE_W))
        f.write(struct.pack("<i", TREE_H))
        f.write(struct.pack("<HH", 1, 8))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pixel_data_size))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<I", 0))  # ncolors=0（原版格式）
        f.write(struct.pack("<I", 0))

        for i in range(256):
            f.write(struct.pack("BBBB", i, i, i, 0))

        pad_bytes = b"\x00" * padding
        empty_row = b"\x00" * TREE_W  # 0 = 无树（不能用 255）
        for _ in range(TREE_H):
            f.write(empty_row)
            if padding:
                f.write(pad_bytes)


def write_cities_bmp(output_dir: str) -> None:
    """写空白 cities.bmp（与地图同尺寸 8 位索引，全 0 = 无城市）。
    必须严格匹配 vanilla 格式：colors_used=255（不是256），调色板 255×4 字节，
    pixel_offset=14+40+1020=1074。否则 HOI4 报 "Missing cities mask bitmap" 并崩。
    """
    from data.constants import MAP_WIDTH, MAP_HEIGHT, DEFAULT_HOI4_PATH
    map_dir = os.path.join(output_dir, "map")
    os.makedirs(map_dir, exist_ok=True)
    file_path = os.path.join(map_dir, "cities.bmp")

    row_bytes = MAP_WIDTH
    padding = (4 - row_bytes % 4) % 4
    padded_row_bytes = row_bytes + padding
    n_colors = 255
    palette_size = n_colors * 4
    pixel_data_size = padded_row_bytes * MAP_HEIGHT
    pixel_offset = 14 + 40 + palette_size
    file_size = pixel_offset + pixel_data_size

    # 从 vanilla 读 255 色调色板
    vanilla_cities = os.path.join(DEFAULT_HOI4_PATH, "map", "cities.bmp")
    vanilla_palette = None
    if os.path.exists(vanilla_cities):
        with open(vanilla_cities, "rb") as vf:
            vf.seek(14 + 40)
            vanilla_palette = vf.read(n_colors * 4)

    with open(file_path, "wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<I", file_size))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", pixel_offset))
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<i", MAP_WIDTH))
        f.write(struct.pack("<i", MAP_HEIGHT))
        f.write(struct.pack("<HH", 1, 8))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pixel_data_size))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<i", 2835))
        f.write(struct.pack("<I", n_colors))
        f.write(struct.pack("<I", n_colors))
        if vanilla_palette and len(vanilla_palette) == palette_size:
            f.write(vanilla_palette)
        else:
            for i in range(n_colors):
                f.write(struct.pack("BBBB", i, i, i, 0))
        empty_row = b"\x00" * MAP_WIDTH
        pad_bytes = b"\x00" * padding
        for _ in range(MAP_HEIGHT):
            f.write(empty_row)
            if padding:
                f.write(pad_bytes)
