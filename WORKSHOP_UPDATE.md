# v1.0.1 更新日志 / Patch Notes

---

## 中文版（粘贴到创意工坊）

**v1.0.1 - 崩溃修复 + 中文命名支持**

### 🐛 修复崩溃
- **修复：导出 MOD 进游戏点"开始"即崩溃**
  - 根因：战略区/海岸省份坐标判定的三重不同步
  - 具体：① coastal 判定改用 HOI4 一致的省级邻接 ② tile_map 自动对齐省份分类 ③ naval_base 坐标改用像素中心（+0.5）避免 HOI4 floor 取整落海像素
- **修复：战略区名字输入中文直接崩游戏**
  - 根因：战略区 .txt 里的 name 字段直接写了中文
  - 修复：name 字段永远只写 localisation key，中文走 yml 本地化

### ✨ 新功能：命名支持双语
- State / 战略区 / VP 城市 都新增"英文名"独立输入框
- 英文 yml 用英文名，中文 yml 用中文名，不再共用一份
- 留空自动用默认值（如 `State 123` / `Region 5`）
- 兼容旧项目数据

### 🔧 其他修复
- 战略区生成按州连贯（之前会跳省份）
- 州算法连通性修复
- 平滑省份 / 平滑陆地功能
- 右键设置胜利点

---

## English Version

**v1.0.1 - Crash Fix + Bilingual Naming**

### 🐛 Crash Fixes
- **Fixed: Game crashes on "Start" after exporting MOD**
  - Root cause: 3-way mismatch in coastal province detection
  - Fix: ① Coastal detection now uses HOI4-compatible province-level adjacency ② tile_map auto-aligned to province classification ③ naval_base coordinates use pixel center (+0.5) to avoid HOI4 floor-rounding to sea pixels
- **Fixed: Game crash when strategic region name contains Chinese**
  - Root cause: Strategic region .txt wrote Chinese name directly
  - Fix: name field always writes localisation key; display names go through yml localization

### ✨ New Feature: Bilingual Naming
- States / Strategic Regions / VP Cities now have separate "English Name" input fields
- English yml uses English name, Chinese yml uses Chinese name (no longer shared)
- Leave empty to use defaults (e.g. `State 123` / `Region 5`)
- Backward compatible with old project files

### 🔧 Other Fixes
- Strategic region generation now follows state boundaries (no more province skipping)
- State algorithm connectivity fix
- Province / land smoothing feature
- Right-click to set victory points
