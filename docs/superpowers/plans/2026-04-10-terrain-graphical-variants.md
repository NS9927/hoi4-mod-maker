# 地形系统完善 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 支持全部 vanilla graphical terrain 变体（22 种），改地形时联动高度，海洋/湖泊省份不可改地形，definition.csv 写入正确的 provincial terrain。

**Architecture:** 扩展 `data/terrain_types.py` 加入 `GRAPHICAL_TERRAINS` 全表（从 vanilla `00_terrain.txt` 的 `terrain = {}` 块映射），UI 按 provincial terrain type 分组显示所有变体，canvas 点击时同步更新 terrain_map + height_map，导出时 definition.csv 从 terrain_map 反查 provincial terrain type。

**Tech Stack:** Python 3.10+, PyQt5, NumPy

---

## File Structure

| 文件 | 职责 | 改动 |
|------|------|------|
| `data/terrain_types.py` | 地形数据定义 | 新增 `GraphicalTerrain` + `GRAPHICAL_TERRAINS` 全表 + `PALETTE_TO_TYPE` 反查表 |
| `features/map/terrain/page.py` | 地形编辑器 UI | 重写：按 type 分组显示全部变体按钮 |
| `ui/canvas_widget.py` | 画布交互 | 地形点击加海洋保护 + 联动高度；LUT 扩展到全部索引 |
| `export/csv_writer.py` | definition.csv 导出 | `_default_terrain()` 改为从 terrain_map 查实际 type |
| `services/terrain_service.py` | 自动生成服务 | 无改动 |
| `export/bmp_writer.py` | terrain.bmp 导出 | 无改动（已按调色板索引直接写入） |

---

### Task 1: 扩展 terrain 数据定义

**Files:**
- Modify: `data/terrain_types.py`

- [ ] **Step 1: 在 `data/terrain_types.py` 末尾新增 `GraphicalTerrain` 和全表**

```python
class GraphicalTerrain(NamedTuple):
    """terrain.bmp 的 graphical terrain 条目 (来自 00_terrain.txt terrain={} 块)"""
    id: str                # 原版条目名: "terrain_0", "desert_mountain" 等
    type: str              # provincial terrain 类型: plains/forest/mountain 等
    palette_index: int     # terrain.bmp 调色板索引
    texture: int           # atlas0.dds 贴图编号 (0-15)
    name_cn: str           # 中文显示名
    perm_snow: bool        # 永雪覆盖
    spawn_city: bool       # 自动生成城市模型


# 原版 00_terrain.txt terrain={} 块全部条目
# 每条对应 terrain.bmp 一个调色板索引 → 一种游戏内外观
GRAPHICAL_TERRAINS: list[GraphicalTerrain] = [
    GraphicalTerrain("terrain_0",             "plains",   0,  1,  "平原",           False, False),
    GraphicalTerrain("terrain_1",             "forest",   1,  4,  "森林",           False, False),
    GraphicalTerrain("desert_mountain",       "hills",    2,  3,  "沙漠丘陵",       False, False),
    GraphicalTerrain("desert",                "desert",   3,  9,  "沙漠",           False, False),
    GraphicalTerrain("terrain_4",             "forest",   4,  5,  "森林(变体)",     False, False),
    GraphicalTerrain("terrain_5",             "plains",   5,  0,  "平原(变体)",     False, False),
    GraphicalTerrain("terrain_6",             "mountain", 6,  11, "山地",           False, False),
    GraphicalTerrain("terrain_7",             "desert",   7,  12, "沙漠(变体)",     False, False),
    GraphicalTerrain("desert_hills",          "desert",   8,  14, "沙漠丘陵",       False, False),
    GraphicalTerrain("terrain_9",             "marsh",    9,  6,  "沼泽",           False, False),
    GraphicalTerrain("terrain_10",            "mountain", 10, 13, "山地(变体)",     False, False),
    GraphicalTerrain("desert_mountain_11",    "mountain", 11, 11, "沙漠山地",       False, False),
    GraphicalTerrain("desert_12",             "desert",   12, 8,  "沙漠(岩地)",     False, False),
    GraphicalTerrain("forest_13",             "urban",    13, 10, "城市",           False, True),
    GraphicalTerrain("forest_14",             "lakes",    14, 255, "湖泊",          False, False),
    GraphicalTerrain("ocean_15",              "ocean",    15, 9,  "海洋",           False, False),
    GraphicalTerrain("snow_16",               "mountain", 16, 11, "雪山",           True,  False),
    GraphicalTerrain("hills_blend",           "hills",    17, 2,  "丘陵",           False, False),
    GraphicalTerrain("mountain_variation_sand","mountain", 18, 7,  "沙色山地",      False, False),
    GraphicalTerrain("plains_snow",           "plains",   19, 0,  "雪原",           True,  False),
    GraphicalTerrain("mountain_variation_grass","mountain",20, 7,  "草地山地",      False, False),
    GraphicalTerrain("jungle_18",             "jungle",   21, 4,  "丛林",           False, False),
    GraphicalTerrain("jungle_blend_18",       "jungle",   22, 5,  "丛林(变体)",     False, False),
    GraphicalTerrain("jungle_mountain",       "mountain", 27, 7,  "丛林山地",       False, False),
    GraphicalTerrain("desert_mountain_tops",  "mountain", 31, 15, "沙漠山顶",       False, False),
]

# 调色板索引 → GraphicalTerrain 快速查找
GRAPHICAL_TERRAIN_BY_INDEX: dict[int, GraphicalTerrain] = {
    gt.palette_index: gt for gt in GRAPHICAL_TERRAINS
}

# 调色板索引 → provincial terrain type 名称 (用于 definition.csv)
PALETTE_TO_TYPE: dict[int, str] = {
    gt.palette_index: gt.type for gt in GRAPHICAL_TERRAINS
}

# 按 provincial terrain type 分组的可画变体 (排除 ocean/lakes)
PAINTABLE_GROUPS: dict[str, list[GraphicalTerrain]] = {}
for _gt in GRAPHICAL_TERRAINS:
    if _gt.type not in ("ocean", "lakes"):
        PAINTABLE_GROUPS.setdefault(_gt.type, []).append(_gt)
```

- [ ] **Step 2: 验证数据无重复索引**

运行 Python 交互检查：
```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && python -c "
from data.terrain_types import GRAPHICAL_TERRAINS
indices = [gt.palette_index for gt in GRAPHICAL_TERRAINS]
assert len(indices) == len(set(indices)), f'重复索引: {[i for i in indices if indices.count(i) > 1]}'
print(f'OK: {len(GRAPHICAL_TERRAINS)} 种 graphical terrain, 索引无重复')
"
```
Expected: `OK: 25 种 graphical terrain, 索引无重复`

- [ ] **Step 3: Commit**

```bash
git add data/terrain_types.py
git commit -m "feat: 扩展 graphical terrain 全表 (25 种 vanilla 变体)"
```

---

### Task 2: 扩展 canvas 颜色 LUT

**Files:**
- Modify: `ui/canvas_widget.py:37-46`

- [ ] **Step 1: 替换 LUT 构建代码**

将 `canvas_widget.py` 第 37-46 行的 LUT 构建从旧的 `TERRAIN_PALETTE_INDEX` 改为新的 `GRAPHICAL_TERRAINS`：

```python
# 构建 terrain 索引 → BGRA 颜色查找表 (覆盖全部 graphical terrain)
from data.terrain_types import GRAPHICAL_TERRAINS, TERRAIN_TYPES

# 构建 terrain 颜色 LUT (numpy数组, 256 entries, BGRA)
_TERRAIN_COLOR_LUT = np.zeros((256, 4), dtype=np.uint8)
for _gt in GRAPHICAL_TERRAINS:
    # 用 provincial terrain type 的颜色作为基色
    _base = TERRAIN_TYPES[_gt.type].color  # (R, G, B)
    _r, _g, _b = _base
    # 变体用亮度微调区分 (palette_index 的低位偏移)
    _shift = ((_gt.palette_index * 7) % 30) - 15  # -15 ~ +14
    _r = max(0, min(255, _r + _shift))
    _g = max(0, min(255, _g + _shift))
    _b = max(0, min(255, _b + _shift))
    # 永雪变体叠加蓝白色调
    if _gt.perm_snow:
        _r = min(255, _r + 40)
        _g = min(255, _g + 40)
        _b = min(255, _b + 60)
    _TERRAIN_COLOR_LUT[_gt.palette_index] = (_b, _g, _r, 255)
```

- [ ] **Step 2: 删除旧的 import**

移除不再需要的 `TERRAIN_PALETTE_INDEX` import（第 23 行），改为：
```python
from data.terrain_types import TERRAIN_TYPES, GRAPHICAL_TERRAINS
```

- [ ] **Step 3: 验证渲染不崩**

```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && python -c "
from ui.canvas_widget import _TERRAIN_COLOR_LUT
import numpy as np
assert _TERRAIN_COLOR_LUT.shape == (256, 4)
non_zero = np.any(_TERRAIN_COLOR_LUT != 0, axis=1).sum()
print(f'OK: LUT 有 {non_zero} 个非零条目')
"
```
Expected: `OK: LUT 有 25 个非零条目`

- [ ] **Step 4: Commit**

```bash
git add ui/canvas_widget.py
git commit -m "feat: terrain LUT 扩展到全部 25 种 graphical terrain"
```

---

### Task 3: 重写 terrain UI page

**Files:**
- Modify: `features/map/terrain/page.py`

- [ ] **Step 1: 重写 `build_page()` — 按 type 分组显示全部变体**

```python
"""terrain feature 页面 — 按 provincial terrain type 分组显示全部 graphical terrain 变体."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QScrollArea,
)

from data.terrain_types import (
    TERRAIN_TYPES, PAINTABLE_GROUPS, GRAPHICAL_TERRAINS,
)

from ui.styles import (
    _BG, _DIM, _SECTION_STYLE, _PRIMARY_BTN_STYLE,
)


# 分组显示顺序
_GROUP_ORDER = ["plains", "forest", "hills", "mountain", "desert", "marsh", "jungle", "urban"]

# 分组中文名
_GROUP_CN = {
    "plains": "平原", "forest": "森林", "hills": "丘陵", "mountain": "山地",
    "desert": "沙漠", "marsh": "沼泽", "jungle": "丛林", "urban": "城市",
}


def build_page(panel) -> QWidget:
    """构建 terrain 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(4)

    # 提示
    hint = QLabel("选择地形变体，然后点击省份分配")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
    hint.setWordWrap(True)
    outer.addWidget(hint)

    # 可滚动区域
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; }")
    scroll_content = QWidget()
    lay = QVBoxLayout(scroll_content)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)

    for group_type in _GROUP_ORDER:
        variants = PAINTABLE_GROUPS.get(group_type, [])
        if not variants:
            continue

        tt = TERRAIN_TYPES[group_type]
        group_name = _GROUP_CN.get(group_type, group_type)
        box = panel._make_section(f"{group_name} ({len(variants)})")
        grid = QGridLayout()
        grid.setSpacing(3)

        for i, gt in enumerate(variants):
            label = gt.name_cn
            if gt.perm_snow:
                label += " *"
            btn = QPushButton(label)
            btn.setToolTip(
                f"索引: {gt.palette_index}  贴图: {gt.texture}\n"
                f"类型: {gt.type}  ID: {gt.id}"
            )

            r, g, b = tt.color
            # 变体微调亮度以区分
            shift = ((gt.palette_index * 7) % 30) - 15
            r = max(0, min(255, r + shift))
            g = max(0, min(255, g + shift))
            b = max(0, min(255, b + shift))
            if gt.perm_snow:
                r = min(255, r + 40)
                g = min(255, g + 40)
                b = min(255, b + 60)

            brightness = r * 0.299 + g * 0.587 + b * 0.114
            fg = "#000000" if brightness > 140 else "#ffffff"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgb({r},{g},{b});
                    border: 2px solid transparent;
                    color: {fg};
                    padding: 4px 2px;
                    font-size: 10px;
                    font-weight: 600;
                    border-radius: 3px;
                    min-width: 50px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)
            btn.clicked.connect(
                lambda _, idx=gt.palette_index: panel.terrain_index_changed.emit(idx)
            )
            grid.addWidget(btn, i // 2, i % 2)

        box.layout().addLayout(grid)
        lay.addWidget(box)

    lay.addStretch()
    scroll.setWidget(scroll_content)
    outer.addWidget(scroll)

    # 自动生成
    auto_btn = QPushButton("从陆地自动生成")
    auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    auto_btn.clicked.connect(panel.auto_terrain_requested.emit)
    outer.addWidget(auto_btn)

    return page
```

- [ ] **Step 2: 启动工具验证 UI 不崩**

```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && python main.py
```

切到地形模式，确认：
- 8 个分组都有标题
- 每组内有对应数量的变体按钮（如山地组 7 个）
- 点击按钮后状态栏无报错

- [ ] **Step 3: Commit**

```bash
git add features/map/terrain/page.py
git commit -m "feat: terrain UI 按类型分组显示全部 25 种 graphical terrain 变体"
```

---

### Task 4: 海洋保护 + 高度联动

**Files:**
- Modify: `ui/canvas_widget.py:879-891`

- [ ] **Step 1: 修改地形点击处理 — 加海洋/湖泊保护 + 高度联动**

将 `canvas_widget.py` 第 886-891 行替换为：

```python
                        # 地形模式：点击省份 → 整个省份填充当前地形
                        if self._display_mode == "terrain":
                            # 海洋/湖泊省份不可改地形
                            tile_val = self._tile_map[sy, sx]
                            if tile_val in (TILE_SEA, TILE_LAKE):
                                event.accept()
                                return
                            self.stroke_started.emit()
                            self._terrain_map[mask] = self._current_terrain_index
                            # 联动高度：根据 graphical terrain 的 type 查 height_base
                            from data.terrain_types import PALETTE_TO_TYPE, TERRAIN_TYPES
                            ptype = PALETTE_TO_TYPE.get(self._current_terrain_index)
                            if ptype and ptype in TERRAIN_TYPES:
                                self._height_map[mask] = TERRAIN_TYPES[ptype].height_base
                            self._full_render()
                            self.stroke_ended.emit()
```

- [ ] **Step 2: 确认 `TILE_SEA` 和 `TILE_LAKE` 已 import**

检查文件顶部 import，确认有：
```python
from data.constants import (
    ..., TILE_SEA, TILE_LAKE, ...
)
```
（已有，无需改动）

- [ ] **Step 3: 手动测试**

```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && python main.py
```

测试步骤：
1. 切到地形模式
2. 选"山地"变体，点一个陆地省份 → 应变成山地颜色
3. 切到高度模式查看 → 该省份高度应自动变高 (220)
4. 切回地形模式，点一个海洋省份 → 应无反应
5. 点一个湖泊省份 → 应无反应

- [ ] **Step 4: Commit**

```bash
git add ui/canvas_widget.py
git commit -m "feat: 地形编辑加海洋保护 + 高度联动"
```

---

### Task 5: definition.csv 写入正确的 provincial terrain

**Files:**
- Modify: `export/csv_writer.py:45-93` 和 `export/csv_writer.py:127-134`

- [ ] **Step 1: 修改 `write_definition_csv` 签名 — 接收 terrain_map**

在函数签名加 `terrain_map` 参数：

```python
def write_definition_csv(
    province_map: np.ndarray,
    tile_map: np.ndarray,
    output_dir: str,
    colors: dict[int, tuple[int, int, int]] | None = None,
    continent_mgr=None,
    terrain_map: np.ndarray | None = None,
) -> None:
```

- [ ] **Step 2: 修改地形字段逻辑 — 从 terrain_map 查**

将第 82-83 行的：
```python
            # 默认地形
            terrain = _default_terrain(ptype)
```
替换为：
```python
            # 地形：优先从 terrain_map 查实际 graphical terrain 的 type
            terrain = _resolve_terrain(ptype, pid, province_map, terrain_map)
```

- [ ] **Step 3: 新增 `_resolve_terrain` 函数**

在 `_default_terrain` 下方添加：

```python
def _resolve_terrain(
    ptype: str,
    pid: int,
    province_map: np.ndarray,
    terrain_map: np.ndarray | None,
) -> str:
    """从 terrain_map 解析省份的 provincial terrain type."""
    # 海/湖强制
    if ptype == "sea":
        return "ocean"
    if ptype == "lake":
        return "lakes"

    if terrain_map is None:
        return "plains"

    from data.terrain_types import PALETTE_TO_TYPE

    # 取该省份区域内 terrain_map 的众数 (最多的那个索引)
    mask = province_map == pid
    indices = terrain_map[mask]
    if indices.size == 0:
        return "plains"

    counts = np.bincount(indices)
    dominant_index = int(counts.argmax())
    return PALETTE_TO_TYPE.get(dominant_index, "plains")
```

确保文件顶部有 `import numpy as np`（已有）。

- [ ] **Step 4: 找到 mod_exporter 调用 `write_definition_csv` 的位置，传入 terrain_map**

搜索 mod_exporter.py 中调用 `write_definition_csv` 的地方，加上 `terrain_map=` 参数：

```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && grep -n "write_definition_csv" export/mod_exporter.py
```

在调用处添加 `terrain_map=terrain_map` 参数。

- [ ] **Step 5: 验证导出**

```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && python -c "
# 模拟检查 _resolve_terrain 逻辑
import numpy as np
from export.csv_writer import _resolve_terrain
pm = np.array([[1,1,2,2],[1,1,2,2]])
tm = np.array([[6,6,0,0],[6,6,0,0]])  # pid=1→索引6(mountain), pid=2→索引0(plains)
assert _resolve_terrain('land', 1, pm, tm) == 'mountain'
assert _resolve_terrain('land', 2, pm, tm) == 'plains'
assert _resolve_terrain('sea', 1, pm, tm) == 'ocean'
assert _resolve_terrain('lake', 1, pm, tm) == 'lakes'
print('OK: _resolve_terrain 逻辑正确')
"
```
Expected: `OK: _resolve_terrain 逻辑正确`

- [ ] **Step 6: Commit**

```bash
git add export/csv_writer.py export/mod_exporter.py
git commit -m "feat: definition.csv 从 terrain_map 写入正确的 provincial terrain"
```

---

### Task 6: 端到端验证

- [ ] **Step 1: 启动工具完整流程测试**

```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && python main.py
```

操作步骤：
1. 打开现有项目或新建
2. 切到地形模式 → 确认 8 组变体按钮全部显示
3. 选"雪山"(索引 16) → 点一个陆地省份 → 确认变色
4. 选"丛林"(索引 21) → 点另一个陆地省份 → 确认变色
5. 点海洋省份 → 确认无反应
6. 切到高度模式 → 确认步骤 3 的省份高度为 220 (mountain)，步骤 4 的为 125 (jungle)
7. 导出 MOD
8. 检查 `definition.csv` → 步骤 3 的省份 terrain 列应为 `mountain`，步骤 4 应为 `jungle`
9. 检查 `terrain.bmp` 可用 hex 编辑器确认像素值

- [ ] **Step 2: 运行现有测试确认无回归**

```bash
cd C:/Users/Administrator.SKY-20180310BMB/Desktop/MOD/hoi4_map_maker && pytest -v
```

Expected: 全部通过

- [ ] **Step 3: 最终 Commit**

```bash
git add -A
git commit -m "feat: 地形系统完善 — 全 vanilla graphical terrain + 高度联动 + 海洋保护"
```
