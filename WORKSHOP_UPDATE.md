# v1.2.0 更新日志 / Patch Notes

> 含 v1.1.2 起的新内容（state 三层叠加视图）

---

## 中文版（粘贴到创意工坊）

**v1.2.0 — 俄语支持 + 13 page UI 审计 + 一堆崩溃修复**

### 🌍 多语言
- **新增俄语 (ru) 支持** — 三语 1061 key 齐全
- 新工具 `tools/i18n_audit.py` / `tools/i18n_add_key.py`，加新语言/新 key 不用手动 grep
- `tr()` 加 kwargs 支持，placeholder 异常不再静默吞
- 修复俄语 UI 字间距异常 + tab 文字截断 (qdarktheme + CJK 字体冲突)

### 🎨 UI 全套审计完成
- **13 个 page 视觉统一**：Land / Density / Province / Height / Terrain / River / State / Country / Continent / StrategicRegion / Logistics / Colormap / DefaultMap
- 大陆页：全 manager 操作可撤销 (Ctrl+Z 全部能回滚)
- 省份页：新增「查找省份」按 ID 跳转 + 高亮
- ContinentPage 跟其他 page 统一视觉 + 改名按真名

### 🗺 State 模式三层叠加视图（v1.1.2 起）
编辑省份归属时一眼分清哪国：
- 底色 = state 色 ⊗ 国家色 50/50 混合（同国家整体偏向 owner 色，相邻 state 仍可区分）
- 3 像素白色国家边界（只画两个已分配国家之间）
- 选中某州 → 同 owner 全国暖黄高亮

### 🐛 崩溃修复
- **打包后启动崩溃**：qdarktheme 数据文件缺失 (.qss / .svg)
- 战略区 / 省份合并 / 增量生成相关 BUG
- 选中州时 `AttributeError get_state_owner` → 改用 `get_owner_of_state`
- 7 个崩溃 BUG + Vanilla 命名空间隔离

### 📤 导出
- 新增「descriptor 独立开关」— 允许只导出内容文件，不覆盖现有 descriptor.mod
- 修：导出尺寸限制 / from-import 陷阱 / transform 复制 BUG

### 🧪 测试
- 165 测试全过
- i18n smoke 测试覆盖三语 1061 key

---

## English Version

**v1.2.0 — Russian Support + 13-Page UI Audit + Crash Fixes**

### 🌍 Localization
- **Russian (ru) support added** — 1061 keys complete across all 3 languages
- New tools `tools/i18n_audit.py` / `tools/i18n_add_key.py` — adding a new language or new key no longer requires manual grep
- `tr()` now supports kwargs; placeholder exceptions no longer silently swallowed
- Fixed Russian UI letter-spacing anomaly + tab text truncation (qdarktheme + CJK font conflict)

### 🎨 Full UI Audit Done
- **13 pages visually unified**: Land / Density / Province / Height / Terrain / River / State / Country / Continent / StrategicRegion / Logistics / Colormap / DefaultMap
- Continent page: every manager action now undoable (Ctrl+Z rolls back everything)
- Province page: new "Find Province" jump-to-ID + highlight
- ContinentPage visually aligned with other pages + renamed to its real name

### 🗺 State Mode 3-Layer Overlay (since v1.1.2)
See at a glance which country owns what while editing province assignments:
- Base = state color ⊗ country color 50/50 (same country tints toward owner color, adjacent states still distinguishable)
- 3-pixel white country borders (only between two assigned countries)
- Select a state → entire same-owner country highlighted in warm yellow

### 🐛 Crash Fixes
- **Startup crash after packaging**: qdarktheme data files missing (.qss / .svg)
- Strategic region / province merge / incremental generation bugs
- Select state `AttributeError get_state_owner` → use `get_owner_of_state`
- 7 crash bugs + Vanilla namespace isolation

### 📤 Export
- New "descriptor standalone toggle" — allows exporting only content files without overwriting existing descriptor.mod
- Fixed: export size limit / from-import trap / transform copy bug

### 🧪 Testing
- 165 tests all pass
- i18n smoke test covers all 1061 keys across 3 languages
