"""地形展示 MOD 生成器 — 展示全部 25 种 graphical terrain 变体

每种 graphical terrain 至少分配给一个省份，让玩家在游戏内能看到所有地形贴图。
输出目录: D:/Documents/Paradox Interactive/Hearts of Iron IV/mod/WorldTest/
"""
import os
import shutil
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from export.mod_exporter import export_full_mod
from data.constants import (
    MAP_WIDTH, MAP_HEIGHT, TILE_LAND, TILE_SEA,
    OCEAN_HEIGHT, SEA_LEVEL, LAND_BASE_HEIGHT,
)
from data.terrain_types import GRAPHICAL_TERRAINS, GRAPHICAL_TERRAIN_BY_INDEX
from domain.managers.state import StateManager
from domain.managers.country import CountryManager
from domain.generators.province import generate_provinces

MOD_DIR = "D:/Documents/Paradox Interactive/Hearts of Iron IV/mod/WorldTest"
MOD_NAME = "WorldTest"

# ─── 1. 清理旧 MOD ─────────────────────────────────────
if os.path.exists(MOD_DIR):
    shutil.rmtree(MOD_DIR)
os.makedirs(MOD_DIR, exist_ok=True)
outer = os.path.join(os.path.dirname(MOD_DIR), f"{MOD_NAME}.mod")
if os.path.exists(outer):
    os.remove(outer)

# ─── 2. 地形分类 ────────────────────────────────────────
# 分出可画陆地地形 (排除 ocean=15, lakes=14)
LAND_TERRAINS = [gt for gt in GRAPHICAL_TERRAINS if gt.type not in ("ocean", "lakes")]
OCEAN_IDX = 15
LAKE_IDX = 14

print(f"地图尺寸: {MAP_WIDTH}x{MAP_HEIGHT}")
print(f"陆地地形变体: {len(LAND_TERRAINS)} 种")
for gt in LAND_TERRAINS:
    print(f"  palette={gt.palette_index:2d}  type={gt.type:10s}  id={gt.id}  ({gt.name_cn})")

# ─── 3. 构建 tile_map — 横向铺满（无缝循环）──────────────
H, W = MAP_HEIGHT, MAP_WIDTH  # 1024 × 2048
tile_map = np.full((H, W), TILE_SEA, dtype=np.uint8)

# 横向铺满，上下留窄海洋带（HOI4 需要顶底有海）
# 上下留海洋带（HOI4 需要顶底有海洋省份），左右也留海洋做横向循环
# 跟 vanilla 一样：上下不留海洋，左右留 40px 海洋做横向循环
LAND_TOP = 0
LAND_BOT = H
LAND_LEFT = 40
LAND_RIGHT = W - 40
tile_map[LAND_TOP:LAND_BOT, LAND_LEFT:LAND_RIGHT] = TILE_LAND

print(f"\n大陆范围: y=[{LAND_TOP},{LAND_BOT}), x=[{LAND_LEFT},{LAND_RIGHT})")
land_pixels = int(np.sum(tile_map == TILE_LAND))
print(f"陆地像素: {land_pixels:,}")

# ─── 4. 构建 terrain_map — 垂直条带，每种地形一条 ────────
terrain_map = np.full((H, W), OCEAN_IDX, dtype=np.uint8)

num_land = len(LAND_TERRAINS)  # 23
land_width = LAND_RIGHT - LAND_LEFT
strip_w = land_width // num_land

for i, gt in enumerate(LAND_TERRAINS):
    x_start = LAND_LEFT + i * strip_w
    x_end = LAND_RIGHT if i == num_land - 1 else LAND_LEFT + (i + 1) * strip_w
    mask = tile_map[LAND_TOP:LAND_BOT, x_start:x_end] == TILE_LAND
    terrain_map[LAND_TOP:LAND_BOT, x_start:x_end][mask] = gt.palette_index
    print(f"  条带 {i:2d}: x=[{x_start},{x_end})  palette={gt.palette_index:2d}  {gt.name_cn}")

# ─── 5. 构建 height_map（依据地形类型）──────────────────
height_map = np.full((H, W), OCEAN_HEIGHT, dtype=np.uint8)
# 按 type 分配基础高度
TYPE_HEIGHT = {
    "plains":   120,
    "forest":   130,
    "hills":    160,
    "mountain": 220,
    "desert":   110,
    "marsh":    100,
    "jungle":   125,
    "urban":    125,
}
for gt in LAND_TERRAINS:
    base_h = TYPE_HEIGHT.get(gt.type, LAND_BASE_HEIGHT)
    height_map[terrain_map == gt.palette_index] = base_h

# 平滑高度过渡
from scipy.ndimage import gaussian_filter
height_map = gaussian_filter(height_map.astype(np.float32), sigma=6)
height_map = np.clip(height_map, 0, 255).astype(np.uint8)

# HOI4 要求顶底行高度 ≤ 海平面（vanilla 顶底行 ~89），否则加载崩溃
height_map[0, :] = np.minimum(height_map[0, :], SEA_LEVEL)
height_map[-1, :] = np.minimum(height_map[-1, :], SEA_LEVEL)

# ─── 6. 生成省份 (Voronoi) ───────────────────────────────
province_map, pcount = generate_provinces(tile_map, target_count=500)
print(f"\n省份数量: {pcount}")

# ─── 7. 自动分 State ─────────────────────────────────────
state_mgr = StateManager()
state_mgr.auto_split(province_map, tile_map, per_state=4)
print(f"State 数量: {len(state_mgr.states)}")

# ─── 8. 创建国家 ─────────────────────────────────────────
country_mgr = CountryManager()

# 3 个国家，按 x 坐标三等分
countries_cfg = [
    ("AAA", "Westland",  (60, 130, 220), "democratic"),
    ("BBB", "Centerion", (200, 40, 50),  "neutrality"),
    ("CCC", "Eastmark",  (40, 160, 90),  "fascism"),
]
for tag, name, color, party in countries_cfg:
    c = country_mgr.create_country(tag, name, color)
    c.ruling_party = party
    c.popularities = {"democratic": 25, "fascism": 25, "communism": 25, "neutrality": 25}
    c.popularities[party] = 55
    # 重新归一化到 100
    total = sum(c.popularities.values())
    for k in c.popularities:
        if k != party:
            c.popularities[k] = (100 - 55) // 3
    c.popularities[party] = 100 - sum(v for k, v in c.popularities.items() if k != party)


def state_centroid(state):
    """计算 state 的近似中心 (cy, cx)"""
    if not state.provinces:
        return (0, 0)
    pts = []
    for p in state.provinces[:3]:
        ys, xs = np.where(province_map == p)
        if len(ys):
            pts.append((float(ys.mean()), float(xs.mean())))
    if not pts:
        return (0, 0)
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


# 按 x 坐标分三段
x_third = W / 3
for sid, state in state_mgr.states.items():
    cy, cx = state_centroid(state)
    if cx < x_third:
        tag = "AAA"
    elif cx < x_third * 2:
        tag = "BBB"
    else:
        tag = "CCC"
    country_mgr.assign_state(sid, tag)
    state.owner_tag = tag

# 设首都
for tag, c in country_mgr.countries.items():
    state_ids = country_mgr.get_states_of_country(tag)
    if state_ids:
        first_state = state_mgr.get_state(state_ids[0])
        if first_state and first_state.provinces:
            c.capital = first_state.provinces[0]

# 打印国家分布
print("\n=== 国家与领土 ===")
for tag, c in country_mgr.countries.items():
    sids = country_mgr.get_states_of_country(tag)
    print(f"  {tag} {c.name:12s} → {len(sids):3d} states  party={c.ruling_party}")

# ─── 9. 导出 MOD ─────────────────────────────────────────
export_full_mod(
    tile_map=tile_map,
    province_map=province_map,
    output_dir=MOD_DIR,
    mod_name=MOD_NAME,
    tag="AAA",
    state_mgr=state_mgr,
    country_mgr=country_mgr,
    terrain_map=terrain_map,
    height_map=height_map,
)

print(f"\n[OK] WorldTest MOD 已导出: {MOD_DIR}")
file_count = sum(len(files) for _, _, files in os.walk(MOD_DIR))
print(f"     总文件数: {file_count}")

# 验证每种地形都至少有省份使用
print("\n=== 地形覆盖检查 ===")
all_palette_indices = set()
for gt in GRAPHICAL_TERRAINS:
    all_palette_indices.add(gt.palette_index)

used_indices = set(np.unique(terrain_map))
missing = all_palette_indices - used_indices
if missing:
    print(f"  警告: 以下调色板索引未在地图中使用: {sorted(missing)}")
else:
    print(f"  全部 {len(all_palette_indices)} 种地形均已覆盖 (含 ocean/lakes)")

# 检查陆地地形
land_mask = tile_map == TILE_LAND
land_terrain_indices = set(np.unique(terrain_map[land_mask]))
land_expected = {gt.palette_index for gt in LAND_TERRAINS}
land_missing = land_expected - land_terrain_indices
if land_missing:
    print(f"  警告: 以下陆地地形未在陆地上使用: {sorted(land_missing)}")
else:
    print(f"  全部 {len(land_expected)} 种陆地地形均已覆盖")
