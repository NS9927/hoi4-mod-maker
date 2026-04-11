"""从用户保存的 .hoi4proj 加载地图，补全缺失内容，导出可玩 MOD。

用法: python gen_from_project.py <项目路径>
"""
import os
import sys
import json
import zipfile
import shutil
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT, TILE_LAND, TILE_SEA, TILE_LAKE,
    OCEAN_HEIGHT, SEA_LEVEL, LAND_BASE_HEIGHT,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX
from domain.managers.state import StateManager
from domain.managers.country import CountryManager
from export.mod_exporter import export_full_mod

# ─── 配置 ───
PROJECT_PATH = sys.argv[1] if len(sys.argv) > 1 else \
    "C:/Users/Administrator.SKY-20180310BMB/Desktop/欧若拉/1.hoi4proj"
MOD_DIR = "D:/Documents/Paradox Interactive/Hearts of Iron IV/mod/WorldTest"
MOD_NAME = "WorldTest"

# ─── 1. 加载项目 ───
print(f"加载项目: {PROJECT_PATH}")
with zipfile.ZipFile(PROJECT_PATH) as z:
    tile_map = np.load(z.open('tile_map.npy'))
    province_map = np.load(z.open('province_map.npy'))
    terrain_map = np.load(z.open('terrain_map.npy'))
    height_map = np.load(z.open('height_map.npy'))
    river_map = np.load(z.open('river_map.npy'))
    states_data = json.load(z.open('states.json'))
    countries_data = json.load(z.open('countries.json'))

H, W = tile_map.shape
pcount = int(province_map.max())
land_pixels = int(np.sum(tile_map == TILE_LAND))
sea_pixels = int(np.sum(tile_map == TILE_SEA))
print(f"地图: {W}x{H}, 省份: {pcount}, 陆地: {land_pixels:,}, 海洋: {sea_pixels:,}")

# ─── 2. 自动生成地形（如果全是默认） ───
unique_terrain = np.unique(terrain_map)
print(f"地形索引: {unique_terrain.tolist()}")

# 修正：陆地上不应该有 ocean 地形，改为 plains
land_mask = tile_map == TILE_LAND
ocean_idx = TERRAIN_PALETTE_INDEX["ocean"]  # 15
plains_idx = TERRAIN_PALETTE_INDEX["plains"]  # 0
bad_terrain = land_mask & (terrain_map == ocean_idx)
bad_count = int(np.sum(bad_terrain))
if bad_count > 0:
    terrain_map[bad_terrain] = plains_idx
    print(f"修正: {bad_count:,} 个陆地像素的地形从 ocean 改为 plains")

# 修正：海洋上不应该有陆地地形
sea_mask = tile_map == TILE_SEA
sea_bad = sea_mask & (terrain_map != ocean_idx)
sea_bad_count = int(np.sum(sea_bad))
if sea_bad_count > 0:
    terrain_map[sea_bad] = ocean_idx
    print(f"修正: {sea_bad_count:,} 个海洋像素的地形改为 ocean")

# ─── 3. 自动生成高度图（如果全是默认） ───
land_mask = tile_map == TILE_LAND
if np.all(height_map[land_mask] == height_map[land_mask][0] if land_mask.any() else True):
    print("高度未调整，自动生成...")
    from services.terrain_service import auto_height
    height_map = auto_height(tile_map)
else:
    print("高度已调整")

# ─── 4. State 管理器 ───
state_mgr = StateManager()
if states_data.get('states'):
    state_mgr.from_dict(states_data)
    print(f"已有 State: {len(state_mgr.states)}")
else:
    print("没有 State，自动生成...")
    state_mgr.auto_split(province_map, tile_map, per_state=20)
    print(f"自动生成 State: {len(state_mgr.states)}")

# ─── 5. 国家 ───
country_mgr = CountryManager()
has_countries = bool(countries_data.get('countries', {}).get('countries'))
if has_countries:
    country_mgr.from_dict(countries_data)
    print(f"已有国家: {list(country_mgr.countries.keys())}")
else:
    print("没有国家，自动创建测试国家...")
    # 创建一个测试国家拥有所有陆地
    c = country_mgr.create_country("AAA", "Aurora", (60, 130, 220))
    c.ruling_party = "democratic"
    c.popularities = {"democratic": 60, "fascism": 10, "communism": 10, "neutrality": 20}

    # 所有 state 归 AAA
    for sid in state_mgr.states:
        country_mgr.assign_state(sid, "AAA")
        state = state_mgr.get_state(sid)
        if state:
            state.owner_tag = "AAA"

    # 设首都
    first_state = state_mgr.get_state(1)
    if first_state and first_state.provinces:
        c.capital = first_state.provinces[0]

    print(f"创建国家 AAA, {len(state_mgr.states)} states")

# ─── 6. 清理旧 MOD ───
if os.path.exists(MOD_DIR):
    shutil.rmtree(MOD_DIR)
os.makedirs(MOD_DIR, exist_ok=True)

# ─── 7. 导出 ───
print(f"\n导出到: {MOD_DIR}")
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

file_count = sum(len(files) for _, _, files in os.walk(MOD_DIR))
print(f"\n[OK] {MOD_NAME} 导出完成: {file_count} 个文件")
print("可以进游戏测试了！")
