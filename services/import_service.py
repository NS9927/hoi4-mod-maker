"""
导入MOD地图 — 从 HOI4 mod/vanilla 目录读取地图图层。

读取 map/ 子目录下的:
- provinces.bmp (24-bit) → province_map + color→ID 映射
- definition.csv → tile_map (land/sea/lake) + provincial_terrain
- terrain.bmp (8-bit indexed) → terrain_map
- heightmap.bmp (8-bit grayscale) → height_map
- rivers.bmp (8-bit indexed) → river_map
"""

from __future__ import annotations

import csv
import os
from typing import Any

import numpy as np
from PIL import Image

from data.constants import TILE_LAND, TILE_SEA, TILE_LAKE


# definition.csv 类型名 → 内部常量
_TYPE_MAP = {
    "land": TILE_LAND,
    "sea": TILE_SEA,
    "lake": TILE_LAKE,
}


def validate_mod_directory(mod_dir: str) -> list[str]:
    """检查目录结构，返回缺失文件列表。"""
    required = ["map/provinces.bmp"]
    optional = [
        "map/definition.csv",
        "map/terrain.bmp",
        "map/heightmap.bmp",
        "map/rivers.bmp",
    ]
    missing = []
    for f in required:
        path = os.path.join(mod_dir, f.replace("/", os.sep))
        if not os.path.isfile(path):
            missing.append(f)
    return missing


def _parse_definition_csv(csv_path: str) -> dict[tuple[int, int, int], dict[str, Any]]:
    """解析 definition.csv，返回 {(R,G,B): {id, type, terrain}} 映射。

    格式: ID;R;G;B;type;coastal;terrain;continent
    """
    color_info: dict[tuple[int, int, int], dict[str, Any]] = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if len(row) < 5:
                continue
            try:
                pid = int(row[0])
                r, g, b = int(row[1]), int(row[2]), int(row[3])
                ptype = row[4].strip().lower()
                terrain = row[6].strip() if len(row) > 6 else ""
            except (ValueError, IndexError):
                continue
            if pid <= 0:
                continue
            color_info[(r, g, b)] = {
                "id": pid,
                "type": ptype,
                "terrain": terrain,
            }
    return color_info


def _read_provinces_bmp(bmp_path: str) -> tuple[np.ndarray, dict[tuple[int, int, int], int]]:
    """读取 provinces.bmp，返回 (rgb_array[H,W,3], color→auto_id 映射)。

    PIL 会自动处理 BMP 的 bottom-up 行序。
    """
    img = Image.open(bmp_path).convert("RGB")
    rgb = np.array(img, dtype=np.uint8)
    # 扫描唯一颜色，跳过 (0,0,0)
    h, w = rgb.shape[:2]
    flat = rgb.reshape(-1, 3)
    # 用结构化数组做 unique
    flat_view = flat.view(np.dtype([("r", np.uint8), ("g", np.uint8), ("b", np.uint8)]))
    unique_colors = np.unique(flat_view)

    auto_map: dict[tuple[int, int, int], int] = {}
    next_id = 1
    for c in unique_colors:
        r, g, b = int(c["r"]), int(c["g"]), int(c["b"])
        if (r, g, b) == (0, 0, 0):
            continue
        auto_map[(r, g, b)] = next_id
        next_id += 1

    return rgb, auto_map


def _build_province_map(
    rgb: np.ndarray,
    color_to_id: dict[tuple[int, int, int], int],
) -> np.ndarray:
    """从 RGB 数组和颜色映射构建 province_map (int32)。"""
    h, w = rgb.shape[:2]
    province_map = np.zeros((h, w), dtype=np.int32)

    # 构建查找表：把 RGB 编码为 24-bit int 做高效映射
    flat = rgb.reshape(-1, 3).astype(np.int32)
    keys = (flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]

    # 构建 key→id 字典
    key_to_id: dict[int, int] = {}
    for (r, g, b), pid in color_to_id.items():
        key_to_id[(r << 16) | (g << 8) | b] = pid

    # 向量化查找
    unique_keys, inverse = np.unique(keys, return_inverse=True)
    id_array = np.zeros(len(unique_keys), dtype=np.int32)
    for i, k in enumerate(unique_keys):
        id_array[i] = key_to_id.get(int(k), 0)

    province_map = id_array[inverse].reshape(h, w)
    return province_map


def _build_tile_map(
    province_map: np.ndarray,
    color_to_id: dict[tuple[int, int, int], int],
    definition_info: dict[tuple[int, int, int], dict[str, Any]] | None,
) -> tuple[np.ndarray, dict[int, str]]:
    """构建 tile_map (land/sea/lake) 和 provincial_terrain 字典。

    如果有 definition.csv，用它的 type 列；否则全部默认为 land。
    """
    h, w = province_map.shape
    tile_map = np.full((h, w), TILE_LAND, dtype=np.uint8)
    provincial_terrain: dict[int, str] = {}

    if definition_info is None:
        return tile_map, provincial_terrain

    # 构建 province_id → (tile_type, terrain)
    id_to_type: dict[int, int] = {}
    for color, info in definition_info.items():
        pid = info["id"]
        ptype = _TYPE_MAP.get(info["type"], TILE_LAND)
        id_to_type[pid] = ptype
        if info.get("terrain"):
            provincial_terrain[pid] = info["terrain"]

    # 向量化：对每个省份 ID 设置 tile_type
    unique_ids = np.unique(province_map)
    for pid in unique_ids:
        pid_int = int(pid)
        if pid_int <= 0:
            continue
        ttype = id_to_type.get(pid_int, TILE_LAND)
        if ttype != TILE_LAND:
            tile_map[province_map == pid_int] = ttype

    return tile_map, provincial_terrain


def _read_indexed_bmp(bmp_path: str) -> np.ndarray:
    """读取 8-bit 索引 BMP，返回调色板索引数组 (uint8)。"""
    img = Image.open(bmp_path)
    if img.mode == "P":
        # 直接获取调色板索引
        data = np.array(img, dtype=np.uint8)
    elif img.mode == "L":
        # 灰度图直接用
        data = np.array(img, dtype=np.uint8)
    else:
        # 转灰度作为 fallback
        data = np.array(img.convert("L"), dtype=np.uint8)
    return data


def _extract_block_value(text: str, key: str) -> str:
    """从 Clausewitz 脚本里提取 key={...} 或 key=value。"""
    import re
    # key = { ... }
    m = re.search(rf'{key}\s*=\s*\{{([^}}]*)\}}', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # key = value
    m = re.search(rf'{key}\s*=\s*(\S+)', text)
    if m:
        return m.group(1).strip().strip('"')
    return ""


def _parse_state_file(path: str) -> dict | None:
    """解析 history/states/*.txt，返回 {id, name, provinces, owner, manpower, category}。"""
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        text = f.read()

    sid_str = _extract_block_value(text, "id")
    if not sid_str:
        return None
    try:
        sid = int(sid_str)
    except ValueError:
        return None

    name = _extract_block_value(text, "name") or f"STATE_{sid}"
    owner = _extract_block_value(text, "owner") or ""
    manpower_str = _extract_block_value(text, "manpower")
    manpower = int(manpower_str) if manpower_str.isdigit() else 100000
    category = _extract_block_value(text, "state_category") or "town"

    # 省份列表
    provinces_str = _extract_block_value(text, "provinces")
    province_ids = []
    for token in provinces_str.split():
        try:
            province_ids.append(int(token))
        except ValueError:
            pass

    if not province_ids:
        return None

    return {
        "id": sid,
        "name": name,
        "provinces": province_ids,
        "owner": owner,
        "manpower": manpower,
        "category": category,
    }


def _parse_strategic_region_file(path: str) -> dict | None:
    """解析 map/strategicregions/*.txt，返回 {id, name, provinces}。"""
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        text = f.read()

    rid_str = _extract_block_value(text, "id")
    if not rid_str:
        return None
    try:
        rid = int(rid_str)
    except ValueError:
        return None

    name = _extract_block_value(text, "name") or f"STRATEGICREGION_{rid}"
    provinces_str = _extract_block_value(text, "provinces")
    province_ids = []
    for token in provinces_str.split():
        try:
            province_ids.append(int(token))
        except ValueError:
            pass

    return {
        "id": rid,
        "name": name,
        "provinces": province_ids,
    }


def import_mod_map(mod_dir: str) -> dict[str, Any]:
    """从 HOI4 mod/vanilla 目录导入地图图层。

    参数:
        mod_dir: 包含 map/ 子目录的根目录

    返回:
        {
            "width": int,
            "height": int,
            "tile_map": np.ndarray,
            "province_map": np.ndarray,
            "terrain_map": np.ndarray,
            "height_map": np.ndarray,
            "river_map": np.ndarray,
            "province_count": int,
            "provincial_terrain": dict[int, str],
            "warnings": list[str],
        }

    异常:
        FileNotFoundError: provinces.bmp 不存在
        ValueError: BMP 格式错误
    """
    map_dir = os.path.join(mod_dir, "map")
    provinces_path = os.path.join(map_dir, "provinces.bmp")

    if not os.path.isfile(provinces_path):
        raise FileNotFoundError(f"provinces.bmp 不存在: {provinces_path}")

    warnings: list[str] = []

    # 1. 读取 provinces.bmp
    rgb, auto_color_map = _read_provinces_bmp(provinces_path)
    h, w = rgb.shape[:2]

    # 2. 读取 definition.csv (可选)
    definition_path = os.path.join(map_dir, "definition.csv")
    definition_info: dict[tuple[int, int, int], dict[str, Any]] | None = None
    if os.path.isfile(definition_path):
        definition_info = _parse_definition_csv(definition_path)
        # 用 definition.csv 的 ID 映射替代自动分配
        csv_color_map: dict[tuple[int, int, int], int] = {}
        for color, info in definition_info.items():
            csv_color_map[color] = info["id"]
        # 检查 provinces.bmp 中有没有 definition.csv 没覆盖的颜色
        missing_colors = set(auto_color_map.keys()) - set(csv_color_map.keys())
        if missing_colors:
            warnings.append(
                f"provinces.bmp 中有 {len(missing_colors)} 种颜色不在 definition.csv 中，已自动分配 ID"
            )
            # 为缺失颜色分配 ID (从 definition.csv 最大 ID 之后开始)
            max_csv_id = max(csv_color_map.values()) if csv_color_map else 0
            next_id = max_csv_id + 1
            for color in sorted(missing_colors):
                csv_color_map[color] = next_id
                next_id += 1
        color_to_id = csv_color_map
    else:
        color_to_id = auto_color_map
        warnings.append("未找到 definition.csv，省份类型全部设为陆地")

    # 3. 构建 province_map
    province_map = _build_province_map(rgb, color_to_id)
    province_count = int(province_map.max())

    # 4. 构建 tile_map + provincial_terrain
    tile_map, provincial_terrain = _build_tile_map(
        province_map, color_to_id, definition_info
    )

    # 5. 读取 terrain.bmp (可选)
    terrain_path = os.path.join(map_dir, "terrain.bmp")
    if os.path.isfile(terrain_path):
        terrain_map = _read_indexed_bmp(terrain_path)
        if terrain_map.shape != (h, w):
            warnings.append(
                f"terrain.bmp 尺寸 {terrain_map.shape[1]}x{terrain_map.shape[0]} "
                f"与 provinces.bmp {w}x{h} 不匹配，已缩放"
            )
            img = Image.fromarray(terrain_map)
            img = img.resize((w, h), Image.Resampling.NEAREST)
            terrain_map = np.array(img, dtype=np.uint8)
    else:
        terrain_map = np.zeros((h, w), dtype=np.uint8)
        warnings.append("未找到 terrain.bmp，地形图层设为空")

    # 6. 读取 heightmap.bmp (可选)
    heightmap_path = os.path.join(map_dir, "heightmap.bmp")
    if os.path.isfile(heightmap_path):
        height_map = _read_indexed_bmp(heightmap_path)
        if height_map.shape != (h, w):
            warnings.append(
                f"heightmap.bmp 尺寸 {height_map.shape[1]}x{height_map.shape[0]} "
                f"与 provinces.bmp {w}x{h} 不匹配，已缩放"
            )
            img = Image.fromarray(height_map)
            img = img.resize((w, h), Image.Resampling.NEAREST)
            height_map = np.array(img, dtype=np.uint8)
    else:
        height_map = np.full((h, w), 40, dtype=np.uint8)
        warnings.append("未找到 heightmap.bmp，高度图层设为默认值")

    # 7. 读取 rivers.bmp (可选)
    rivers_path = os.path.join(map_dir, "rivers.bmp")
    if os.path.isfile(rivers_path):
        river_map = _read_indexed_bmp(rivers_path)
        if river_map.shape != (h, w):
            warnings.append(
                f"rivers.bmp 尺寸 {river_map.shape[1]}x{river_map.shape[0]} "
                f"与 provinces.bmp {w}x{h} 不匹配，已缩放"
            )
            img = Image.fromarray(river_map)
            img = img.resize((w, h), Image.Resampling.NEAREST)
            river_map = np.array(img, dtype=np.uint8)
    else:
        river_map = np.full((h, w), 255, dtype=np.uint8)
        warnings.append("未找到 rivers.bmp，河流图层设为空")

    # 8. 读取 states (可选)
    states_dir = os.path.join(mod_dir, "history", "states")
    states_data: list[dict] = []
    if os.path.isdir(states_dir):
        for fn in sorted(os.listdir(states_dir)):
            if not fn.endswith(".txt"):
                continue
            try:
                sd = _parse_state_file(os.path.join(states_dir, fn))
                if sd:
                    states_data.append(sd)
            except Exception:
                pass
        if states_data:
            warnings.append(f"读取了 {len(states_data)} 个 State 文件")
    else:
        warnings.append("未找到 history/states/ 目录")

    # 9. 读取 strategic regions (可选)
    sr_dir = os.path.join(mod_dir, "map", "strategicregions")
    sr_data: list[dict] = []
    if os.path.isdir(sr_dir):
        for fn in sorted(os.listdir(sr_dir)):
            if not fn.endswith(".txt"):
                continue
            try:
                rd = _parse_strategic_region_file(os.path.join(sr_dir, fn))
                if rd:
                    sr_data.append(rd)
            except Exception:
                pass
        if sr_data:
            warnings.append(f"读取了 {len(sr_data)} 个战略区域文件")
    else:
        warnings.append("未找到 map/strategicregions/ 目录")

    return {
        "width": w,
        "height": h,
        "tile_map": tile_map,
        "province_map": province_map,
        "terrain_map": terrain_map,
        "height_map": height_map,
        "river_map": river_map,
        "province_count": province_count,
        "provincial_terrain": provincial_terrain,
        "states": states_data,
        "strategic_regions": sr_data,
        "warnings": warnings,
    }
