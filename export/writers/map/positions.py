"""positions.txt — 省份单位/文字/城市/港口位置坐标."""
import os
import numpy as np
from data.constants import MAP_WIDTH, MAP_HEIGHT


def _safe_coord(pid, province_map, pid_count, sum_x, sum_y):
    """返回保证在该省份像素内的坐标 (cx, cy)。"""
    cx = sum_x[pid] / pid_count[pid]
    cy = sum_y[pid] / pid_count[pid]
    icy, icx = int(round(cy)), int(round(cx))
    h, w = province_map.shape
    if 0 <= icy < h and 0 <= icx < w and province_map[icy, icx] == pid:
        return cx, cy
    ys, xs = np.where(province_map == pid)
    if len(ys) == 0:
        return cx, cy
    mid = len(ys) // 2
    return float(xs[mid]), float(ys[mid])


def write_positions_txt(province_map: np.ndarray,
                        tile_map: np.ndarray,
                        output_dir: str,
                        pid_count=None, sum_x=None, sum_y=None) -> None:
    """为每个省份生成 positions.txt。
    如果传入预计算的 pid_count/sum_x/sum_y，直接使用；否则自行计算。
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    province_count = int(province_map.max())
    if province_count == 0:
        return

    # 使用预计算数据，或自行计算
    if pid_count is None:
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
        cx, cy = _safe_coord(pid, province_map, pid_count, sum_x, sum_y)
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
