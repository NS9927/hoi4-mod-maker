# HOI4 建筑与补给规则

> 编译自 Paradox Wiki "Building modding" 页面

## buildings.txt 格式 (关键!)

路径: `/map/buildings.txt`

```
StateID;BuildingType;X;Y;Z;Rotation;AdjacentSeaProvince
```

| 字段 | 说明 |
|------|------|
| StateID | 所属 state ID |
| BuildingType | 建筑内部名 |
| X | 水平坐标(像素对齐 provinces.bmp) |
| Y | 高度(heightmap 0-255 归一化到 0-25.5) |
| Z | 垂直坐标(像素对齐 provinces.bmp, 从下往上) |
| Rotation | 弧度(0=默认, 2π=360度) |
| **AdjacentSeaProvince** | **naval_base/floating_harbour 必须填相邻海洋省份 ID; 其他建筑必须=0** |

## 致命规则

| 规则 | 违反后果 |
|------|----------|
| buildings.txt **不能为空** | **[崩溃]** |
| naval_base 的 AdjacentSeaProvince 必须有效 | **[崩溃]** CPU/GPU 死循环 |
| **每个被引擎判定为 coastal 的省份都必须有 naval_base_spawn 记录** | **[崩溃]** error.log: `Province X is setup as coastal but has no port building` |
| 坐标必须落在该省份的陆地像素上 | HOI4 忽略该行 → 等于没有 |
| airports.txt / rocketsites.txt 缺失 | **[崩溃]** 无 debug 模式无法启动 |

## naval_base 特殊规则

```
# 1. common/buildings/ 中: is_port = yes, only_costal = yes, province_max = 10
# 2. map/buildings.txt 中: 第7字段必须填有效的相邻海洋省份ID
# 3. 每个 coastal 省份都必须在 buildings.txt 中有 naval_base_spawn 记录
# 4. 缺少任何一条 → AI 建造/使用时无限循环崩溃(client_ping)
```

注意: `only_costal` 是原版拼写(不是 coastal)。

## 建筑三大类型

| 类型 | 槽位机制 | 典型建筑 |
|------|----------|----------|
| **Shared** | 共享 25 槽池 | arms_factory, industrial_complex, dockyard, synthetic_refinery, rocket_site, nuclear_reactor |
| **Non-shared** | 每种独立槽位/state | infrastructure, air_base, anti_air_building, radar_station |
| **Provincial** | 每种独立槽位/province | naval_base, bunker, coastal_bunker, supply_node, rail_way |

## 完整建筑列表 (vanilla 1.17)

| 建筑名 | 内部名 | 最大等级 | 类型 |
|--------|--------|----------|------|
| Infrastructure | infrastructure | 5 | Non-shared |
| Military factory | arms_factory | 20 | Shared |
| Civilian factory | industrial_complex | 20 | Shared |
| Air base | air_base | 10 | Non-shared |
| Supply hub | supply_node | 1 | Provincial |
| Railway | rail_way | 5 | Provincial |
| Naval base | naval_base | 10 | Provincial |
| Land fort | bunker | 10 | Provincial |
| Coastal fort | coastal_bunker | 10 | Provincial |
| Naval dockyard | dockyard | 20 | Shared |
| Anti-air | anti_air_building | 5 | Non-shared |
| Synthetic refinery | synthetic_refinery | 3 | Shared |
| Fuel silo | fuel_silo | 15 | Shared |
| Radar station | radar_station | 6 | Non-shared |
| Rocket site | rocket_site | 3 | Shared |

## Railway/Supply 特殊规则

- 初始等级在 map/supply_nodes.txt 和 map/railways.txt 定义，不在 state history
- 游戏内建造必须用 `build_railway` 效果，不能用 `add_building_construction`
- 用 `add_building_construction` 操作铁路 → **[崩溃]**
