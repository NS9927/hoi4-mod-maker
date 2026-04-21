# 高度图局部精修（Refine）功能设计

**日期**：2026-04-21
**一句话**：选一块区域 → 保留用户画的高度形状 → 算法在其上叠加山脊/侵蚀/噪声 → 边界羽化融入周围。

---

## 1. 问题

用户手画 heightmap 时会得到"形状对、但看起来像大饼"的结果：
- 山脉顶是平的（没尖）
- 没有沟壑（缺侵蚀感）
- 全图均匀（缺岩石/质感）

现有工具的不足：
- 「智能生成高度」是**全图**重生成，会覆盖用户手画的山脉位置 → 和用户意图打架
- 「画山脉」（ridge 工具）是**画一条线**生成新山脊 → 不能"润色已画的大饼"
- 「高度画笔（抬升/下沉/平滑）」是手动雕刻 → 用户已经画累了才来找局部重塑

**用户真实需求**：以我画的为基础，让算法帮我"美化"选中的一块。

---

## 2. 目标

设计一个**局部精修（Refine Heightmap Region）**功能，满足：

1. **非破坏**：用户画的高度形状（哪高哪低）100% 保留
2. **选区**：通过套索自由画一个圈，只精修圈内
3. **可调强度**：滑块 0% = 不动，100% = 狠狠加
4. **三种加工可单选**：山脊尖锐化 / 侵蚀沟壑 / 噪声质感
5. **边界羽化**：圈外→圈内渐变 20 像素宽，不出现硬边
6. **可预览**：勾选「实时预览」拖滑块就看得到
7. **可撤销**：Ctrl+Z 回滚

---

## 3. UX 流程

```
用户在「高度」模式
   ↓
① 点【局部精修】按钮（新增）
   ↓
② 鼠标变套索光标 → 按住左键画一个闭合圈
   ↓
③ 松开鼠标 → 弹出【精修参数】对话框：
     ┌─────────────────────────────────┐
     │  精修强度:  [▓▓▓▓▓░░░░░] 50%    │
     │                                 │
     │  ☑ 加山脊 (让山更尖)            │
     │  ☑ 加侵蚀 (加沟壑)              │
     │  ☐ 加噪声 (岩石质感)            │
     │                                 │
     │  种子: [42]  [🎲 随机]           │
     │                                 │
     │  ☑ 实时预览                     │
     │                                 │
     │        [取消]  [确定]           │
     └─────────────────────────────────┘
   ↓
④ 拖滑块/切开关 → 画布实时刷新预览
   ↓
⑤ 确定 → 写入 heightmap（入 undo 栈）
   取消 → 恢复原高度
```

**边界情况**：
- 套索圈太小（< 20×20 像素）→ 弹提示"选区太小"
- 圈在全海洋区域 → 什么都不做（算法只作用于陆地）
- 用户按 ESC → 退出精修模式

---

## 4. 架构

### 新增文件

| 文件 | 职责 |
|---|---|
| `domain/tools/lasso_selection.py` | 通用套索选区工具（产出 bool mask） |
| `commands/map/refine_height_region.py` | 局部精修 Command（支持 undo） |
| `features/map/height/refine_dialog.py` | 精修参数对话框（含实时预览） |

### 修改文件

| 文件 | 改动 |
|---|---|
| `services/terrain_service.py` | 新增 `refine_heightmap_region(height, mask, strength, enable_ridge, enable_erosion, enable_noise, seed) -> np.ndarray` |
| `features/map/height/page.py` | 加【局部精修】按钮 + 启动精修模式 + 接收选区 → 开对话框 |
| `domain/tools/registry.py` | 注册新的 `lasso_selection` 工具 |
| `ui/i18n/zh/height.py` + `ui/i18n/en/height.py` | 加新 key |

### 数据流

```
┌─ [局部精修] 按钮 ──→ 激活 lasso_selection 工具
│                           │
│                           ↓
│                      用户画圈（产出 mask : bool[H,W]）
│                           │
│                           ↓
│                      RefineDialog(mask, map_data)
│                           │     ↑
│                           │     └─── 滑块/开关变化
│                           ↓
│                      实时调用 refine_heightmap_region(...)
│                      更新 preview_height_map（临时数组）
│                           │
│                           ↓（用户点确定）
│                      RefineHeightRegionCommand.execute()
│                      → map_data.height_map = new_height
│                      → CommandBus.push(undo)
│                      → EventBus.emit("height_changed")
```

---

## 5. 算法详细：`refine_heightmap_region`

**输入**：
- `height: np.ndarray (H,W) uint8` — 原高度图
- `mask: np.ndarray (H,W) bool` — 精修区域
- `strength: float ∈ [0, 1]` — 精修强度
- `enable_ridge, enable_erosion, enable_noise: bool` — 三个开关
- `seed: int` — 随机种子（控制侵蚀/噪声的随机模式）
- `tile_map: np.ndarray (H,W) uint8` — 用来区分陆/海/湖（不处理非陆地）

**输出**：`np.ndarray (H,W) uint8` — 新高度图（整张，非选区部分和输入相同）

**流程**（只在 `mask & (tile_map == LAND)` 上做加工，其他像素原样返回）：

```
1. 边界羽化权重图
   w = distance_transform_edt(mask)              # 每像素到边界距离
   w = clip(w / 20.0, 0, 1)                       # 0..20 线性渐变，>20 全权重
   w *= strength                                  # 乘上强度滑块

2. 山脊尖锐化（可选）
   if enable_ridge:
       # 用 Laplacian 找局部极大值（山脊特征）
       from scipy.ndimage import maximum_filter
       local_max = maximum_filter(height, size=5)
       ridge_mask = (height == local_max) & (height > SEA_LEVEL + 20)
       # 把脊线像素及其邻域抬 15 像素
       ridge_boost = gaussian_filter(ridge_mask.astype(f32) * 15.0, sigma=2)
       height_work += ridge_boost * w

3. 侵蚀沟壑（可选）
   if enable_erosion:
       # 简化水力侵蚀：从每个高点沿最陡坡向模拟水流 30 步，削低路径
       # 复用 scipy 梯度 + 随机起点（用 seed）
       erosion = _simulate_erosion(height_work, seed, iterations=30)
       height_work -= erosion * w * 10.0

4. 高度相关噪声（可选）
   if enable_noise:
       # 高处加更多噪声（岩石质感），低处少加（平原）
       rng = np.random.default_rng(seed)
       noise = rng.standard_normal(height.shape) * 4.0
       noise = gaussian_filter(noise, sigma=1.5)   # 稍微平滑
       height_factor = clip((height - SEA_LEVEL) / 100, 0, 1)
       height_work += noise * height_factor * w

5. 合成输出
   result = height.copy()
   result[mask & land] = clip(height_work[mask & land], SEA_LEVEL + 1, 255)
   return result.astype(uint8)
```

**关键设计**：
- `w` 是羽化权重，边界处 0→1 过渡 20 像素，**保证无硬边**
- 所有加工都是**加减**，不重算高度；`strength=0` 时 `w=0`，完全不动原图
- `height[!mask]` 永不被修改
- 保留 HOI4 海陆约束：陆地 ≥ SEA_LEVEL+1，不会把陆地削到海平面以下

**`_simulate_erosion` 简化算法**（不做流体模拟，用 ridge 反向）：
```
for 随机起点 P (数量 = 选区像素数 × 0.005):
    for step in range(30):
        在 P 的 3x3 邻域找最低点 N
        erosion[N] += 0.3
        erosion[P] += 0.1
        P = N  # 水流到 N
        if P 是海 or erosion 达上限: break
return erosion  # 将在第 3 步乘以 w * 10
```

---

## 6. Command 细节

```python
# commands/map/refine_height_region.py
class RefineHeightRegionCommand(Command):
    label = "局部精修高度"

    def __init__(self, map_data, mask, refine_params):
        self._map_data = map_data
        self._mask = mask.copy()
        self._params = refine_params  # dict: strength, ridge, erosion, noise, seed
        self._old_heights: np.ndarray | None = None

    def execute(self):
        # 保存选区内原高度
        self._old_heights = self._map_data.height_map[self._mask].copy()
        # 跑算法
        new_map = refine_heightmap_region(
            height=self._map_data.height_map,
            mask=self._mask,
            tile_map=self._map_data.tile_map,
            **self._params,
        )
        self._map_data.height_map[:] = new_map

    def undo(self):
        if self._old_heights is not None:
            self._map_data.height_map[self._mask] = self._old_heights
```

---

## 7. 对话框行为

**实时预览实现要点**：
- 打开对话框时 **snapshot** 当前 `height_map` → `self._original_height = height_map.copy()`
- 每次参数变化（滑块/开关），**不改 map_data**，只计算一次 refine → 更新 renderer 的显示 buffer
- 点「取消」→ 渲染恢复原始
- 点「确定」→ 把算出的 new_height 作为参数创建 Command，push undo 栈

**性能**：
- 选区一般 200×200 ~ 800×800 像素，算法每次 50-200ms 可接受
- 实时预览用 `QTimer.singleShot(100)` debounce，避免拖滑块时疯狂计算

---

## 8. i18n 新 key（加到 `ui/i18n/{zh,en}/height.py`）

```python
# height.py 新增
"height_btn_refine": "局部精修" / "Local Refine"
"height_btn_refine_tip": "框选一块区域，以你画的高度为基础加入山脊/侵蚀/噪声" /
                         "Select an area; enhance your painted heights with ridges/erosion/noise"
"refine_dlg_title": "局部精修高度" / "Refine Height Locally"
"refine_dlg_strength": "精修强度" / "Refine Strength"
"refine_dlg_ridge": "加山脊 (让山更尖)" / "Add Ridges (Sharpen peaks)"
"refine_dlg_erosion": "加侵蚀 (加沟壑)" / "Add Erosion (Carve valleys)"
"refine_dlg_noise": "加噪声 (岩石质感)" / "Add Noise (Rocky texture)"
"refine_dlg_seed": "种子" / "Seed"
"refine_dlg_randomize": "随机" / "Randomize"
"refine_dlg_preview": "实时预览" / "Live Preview"
"refine_dlg_area_too_small": "选区太小（需要至少 20×20 像素）" /
                              "Selection too small (need at least 20x20 pixels)"
"status_refine_mode": "局部精修模式：画一个圈框住要精修的区域" /
                      "Refine mode: draw a loop to select the area"
"status_refine_done": "局部精修完成" / "Local refine applied"
```

---

## 9. 测试

**单元测试** `tests/services/test_terrain_refine.py`：
1. `strength=0` → 输出 === 输入（逐像素）
2. `mask` 内无陆地 → 输出 === 输入
3. 所有开关关 → 输出 === 输入
4. 只开 ridge，原图有明显山脉 → 山脉像素高度上升，非山脉不变
5. 只开 erosion，原图平原 → 有部分像素高度下降
6. `mask` 边界 20 像素外的高度**完全不变**
7. 跑完后陆地高度仍 ≥ `SEA_LEVEL + 1`（不会把陆变海）

**手动测试**：
1. 画一片"大饼山"（高度均匀的圆盘）→ 精修 100% 山脊开启 → 看到山脊浮现
2. 精修后按 Ctrl+Z → 恢复原状
3. 选区画在海上 → 点确定不崩
4. 实时预览拖滑块 → 画布跟着变化，松手后稳定在最终值

---

## 10. 风险与回滚

**潜在风险**：
- 预览实现不当可能导致画布刷新抖动 → 用 QTimer debounce 100ms
- 侵蚀算法在超大选区（>2000×2000）可能慢 → 首版限制选区面积 ≤ 500000 像素，超了提示用户
- 羽化宽度 20 像素在极小选区（<40×40）效果差 → 自动缩到 `min(20, min(选区尺寸)/3)`

**回滚**：
- 本功能是**加功能**，和现有代码无冲突。关掉不影响其他任何地方
- 如发现算法输出异常，`git revert <commit>` 即可
- 现有的 SetHeightCommand/SmoothHeight 等工具不受影响

---

## 11. 实施顺序（给 writing-plans 阶段用）

1. **算法优先**：先写 `refine_heightmap_region` + 单测（可先用 matplotlib 手动肉眼验证效果）
2. **Command 接入**：接 `RefineHeightRegionCommand`
3. **套索工具**：`LassoSelectionTool` → 产出 bool mask
4. **UI 接入**：页面按钮 + RefineDialog（先不带实时预览）
5. **实时预览**：加 preview snapshot + QTimer debounce
6. **i18n**：补齐翻译
7. **手动跑一遍**：画个大饼山验证效果
8. **单测补齐**：边界条件

---

## 12. 不做的事（YAGNI）

- 不做完整的水力侵蚀流体模拟（只做简化版，性能和效果够用即可）
- 不做 3D 可视化预览（2D 高度色带已够判断）
- 不支持多选区合并精修（一次只处理一个圈）
- 不支持保存"常用预设"（等用户提出再加）
- 不加 undo 记录每个中间预览（只 undo 最终结果）
