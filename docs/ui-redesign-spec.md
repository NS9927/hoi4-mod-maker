# UI 重设计规格 — 2026-04-10

## 核心改动
1. **分组折叠 tab** 替换平铺 tab（三组：地图绘制/区域管理/后勤配置）
2. **图标 + 文字** 按钮
3. **全部去弹窗** — 所有编辑内联侧边栏，复杂内容用折叠 section + 滚动
4. **侧边栏可拖拽调宽**（默认 320px，最小 260，最大 500）
5. **全新配色** — 中性深灰 + 紫蓝强调（参考 VS Code/Figma 深色主题）

## 分组

### 🗺 地图绘制
- 大陆 (land)
- 省份 (province)
- 地形 (terrain)
- 高度 (height)
- 河流 (river)

### 📋 区域管理
- State (state) — 内联详情: 基础/资源/建筑/省份建筑/核心宣称 各一个折叠 section
- 国家 (country)
- 大陆分区 (continent) — 从菜单弹窗迁来
- 战略区 (strategic_region) — 从菜单弹窗迁来

### ⚙ 后勤 / 配置
- 后勤 (logistics) — adjacencies + 铁路 + 补给 + adjacency_rules
- 总览贴图 (colormap) — 从菜单弹窗迁来
- 地图配置 (default_map) — 从菜单弹窗迁来

## 配色
- 背景: #1e1e2e
- 面板: #252535
- 强调: #6c6cf0 (紫蓝)
- 分组标题: #7c7cff
- 文字: #e0e0f0
- 边框: #3a3a4a
- 选中: #6c6cf0 白字
- 按钮hover: rgba(108,108,240,0.15)
- 成功(导出): #22c55e

## 侧边栏
- 默认宽度 320px
- 用 QSplitter 实现可拖拽
- 每个 page 内容包在 QScrollArea
- 折叠 section 用 QToolButton + QFrame 动画展开

## 删除
- 工具菜单的 5 个弹窗入口
- main_window 的 5 套 dialog handler
- State 的 "详情..." 弹窗入口（内联替代）
