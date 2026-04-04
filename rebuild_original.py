"""回滚到最初能进游戏的版本"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.ndimage import gaussian_filter, sobel

out = "D:/Documents/Paradox Interactive/Hearts of Iron IV/mod/RandomHoi4"
MAP_W, MAP_H = 5632, 2048
SEA_LEVEL = 95

# 创建地图
tile_map = np.full((MAP_H, MAP_W), 2, dtype=np.uint8)
tile_map[400:1600, 1000:4600] = 1

# 生成省份
from core.province_generator import generate_provinces, generate_province_colors
pm, cnt = generate_provinces(tile_map, 500)
colors = generate_province_colors(cnt)
print(f"Provinces: {cnt}")

os.makedirs(f"{out}/map", exist_ok=True)

# --- provinces.bmp ---
row_bytes = MAP_W * 3
padding = (4 - (row_bytes % 4)) % 4
max_pid = int(pm.max())
lut = np.ones((max_pid + 1, 3), dtype=np.uint8)
for pid, (r, g, b) in colors.items():
    if pid <= max_pid:
        lut[pid] = [b, g, r]
pix_size = (row_bytes + padding) * MAP_H
with open(f"{out}/map/provinces.bmp", "wb") as f:
    f.write(b"BM")
    f.write(struct.pack("<I", 54 + pix_size))
    f.write(struct.pack("<HH", 0, 0))
    f.write(struct.pack("<I", 54))
    f.write(struct.pack("<I", 40))
    f.write(struct.pack("<ii", MAP_W, MAP_H))
    f.write(struct.pack("<HH", 1, 24))
    f.write(struct.pack("<I", 0))
    f.write(struct.pack("<I", pix_size))
    f.write(struct.pack("<ii", 2835, 2835))
    f.write(struct.pack("<II", 0, 0))
    pad24 = b"\x00" * padding
    for y in range(MAP_H - 1, -1, -1):
        f.write(lut[pm[y, :]].tobytes())
        if padding:
            f.write(pad24)
print("provinces.bmp done")

# --- definition.csv (原始格式，有表头) ---
from core.province_validator import get_coastal_provinces
coastal_set = get_coastal_provinces(tile_map, pm)
sea_ids = []
land_ids = []
with open(f"{out}/map/definition.csv", "w") as f:
    f.write("province;red;green;blue;type;coastal;terrain;continent\n")
    for pid in range(1, cnt + 1):
        r, g, b = colors.get(pid, (1, 1, 1))
        mask = pm == pid
        tiles = tile_map[mask]
        is_sea = int(np.sum(tiles == 2)) > int(np.sum(tiles == 1))
        ptype = "sea" if is_sea else "land"
        terrain = "ocean" if is_sea else "plains"
        continent = 0 if is_sea else 1
        coastal = "true" if pid in coastal_set and not is_sea else "false"
        f.write(f"{pid};{r};{g};{b};{ptype};{coastal};{terrain};{continent}\n")
        if is_sea:
            sea_ids.append(pid)
        else:
            land_ids.append(pid)
print("definition.csv done")

# --- heightmap.bmp ---
hm = np.full((MAP_H, MAP_W), 40, dtype=np.float32)
hm[tile_map == 1] = 120
hm = gaussian_filter(hm, sigma=8)
hm[tile_map == 2] = np.minimum(hm[tile_map == 2], 94)
hm[tile_map == 1] = np.maximum(hm[tile_map == 1], 96)
hm = np.clip(hm, 0, 255).astype(np.uint8)

row8 = MAP_W
pad8 = (4 - (row8 % 4)) % 4
pix8 = (row8 + pad8) * MAP_H
def write_8bit_bmp(path, data):
    with open(path, "wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<I", 14+40+1024+pix8))
        f.write(struct.pack("<HH", 0, 0))
        f.write(struct.pack("<I", 14+40+1024))
        f.write(struct.pack("<I", 40))
        f.write(struct.pack("<ii", MAP_W, MAP_H))
        f.write(struct.pack("<HH", 1, 8))
        f.write(struct.pack("<I", 0))
        f.write(struct.pack("<I", pix8))
        f.write(struct.pack("<ii", 2835, 2835))
        f.write(struct.pack("<II", 256, 256))
        for i in range(256):
            f.write(struct.pack("BBBB", i, i, i, 0))
        p = b"\x00" * pad8
        for y in range(MAP_H - 1, -1, -1):
            f.write(data[y, :].tobytes())
            if pad8:
                f.write(p)

write_8bit_bmp(f"{out}/map/heightmap.bmp", hm)
print("heightmap.bmp done")

# --- terrain.bmp (原始格式，自己的调色板) ---
terrain_data = np.full((MAP_H, MAP_W), 0, dtype=np.uint8)  # 0=ocean
terrain_data[tile_map == 1] = 5  # 5=plains
write_8bit_bmp(f"{out}/map/terrain.bmp", terrain_data)
print("terrain.bmp done")

# --- trees.bmp (全白) ---
write_8bit_bmp(f"{out}/map/trees.bmp", np.full((MAP_H, MAP_W), 255, dtype=np.uint8))

# --- rivers.bmp (全白24bit) ---
with open(f"{out}/map/rivers.bmp", "wb") as f:
    f.write(b"BM")
    f.write(struct.pack("<I", 54 + pix_size))
    f.write(struct.pack("<HH", 0, 0))
    f.write(struct.pack("<I", 54))
    f.write(struct.pack("<I", 40))
    f.write(struct.pack("<ii", MAP_W, MAP_H))
    f.write(struct.pack("<HH", 1, 24))
    f.write(struct.pack("<I", 0))
    f.write(struct.pack("<I", pix_size))
    f.write(struct.pack("<ii", 2835, 2835))
    f.write(struct.pack("<II", 0, 0))
    white = b"\xff" * row_bytes
    for _ in range(MAP_H):
        f.write(white)
        if padding:
            f.write(pad24)

# --- world_normal.bmp ---
h_f = hm.astype(np.float32) / 255.0
dx = sobel(h_f, axis=1)
dy = -sobel(h_f, axis=0)
nx, ny, nz = -dx, -dy, np.ones_like(h_f)
length = np.sqrt(nx**2 + ny**2 + nz**2)
length[length == 0] = 1
nx /= length; ny /= length; nz /= length
nr = ((nx + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
ng = ((ny + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
nb = ((nz + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
with open(f"{out}/map/world_normal.bmp", "wb") as f:
    f.write(b"BM")
    f.write(struct.pack("<I", 54 + pix_size))
    f.write(struct.pack("<HH", 0, 0))
    f.write(struct.pack("<I", 54))
    f.write(struct.pack("<I", 40))
    f.write(struct.pack("<ii", MAP_W, MAP_H))
    f.write(struct.pack("<HH", 1, 24))
    f.write(struct.pack("<I", 0))
    f.write(struct.pack("<I", pix_size))
    f.write(struct.pack("<ii", 2835, 2835))
    f.write(struct.pack("<II", 0, 0))
    for y in range(MAP_H - 1, -1, -1):
        row_bgr = np.stack([nb[y, :], ng[y, :], nr[y, :]], axis=1)
        f.write(row_bgr.tobytes())
        if padding:
            f.write(pad24)
print("BMP files done")

# --- default.map (原始格式) ---
with open(f"{out}/map/default.map", "w") as f:
    f.write(f"max_provinces = {cnt + 1}\n")
    f.write('definitions = "definition.csv"\nprovinces = "provinces.bmp"\n')
    f.write('rivers = "rivers.bmp"\nterrain = "terrain.bmp"\n')
    f.write('heightmap = "heightmap.bmp"\ntree_definition = "trees.bmp"\n')
    f.write('continent = "continent.txt"\nadjacencies = "adjacencies.csv"\n')
    f.write('adjacency_rules = "adjacency_rules.txt"\n')
    f.write('ambient_object = "ambient_object.txt"\nseasons = "seasons.txt"\n\n')
    if sea_ids:
        f.write("sea_starts = {\n")
        for i in range(0, len(sea_ids), 20):
            f.write("    " + " ".join(str(x) for x in sea_ids[i:i + 20]) + "\n")
        f.write("}\n\n")
    f.write("force_coastal = { }\n")

# --- 其他文本文件 ---
with open(f"{out}/map/continent.txt", "w") as f:
    f.write('continents = {\n    1 = "fantasy_continent"\n}\n')
with open(f"{out}/map/adjacencies.csv", "w") as f:
    f.write("From;To;Type;Through;start_x;start_y;stop_x;stop_y;adjacency_rule_name;Comment\n;;;;;;;;;\n")
for fname in ["adjacency_rules.txt", "ambient_object.txt",
              "weatherpositions.txt", "unitstacks.txt", "rocket_sites.txt"]:
    open(f"{out}/map/{fname}", "w").close()
with open(f"{out}/map/seasons.txt", "w") as f:
    f.write("# Seasons definition\n")

first_land = land_ids[0] if land_ids else 1
with open(f"{out}/map/supply_nodes.txt", "w") as f:
    f.write(f"1 {first_land}\n")
with open(f"{out}/map/railways.txt", "w") as f:
    f.write(f"1 2 {first_land} {first_land}\n")
with open(f"{out}/map/buildings.txt", "w") as f:
    f.write("1;infrastructure;100.0;10.0;100.0;0.0;0\n")

# strategic region
os.makedirs(f"{out}/map/strategicregions", exist_ok=True)
all_ids = list(range(1, cnt + 1))
with open(f"{out}/map/strategicregions/1-fantasy_region.txt", "w") as f:
    f.write("strategic_region = {\n    id = 1\n")
    f.write('    name = "STRATEGICREGION_1"\n    provinces = {\n')
    f.write("        " + " ".join(str(x) for x in all_ids) + "\n    }\n")
    f.write("    weather = {\n        period = {\n")
    f.write("            between = { 0.0 30.0 }\n            temperature = { -5.0 25.0 }\n")
    f.write("            no_phenomenon = 0.500\n            rain_light = 0.200\n")
    f.write("            rain_heavy = 0.100\n            mud = 0.050\n")
    f.write("            blizzard = 0.050\n            sandstorm = 0.000\n")
    f.write("            snow = 0.100\n        }\n    }\n}\n")

# State
os.makedirs(f"{out}/history/states", exist_ok=True)
with open(f"{out}/history/states/1-STATE_1.txt", "w") as f:
    f.write("state = {\n    id = 1\n")
    f.write('    name = "STATE_1"\n    manpower = 100000\n    state_category = town\n\n')
    f.write("    history = {\n        owner = AAA\n")
    f.write("        buildings = {\n            infrastructure = 1\n        }\n")
    f.write(f"        victory_points = {{\n            {first_land} 1\n        }}\n")
    f.write("    }\n\n    provinces = {\n")
    f.write("        " + " ".join(str(x) for x in land_ids) + "\n    }\n}\n")

# 国家
os.makedirs(f"{out}/common/country_tags", exist_ok=True)
os.makedirs(f"{out}/common/countries", exist_ok=True)
os.makedirs(f"{out}/history/countries", exist_ok=True)
os.makedirs(f"{out}/history/units", exist_ok=True)
with open(f"{out}/common/country_tags/00_countries.txt", "w") as f:
    f.write('AAA = "countries/AAA.txt"\n')
with open(f"{out}/common/countries/AAA.txt", "w") as f:
    f.write("graphical_culture = western_european_gfx\ngraphical_culture_2d = western_european_2d\ncolor = { 100 100 200 }\n")
with open(f"{out}/history/countries/AAA - FantasyCountry.txt", "w") as f:
    f.write(f"capital = {first_land}\n")
    f.write('oob = "AAA_1936"\nset_politics = {\n    ruling_party = neutrality\n')
    f.write('    last_election = "1932.1.1"\n    election_frequency = 48\n    elections_allowed = no\n}\n')
    f.write("set_popularities = {\n    democratic = 10\n    fascism = 5\n    communism = 5\n    neutrality = 80\n}\n")
with open(f"{out}/history/units/AAA_1936.txt", "w") as f:
    f.write("units = { }\n")

# descriptor
with open(f"{out}/descriptor.mod", "w") as f:
    f.write('version="0.1"\ntags={\n    "Alternative History"\n    "Map"\n    "Total Conversion"\n}\n')
    f.write('name="Fantasy World"\nsupported_version="1.16.*"\n')
    f.write('replace_path="history/countries"\nreplace_path="history/states"\n')
    f.write('replace_path="history/units"\nreplace_path="map/strategicregions"\n')
    f.write('replace_path="map/supplyareas"\n')

# 本地化
os.makedirs(f"{out}/localisation", exist_ok=True)
with open(f"{out}/localisation/Fantasy_World_l_english.yml", "w", encoding="utf-8-sig") as f:
    f.write("l_english:\n")
    f.write(' STATE_1:0 "Fantasy State"\n')
    f.write(' STRATEGICREGION_1:0 "Fantasy Region"\n')
    f.write(' AAA:0 "Fantasy Country"\n')
    f.write(' AAA_DEF:0 "Fantasy Country"\n')
    f.write(' AAA_ADJ:0 "Fantasy"\n')

print("=== DONE - original format restored ===")
