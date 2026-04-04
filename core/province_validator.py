"""
省份验证器 — 检测 HOI4 省份地图中的各种问题
"""
import numpy as np
from collections import defaultdict

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_LAND, TILE_SEA, TILE_LAKE,
    MIN_PROVINCE_PIXELS,
)


def validate_provinces(
    tile_map: np.ndarray,
    province_map: np.ndarray,
) -> dict:
    """
    验证省份地图，检测所有可能导致 HOI4 崩溃的问题。

    返回:
        {
            "x_crossings": int,          # X型交叉数量
            "x_crossing_positions": list, # 交叉位置列表 [(y, x), ...]
            "too_small": int,             # 过小省份数量
            "too_small_ids": list,        # 过小省份ID列表
            "not_contiguous": int,        # 不连续省份数量
            "not_contiguous_ids": list,   # 不连续省份ID列表
            "coastal_mismatch": int,      # 沿海状态不一致数量
            "coastal_mismatch_ids": list, # 不一致的省份ID列表
        }
    """
    results = {
        "x_crossings": 0,
        "x_crossing_positions": [],
        "too_small": 0,
        "too_small_ids": [],
        "not_contiguous": 0,
        "not_contiguous_ids": [],
        "coastal_mismatch": 0,
        "coastal_mismatch_ids": [],
    }

    if province_map.max() == 0:
        return results

    # 1. X型交叉检测
    x_positions = detect_x_crossings(province_map)
    results["x_crossings"] = len(x_positions)
    results["x_crossing_positions"] = x_positions

    # 2. 过小省份检测
    small_ids = detect_small_provinces(province_map)
    results["too_small"] = len(small_ids)
    results["too_small_ids"] = small_ids

    # 3. 连续性检测
    non_contiguous = detect_non_contiguous(province_map)
    results["not_contiguous"] = len(non_contiguous)
    results["not_contiguous_ids"] = non_contiguous

    # 4. 沿海一致性检测
    coastal_issues = detect_coastal_mismatch(tile_map, province_map)
    results["coastal_mismatch"] = len(coastal_issues)
    results["coastal_mismatch_ids"] = coastal_issues

    return results


def detect_x_crossings(province_map: np.ndarray) -> list[tuple[int, int]]:
    """
    检测 X 型交叉：2×2 像素块中出现4种不同省份ID。
    HOI4 不允许这种情况，会导致崩溃。

    返回交叉位置列表 [(y, x), ...]，坐标是2×2块的左上角。
    """
    positions = []

    # 取2×2窗口的四个角
    tl = province_map[:-1, :-1]  # 左上
    tr_ = province_map[:-1, 1:]  # 右上
    bl = province_map[1:, :-1]   # 左下
    br = province_map[1:, 1:]    # 右下

    # 四个值互不相同的位置就是 X 型交叉
    # 用集合大小判断：如果4个值全不同，说明有交叉
    # 优化：先找出至少有3种不同值的位置，再精确判断
    diff1 = tl != tr_
    diff2 = tl != bl
    diff3 = tl != br
    diff4 = tr_ != bl
    diff5 = tr_ != br
    diff6 = bl != br

    # 6个两两比较都不同 → 4个值互不相同
    all_different = diff1 & diff2 & diff3 & diff4 & diff5 & diff6

    ys, xs = np.where(all_different)
    positions = [(int(y), int(x)) for y, x in zip(ys, xs)]

    return positions


def fix_x_crossings(province_map: np.ndarray) -> int:
    """
    修复 X 型交叉：将2×2块中右下角的像素改为左上角的省份ID。

    返回修复数量。
    """
    fixed = 0
    positions = detect_x_crossings(province_map)
    for y, x in positions:
        # 将右下角改为与左上角相同
        province_map[y + 1, x + 1] = province_map[y, x]
        fixed += 1
    return fixed


def detect_small_provinces(
    province_map: np.ndarray,
    min_pixels: int = MIN_PROVINCE_PIXELS,
) -> list[int]:
    """
    检测像素数少于 min_pixels 的省份。
    返回过小省份ID列表。
    """
    if province_map.max() == 0:
        return []

    # 统计每个省份的像素数
    ids, counts = np.unique(province_map, return_counts=True)
    small = []
    for pid, count in zip(ids, counts):
        if pid > 0 and count < min_pixels:
            small.append(int(pid))
    return small


def detect_non_contiguous(province_map: np.ndarray) -> list[int]:
    """
    检测不连续的省份 — 用整图一次性标记连通分量，O(n)复杂度。
    不再逐省份扫描，而是对整张地图做一次 label，再比较省份ID和连通分量。
    """
    from scipy.ndimage import label

    max_pid = int(province_map.max())
    if max_pid == 0:
        return []

    # 对整张图做连通分量标记（相邻且值相同的像素归为一组）
    # structure: 4-connectivity
    struct = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int32)
    labeled, num_features = label(province_map, structure=struct)

    # 如果省份是连续的，同一个pid应该只对应1个连通分量
    # 用 bincount 统计每个pid对应了多少个不同的label
    flat_pm = province_map.ravel()
    flat_lb = labeled.ravel()

    # 对每个pid，找它对应的所有label值，看是否>1个
    # 优化：构建 pid → set(labels) 的映射
    # 先用 pandas-free 方法：按pid分组统计唯一label数
    pid_label_pairs = flat_pm.astype(np.int64) * (num_features + 1) + flat_lb
    unique_pairs = np.unique(pid_label_pairs)

    # 从 pair 还原 pid
    pair_pids = unique_pairs // (num_features + 1)
    # 统计每个pid出现了几个不同的pair（= 几个不同的label）
    pid_counts = np.bincount(pair_pids.astype(np.intp), minlength=max_pid + 1)

    non_contiguous = []
    for pid in range(1, max_pid + 1):
        if pid_counts[pid] > 1:
            non_contiguous.append(pid)

    return non_contiguous


def detect_coastal_mismatch(
    tile_map: np.ndarray,
    province_map: np.ndarray,
) -> list[int]:
    """
    检测沿海状态不一致的省份。
    规则：如果一个 land 省份的任何像素与一个 sea 省份的像素相邻，
    则该 land 省份必须标记为 coastal=true。

    返回应该标记为 coastal 但当前可能未标记的省份ID列表。
    （这里只检测哪些陆地省份是沿海的，供导出时使用）
    """
    coastal_provinces = set()

    # 陆地和海洋省份的 mask
    land_mask = tile_map == TILE_LAND
    sea_mask = (tile_map == TILE_SEA) | (tile_map == TILE_LAKE)

    # 检查每个陆地像素的4邻域是否有海洋像素
    # 上方
    coastal_up = land_mask[1:, :] & sea_mask[:-1, :]
    # 下方
    coastal_down = land_mask[:-1, :] & sea_mask[1:, :]
    # 左方
    coastal_left = land_mask[:, 1:] & sea_mask[:, :-1]
    # 右方
    coastal_right = land_mask[:, :-1] & sea_mask[:, 1:]

    # 收集沿海陆地像素对应的省份ID
    if np.any(coastal_up):
        ys, xs = np.where(coastal_up)
        for pid in np.unique(province_map[ys + 1, xs]):
            if pid > 0:
                coastal_provinces.add(int(pid))

    if np.any(coastal_down):
        ys, xs = np.where(coastal_down)
        for pid in np.unique(province_map[ys, xs]):
            if pid > 0:
                coastal_provinces.add(int(pid))

    if np.any(coastal_left):
        ys, xs = np.where(coastal_left)
        for pid in np.unique(province_map[ys, xs + 1]):
            if pid > 0:
                coastal_provinces.add(int(pid))

    if np.any(coastal_right):
        ys, xs = np.where(coastal_right)
        for pid in np.unique(province_map[ys, xs]):
            if pid > 0:
                coastal_provinces.add(int(pid))

    return sorted(coastal_provinces)


def get_coastal_provinces(
    tile_map: np.ndarray,
    province_map: np.ndarray,
) -> set[int]:
    """
    获取所有沿海陆地省份的ID集合。
    用于导出 definition.csv 时设置 coastal 字段。
    """
    return set(detect_coastal_mismatch(tile_map, province_map))
