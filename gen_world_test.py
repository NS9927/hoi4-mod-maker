"""复杂测试世界生成器 — 3 大陆 + 6 地形 + 5 国家 + 民族精神

输出 D:/Documents/Paradox.../mod/WorldTest，与 TestMOD 并存。
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
from data.terrain_types import TERRAIN_PALETTE_INDEX
from domain.managers.state import StateManager
from domain.managers.country import CountryManager, NationalSpirit

MOD_DIR = "D:/Documents/Paradox Interactive/Hearts of Iron IV/mod/WorldTest"
MOD_NAME = "WorldTest"

# ─── 1. 清理旧 MOD ─────────────────────────────────────
if os.path.exists(MOD_DIR):
    shutil.rmtree(MOD_DIR)
os.makedirs(MOD_DIR, exist_ok=True)
outer = os.path.join(os.path.dirname(MOD_DIR), f"{MOD_NAME}.mod")
if os.path.exists(outer):
    os.remove(outer)

# ─── 2. 构建复杂 tile_map（多大陆 + 岛屿）───────────────
H, W = MAP_HEIGHT, MAP_WIDTH  # 1024 × 2048
tile_map = np.full((H, W), TILE_SEA, dtype=np.uint8)

# 北方大陆 Boreas（寒冷山地）：y=80..380, x=200..900
tile_map[80:380, 200:900] = TILE_LAND
# 中央大陆 Aurelia（核心平原）：y=350..680, x=300..1500
tile_map[350:680, 300:1500] = TILE_LAND
# 北中两陆地有少量重叠 → 两块连成一片大陆

# 南方大岛 Crimsonia（丛林）：y=720..920, x=550..1300
tile_map[720:920, 550:1300] = TILE_LAND

# 西部岛 Estoria：y=480..680, x=50..220
tile_map[480:680, 50:220] = TILE_LAND

# 东部岛 Drakonia：y=200..500, x=1700..1920
tile_map[200:500, 1700:1920] = TILE_LAND

# ─── 3. 构建 terrain_map（地形分布）──────────────────────
PI = TERRAIN_PALETTE_INDEX
terrain_map = np.full((H, W), PI["ocean"], dtype=np.uint8)
terrain_map[tile_map == TILE_LAND] = PI["plains"]  # 默认陆地=平原

# 北方 Boreas：山地 + 森林
terrain_map[100:200, 250:850] = PI["mountain"]    # 北部主山脉
terrain_map[200:280, 250:850][tile_map[200:280, 250:850] == TILE_LAND] = PI["hills"]
terrain_map[280:380, 300:850][tile_map[280:380, 300:850] == TILE_LAND] = PI["forest"]

# Aurelia 中央：plains + hills + 一些 forest + 沙漠
terrain_map[400:500, 600:1000][tile_map[400:500, 600:1000] == TILE_LAND] = PI["hills"]
terrain_map[500:600, 350:600][tile_map[500:600, 350:600] == TILE_LAND] = PI["forest"]
terrain_map[450:600, 1100:1500][tile_map[450:600, 1100:1500] == TILE_LAND] = PI["desert"]

# Crimsonia 南方：jungle + marsh
terrain_map[720:920, 550:1300][tile_map[720:920, 550:1300] == TILE_LAND] = PI["jungle"]
terrain_map[820:900, 700:900][tile_map[820:900, 700:900] == TILE_LAND] = PI["marsh"]

# Estoria 西岛：forest
terrain_map[480:680, 50:220][tile_map[480:680, 50:220] == TILE_LAND] = PI["forest"]

# Drakonia 东岛：mountain + plains
terrain_map[200:350, 1700:1920][tile_map[200:350, 1700:1920] == TILE_LAND] = PI["mountain"]
terrain_map[350:500, 1700:1920][tile_map[350:500, 1700:1920] == TILE_LAND] = PI["hills"]

# ─── 4. 构建 height_map（依地形）─────────────────────────
height_map = np.full((H, W), OCEAN_HEIGHT, dtype=np.uint8)
height_map[tile_map == TILE_LAND] = LAND_BASE_HEIGHT
height_map[terrain_map == PI["hills"]] = 150
height_map[terrain_map == PI["forest"]] = 130
height_map[terrain_map == PI["desert"]] = 115
height_map[terrain_map == PI["jungle"]] = 125
height_map[terrain_map == PI["marsh"]] = 100
height_map[terrain_map == PI["mountain"]] = 220

# ─── 5. 构建省份图（Voronoi，避免 X-crossing）─────────
# 之前的网格法每个角 4 省相接 = X-crossing 噩梦, 修完还会产生 1 像素碎片.
# Voronoi 天然无 X-crossing.
from domain.generators.province import generate_provinces
province_map, pcount = generate_provinces(tile_map, target_count=500)
print(f"省份数量: {pcount}")

# ─── 6. 自动分 State ─────────────────────────────────────
state_mgr = StateManager()
state_mgr.auto_split(province_map, tile_map, per_state=4)
print(f"State 数量: {len(state_mgr.states)}")

# 决定每个 State 属于哪个国家（按地理中心）
def state_centroid(state):
    """计算 state 的近似中心 (cy, cx)"""
    if not state.provinces:
        return (0, 0)
    pts = []
    for p in state.provinces[:3]:  # 取前 3 省加速
        ys, xs = np.where(province_map == p)
        if len(ys):
            pts.append((float(ys.mean()), float(xs.mean())))
    if not pts:
        return (0, 0)
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

# ─── 7. 创建 5 个国家 + 民族精神 ────────────────────────
country_mgr = CountryManager()

# AAA Aurelia — 中央平原大国，民主，蓝色
aurelia = country_mgr.create_country("AAA", "Aurelia", (60, 130, 220))
aurelia.ruling_party = "democratic"
aurelia.popularities = {"democratic": 65, "fascism": 10, "communism": 10, "neutrality": 15}
aurelia.national_spirits = [
    NationalSpirit(
        id="AAA_breadbasket_of_the_world",
        name="世界粮仓",
        desc="Aurelia 广袤的平原养育着无数人民。",
        modifiers={
            "consumer_goods_factor": -0.05,
            "stability_factor": 0.10,
            "monthly_population": 0.10,
        },
    ),
    NationalSpirit(
        id="AAA_central_democracy",
        name="共和的灯塔",
        desc="Aurelian 民主制度照耀着整个已知世界。",
        modifiers={
            "political_power_gain": 0.15,
            "research_speed_factor": 0.05,
        },
    ),
]

# BBB Boreas — 北方山地寒国，中立，白色
boreas = country_mgr.create_country("BBB", "Boreas", (210, 220, 230))
boreas.ruling_party = "neutrality"
boreas.popularities = {"democratic": 15, "fascism": 5, "communism": 5, "neutrality": 75}
boreas.national_spirits = [
    NationalSpirit(
        id="BBB_mountain_fortress",
        name="山地堡垒",
        desc="敌人在 Boreas 的雪山前望而却步。",
        modifiers={
            "army_core_defence_factor": 0.20,
            "winter_attrition_factor": -0.30,
            "supply_consumption_factor": 0.05,
        },
        picture="generic_morale_bonus",
    ),
]

# CCC Crimsonia — 南方丛林革命国，共产主义，红色
crimsonia = country_mgr.create_country("CCC", "Crimsonia", (200, 40, 50))
crimsonia.ruling_party = "communism"
crimsonia.popularities = {"democratic": 5, "fascism": 5, "communism": 75, "neutrality": 15}
crimsonia.national_spirits = [
    NationalSpirit(
        id="CCC_revolutionary_fervor",
        name="革命的烈火",
        desc="人民的怒火席卷了 Crimsonia 的丛林。",
        modifiers={
            "war_support_factor": 0.20,
            "army_morale_factor": 0.15,
            "production_speed_buildings_factor": 0.10,
        },
    ),
    NationalSpirit(
        id="CCC_jungle_warfare",
        name="丛林战大师",
        desc="Crimsonian 战士与丛林融为一体。",
        modifiers={
            "jungle_attack_factor": 0.20,
            "jungle_defence_factor": 0.20,
        },
        picture="generic_acquire_tech",
    ),
]

# DDD Drakonia — 东岛山地军国，法西斯，黑色
drakonia = country_mgr.create_country("DDD", "Drakonia", (40, 40, 50))
drakonia.ruling_party = "fascism"
drakonia.popularities = {"democratic": 5, "fascism": 75, "communism": 5, "neutrality": 15}
drakonia.national_spirits = [
    NationalSpirit(
        id="DDD_warrior_culture",
        name="尚武民族",
        desc="Drakonia 的孩子从小就握剑而生。",
        modifiers={
            "conscription": 0.025,
            "army_attack_factor": 0.10,
            "training_time_factor": -0.10,
        },
    ),
]

# EEE Estoria — 西岛森林海洋国，中立，绿色
estoria = country_mgr.create_country("EEE", "Estoria", (60, 160, 90))
estoria.ruling_party = "neutrality"
estoria.popularities = {"democratic": 30, "fascism": 5, "communism": 5, "neutrality": 60}
estoria.national_spirits = [
    NationalSpirit(
        id="EEE_seafaring_tradition",
        name="航海传统",
        desc="Estoria 的木船曾远航至世界尽头。",
        modifiers={
            "navy_max_range_factor": 0.15,
            "naval_speed_factor": 0.10,
            "production_speed_dockyard_factor": 0.10,
        },
        picture="generic_navy_bonus",
    ),
]

# ─── 8. 把 state 按地理位置分配给国家 ────────────────────
def assign_country_by_position(cy, cx):
    # 北方 (y<350) 偏左 → BBB
    if cy < 350 and cx < 1000:
        return "BBB"
    # 东岛 (x>1600) → DDD
    if cx > 1600:
        return "DDD"
    # 西岛 (x<260) → EEE
    if cx < 260:
        return "EEE"
    # 南方 (y>700) → CCC
    if cy > 700:
        return "CCC"
    # 其他全部归 AAA
    return "AAA"

for sid, state in state_mgr.states.items():
    cy, cx = state_centroid(state)
    tag = assign_country_by_position(cy, cx)
    country_mgr.assign_state(sid, tag)
    state.owner_tag = tag

# 设首都：每个国家选自己第一个 state 的第一个省份作为 capital
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
    print(f"  {tag} {c.name:12s} → {len(sids):3d} states  party={c.ruling_party:12s}  spirits={len(c.national_spirits)}")

# ─── 9. 调用导出器 ────────────────────────────────────
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

print(f"\n[OK] WorldTest MOD: {MOD_DIR}")
file_count = sum(len(files) for _, _, files in os.walk(MOD_DIR))
print(f"     总文件数: {file_count}")
