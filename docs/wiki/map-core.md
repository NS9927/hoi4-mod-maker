# HOI4 Map 核心规则

> 编译自 Paradox Wiki "Map modding" 页面。每条规则标注违反后果：**[崩溃]** / **[错误]** / **[警告]** / **[视觉异常]**

---

## 1. BMP 文件格式总表

| 文件 | 位深 | 模式 | 尺寸要求 | 备注 |
|------|------|------|----------|------|
| `provinces.bmp` | 24-bit | RGB | 宽高均为 256 的倍数; 总像素 ≤ 13,238,272 | **[崩溃]** 32-bit 会报 `X4008: floating point division by zero` |
| `heightmap.bmp` | 8-bit | 灰度/索引灰度 | 同 provinces.bmp | **[崩溃]** Paint.net/MS Paint 会破坏调色板 |
| `terrain.bmp` | 8-bit | 索引色 | 同 provinces.bmp | **[视觉异常]** 调色板被改 = 地形全乱 |
| `rivers.bmp` | 8-bit | 索引色 | 同 provinces.bmp | |
| `trees.bmp` | 8-bit | 索引色 | 各边 = provinces 的 75/256 | |
| `cities.bmp` | 8-bit | 索引色 | **同 provinces.bmp** | **[崩溃]** 尺寸不同报 invalid size |
| `world_normal.bmp` | 24-bit | RGB | 同 provinces.bmp 或其一半 | |

**通用 BMP 规则：**

- **[崩溃]** 禁止任何压缩，必须为无压缩 BMP
- **[崩溃]** DIB header 必须为 `BITMAPINFOHEADER`（GIMP 导出时**必须勾选 "do not write color space information"**）
- **[视觉异常]** 8-bit 索引 BMP 的调色板(colourmap)不可修改、不可切换图像模式再切回
- 仅 `provinces.bmp` 和 `world_normal.bmp` 可用 Paint.net/MS Paint 编辑

---

## 2. 坐标系统

```
X = 像素水平位置 (左→右, 0 在左边缘, 地图水平循环)
Y = 高度值 / 10  (heightmap 0→Y=0, 255→Y=25.5, 海平面 Y=9.5 即值 95)
Z = 像素垂直位置 (下→上, 0 在南边缘, 注意：大多数图像编辑器 Y 轴相反)
```

---

## 3. provinces.bmp

| 规则 | 后果 |
|------|------|
| 24-bit RGB，禁止 32-bit | **[崩溃]** |
| 宽高均为 256 的倍数 | **[崩溃]** |
| 总像素 ≤ ~13,238,272 | **[崩溃]** |
| 禁止颜色 `(0,0,0)` | **[错误]** |
| 禁止抗锯齿 | **[错误]** 产生意外颜色 → 幽灵省份 |
| 每个颜色必须唯一对应一个省份 | **[错误]** 重复颜色 → `TOO LARGE BOX` |
| 每个省份最小 8 像素 | **[警告]** |
| 省份边界上限约 21,000 个省份 | **[视觉异常]** |
| 四省共角 (X-crossing) | **[警告]** |
| 省份宽/高不得超过地图宽/高的 1/8 | **[警告]** `TOO LARGE BOX` |

---

## 4. definition.csv

```
格式: Province_ID;R;G;B;type;coastal;terrain;continent
示例: 0;0;0;0;land;false;unknown;0
      114;40;15;15;land;false;plains;1
      260;170;235;235;land;true;urban;1
```

| 字段 | 规则 | 后果 |
|------|------|------|
| Province ID | **必须连续递增，不可有间隔** | **[错误]** 间隔后所有省份属性偏移 |
| R, G, B | 必须唯一 | **[错误]** |
| type | `land`/`sea`/`lake`; lake→terrain=lakes; sea→terrain=ocean | **[错误]** |
| coastal | 与 BMP 实际邻接不一致时**以 BMP 为准** | **[警告]** |
| continent | sea=0, **land 必须 >0** | **[错误]** `has no continent` |
| 换行符 | **必须 CRLF** (Windows) | **[错误]** Unix LF 导致所有大陆解析失败 |

---

## 5. heightmap.bmp

| 规则 | 值 |
|------|-----|
| 格式 | 8-bit 灰度 |
| 像素值范围 | 0 (纯黑=高度0) ~ 255 (纯白=高度25.5) |
| 海平面 | 值 95 (Y=9.5) |
| <95 | 水下 |
| ≥95 | 陆地 |

---

## 6. terrain.bmp 调色板

8-bit 索引色。**游戏读取调色板索引 ID，不是颜色值。**

| ID | 对应省份地形 | 备注 |
|----|-------------|------|
| 0 | plains | |
| 1 | forest | 密林 |
| 2 | hills | |
| 3 | desert | |
| 4 | forest | 疏林 |
| 5 | plains | 农田 |
| 6 | mountain | |
| 9 | marsh | |
| 13 | urban | spawn_city=yes |
| 14 | lakes | |
| 15 | ocean | |
| 16 | mountain | 永久积雪 |
| 21 | jungle | |

---

## 7. rivers.bmp 调色板

河流**必须恰好 1 像素宽**，只能正交方向。

| 索引 | 功能 |
|------|------|
| 0 | **河流源头** (每条河必须恰好 1 个) |
| 1 | 汇入源 (支流合并到主河) |
| 2 | 分流源 (从主河分出支流) |
| 3-11 | 河流宽度 (3=最窄, 11=最宽) |
| 254 | 海洋背景 |
| 255 | 陆地背景 |

---

## 8. buildings.txt

```
格式: State_ID;building_type;X;Y;Z;Rotation;Adjacent_sea_province
示例: 123;naval_base_spawn;1234.56;9.50;789.01;0.00;5579
```

| 规则 | 后果 |
|------|------|
| **文件不能为空** | **[崩溃]** |
| Adjacent sea province 仅 `naval_base_spawn` 和 `floating_harbor` 需要填，其余填 0 | |
| **每个被引擎判定为 coastal 的省份都必须有 naval_base_spawn** | **[崩溃]** 无限循环 → CPU 过载 |
| 坐标必须落在该省份的陆地像素上 | HOI4 忽略该行 → 等于没有 |

---

## 9. supply_nodes.txt / railways.txt

```
# supply_nodes.txt
Level Province
1 1234

# railways.txt
Level ProvinceCount Prov1 Prov2 ...
4 4 693 1444 12 11
```

| 规则 | 后果 |
|------|------|
| 两个文件都**不能为空** | **[崩溃]** |
| 铁路经过不存在/无 state 的省份 | **[崩溃]** |
| supply node 等级上限 1, railway 等级上限 5 | |

---

## 10. adjacencies.csv

```
格式: Start;End;Type;Through;Start_X;Start_Y;End_X;End_Y;Rule;Comment
最后一行: -1;-1;;-1;-1;-1;-1;-1;-1
```

**[崩溃]** 缺少 `-1;-1;...` 终止行会导致加载挂起。

---

## 11. 关键 Defines

```
WATER_HEIGHT = 9.5f              # 海平面
MINIMUM_PROVINCE_SIZE_IN_PIXELS = 8
MAX_RAILWAY_LEVEL = 5
RIVER_RAILWAY_LEVEL = 1          # 河流=1级铁路
```
