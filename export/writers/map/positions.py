"""positions.txt — 省份单位/文字/城市/港口位置坐标."""
import os
import numpy as np
from data.constants import MAP_WIDTH, MAP_HEIGHT


def write_positions_txt(province_map: np.ndarray,
                        tile_map: np.ndarray,
                        output_dir: str) -> None:
    """为每个省份生成 positions.txt，包含单位、文字、城市、港口的 3D 坐标。

    HOI4 格式 (vanilla):
        PROVINCE_ID={
            position={
                X 9.5 Z    # unit
                X 9.5 Z    # text
                X 9.5 Z    # city
                X 9.5 Z    # port
                X 9.5 Z    # text2
                X 9.5 Z    # city2
            }
            rotation={
                0.0 0.0 0.0 0.0 0.0 0.0
            }
            height={
                0.0 0.0 0.0 0.0 0.0 0.0
            }
        }

    坐标系: X = 像素列, Z = MAP_HEIGHT - 像素行 (从底部算), Y = 9.5 (海平面高度)
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    province_count = int(province_map.max())
    if province_count == 0:
        return

    # 向量化计算所有省份质心
    flat_pm = province_map.ravel()
    n = province_count + 1
    pid_count = np.bincount(flat_pm, minlength=n)
    ys_grid, xs_grid = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
    sum_y = np.bincount(flat_pm, weights=ys_grid.ravel().astype(np.float64), minlength=n)
    sum_x = np.bincount(flat_pm, weights=xs_grid.ravel().astype(np.float64), minlength=n)

    lines = []
    for pid in range(1, province_count + 1):
        if pid_count[pid] == 0:
            continue
        cx = sum_x[pid] / pid_count[pid]
        cy = sum_y[pid] / pid_count[pid]
        # 转换为 HOI4 坐标系: Z 从底部算
        hoi4_x = cx
        hoi4_z = MAP_HEIGHT - cy
        y = 9.500

        # 所有 6 个位置槽都用质心
        pos_line = f"{hoi4_x:.3f} {y:.3f} {hoi4_z:.3f}"
        positions = "\n\t\t".join([pos_line] * 6)
        rotations = " ".join(["0.000"] * 6)
        heights = " ".join(["0.000"] * 6)

        lines.append(
            f"{pid}={{\n"
            f"\tposition={{\n"
            f"\t\t{positions}\n"
            f"\t}}\n"
            f"\trotation={{\n"
            f"\t\t{rotations}\n"
            f"\t}}\n"
            f"\theight={{\n"
            f"\t\t{heights}\n"
            f"\t}}\n"
            f"}}"
        )

    # 用 binary 模式写入避免 Windows 上 \n → \r\n 自动转换
    with open(os.path.join(d, "positions.txt"), "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))
