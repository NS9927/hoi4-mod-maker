"""国旗 TGA 生成."""
import os


def write_country_flags(tags, output_dir, country_mgr=None):
    """为每个国家生成国旗文件。
    HOI4 需要 gfx/flags/TAG.tga 存在，否则UI报错（可能影响交互）。
    格式：82x52 TGA，24位BGR bottom-up。
    """
    import struct
    flag_dir = os.path.join(output_dir, "gfx", "flags")
    os.makedirs(flag_dir, exist_ok=True)
    # 中等、小旗也需要
    med_dir = os.path.join(flag_dir, "medium")
    small_dir = os.path.join(flag_dir, "small")
    os.makedirs(med_dir, exist_ok=True)
    os.makedirs(small_dir, exist_ok=True)

    # 一组默认颜色，按TAG哈希
    default_colors = [
        (200, 80, 80), (80, 80, 200), (80, 200, 80), (200, 200, 80),
        (200, 80, 200), (80, 200, 200), (150, 100, 50), (100, 150, 200),
    ]

    def make_tga(path, w, h, rgb):
        r, g, b = rgb
        # TGA 文件头（18字节） - 32bpp BGRA 格式（HOI4推荐，读取更快）
        header = struct.pack(
            "<BBBHHBHHHHBB",
            0,      # ID length
            0,      # Color map type
            2,      # Image type (uncompressed true color)
            0, 0, 0,    # Color map spec
            0, 0,       # X, Y origin
            w, h,       # Width, Height
            32,         # Pixel depth (32bpp)
            8,          # Image descriptor: 8 = 8bit alpha + bottom-up
        )
        # 像素数据：BGRA 顺序，A=255（不透明）
        pixel = bytes([b, g, r, 255]) * (w * h)
        with open(path, "wb") as f:
            f.write(header)
            f.write(pixel)

    ideologies = ["neutrality", "democratic", "fascism", "communism"]

    for i, tag in enumerate(tags):
        # 获取国家颜色
        if country_mgr and tag in country_mgr.countries:
            rgb = country_mgr.countries[tag].color
        else:
            rgb = default_colors[i % len(default_colors)]

        # 主国旗 82x52
        make_tga(os.path.join(flag_dir, f"{tag}.tga"), 82, 52, rgb)
        # 意识形态变体（HOI4 需要 TAG_ideology.tga）
        for ideo in ideologies:
            make_tga(os.path.join(flag_dir, f"{tag}_{ideo}.tga"), 82, 52, rgb)
        # 中等国旗 41x26
        make_tga(os.path.join(med_dir, f"{tag}.tga"), 41, 26, rgb)
        for ideo in ideologies:
            make_tga(os.path.join(med_dir, f"{tag}_{ideo}.tga"), 41, 26, rgb)
        # 小国旗 10x7
        make_tga(os.path.join(small_dir, f"{tag}.tga"), 10, 7, rgb)
        for ideo in ideologies:
            make_tga(os.path.join(small_dir, f"{tag}_{ideo}.tga"), 10, 7, rgb)

