"""
国际化支持 — 中英文切换
"""

# 当前语言（启动时从 QSettings 读取）
def _load_saved_language() -> str:
    try:
        from PyQt5.QtCore import QSettings
        s = QSettings("HOI4MapMaker", "Settings")
        return s.value("language", "zh")
    except Exception:
        return "zh"

_current_lang = _load_saved_language()

# 翻译字典
_translations: dict[str, dict[str, str]] = {
    # === 主窗口 ===
    "app_title": {
        "zh": "HOI4 幻想世界 MOD 制作工具","en": "HOI4 Fantasy World MOD Maker",},
    # 菜单 - 文件
    "menu_file": {"zh": "文件(&F)", "en": "&File"},
    "action_new": {"zh": "新建项目", "en": "New Project"},
    "action_open": {"zh": "打开项目", "en": "Open Project"},
    "action_save": {"zh": "保存项目", "en": "Save Project"},
    "action_import_image": {"zh": "导入参考图片", "en": "Import Reference Image"},
    "action_export_mod": {"zh": "导出 MOD", "en": "Export MOD"},
    "action_exit": {"zh": "退出", "en": "Exit"},

    # 菜单 - 编辑
    "menu_edit": {"zh": "编辑(&E)", "en": "&Edit"},
    "action_undo": {"zh": "撤销", "en": "Undo"},
    "action_redo": {"zh": "重做", "en": "Redo"},

    # 菜单 - 视图
    "menu_view": {"zh": "视图(&V)", "en": "&View"},
    "action_zoom_in": {"zh": "放大", "en": "Zoom In"},
    "action_zoom_out": {"zh": "缩小", "en": "Zoom Out"},
    "action_zoom_fit": {"zh": "适应窗口", "en": "Fit to Window"},
    "action_show_grid": {"zh": "显示网格", "en": "Show Grid"},
    "action_show_ref": {"zh": "显示参考图", "en": "Show Reference Image"},

    # 菜单 - 工具
    "menu_tools": {"zh": "工具(&T)", "en": "&Tools"},
    "action_generate_provinces": {"zh": "生成省份", "en": "Generate Provinces"},
    "action_validate": {"zh": "验证省份", "en": "Validate Provinces"},
    "action_generate_heightmap": {"zh": "生成高度图", "en": "Generate Heightmap"},

    # 菜单 - 设置
    "menu_settings": {"zh": "设置(&S)", "en": "&Settings"},
    "action_language": {"zh": "语言 / Language", "en": "Language / 语言"},
    "action_paths": {"zh": "路径设置", "en": "Path Settings"},

    # 菜单 - 帮助
    "menu_help": {"zh": "帮助(&H)", "en": "&Help"},
    "action_about": {"zh": "关于", "en": "About"},

    # === 工具面板 ===
    "panel_tools": {"zh": "工具", "en": "Tools"},
    "tool_brush": {"zh": "画笔", "en": "Brush"},
    "tool_eraser": {"zh": "橡皮擦", "en": "Eraser"},
    "tool_fill": {"zh": "填充", "en": "Fill"},
    "tool_pan": {"zh": "平移", "en": "Pan"},
    "tool_select": {"zh": "选择", "en": "Select"},

    "panel_brush_settings": {"zh": "画笔设置", "en": "Brush Settings"},
    "label_brush_size": {"zh": "大小:", "en": "Size:"},
    "label_brush_type": {"zh": "类型:", "en": "Type:"},

    "panel_tile_type": {"zh": "地块类型", "en": "Tile Type"},
    "tile_land": {"zh": "陆地", "en": "Land"},
    "tile_sea": {"zh": "海洋", "en": "Sea"},
    "tile_lake": {"zh": "湖泊", "en": "Lake"},

    "panel_terrain": {"zh": "地形类型", "en": "Terrain Type"},

    # === 省份生成 ===
    "dlg_generate_title": {"zh": "生成省份", "en": "Generate Provinces"},
    "label_province_count": {"zh": "省份数量:", "en": "Province Count:"},
    "label_land_ratio": {"zh": "陆地密度倍率:", "en": "Land Density Ratio:"},
    "btn_generate": {"zh": "生成", "en": "Generate"},
    "btn_cancel": {"zh": "取消", "en": "Cancel"},

    # === 验证 ===
    "validate_title": {"zh": "省份验证结果", "en": "Province Validation Results"},
    "validate_ok": {"zh": "验证通过，无问题", "en": "Validation passed, no issues"},
    "validate_x_crossing": {"zh": "X型交叉: {} 处", "en": "X-type crossings: {} found"},
    "validate_too_small": {"zh": "过小省份(<8像素): {} 个", "en": "Too small provinces (<8px): {} found"},
    "validate_not_contiguous": {"zh": "不连续省份: {} 个", "en": "Non-contiguous provinces: {} found"},
    "validate_coastal_mismatch": {"zh": "沿海状态不一致: {} 个", "en": "Coastal status mismatch: {} found"},
    "validate_color_duplicate": {"zh": "重复颜色: {} 组", "en": "Duplicate colors: {} found"},

    # === 导出 ===
    "export_title": {"zh": "导出 MOD", "en": "Export MOD"},
    "export_success": {"zh": "MOD 导出成功！\n路径: {}", "en": "MOD exported successfully!\nPath: {}"},
    "export_failed": {"zh": "导出失败: {}", "en": "Export failed: {}"},

    # === 状态栏 ===
    "status_ready": {"zh": "就绪", "en": "Ready"},
    "status_pos": {"zh": "位置: ({}, {})", "en": "Position: ({}, {})"},
    "status_zoom": {"zh": "缩放: {:.0%}", "en": "Zoom: {:.0%}"},
    "status_provinces": {"zh": "省份: {} 个", "en": "Provinces: {}"},
    "status_generating": {"zh": "正在生成省份...", "en": "Generating provinces..."},
    "status_validating": {"zh": "正在验证...", "en": "Validating..."},
    "status_exporting": {"zh": "正在导出...", "en": "Exporting..."},

    # === 河流 ===
    "mode_river": {"zh": "河流", "en": "River"},

    # === State 页面 ===
    "state_auto_btn": {"zh": "自动分组", "en": "Auto Group"},
    "state_per_spin_label": {"zh": "每State省份数:", "en": "Provinces per State:"},
    "state_batch_section": {"zh": "批量建州", "en": "Batch Create States"},
    "state_batch_select_btn": {"zh": "选择省份建州", "en": "Select Provinces to Create State"},
    "state_batch_select_tip": {"zh": "开启后点击省份多选，然后点确认创建新州", "en": "Enable to multi-select provinces, then confirm to create a new state"},
    "state_batch_confirm_btn": {"zh": "确认创建新州", "en": "Confirm Create State"},
    "state_list_section": {"zh": "State 列表", "en": "State List"},
    "state_props_section": {"zh": "State 属性", "en": "State Properties"},
    "state_name_label": {"zh": "名称:", "en": "Name:"},
    "state_manpower_label": {"zh": "人口:", "en": "Manpower:"},
    "state_category_label": {"zh": "类别:", "en": "Category:"},
    "state_detail_btn": {"zh": "详情... (资源/建筑/核心/宣称)", "en": "Details... (Resources/Buildings/Cores/Claims)"},
    "state_hint": {"zh": "选中State后点击省份可移入。双击State打开详情编辑资源/建筑/VP", "en": "Select a state then click provinces to assign. Double-click a state for resource/building/VP details"},

    # === 国家页面 ===
    "country_create_btn": {"zh": "创建国家", "en": "Create Country"},
    "country_quick_create_btn": {"zh": "快速创建国家", "en": "Quick Create Country"},
    "country_quick_create_tip": {"zh": "输入 TAG/名称/执政党，一键创建并进入领土分配模式", "en": "Enter TAG/name/ruling party, create and enter territory assignment mode"},
    "country_list_section": {"zh": "国家列表", "en": "Country List"},
    "country_props_section": {"zh": "国家属性", "en": "Country Properties"},
    "country_name_label": {"zh": "名称:", "en": "Name:"},
    "country_party_label": {"zh": "执政党:", "en": "Ruling Party:"},
    "country_color_label": {"zh": "颜色:", "en": "Color:"},
    "country_color_tip": {"zh": "点击修改颜色", "en": "Click to change color"},
    "country_capital_label": {"zh": "首都:", "en": "Capital:"},
    "country_capital_unset": {"zh": "未设置", "en": "Not Set"},
    "country_hint": {"zh": "选中国家后，点击State可分配领土\n快速创建: 创建后自动进入领土分配模式", "en": "Select a country, then click states to assign territory\nQuick create: auto-enters territory assignment mode"},
    "country_quick_dlg_title": {"zh": "快速创建国家", "en": "Quick Create Country"},
    "country_tag_placeholder": {"zh": "如 KAR (3个大写字母)", "en": "e.g. KAR (3 uppercase letters)"},
    "country_tag_row": {"zh": "TAG:", "en": "TAG:"},
    "country_name_placeholder": {"zh": "国家名称", "en": "Country Name"},
    "country_pick_color_title": {"zh": "选择国家颜色", "en": "Choose Country Color"},
    "country_tag_invalid": {"zh": "TAG 必须是 3 个字母", "en": "TAG must be 3 letters"},

    # === 大陆页面 ===
    "continent_tip": {"zh": "定义大陆 + 把省份指派到大陆.\nHOI4 要求所有陆地省份必须属于某个大洲，\n影响 continent.txt 和 definition.csv.\n先创建大陆(如 europe, asia)，再用拾取模式\n点击省份分配到选中的大陆.", "en": "Define continents and assign provinces.\nHOI4 requires all land provinces belong to a continent,\naffects continent.txt and definition.csv.\nCreate continents first (e.g. europe, asia), then use pick mode\nto assign provinces to the selected continent."},
    "continent_add_btn": {"zh": "添加", "en": "Add"},
    "continent_rename_btn": {"zh": "重命名", "en": "Rename"},
    "continent_delete_btn": {"zh": "删除", "en": "Delete"},
    "continent_pick_btn": {"zh": "开始指派省份", "en": "Start Assigning Provinces"},
    "continent_assign_by_state": {"zh": "按州(State)批量分配", "en": "Assign by State"},
    "continent_add_dlg_title": {"zh": "添加大陆", "en": "Add Continent"},
    "continent_add_dlg_label": {"zh": "大陆名 (英文):", "en": "Continent name (English):"},
    "continent_rename_dlg_title": {"zh": "重命名", "en": "Rename"},
    "continent_rename_dlg_label": {"zh": "新名字:", "en": "New name:"},

    # === 战略区域页面 ===
    "sr_tip": {"zh": "战略区域: 省份分组 + 天气 + 海军地形.\n建议先点'自动生成'按 State 创建初始分组，\n再手动调整。每个区域可设天气和海军地形类型.\n用拾取模式点省份可移入选中的区域.", "en": "Strategic regions: province grouping + weather + naval terrain.\nSuggest clicking 'Auto Generate' to create initial groups by state,\nthen adjust manually. Each region can set weather and naval terrain.\nUse pick mode to move provinces into the selected region."},
    "sr_auto_btn": {"zh": "自动生成 (按 State 分组)", "en": "Auto Generate (Group by State)"},
    "sr_auto_weather_btn": {"zh": "\U0001f30d 按纬度自动分配天气", "en": "\U0001f30d Auto-Assign Weather by Latitude"},
    "sr_from_states_btn": {"zh": "选择州 → 创建战略区域", "en": "Select States → Create Strategic Region"},
    "sr_from_states_tip": {"zh": "开启后点击地图选择多个州，然后点确认合并为一个战略区域", "en": "Enable to select multiple states on map, then confirm to merge into one strategic region"},
    "sr_from_states_confirm_btn": {"zh": "确认创建战略区域", "en": "Confirm Create Strategic Region"},
    "sr_new_btn": {"zh": "新建空区域", "en": "New Empty Region"},
    "sr_delete_btn": {"zh": "删除", "en": "Delete"},
    "sr_name_label": {"zh": "名字:", "en": "Name:"},
    "sr_weather_label": {"zh": "天气:", "en": "Weather:"},
    "sr_naval_label": {"zh": "Naval:", "en": "Naval:"},
    "sr_naval_none": {"zh": "(无)", "en": "(None)"},
    "sr_prov_count": {"zh": "省份: {}", "en": "Provinces: {}"},
    "sr_pick_btn": {"zh": "开始拾取省份（陆地+海洋）", "en": "Start Picking Provinces (Land + Ocean)"},

    # === 后勤页面 ===
    "logistics_tip": {"zh": "后勤系统管理: 海峡 / 铁路 / 补给节点\n相邻关系: 定义海峡通道/运河/不可通行区域\n铁路: 连接省份的补给线路(1-5级)\n补给节点: 陆地省份上的物资中转站", "en": "Logistics management: Straits / Railways / Supply Nodes\nAdjacency: Define strait passages/canals/impassable areas\nRailways: Supply lines between provinces (level 1-5)\nSupply nodes: Material transit stations on land provinces"},
    "logistics_adj_section": {"zh": "相邻关系 (海峡 / 运河 / 阻塞)", "en": "Adjacency (Straits / Canals / Impassable)"},
    "logistics_adj_count": {"zh": "{} 条", "en": "{} entries"},
    "logistics_adj_editor_btn": {"zh": "打开相邻关系编辑器...", "en": "Open Adjacency Editor..."},
    "logistics_rail_section": {"zh": "铁路", "en": "Railways"},
    "logistics_rail_count": {"zh": "{} 条", "en": "{} entries"},
    "logistics_rail_level_label": {"zh": "画笔等级:", "en": "Brush Level:"},
    "logistics_rail_draw_btn": {"zh": "启用铁路画笔", "en": "Enable Railway Brush"},
    "logistics_rail_list_btn": {"zh": "铁路列表...", "en": "Railway List..."},
    "logistics_supply_section": {"zh": "补给节点", "en": "Supply Nodes"},
    "logistics_supply_count": {"zh": "{} 个", "en": "{} nodes"},
    "logistics_supply_pick_btn": {"zh": "启用补给点拾取", "en": "Enable Supply Node Picker"},
    "logistics_supply_hint": {"zh": "开启后点击陆地省份: 切换该省是否为补给节点", "en": "When enabled, click land provinces to toggle supply node status"},

    # === 总览贴图颜色页面 ===
    "colormap_tip": {"zh": "战略视角缩放时的全图底色(colormap).\n这是 HOI4 缩到最远时看到的颜色贴图，\n分别设置陆地/海洋/湖泊的底色.\n改颜色后下次导出生效.", "en": "Strategic view base colors (colormap).\nThis is the color map seen when zoomed out fully in HOI4.\nSet base colors for land/sea/lake separately.\nColor changes take effect on next export."},
    "colormap_land_label": {"zh": "陆地:", "en": "Land:"},
    "colormap_sea_label": {"zh": "海洋:", "en": "Sea:"},
    "colormap_lake_label": {"zh": "湖泊:", "en": "Lake:"},
    "colormap_reset_btn": {"zh": "恢复默认", "en": "Reset to Default"},
    "colormap_pick_color_title": {"zh": "选择{}颜色", "en": "Choose {} Color"},

    # === 地图配置页面 ===
    "defmap_tip": {"zh": "HOI4 引擎 default.map 配置.\n河流最大等级: 河流渲染时的最粗级别(默认5)\n树木调色板: 控制地图上森林/树木的显示色号\n修改后下次导出生效.", "en": "HOI4 engine default.map configuration.\nMax river level: thickest river rendering level (default 5)\nTree palette: controls forest/tree display color indices\nChanges take effect on next export."},
    "defmap_river_max_label": {"zh": "河流最大等级:", "en": "Max River Level:"},
    "defmap_tree_palette_label": {"zh": "树木调色板索引:", "en": "Tree Palette Indices:"},
    "defmap_add_btn": {"zh": "添加", "en": "Add"},
    "defmap_delete_btn": {"zh": "删除", "en": "Delete"},
    "defmap_reset_btn": {"zh": "恢复默认", "en": "Reset to Default"},

    # === 通用 ===
    "btn_ok": {"zh": "确定", "en": "OK"},
    "btn_apply": {"zh": "应用", "en": "Apply"},
    "btn_close": {"zh": "关闭", "en": "Close"},
    "btn_yes": {"zh": "是", "en": "Yes"},
    "btn_no": {"zh": "否", "en": "No"},
    "dlg_confirm": {"zh": "确认", "en": "Confirm"},
    "dlg_warning": {"zh": "警告", "en": "Warning"},
    "dlg_error": {"zh": "错误", "en": "Error"},

    # === 页面 UI (自动生成) ===
    "colormap_lake_label": {"zh": "湖泊:", "en": "Lake:"},
    "colormap_land_label": {"zh": "陆地:", "en": "Land:"},
    "colormap_pick_color_title": {"zh": "选择{}颜色", "en": "Choose {} Color"},
    "colormap_reset_btn": {"zh": "恢复默认", "en": "Reset to Default"},
    "colormap_sea_label": {"zh": "海洋:", "en": "Sea:"},
    "colormap_tip": {"zh": "战略视角缩放时的全图底色(colormap).\n分别设置陆地/海洋/湖泊的底色.\n改颜色后下次导出生效.", "en": "Strategic view base colors.\nSet land/sea/lake colors.\nChanges apply on next export."},
    "continent_add_btn": {"zh": "添加", "en": "Add"},
    "continent_add_dlg_label": {"zh": "大陆名 (英文):", "en": "Continent name (English):"},
    "continent_add_dlg_title": {"zh": "添加大陆", "en": "Add Continent"},
    "continent_delete_btn": {"zh": "删除", "en": "Delete"},
    "continent_pick_btn": {"zh": "开始指派省份", "en": "Start Assigning Provinces"},
    "continent_rename_btn": {"zh": "重命名", "en": "Rename"},
    "continent_rename_dlg_label": {"zh": "新名字:", "en": "New name:"},
    "continent_rename_dlg_title": {"zh": "重命名", "en": "Rename"},
    "continent_tip": {"zh": "定义大陆 + 把省份指派到大陆.HOI4 要求所有陆地省份必须属于某个大洲，影响 continent.txt 和 definition.csv.先创建大陆(如 europe, asia)，再用拾取模式点击省份分配到选中的大陆.", "en": "Define continents and assign provinces.HOI4 requires all land provinces belong to a continent,affects continent.txt and definition.csv.Create continents first (e.g. europe, asia), then use pick modeto assign provinces to the selected continent."},
    "country_capital_label": {"zh": "首都:", "en": "Capital:"},
    "country_capital_unset": {"zh": "未设置", "en": "Not Set"},
    "country_color_label": {"zh": "颜色:", "en": "Color:"},
    "country_color_tip": {"zh": "点击修改颜色", "en": "Click to change color"},
    "country_create_btn": {"zh": "创建国家", "en": "Create Country"},
    "country_hint": {"zh": "选中国家后，点击State可分配领土快速创建: 创建后自动进入领土分配模式", "en": "Select a country, then click states to assign territoryQuick create: auto-enters territory assignment mode"},
    "country_list_section": {"zh": "国家列表", "en": "Country List"},
    "country_name_label": {"zh": "名称:", "en": "Name:"},
    "country_name_placeholder": {"zh": "国家名称", "en": "Country Name"},
    "country_party_label": {"zh": "执政党:", "en": "Ruling Party:"},
    "country_pick_color_title": {"zh": "选择国家颜色", "en": "Choose Country Color"},
    "country_props_section": {"zh": "国家属性", "en": "Country Properties"},
    "country_quick_create_btn": {"zh": "快速创建国家", "en": "Quick Create Country"},
    "country_quick_create_tip": {"zh": "输入 TAG/名称/执政党，一键创建并进入领土分配模式", "en": "Enter TAG/name/ruling party, create and enter territory assignment mode"},
    "country_quick_dlg_title": {"zh": "快速创建国家", "en": "Quick Create Country"},
    "country_tag_invalid": {"zh": "TAG 必须是 3 个字母", "en": "TAG must be 3 letters"},
    "country_tag_placeholder": {"zh": "如 KAR (3个大写字母)", "en": "e.g. KAR (3 uppercase letters)"},
    "country_tag_row": {"zh": "TAG:", "en": "TAG:"},
    "defmap_add_btn": {"zh": "添加", "en": "Add"},
    "defmap_delete_btn": {"zh": "删除", "en": "Delete"},
    "defmap_reset_btn": {"zh": "恢复默认", "en": "Reset to Default"},
    "defmap_river_max_label": {"zh": "河流最大等级:", "en": "Max River Level:"},
    "defmap_tip": {"zh": "HOI4 引擎 default.map 配置.河流最大等级: 河流渲染时的最粗级别(默认5)树木调色板: 控制地图上森林/树木的显示色号修改后下次导出生效.", "en": "HOI4 engine default.map configuration.Max river level: thickest river rendering level (default 5)Tree palette: controls forest/tree display color indicesChanges take effect on next export."},
    "defmap_tree_palette_label": {"zh": "树木调色板索引:", "en": "Tree Palette Indices:"},
    "group_logistics_config": {"zh": "后勤与配置", "en": "Logistics & Config"},
    "group_map_drawing": {"zh": "地图绘制", "en": "Map Drawing"},
    "group_region_mgmt": {"zh": "区域管理", "en": "Region Management"},
    "height_brush_hint": {"zh": "选一个高度值，然后在地图上画。用于局部调高/调低", "en": "Pick a height value and paint on map. For local adjustments"},
    "height_btn_auto_gen": {"zh": "智能生成高度", "en": "Smart Generate Height"},
    "height_btn_auto_gen_tip": {"zh": "根据陆地形状自动算出海岸低、内陆高、有山脉有谷地的高度图", "en": "Auto-generate heightmap: low coast, high inland, with mountains and valleys"},
    "height_btn_random": {"zh": "随机", "en": "Random"},
    "height_btn_smooth": {"zh": "平滑高度", "en": "Smooth Height"},
    "height_btn_smooth_tip": {"zh": "高斯模糊让高度过渡更柔和", "en": "Gaussian blur for smoother height transitions"},
    "height_section_ridge": {"zh": "山脉画线", "en": "Draw Mountain Ridge"},
    "height_ridge_hint": {"zh": "在地图上拖拽画出山脉走向，松开鼠标后自动生成山脊和两侧衰减", "en": "Drag on the map to draw a mountain ridge. Heights fall off naturally from the ridge line."},
    "height_btn_ridge": {"zh": "画山脉模式", "en": "Ridge Drawing Mode"},
    "height_btn_ridge_confirm": {"zh": "确认生成山脉", "en": "Confirm Ridge"},
    "height_label_ridge_peak": {"zh": "山峰高度:", "en": "Peak Height:"},
    "height_label_ridge_falloff": {"zh": "衰减距离:", "en": "Falloff Distance:"},
    "status_ridge_mode_on": {"zh": "山脉画线模式：在地图上拖拽画山脉", "en": "Ridge mode: drag on map to draw mountains"},
    "status_ridge_mode_off": {"zh": "山脉画线模式已关闭", "en": "Ridge drawing mode off"},
    "status_ridge_applied": {"zh": "山脉已生成", "en": "Mountain ridge applied"},
    "status_ridge_preview": {"zh": "山脉预览中 — 调整参数后点「确认生成山脉」", "en": "Ridge preview — adjust params then click Confirm"},
    "height_hint": {"zh": "① 先画好陆地/海洋② 点「智能生成高度」自动算出山谷起伏③ 不满意可换种子重来，或用画笔微调④ 高度图做好后，切「地形」模式生成地形", "en": "1. Draw land/sea first2. Click Smart Generate for auto heightmap3. Change seed or brush-adjust if needed4. Switch to Terrain mode after"},
    "height_label_mountain": {"zh": "山脉强度:", "en": "Mountain Strength:"},
    "height_label_seed": {"zh": "种子:", "en": "Seed:"},
    "height_label_value": {"zh": "高度值:", "en": "Height Value:"},
    "height_preset_flat": {"zh": "平地", "en": "Flat"},
    "height_preset_hills": {"zh": "丘陵", "en": "Hills"},
    "height_preset_mountain": {"zh": "山", "en": "Mountain"},
    "height_preset_seabed": {"zh": "海底", "en": "Seabed"},
    "height_preset_sealevel": {"zh": "海面", "en": "Sea Level"},
    "height_preset_tip": {"zh": "高度值 = {}", "en": "Height value = {}"},
    "height_ref_text": {"zh": "0-94: 海底 (深色)95: 海平面96-114: 沿海低地 → 平原115-129: 中等 → 森林130-164: 较高 → 丘陵165-209: 高 → 山地210+: 极高 → 雪山", "en": "0-94: Seabed (dark)95: Sea level96-114: Coastal lowland → Plains115-129: Medium → Forest130-164: Higher → Hills165-209: High → Mountains210+: Very high → Snow peaks"},
    "height_section_auto_gen": {"zh": "智能生成", "en": "Smart Generation"},
    "height_section_brush": {"zh": "手动画笔", "en": "Manual Brush"},
    "height_section_manual": {"zh": "手动微调", "en": "Manual Fine-tune"},
    "height_import_btn": {"zh": "导入高度图", "en": "Import Heightmap"},
    "height_import_tip": {"zh": "导入灰度图（BMP/PNG）作为高度图，自动缩放到地图尺寸", "en": "Import a grayscale image (BMP/PNG) as heightmap, auto-scaled to map size"},
    "height_import_success": {"zh": "高度图导入成功", "en": "Heightmap imported successfully"},
    "height_import_fail": {"zh": "高度图导入失败: {}", "en": "Heightmap import failed: {}"},
    "height_brush_section": {"zh": "雕刻画笔", "en": "Sculpt Brush"},
    "height_brush_raise": {"zh": "抬升", "en": "Raise"},
    "height_brush_raise_tip": {"zh": "按住鼠标在陆地上刷，每笔让区域抬高（中心最强, 边缘衰减）", "en": "Hold & drag over land to raise terrain (strongest at center)"},
    "height_brush_lower": {"zh": "下沉", "en": "Lower"},
    "height_brush_lower_tip": {"zh": "按住鼠标在陆地上刷，每笔让区域下沉（但不会沉到海平面以下）", "en": "Hold & drag over land to lower terrain (but stays above sea level)"},
    "height_brush_smooth": {"zh": "平滑", "en": "Smooth"},
    "height_brush_smooth_tip": {"zh": "按住鼠标局部柔化高度，不破坏笔刷外的地形", "en": "Hold & drag to smooth heights locally (other areas untouched)"},
    "height_brush_size": {"zh": "画笔尺寸", "en": "Brush Size"},
    "height_brush_strength": {"zh": "强度", "en": "Strength"},
    "height_section_ref": {"zh": "高度含义", "en": "Height Reference"},
    "land_btn_fit_map": {"zh": "铺满地图", "en": "Fit to Map"},
    "land_btn_generate": {"zh": "生成省份", "en": "Generate Provinces"},
    "land_density_hint": {"zh": "可选：画密度图控制省份疏密（亮=密集，暗=稀疏）", "en": "Optional: paint density map to control province distribution (bright=dense, dark=sparse)"},
    "land_btn_paint_density": {"zh": "画密度图", "en": "Paint Density"},
    "land_btn_paint_density_tip": {"zh": "在地图上涂抹省份密度（亮色=省份多，暗色=省份少）", "en": "Paint province density on the map (bright=more provinces, dark=fewer)"},
    "land_btn_load_density": {"zh": "导入", "en": "Import"},
    "land_btn_clear_density": {"zh": "清除", "en": "Clear"},
    "land_label_density_value": {"zh": "画笔密度:", "en": "Brush Density:"},
    "land_density_none": {"zh": "未设置密度图（均匀生成）", "en": "No density map (uniform generation)"},
    "land_density_loaded": {"zh": "✓ 密度图已加载", "en": "✓ Density map loaded"},
    "land_density_painting": {"zh": "✓ 密度画笔模式（在地图上涂抹）", "en": "✓ Density paint mode (draw on map)"},
    "status_density_cleared": {"zh": "密度图已清除", "en": "Density map cleared"},

    # === 密度模式 ===
    "mode_density": {"zh": "省份密度", "en": "Province Density"},
    "density_hint": {"zh": "在地图上涂抹省份密度。亮色区域省份多（密集），暗色区域省份少（稀疏）。画完切到「省份」模式生成即可。", "en": "Paint province density on the map. Bright areas = more provinces (dense), dark areas = fewer (sparse). Switch to 'Province' mode to generate."},
    "density_section_brush": {"zh": "画笔", "en": "Brush"},
    "density_label_brush_size": {"zh": "画笔大小:", "en": "Brush Size:"},
    "density_label_soft_edge": {"zh": "软边缘:", "en": "Soft Edge:"},
    "density_section_value": {"zh": "密度值", "en": "Density Value"},
    "density_label_value": {"zh": "密度:", "en": "Density:"},
    "density_preset_sparse": {"zh": "稀疏", "en": "Sparse"},
    "density_preset_medium": {"zh": "中等", "en": "Medium"},
    "density_preset_dense": {"zh": "密集", "en": "Dense"},
    "density_section_ops": {"zh": "操作", "en": "Actions"},
    "density_btn_clear": {"zh": "清除密度图", "en": "Clear Density Map"},
    "density_btn_clear_tip": {"zh": "清除密度图，恢复均匀生成", "en": "Clear density map, restore uniform generation"},
    "density_op_hint": {"zh": "提示：右键拖拽 = 涂中性值（50%）\n不画密度图时省份均匀分布", "en": "Tip: Right-drag = paint neutral (50%)\nWithout density map, provinces distribute evenly"},
    "land_btn_hide": {"zh": "隐藏", "en": "Hide"},
    "land_btn_smooth_coast": {"zh": "平滑海岸线", "en": "Smooth Coastline"},
    "land_btn_smooth_coast_tip": {"zh": "用高斯模糊平滑陆海边界，让海岸线更自然（建议在生成省份之前使用）", "en": "Gaussian blur to smooth land/sea boundary for natural coastlines (use before generating provinces)"},
    "status_coast_smoothed": {"zh": "海岸线已平滑（全图）", "en": "Coastline smoothed (entire map)"},
    "status_coast_smoothed_region": {"zh": "海岸线已平滑（选区）", "en": "Coastline smoothed (selection)"},
    "land_btn_quick_init": {"zh": "一键初始化（州+战略区+国家）", "en": "Quick Init (State+Region+Country)"},
    "land_btn_quick_init_tip": {"zh": "自动生成州、战略区域、默认国家，一步到位可导出", "en": "Auto-generate states, strategic regions, and default country for export"},
    "land_btn_show": {"zh": "显示", "en": "Show"},
    "land_btn_validate": {"zh": "验证省份", "en": "Validate Provinces"},
    "land_draw_lake": {"zh": "画湖泊", "en": "Draw Lake"},
    "land_draw_land": {"zh": "画陆地", "en": "Draw Land"},
    "land_draw_sea": {"zh": "画海洋", "en": "Draw Sea"},
    "land_hint": {"zh": "画陆地/海洋/湖泊。画笔涂色，填充灌满区域，变换可框选移动/缩放/旋转", "en": "Draw land/sea/lake. Brush paints, fill floods region, transform selects area to move/scale/rotate"},
    "land_label_lake_density": {"zh": "湖泊密度:", "en": "Lake Density:"},
    "land_label_opacity": {"zh": "透明度:", "en": "Opacity:"},
    "land_label_province_count": {"zh": "省份数量:", "en": "Province Count:"},
    "land_label_scale": {"zh": "缩放:", "en": "Scale:"},
    "land_label_sea_density": {"zh": "海洋密度:", "en": "Sea Density:"},
    "land_label_size": {"zh": "大小:", "en": "Size:"},
    "land_section_brush_size": {"zh": "画笔大小", "en": "Brush Size"},
    "land_section_custom_ref": {"zh": "自定义参考图", "en": "Custom Reference Image"},
    "land_section_province_gen": {"zh": "省份生成", "en": "Province Generation"},
    "land_section_tile_draw": {"zh": "大陆绘制", "en": "Tile Drawing"},
    "land_section_tools": {"zh": "工具", "en": "Tools"},
    "land_section_ref": {"zh": "参考图", "en": "Reference Images"},
    "land_section_vanilla_ref": {"zh": "原版参考", "en": "Vanilla Reference"},
    "land_tool_brush": {"zh": "画笔", "en": "Brush"},
    "land_tool_eraser": {"zh": "橡皮", "en": "Eraser"},
    "land_tool_fill": {"zh": "填充 (F)", "en": "Fill (F)"},
    "land_tool_fill_tip": {"zh": "点击一个区域，自动填满相同类型的连通区域（快捷键 F）", "en": "Click a region to flood-fill connected area of same type (shortcut: F)"},
    "land_tool_pan": {"zh": "平移", "en": "Pan"},
    "land_tool_transform": {"zh": "变换", "en": "Transform"},
    "land_tool_transform_tip": {"zh": "框选区域后可移动/缩放/旋转。Enter确认，ESC取消", "en": "Select area to move/scale/rotate. Enter to confirm, ESC to cancel"},
    "logistics_adj_count": {"zh": "{} 条", "en": "{} entries"},
    "logistics_adj_editor_btn": {"zh": "打开相邻关系编辑器...", "en": "Open Adjacency Editor..."},
    "logistics_adj_section": {"zh": "相邻关系 (海峡 / 运河 / 阻塞)", "en": "Adjacency (Straits / Canals / Impassable)"},
    "logistics_rail_count": {"zh": "{} 条", "en": "{} entries"},
    "logistics_rail_draw_btn": {"zh": "启用铁路画笔", "en": "Enable Railway Brush"},
    "logistics_rail_level_label": {"zh": "画笔等级:", "en": "Brush Level:"},
    "logistics_rail_list_btn": {"zh": "铁路列表...", "en": "Railway List..."},
    "logistics_rail_section": {"zh": "铁路", "en": "Railways"},
    "logistics_supply_count": {"zh": "{} 个", "en": "{} nodes"},
    "logistics_supply_hint": {"zh": "开启后点击陆地省份: 切换该省是否为补给节点", "en": "When enabled, click land provinces to toggle supply node status"},
    "logistics_supply_pick_btn": {"zh": "启用补给点拾取", "en": "Enable Supply Node Picker"},
    "logistics_supply_section": {"zh": "补给节点", "en": "Supply Nodes"},
    "logistics_tip": {"zh": "后勤系统管理: 海峡 / 铁路 / 补给节点相邻关系: 定义海峡通道/运河/不可通行区域铁路: 连接省份的补给线路(1-5级)补给节点: 陆地省份上的物资中转站", "en": "Logistics management: Straits / Railways / Supply NodesAdjacency: Define strait passages/canals/impassable areasRailways: Supply lines between provinces (level 1-5)Supply nodes: Material transit stations on land provinces"},
    "mode_colormap": {"zh": "总览贴图", "en": "Colormap"},
    "mode_continent": {"zh": "大洲", "en": "Continent"},
    "mode_country": {"zh": "国家", "en": "Country"},
    "mode_default_map": {"zh": "地图配置", "en": "Map Config"},
    "mode_height": {"zh": "高度", "en": "Height"},
    "mode_land": {"zh": "陆地与海洋", "en": "Land & Sea"},
    "mode_logistics": {"zh": "后勤系统", "en": "Logistics"},
    "mode_province": {"zh": "省份", "en": "Province"},
    "mode_river_nav": {"zh": "河流", "en": "River"},
    "mode_state": {"zh": "州", "en": "State"},
    "mode_strategic_region": {"zh": "战略区", "en": "Strategic Region"},
    "mode_terrain": {"zh": "地形", "en": "Terrain"},
    "panel_export_btn": {"zh": "导出 MOD", "en": "Export MOD"},
    "province_btn_expand": {"zh": "扩张省份", "en": "Expand Province"},
    "province_btn_expand_tip": {"zh": "开启后：点击省份后拖动扩张边界，松手自动关闭", "en": "Enable: click province and drag to expand boundary. Auto-disables on release"},
    "province_btn_merge": {"zh": "合并省份", "en": "Merge Provinces"},
    "province_btn_merge_tip": {"zh": "开启后：点第一个省份，再点第二个省份，自动合并并关闭", "en": "Enable: click first province, then second to merge. Auto-disables after"},
    "province_btn_regen_exec": {"zh": "重新生成选区省份", "en": "Regenerate Selected"},
    "province_btn_regen_exec_tip": {"zh": "对选中的省份区域重新生成，其他区域不受影响", "en": "Regenerate selected province area, other areas unaffected"},
    "province_btn_select_area": {"zh": "选择区域", "en": "Select Area"},
    "province_btn_select_area_tip": {"zh": "开启后点击省份选择区域（多选），再点「重新生成」", "en": "Enable, click provinces to select area (multi), then click Regenerate"},
    "province_btn_split": {"zh": "切割选中省份", "en": "Split Selected Province"},
    "province_btn_split_tip": {"zh": "先点击选中一个省份，再点此按钮切割", "en": "Select a province first, then click to split"},
    "province_coastal_no": {"zh": "否", "en": "No"},
    "province_coastal_yes": {"zh": "是", "en": "Yes"},
    "province_hint_click_info": {"zh": "点击省份查看信息", "en": "Click province to view info"},
    "province_hint_default": {"zh": "点击查看省份信息。合并/扩张/切割需先点对应按钮开启", "en": "Click to view province info. Enable merge/expand/split via buttons first"},
    "province_hint_expand": {"zh": "扩张模式：点击省份后拖动扩张", "en": "Expand mode: click province and drag to expand"},
    "province_hint_split": {"zh": "切割模式：在省份上画一条线，松手沿线切开", "en": "Split mode: draw a line across a province to split it"},
    "province_hint_merge": {"zh": "合并模式：点第一个省份，再点第二个", "en": "Merge mode: click first province, then second"},
    "province_hint_regen": {"zh": "增量生成：点击省份选择区域（多选），然后点「重新生成」", "en": "Regen: click provinces to select (multi), then click Regenerate"},
    "province_info_coastal": {"zh": "沿海", "en": "Coastal"},
    "province_info_id": {"zh": "省份 ID", "en": "Province ID"},
    "province_info_pixels": {"zh": "像素数", "en": "Pixels"},
    "province_info_terrain": {"zh": "地形", "en": "Terrain"},
    "province_info_type": {"zh": "类型", "en": "Type"},
    "province_section_info": {"zh": "省份信息", "en": "Province Info"},
    "province_info_compact_default": {"zh": "ID: — | — | — | 0px", "en": "ID: — | — | — | 0px"},
    "province_section_regen": {"zh": "增量生成", "en": "Incremental Regen"},
    "province_section_tools": {"zh": "省份操作", "en": "Province Tools"},
    "river_btn_auto": {"zh": "自动生成河流", "en": "Auto Generate Rivers"},
    "river_btn_auto_tip": {"zh": "根据高度图自动生成河流网络（从山地汇流到海洋）", "en": "Auto-generate river network from heightmap (flow from mountains to ocean)"},
    "river_btn_validate": {"zh": "验证河流", "en": "Validate Rivers"},
    "river_auto_need_provinces": {"zh": "请先生成省份再自动生成河流", "en": "Please generate provinces before auto-generating rivers"},
    "status_auto_river": {"zh": "正在生成河流...", "en": "Generating rivers..."},
    "status_auto_river_done": {"zh": "河流生成完成", "en": "River generation complete"},
    "river_hint": {"zh": "河流规则: 必须1像素宽，只走上下左右(不能斜走)每条河需要1个源头(绿)。红=支流汇入 黄=分叉画笔大小仅影响橡皮擦范围，河流本身必须1像素宽", "en": "River rules: must be 1px wide, only up/down/left/right (no diagonal)Each river needs 1 source (green). Red=tributary merge, Yellow=forkBrush size only affects eraser range; rivers must be 1px wide"},
    "river_label_size": {"zh": "大小:", "en": "Size:"},
    "river_section_brush_size": {"zh": "画笔大小", "en": "Brush Size"},
    "river_section_markers": {"zh": "标记 (单像素)", "en": "Markers (Single Pixel)"},
    "river_section_tools": {"zh": "工具", "en": "Tools"},
    "river_section_width": {"zh": "宽度画笔", "en": "Width Brush"},
    "river_tool_brush": {"zh": "画笔", "en": "Brush"},
    "river_tool_eraser": {"zh": "橡皮", "en": "Eraser"},
    "river_tool_pan": {"zh": "平移", "en": "Pan"},
    "sr_auto_btn": {"zh": "自动生成 (按 State 分组)", "en": "Auto Generate (Group by State)"},
    "sr_auto_weather_btn": {"zh": "\U0001f30d 按纬度自动分配天气", "en": "\U0001f30d Auto-Assign Weather by Latitude"},
    "sr_delete_btn": {"zh": "删除", "en": "Delete"},
    "sr_from_states_btn": {"zh": "选择州 → 创建战略区域", "en": "Select States → Create Strategic Region"},
    "sr_from_states_confirm_btn": {"zh": "确认创建战略区域", "en": "Confirm Create Strategic Region"},
    "sr_from_states_tip": {"zh": "开启后点击地图选择多个州，然后点确认合并为一个战略区域", "en": "Enable to select multiple states on map, then confirm to merge into one strategic region"},
    "sr_name_label": {"zh": "名字:", "en": "Name:"},
    "sr_naval_label": {"zh": "Naval:", "en": "Naval:"},
    "sr_naval_none": {"zh": "(无)", "en": "(None)"},
    "sr_new_btn": {"zh": "新建空区域", "en": "New Empty Region"},
    "sr_pick_btn": {"zh": "开始拾取省份（陆地+海洋）", "en": "Start Picking Provinces (Land + Ocean)"},
    "sr_prov_count": {"zh": "省份: {}", "en": "Provinces: {}"},
    "sr_tip": {"zh": "战略区域: 省份分组 + 天气 + 海军地形.建议先点'自动生成'按 State 创建初始分组，再手动调整。每个区域可设天气和海军地形类型.用拾取模式点省份可移入选中的区域.", "en": "Strategic regions: province grouping + weather + naval terrain.Suggest clicking 'Auto Generate' to create initial groups by state,then adjust manually. Each region can set weather and naval terrain.Use pick mode to move provinces into the selected region."},
    "sr_weather_label": {"zh": "天气:", "en": "Weather:"},
    "state_auto_btn": {"zh": "自动分组", "en": "Auto Group"},
    "state_batch_confirm_btn": {"zh": "确认创建新州", "en": "Confirm Create State"},
    "state_batch_section": {"zh": "批量建州", "en": "Batch Create States"},
    "state_batch_select_btn": {"zh": "选择省份建州", "en": "Select Provinces to Create State"},
    "state_batch_select_tip": {"zh": "开启后点击省份多选，然后点确认创建新州", "en": "Enable to multi-select provinces, then confirm to create a new state"},
    "state_category_label": {"zh": "类别:", "en": "Category:"},
    "state_detail_btn": {"zh": "详情... (资源/建筑/核心/宣称)", "en": "Details... (Resources/Buildings/Cores/Claims)"},
    "state_hint": {"zh": "选中State后点击省份可移入。双击State打开详情编辑资源/建筑/VP", "en": "Select a state then click provinces to assign. Double-click a state for resource/building/VP details"},
    "state_list_section": {"zh": "State 列表", "en": "State List"},
    "state_manpower_label": {"zh": "人口:", "en": "Manpower:"},
    "state_name_label": {"zh": "名称:", "en": "Name:"},
    "state_per_spin_label": {"zh": "每State省份数:", "en": "Provinces per State:"},
    "state_props_section": {"zh": "State 属性", "en": "State Properties"},
    "terrain_btn_auto_gen": {"zh": "智能地形生成", "en": "Smart Terrain Generate"},
    "terrain_btn_random": {"zh": "随机", "en": "Random"},
    "terrain_cb_soft_edge": {"zh": "柔边 (自然过渡)", "en": "Soft Edge (Natural Blend)"},
    "terrain_group_desert": {"zh": "沙漠", "en": "Desert"},
    "terrain_group_forest": {"zh": "森林", "en": "Forest"},
    "terrain_group_hills": {"zh": "丘陵", "en": "Hills"},
    "terrain_group_jungle": {"zh": "丛林", "en": "Jungle"},
    "terrain_group_marsh": {"zh": "沼泽", "en": "Marsh"},
    "terrain_group_mountain": {"zh": "山地", "en": "Mountain"},
    "terrain_group_plains": {"zh": "平原", "en": "Plains"},
    "terrain_group_urban": {"zh": "城市", "en": "Urban"},
    "terrain_hint": {"zh": "按省份: 点选地形后点击省份分配（同时设外观+属性）画笔: 逐像素画地形贴图（只影响外观）", "en": "By Province: select terrain then click province (sets visual+property)Brush: paint terrain pixel by pixel (visual only)"},
    "terrain_label_noise": {"zh": "噪声强度:", "en": "Noise Strength:"},
    "terrain_label_scatter": {"zh": "散点密度:", "en": "Scatter Density:"},
    "terrain_label_seed": {"zh": "种子:", "en": "Seed:"},
    "terrain_label_size": {"zh": "大小:", "en": "Size:"},
    "terrain_mode_brush": {"zh": "画笔", "en": "Brush"},
    "terrain_mode_province": {"zh": "按省份", "en": "By Province"},
    "terrain_section_auto_gen": {"zh": "智能地形生成", "en": "Smart Terrain Generation"},
    "terrain_section_edit_mode": {"zh": "编辑模式", "en": "Edit Mode"},
    "terrain_section_brush": {"zh": "画笔设置", "en": "Brush Settings"},
    "terrain_tip_index": {"zh": "索引", "en": "Index"},
    "terrain_tip_texture": {"zh": "贴图", "en": "Texture"},
    "terrain_tip_type": {"zh": "类型", "en": "Type"},

    # === 欢迎页 ===
    "welcome_title": {"zh": "HOI4 地图制作工具", "en": "HOI4 Map Maker"},
    "welcome_size_picker_title": {"zh": "选择地图尺寸", "en": "Choose Map Size"},
    "welcome_width": {"zh": "宽度:", "en": "Width:"},
    "welcome_height": {"zh": "高度:", "en": "Height:"},
    "welcome_import_mod": {"zh": "导入MOD地图", "en": "Import MOD Map"},
    "welcome_recent": {"zh": "最近项目", "en": "Recent Projects"},
    "welcome_no_recent": {"zh": "(无最近项目)", "en": "(No Recent Projects)"},

    # 右侧信息面板
    "welcome_info_title": {"zh": "关于此工具", "en": "About This Tool"},
    "welcome_info_desc": {
        "zh": "从零开始制作完整的 HOI4 全转换 MOD，无需手动编辑任何游戏文件。\n画大陆 → 生成省份 → 地形高度 → 州和国家 → 一键导出可玩 MOD。",
        "en": "Create complete HOI4 total-conversion mods from scratch — no manual file editing required.\nDraw continents → Generate provinces → Terrain & height → States & countries → One-click export playable MOD.",
    },
    "welcome_features_title": {"zh": "功能亮点", "en": "Highlights"},
    "welcome_features_list": {
        "zh": "- 圆形画笔 / 填充 / 变换工具\n- 泊松盘 + Lloyd 松弛自动生成省份\n- 智能高度图 & 地形 & 河流生成\n- 州 / 国家 / 战略区全流程管理\n- 5 秒导出 2000+ 文件完整 MOD\n- 中英双语界面",
        "en": "- Circular brush / fill / transform tools\n- Poisson disk + Lloyd relaxation province gen\n- Smart heightmap & terrain & river generation\n- Full state / country / region workflow\n- 5-second export of 2000+ file complete MOD\n- Chinese / English bilingual UI",
    },
    "welcome_changelog_title": {"zh": "更新日志 ({ver})", "en": "Changelog ({ver})"},
    "welcome_links": {
        "zh": '<a href="https://github.com/AmonStreeling/hoi4-mod-maker" style="color:#6c6cf0;">GitHub</a>'
              ' &nbsp;|&nbsp; '
              '<a href="https://github.com/AmonStreeling/hoi4-mod-maker/issues" style="color:#6c6cf0;">反馈 / Issues</a>',
        "en": '<a href="https://github.com/AmonStreeling/hoi4-mod-maker" style="color:#6c6cf0;">GitHub</a>'
              ' &nbsp;|&nbsp; '
              '<a href="https://github.com/AmonStreeling/hoi4-mod-maker/issues" style="color:#6c6cf0;">Feedback / Issues</a>',
    },
    "welcome_community_title": {"zh": "社区支持", "en": "Community"},
    "welcome_community": {
        "zh": '工具测试群: <b>1077283666</b><br>'
              '友宣群 图书馆: <b>378525932</b><br>'
              'Discord: <a href="https://discord.gg/njHjBf2ADG" style="color:#6c6cf0;">discord.gg/njHjBf2ADG</a>',
        "en": 'Discord: <a href="https://discord.gg/njHjBf2ADG" style="color:#6c6cf0;">discord.gg/njHjBf2ADG</a>',
    },

    # === 菜单补充 ===
    "action_load_vanilla_ref": {"zh": "加载原版地图参考", "en": "Load Vanilla Map Reference"},
    "action_import_landmask": {"zh": "从图片提取陆海...", "en": "Extract Land/Sea from Image..."},
    "action_import_mod_map": {"zh": "导入MOD地图...", "en": "Import MOD Map..."},
    "action_test_export": {"zh": "测试导出（最小MOD）", "en": "Test Export (Minimal MOD)"},
    "action_shortcut_settings": {"zh": "快捷键设置...", "en": "Shortcut Settings..."},

    # === 状态栏补充 ===
    "status_mode": {"zh": "模式: {mode}", "en": "Mode: {mode}"},
    "status_selected_provinces": {"zh": "已选中 {n} 个省份", "en": "{n} provinces selected"},
    "status_selected_provinces_state": {"zh": "已选中 {n} 个省份建州", "en": "{n} provinces selected for state"},
    "status_selected_states": {"zh": "已选中 {n} 个州", "en": "{n} states selected"},
    "status_province_no_state": {"zh": "省份 {pid} 不属于任何州", "en": "Province {pid} has no state"},
    "status_operation_error": {"zh": "操作异常: {err}", "en": "Operation error: {err}"},
    "status_provinces_cleared": {"zh": "修改大陆数据，省份已清除（需要重新生成）", "en": "Continent data changed, provinces cleared (need regeneration)"},
    "status_expand_mode": {"zh": "扩张模式：点击省份后拖动扩张", "en": "Expand mode: click province and drag to expand"},
    "status_view_mode": {"zh": "回到查看模式", "en": "Back to view mode"},
    "status_regen_mode": {"zh": "增量生成：点击省份选择区域，然后点「重新生成」", "en": "Incremental regen: click provinces to select area, then click Regenerate"},
    "status_batch_state_mode": {"zh": "批量建州：点击省份多选，然后点确认", "en": "Batch create state: click provinces to multi-select, then confirm"},
    "status_sr_from_states_mode": {"zh": "选择州 → 创建战略区域：点击地图选择多个州，然后点确认", "en": "Select states to create strategic region: click map to select states, then confirm"},
    "status_state_updated": {"zh": "State {sid} 已更新", "en": "State {sid} updated"},
    "status_generating_bg": {"zh": "正在生成省份...（后台运行中，请稍候）", "en": "Generating provinces... (running in background, please wait)"},
    "status_gen_done": {"zh": "省份生成完成: {count} 个", "en": "Province generation done: {count}"},
    "status_initializing": {"zh": "正在初始化...", "en": "Initializing..."},
    "status_init_done": {"zh": "初始化完成", "en": "Initialization complete"},
    "status_auto_terrain": {"zh": "正在智能生成地形...", "en": "Smart generating terrain..."},
    "status_auto_terrain_done": {"zh": "智能地形生成完成 (支持 Ctrl+Z 撤销)", "en": "Smart terrain generation done (Ctrl+Z to undo)"},
    "status_auto_height": {"zh": "正在智能生成高度图...", "en": "Smart generating heightmap..."},
    "status_auto_height_done": {"zh": "高度图生成完成 — 切到「地形」生成地形", "en": "Heightmap done - switch to Terrain mode to generate terrain"},
    "status_height_smoothed": {"zh": "高度图已平滑", "en": "Heightmap smoothed"},

    # === 对话框 ===
    "dlg_set_vp_title": {"zh": "设置胜利点", "en": "Set Victory Point"},
    "dlg_set_vp_label": {"zh": "省份 {pid} 的 VP 分值\n(1=小镇, 5=中等, 10=城市, 20=首都):", "en": "VP value for province {pid}\n(1=town, 5=medium, 10=city, 20=capital):"},
    "dlg_merge_hint": {"zh": "先点击要保留的省份，再点击要被合并的省份。\n被合并省份的像素将并入保留省份。", "en": "Click the province to keep first, then click the province to merge.\nMerged province pixels will be absorbed into the kept province."},
    "dlg_expand_hint": {"zh": "点击要扩张的省份，然后拖动画笔将周围像素并入该省份。", "en": "Click the province to expand, then drag the brush to absorb nearby pixels."},
    "dlg_regen_title": {"zh": "增量生成", "en": "Incremental Regen"},
    "dlg_regen_select_first": {"zh": "请先选择要重新生成的省份区域", "en": "Please select province area to regenerate first"},
    "dlg_regen_confirm": {"zh": "将对 {n} 个省份所在区域重新生成省份。\n该区域内的旧省份将被删除并重新划分。\n\n继续吗？", "en": "Will regenerate provinces in the area of {n} provinces.\nOld provinces in this area will be deleted and repartitioned.\n\nContinue?"},
    "dlg_regen_done_title": {"zh": "增量生成完成", "en": "Incremental Regen Complete"},
    "dlg_regen_done": {"zh": "删除 {removed} 个旧省份，新建 {created} 个省份。", "en": "Deleted {removed} old provinces, created {created} new provinces."},
    "dlg_batch_state_title": {"zh": "批量建州", "en": "Batch Create State"},
    "dlg_batch_state_select_first": {"zh": "请先点击省份选择区域", "en": "Please click provinces to select area first"},
    "dlg_batch_state_done": {"zh": "已创建州 {sid}（{n} 个省份）", "en": "Created state {sid} ({n} provinces)"},
    "dlg_sr_from_states_title": {"zh": "创建战略区域", "en": "Create Strategic Region"},
    "dlg_sr_from_states_select_first": {"zh": "请先点击地图选择州", "en": "Please click map to select states first"},
    "dlg_sr_from_states_done": {"zh": "已创建战略区域 #{rid}（包含 {n} 个州）", "en": "Created strategic region #{rid} (containing {n} states)"},
    "dlg_update_title": {"zh": "发现新版本", "en": "New Version Available"},
    "dlg_update_body": {"zh": "当前版本：{current}\n最新版本：{latest}\n\n更新内容：\n{body}\n\n是否前往下载？", "en": "Current version: {current}\nLatest version: {latest}\n\nChangelog:\n{body}\n\nGo to download?"},
    "dlg_file_not_found": {"zh": "文件不存在:\n{path}", "en": "File not found:\n{path}"},
    "dlg_select_mod_dir": {"zh": "选择 HOI4 MOD 或原版目录", "en": "Select HOI4 MOD or Vanilla Directory"},
    "dlg_import_failed": {"zh": "导入失败", "en": "Import Failed"},
    "dlg_import_missing_files": {"zh": "目录缺少必需文件:\n", "en": "Directory missing required files:\n"},
    "dlg_import_read_error": {"zh": "读取MOD文件时出错:\n{err}\n\n{tb}", "en": "Error reading MOD files:\n{err}\n\n{tb}"},
    "dlg_gen_mode_title": {"zh": "省份生成模式", "en": "Province Generation Mode"},
    "dlg_gen_mode_body": {"zh": "当前地图已有省份。\n\n点击 Yes = 只生成新区域的省份（保留已有）\n点击 No = 重新生成全部省份", "en": "Map already has provinces.\n\nClick Yes = generate only for new areas (keep existing)\nClick No = regenerate all provinces"},
    "dlg_quick_init_title": {"zh": "一键初始化", "en": "Quick Init"},
    "dlg_quick_init_no_provinces": {"zh": "请先生成省份", "en": "Please generate provinces first"},
    "dlg_quick_init_body": {"zh": "将自动生成：\n- 州（按地理分组，每州约15个省份）\n- 战略区域（按州分组）\n- 默认国家 AAA（拥有所有领土）\n\n已有的州/战略区域/国家数据将被覆盖。继续吗？", "en": "Will auto-generate:\n- States (grouped geographically, ~15 provinces each)\n- Strategic regions (grouped by state)\n- Default country AAA (owns all territory)\n\nExisting state/region/country data will be overwritten. Continue?"},
    "dlg_quick_init_done": {"zh": "一键初始化完成：\n", "en": "Quick init complete:\n"},
    "dlg_init_failed": {"zh": "初始化失败", "en": "Initialization Failed"},
    "dlg_country_tag_prompt": {"zh": "输入国家 TAG (3个字母):", "en": "Enter country TAG (3 letters):"},
    "dlg_country_name_prompt": {"zh": "输入国家名称 (TAG: {tag}):", "en": "Enter country name (TAG: {tag}):"},
    "dlg_country_pick_color": {"zh": "选择 {tag} 的颜色", "en": "Choose color for {tag}"},
    "dlg_country_create_failed": {"zh": "创建国家失败", "en": "Failed to create country"},
    "dlg_country_change_color": {"zh": "修改 {tag} 的颜色", "en": "Change color for {tag}"},
    "dlg_river_validate_title": {"zh": "河流验证", "en": "River Validation"},
    "dlg_continent_add_failed": {"zh": "添加大陆失败", "en": "Failed to add continent"},
    "dlg_continent_rename_failed": {"zh": "重命名失败", "en": "Rename failed"},
    "dlg_continent_delete_failed": {"zh": "删除失败", "en": "Delete failed"},
    "dlg_defmap_palette_prompt": {"zh": "Palette 索引 (1-13):", "en": "Palette index (1-13):"},
    "dlg_language_title": {"zh": "Language / 语言", "en": "Language / 语言"},
    "dlg_language_switched": {"zh": "语言已切换，部分界面需要重启生效。\nLanguage switched. Some UI elements require restart.", "en": "Language switched. Some UI elements require restart.\n语言已切换，部分界面需要重启生效。"},

    # === 导入 ===
    "import_title": {"zh": "导入MOD", "en": "Import MOD"},
    "import_reading_files": {"zh": "正在读取MOD地图文件...", "en": "Reading MOD map files..."},
    "import_initializing": {"zh": "正在初始化地图...", "en": "Initializing map..."},
    "import_rendering": {"zh": "正在渲染...", "en": "Rendering..."},
    "import_done": {"zh": "MOD地图已导入 ({w}×{h}, {n} 省份)", "en": "MOD map imported ({w}x{h}, {n} provinces)"},
    "import_done_title": {"zh": "导入完成", "en": "Import Complete"},
    "import_warnings": {"zh": "注意:\n", "en": "Note:\n"},

    # === 验证结果补充 ===
    "validate_info": {"zh": "省份总数：{total}    沿海：{coastal}", "en": "Total provinces: {total}    Coastal: {coastal}"},
    "validate_double_click_hint": {"zh": "双击问题项跳转到地图对应位置：", "en": "Double-click an issue to jump to its map location:"},
    "validate_more_xcrossing": {"zh": "... 还有 {n} 个 X-crossing 未列出", "en": "... {n} more X-crossings not listed"},
    "validate_too_small_item": {"zh": "过小省份 ID={pid}（< 8 像素）", "en": "Too small province ID={pid} (< 8 pixels)"},
    "validate_not_contiguous_item": {"zh": "不连通省份 ID={pid}（多个碎片）", "en": "Non-contiguous province ID={pid} (multiple fragments)"},
    "validate_too_large_item": {"zh": "过大省份 ID={pid}", "en": "Too large province ID={pid}"},
    "validate_id_gaps": {"zh": "省份 ID 不连续：缺失 {n} 个（导出时自动修复）", "en": "Province ID gaps: {n} missing (auto-fixed on export)"},
    "validate_no_issues": {"zh": "没有发现任何问题", "en": "No issues found"},

    # === 关于 ===
    "dlg_about_body": {"zh": "HOI4 幻想世界 MOD 制作工具\nHOI4 Fantasy World MOD Maker\n\nVersion 0.15\nMap size: 5632 x 2048", "en": "HOI4 Fantasy World MOD Maker\n\nVersion 0.15\nMap size: 5632 x 2048"},

    # === 单位词 ===
    "unit_provinces": {"zh": "省", "en": "prov."},

    # === 导航栏 (7 模式) ===
    "nav_map_draw": {"zh": "画地图", "en": "Draw Map"},
    "nav_province": {"zh": "省份", "en": "Provinces"},
    "nav_terrain": {"zh": "地形", "en": "Terrain"},
    "nav_river": {"zh": "河流", "en": "Rivers"},
    "nav_region": {"zh": "国家与区域", "en": "Countries"},
    "nav_logistics": {"zh": "后勤", "en": "Logistics"},
    "nav_settings": {"zh": "设置", "en": "Settings"},

    # 子标签页
    "tab_land": {"zh": "陆海", "en": "Land"},
    "tab_density": {"zh": "密度", "en": "Density"},
    "tab_new_land": {"zh": "新大陆", "en": "New Land"},
    "tab_height": {"zh": "高度", "en": "Height"},
    "tab_terrain": {"zh": "地形（视觉）", "en": "Terrain (Visual)"},
    "tab_province_terrain": {"zh": "地形（属性）", "en": "Terrain (Attribute)"},
    "tab_state": {"zh": "州", "en": "State"},
    "tab_country": {"zh": "国家", "en": "Country"},
    "tab_continent": {"zh": "大洲", "en": "Continent"},
    "tab_strategic_region": {"zh": "战略区", "en": "Strategic Region"},
    "tab_logistics": {"zh": "后勤", "en": "Logistics"},
    "tab_colormap": {"zh": "总览贴图", "en": "Colormap"},
    "tab_default_map": {"zh": "地图配置", "en": "Map Config"},

    # === 新手引导对话框 ===
    "guide_title": {"zh": "新手引导", "en": "Getting Started"},
    "guide_step_n": {"zh": "第 {} 步 / 共 {} 步", "en": "Step {} of {}"},
    "guide_prev": {"zh": "上一步", "en": "Previous"},
    "guide_next": {"zh": "下一步", "en": "Next"},
    "guide_start": {"zh": "开始制作", "en": "Start Creating"},
    "guide_dont_show": {"zh": "不再显示", "en": "Don't show again"},

    "guide_step1_title": {"zh": "画大陆轮廓", "en": "Draw Continents"},
    "guide_step1_desc": {
        "zh": "选择「陆地与海洋」模式，用画笔画出大陆的形状。\n\n"
              "• 左键画陆地，切换到「海洋」或「湖泊」画海域\n"
              "• 填充工具可以快速涂满大面积区域\n"
              "• 变换工具可以框选一块区域进行移动/缩放\n"
              "• 也可以导入一张参考图片，对着描绘",
        "en": "Select 'Land & Sea' mode and draw your continent shapes.\n\n"
              "• Left-click to paint land; switch to Sea/Lake to paint water\n"
              "• Use Fill tool to quickly cover large areas\n"
              "• Use Transform tool to select, move, and scale regions\n"
              "• You can also import a reference image to trace over",
    },
    "guide_step2_title": {"zh": "生成省份", "en": "Generate Provinces"},
    "guide_step2_desc": {
        "zh": "画完大陆后，点击「生成省份」按钮自动切分区域。\n\n"
              "• 调整省份数量滑块控制密度（推荐 3000-12000）\n"
              "• 海洋和湖泊密度可以单独调节\n"
              "• 生成后可用合并/切割/套索工具微调边界\n"
              "• 点击「验证省份」检查是否有问题",
        "en": "After drawing continents, click 'Generate Provinces' to auto-split regions.\n\n"
              "• Adjust the province count slider (recommended: 3000-12000)\n"
              "• Sea and lake density can be set independently\n"
              "• Use Merge / Split / Lasso tools to fine-tune borders\n"
              "• Click 'Validate' to check for issues",
    },
    "guide_step3_title": {"zh": "地形与高度", "en": "Terrain & Height"},
    "guide_step3_desc": {
        "zh": "切换到「高度」模式，点击「自动生成」创建高度图。\n"
              "然后切到「地形」模式，点击「自动生成」按高度分配地形。\n\n"
              "• 高度图决定山脉和平原的分布\n"
              "• 地形影响游戏中的移动速度和战斗加成\n"
              "• 也可以用画刷手动调整局部区域",
        "en": "Switch to 'Height' mode and click 'Auto Generate' for a heightmap.\n"
              "Then switch to 'Terrain' and click 'Auto Generate' to assign terrain by height.\n\n"
              "• Heightmap determines mountain and plain distribution\n"
              "• Terrain affects movement speed and combat bonuses in-game\n"
              "• You can also manually paint specific areas with brushes",
    },
    "guide_step4_title": {"zh": "建州与国家", "en": "States & Countries"},
    "guide_step4_desc": {
        "zh": "切换到「州」模式，点击「自动生成州」一键创建。\n"
              "然后切到「国家」模式，创建国家并分配领土。\n\n"
              "• 或者直接点击「一键初始化」自动完成这些步骤\n"
              "• 双击省份可以设置胜利点\n"
              "• 每个州需要归属一个国家才能导出",
        "en": "Switch to 'State' mode and click 'Auto Generate States'.\n"
              "Then switch to 'Country' to create nations and assign territory.\n\n"
              "• Or just click 'Quick Init' to do all of this automatically\n"
              "• Double-click a province to set a victory point\n"
              "• Every state must belong to a country for export",
    },
    "guide_step5_title": {"zh": "后勤配置（可跳过）", "en": "Logistics (Optional)"},
    "guide_step5_desc": {
        "zh": "切换到「后勤系统」模式，可以设置：\n\n"
              "• 邻接关系（跨海连接等特殊通道）\n"
              "• 铁路网络\n"
              "• 补给节点\n\n"
              "这一步可以跳过，导出时会自动补全基础配置。",
        "en": "Switch to 'Logistics' mode to set up:\n\n"
              "• Adjacencies (cross-sea connections, special passages)\n"
              "• Railway networks\n"
              "• Supply nodes\n\n"
              "This step is optional — basic config is auto-generated on export.",
    },
    "guide_step6_title": {"zh": "一键导出", "en": "Export & Play"},
    "guide_step6_desc": {
        "zh": "点击底部的「导出 MOD」按钮，即可生成完整的 HOI4 MOD。\n\n"
              "• 导出前会自动检查并修复常见问题\n"
              "• 生成 2000+ 游戏文件（provinces/states/countries 等）\n"
              "• 导出完成后直接启动 HOI4 即可进入游戏\n\n"
              "祝你的幻想世界玩得愉快！",
        "en": "Click the 'Export MOD' button at the bottom to generate a complete HOI4 MOD.\n\n"
              "• Pre-export checks will auto-fix common issues\n"
              "• Generates 2000+ game files (provinces/states/countries, etc.)\n"
              "• Launch HOI4 after export and jump right into your world\n\n"
              "Enjoy building your fantasy world!",
    },

    # === 帮助菜单 ===
    "action_guide": {"zh": "新手引导", "en": "Getting Started Guide"},
    "action_reset_hints": {"zh": "重置操作提示", "en": "Reset Mode Hints"},
    "guide_reset_done": {"zh": "已重置所有模式提示", "en": "All mode hints have been reset"},

    # === 模式操作提示条 ===
    "hint_mode_land": {
        "zh": "用画笔画出大陆形状，填充可快速涂满区域。完成后切换到「省份」模式。",
        "en": "Draw continent shapes with brush. Use Fill for large areas. Switch to 'Province' when done.",
    },
    "hint_mode_province": {
        "zh": "点击「生成省份」自动切分，用合并/切割/套索微调边界。",
        "en": "Click 'Generate Provinces' to auto-split. Use Merge/Split/Lasso to adjust borders.",
    },
    "hint_mode_height": {
        "zh": "点击「自动生成」创建高度图，或用滑块手动调整。完成后切到「地形」。",
        "en": "Click 'Auto Generate' for heightmap, or adjust manually. Then switch to 'Terrain'.",
    },
    "hint_mode_terrain": {
        "zh": "点击「自动生成」按高度分配地形，或用画刷手动绘制。",
        "en": "Click 'Auto Generate' to assign terrain by height, or paint manually with brushes.",
    },
    "hint_mode_river": {
        "zh": "沿省份边界画河流，从高处画向低处（山地→海洋）。",
        "en": "Draw rivers along province borders, from high to low elevation (mountains → sea).",
    },
    "hint_mode_state": {
        "zh": "点击「自动生成州」一键创建，或框选省份手动建州。双击省份设胜利点。",
        "en": "Click 'Auto Generate States' or select provinces manually. Double-click to set victory points.",
    },
    "hint_mode_country": {
        "zh": "创建国家（TAG+名称+颜色），然后点击州分配领土。",
        "en": "Create a country (TAG + name + color), then click states to assign territory.",
    },
    "hint_mode_continent": {
        "zh": "添加大陆名称，然后点击州分配到对应大陆。",
        "en": "Add continent names, then click states to assign them.",
    },
    "hint_mode_strategic_region": {
        "zh": "点击「自动生成」或从州创建战略区域。",
        "en": "Click 'Auto Generate' or create strategic regions from states.",
    },
    "hint_mode_logistics": {
        "zh": "设置邻接/铁路/补给节点。可跳过，导出时自动补全。",
        "en": "Set adjacencies, railways, and supply nodes. Optional — auto-generated on export.",
    },
    "hint_mode_colormap": {
        "zh": "调整总览贴图的陆地/海洋/湖泊配色。",
        "en": "Adjust land/sea/lake colors for the overview colormap.",
    },
    "hint_mode_default_map": {
        "zh": "配置河流数量上限和树木调色板。",
        "en": "Configure max river count and tree color palette.",
    },

    # === 河流 page (新版 UI) ===
    "river_section_auto": {"zh": "🪄 一键生成河流（推荐）", "en": "🪄 Auto-Generate Rivers (Recommended)"},
    "river_btn_auto_new": {"zh": "🌊 自动生成河流", "en": "🌊 Auto-Generate Rivers"},
    "river_auto_tooltip": {
        "zh": "基于高度图自动生成合理河流网络，几秒完成全图",
        "en": "Auto-generate a reasonable river network based on heightmap, done in seconds",
    },
    "river_auto_tip": {
        "zh": "根据高度图自动画河，不用手动。生成后可手动改/擦除。",
        "en": "Auto-draw rivers from heightmap. Manual edit / erase still works after.",
    },
    "river_section_manual": {"zh": "✏️ 手动画河流（3 步）", "en": "✏️ Manual Drawing (3 Steps)"},
    "river_step1_title": {"zh": "<b>步骤 1：</b>选河流宽度", "en": "<b>Step 1:</b> Select river width"},
    "river_step2_title": {"zh": "<b>步骤 2：</b>在地图上画河", "en": "<b>Step 2:</b> Draw river on map"},
    "river_step2_hint": {
        "zh": "从山上某点按住鼠标 → 拖到海边 → 松手\n⚠️ 只能走上下左右，不能斜线",
        "en": "Click-drag from mountains to sea → release\n⚠️ Only horizontal/vertical, no diagonal",
    },
    "river_step3_title": {"zh": "<b>步骤 3：</b>加起点/终点标记", "en": "<b>Step 3:</b> Add source/mouth markers"},
    "river_step3_hint": {
        "zh": "每条河至少 1 个源头（绿）\n入海口（黄）放河流末端\n汇入点（红）= 两条河合并处",
        "en": "Each river needs ≥1 source (green)\nMouth marker (yellow) at sea entry\nFlow-in (red) where rivers merge",
    },
    "river_brush_btn": {"zh": "画笔", "en": "Brush"},
    "river_eraser_btn": {"zh": "橡皮", "en": "Eraser"},
    "river_pan_btn": {"zh": "平移", "en": "Pan"},
    "river_eraser_range": {"zh": "橡皮范围:", "en": "Eraser size:"},
    "river_width_note": {
        "zh": "💡 河流必须 1px 宽（HOI4 规则），滑块只影响橡皮擦范围",
        "en": "💡 Rivers must be 1px wide (HOI4 rule), slider only affects eraser",
    },
    "river_btn_validate_new": {"zh": "✓ 验证河流是否合法", "en": "✓ Validate Rivers"},
    "river_validate_tooltip": {
        "zh": "检查是否有对角线像素、缺失源头等问题",
        "en": "Check for diagonal pixels, missing sources, etc.",
    },

    # === 属性地形 page ===
    "pterrain_intro": {
        "zh": ("🟢 <b>属性地形</b>（影响战斗 / 补给）\n\n"
               "默认是<b>查看模式</b>：点 province 只显示信息，不改地形。\n"
               "要改地形：勾选下面的<b>「分配模式」</b>，然后点 province。\n\n"
               "💡 此模式只改 gameplay 数据，不动 terrain.bmp 视觉。"),
        "en": ("🟢 <b>Attribute Terrain</b> (affects combat / supply)\n\n"
               "Default is <b>view mode</b>: click province shows info only, no edit.\n"
               "To edit: check <b>'Assign Mode'</b> below, then click province.\n\n"
               "💡 This mode only changes gameplay data, not terrain.bmp visual."),
    },
    "pterrain_assign_mode": {"zh": "🖊 分配模式（开启后点击改地形）", "en": "🖊 Assign Mode (click to change terrain)"},
    "pterrain_section_types": {"zh": "地形类型", "en": "Terrain Types"},
    "pterrain_current_label": {"zh": "当前：{0} ({1})", "en": "Current: {0} ({1})"},

    # === 地形（视觉）顶部大按钮 ===
    "terrain_auto_top_section": {"zh": "🎨 一键生成地形（推荐）", "en": "🎨 One-Click Terrain (Recommended)"},
    "terrain_auto_top_btn": {"zh": "🌋 基于高度图自动生成地形", "en": "🌋 Auto-Generate Terrain from Heightmap"},
    "terrain_auto_top_tooltip": {
        "zh": "根据高度图自动画地形 + 自动同步属性地形。详细参数在下方",
        "en": "Auto-paint terrain from heightmap + sync attribute layer. Advanced params below",
    },
    "terrain_auto_top_tip": {
        "zh": "根据高度图自动生成 + 同步属性层。调完高度就点这个。",
        "en": "Auto-generate + sync attributes. Click after editing heightmap.",
    },

    # === 高度 tab 顶部大按钮 ===
    "height_auto_top_section": {"zh": "🏔 一键生成高度图（推荐）", "en": "🏔 One-Click Heightmap (Recommended)"},
    "height_auto_top_btn": {"zh": "🏔 智能生成高度图", "en": "🏔 Smart Generate Heightmap"},
    "height_auto_top_tooltip": {
        "zh": "根据陆海划分自动生成有起伏的高度图。详细参数在下方",
        "en": "Auto-generate terrain-like heightmap from land/sea mask. Advanced params below",
    },
    "height_auto_top_tip": {
        "zh": "画完陆海就点这个，自动生成合理高度。下方参数可调细节。",
        "en": "Click after editing land/sea. Advanced params below for fine-tuning.",
    },

    # === 导航组 tooltip (风险等级) ===
    "nav_tooltip_map_draw": {"zh": "🟢 基础数据（陆海划分、省份密度）— 低崩溃风险", "en": "🟢 Base data (land/sea, density) — low crash risk"},
    "nav_tooltip_province": {"zh": "🟢 省份编辑 — 基础 gameplay 数据", "en": "🟢 Province editing — base gameplay data"},
    "nav_tooltip_terrain": {"zh": "⛰ 地形组：🟠高度 → 🎨视觉地形(自动生成) → 🟢属性地形(微调)", "en": "⛰ Terrain group: 🟠Height → 🎨Visual → 🟢Attribute"},
    "nav_tooltip_river": {"zh": "🔴 河流 — 崩溃高发区！调色板严格(0-4,6-7,9-11)+必须正交", "en": "🔴 Rivers — crash-prone! Strict palette (0-4,6-7,9-11) + orthogonal only"},
    "nav_tooltip_region": {"zh": "🟢 区域行政（州/国家/大陆）— gameplay 数据", "en": "🟢 Region admin (state/country/continent) — gameplay data"},
    "nav_tooltip_logistics": {"zh": "🟠 物流系统（战略区/铁路/补给）— 影响补给机制", "en": "🟠 Logistics (strategic region/railway/supply) — affects supply"},
    "nav_tooltip_settings": {"zh": "⚙ 设置（🎨 colormap=纯视觉/🟠 default_map=配置）", "en": "⚙ Settings (🎨 colormap=visual / 🟠 default_map=config)"},

    # === 欢迎页 ===
    "welcome_recent_tooltip": {"zh": "双击打开项目；鼠标悬停可看完整路径", "en": "Double-click to open; hover to see full path"},

    # === 状态消息 ===
    "status_pterrain_view": {"zh": "属性地形：查看模式（勾选「分配模式」才能改）", "en": "Attribute terrain: view mode (enable 'Assign Mode' to edit)"},
    "status_pterrain_view_on": {"zh": "👁 查看模式：点 province 只看信息", "en": "👁 View mode: click province to see info"},
    "status_pterrain_assign_on": {"zh": "✏️ 分配模式开启：点击省份将其改为 {0}", "en": "✏️ Assign mode on: click province to set it to {0}"},
    "status_pterrain_selected": {"zh": "已选 {0}，点击省份生效", "en": "Selected {0}, click province to apply"},
    "status_pterrain_selected_view": {"zh": "已选 {0}（请勾选「分配模式」才能改）", "en": "Selected {0} (enable 'Assign Mode' to edit)"},
    "status_pterrain_applied": {"zh": "省份 {0} 属性地形 → {1}", "en": "Province {0} attribute terrain → {1}"},
    "status_pterrain_sea_skip": {"zh": "省份 {0} 是海洋/湖泊，不能改地形", "en": "Province {0} is sea/lake, cannot change terrain"},
    "status_unassigned_warning": {"zh": "⚠️ 有 {0} 个省份未分配到 state（画布上红色高亮）", "en": "⚠️ {0} provinces not assigned to any state (red on canvas)"},
    "status_all_assigned": {"zh": "✅ 所有省份都已分配到 state", "en": "✅ All provinces assigned to states"},
    "status_auto_terrain_synced": {"zh": "（同步 {0} 个省份属性）", "en": " (synced {0} province attributes)"},

    # === 节点区段标题 ===
    "section_tools": {"zh": "工具", "en": "Tools"},

    "terrain_unknown": {"zh": "未知", "en": "Unknown"},

    # === 河流类型按钮 ===
    "river_marker_source": {"zh": "源头", "en": "Source"},
    "river_marker_confluence": {"zh": "汇入点", "en": "Confluence"},
    "river_marker_mouth": {"zh": "入海口", "en": "Mouth"},
    "river_width_1": {"zh": "细流", "en": "Trickle"},
    "river_width_2": {"zh": "小河", "en": "Small"},
    "river_width_4": {"zh": "中河", "en": "Medium"},
    "river_width_5": {"zh": "大河", "en": "Large"},
    "river_width_7": {"zh": "宽河", "en": "Wide"},
    "river_width_8": {"zh": "巨河", "en": "Huge"},
    "river_width_9": {"zh": "最宽", "en": "Widest"},

    # === 地形类型（TerrainType.name） ===
    "terrain_name_ocean":    {"zh": "海洋", "en": "Ocean"},
    "terrain_name_lakes":    {"zh": "湖泊", "en": "Lakes"},
    "terrain_name_plains":   {"zh": "平原", "en": "Plains"},
    "terrain_name_forest":   {"zh": "森林", "en": "Forest"},
    "terrain_name_hills":    {"zh": "丘陵", "en": "Hills"},
    "terrain_name_mountain": {"zh": "山地", "en": "Mountain"},
    "terrain_name_desert":   {"zh": "沙漠", "en": "Desert"},
    "terrain_name_marsh":    {"zh": "沼泽", "en": "Marsh"},
    "terrain_name_jungle":   {"zh": "丛林", "en": "Jungle"},
    "terrain_name_urban":    {"zh": "城市", "en": "Urban"},

    # === Graphical terrain 变体名 ===
    "gt_terrain_0":             {"zh": "平原",        "en": "Plains"},
    "gt_terrain_1":             {"zh": "森林",        "en": "Forest"},
    "gt_desert_mountain":       {"zh": "沙漠丘陵",    "en": "Desert Hills"},
    "gt_desert":                {"zh": "沙漠",        "en": "Desert"},
    "gt_terrain_4":             {"zh": "森林(变体)",  "en": "Forest (var)"},
    "gt_terrain_5":             {"zh": "平原(变体)",  "en": "Plains (var)"},
    "gt_terrain_6":             {"zh": "山地",        "en": "Mountain"},
    "gt_terrain_7":             {"zh": "沙漠(变体)",  "en": "Desert (var)"},
    "gt_desert_hills":          {"zh": "沙漠丘陵",    "en": "Desert Hills"},
    "gt_terrain_9":             {"zh": "沼泽",        "en": "Marsh"},
    "gt_terrain_10":            {"zh": "山地(变体)",  "en": "Mountain (var)"},
    "gt_desert_mountain_11":    {"zh": "沙漠山地",    "en": "Desert Mountain"},
    "gt_desert_12":             {"zh": "沙漠(岩地)",  "en": "Desert (rocky)"},
    "gt_forest_13":             {"zh": "城市",        "en": "Urban"},
    "gt_forest_14":             {"zh": "湖泊",        "en": "Lakes"},
    "gt_ocean_15":              {"zh": "海洋",        "en": "Ocean"},
    "gt_snow_16":               {"zh": "雪山",        "en": "Snow Mountain"},
    "gt_hills_blend":           {"zh": "丘陵",        "en": "Hills"},
    "gt_mountain_variation_sand":  {"zh": "沙色山地", "en": "Sand Mountain"},
    "gt_plains_snow":           {"zh": "雪原",        "en": "Snow Plains"},
    "gt_mountain_variation_grass": {"zh": "草地山地", "en": "Grass Mountain"},
    "gt_jungle_18":             {"zh": "丛林",        "en": "Jungle"},
    "gt_jungle_blend_18":       {"zh": "丛林(变体)",  "en": "Jungle (var)"},
    "gt_jungle_mountain":       {"zh": "丛林山地",    "en": "Jungle Mountain"},
    "gt_desert_mountain_tops":  {"zh": "沙漠山顶",    "en": "Desert Peaks"},

    # === 导出验证 ===
    "export_result_title_ok":    {"zh": "导出完成", "en": "Export Complete"},
    "export_result_title_errors": {"zh": "导出完成（有问题）", "en": "Export Complete (Issues Found)"},
    "export_done_all_pass":      {"zh": "导出成功，验证全部通过！", "en": "Export succeeded, all checks passed!"},
    "export_done_has_errors":    {"zh": "导出成功，但验证发现问题（进游戏可能崩溃）", "en": "Export succeeded, but verification found issues (may crash in game)"},
    "export_result_close":       {"zh": "关闭", "en": "Close"},

    # === 崩溃处理 ===
    "crash_title":    {"zh": "软件崩溃", "en": "Application Crashed"},
    "crash_message":  {"zh": "发生未处理的异常:\n\n{}", "en": "Unhandled exception:\n\n{}"},
    "crash_log_saved": {"zh": "完整信息已保存到:\n{}", "en": "Full details saved to:\n{}"},

    # === 导出对话框 ===
    # 检查项名称
    "export_check_provinces": {"zh": "省份", "en": "Provinces"},
    "export_check_land": {"zh": "陆地", "en": "Land"},
    "export_check_state": {"zh": "State (州)", "en": "State"},
    "export_check_country": {"zh": "国家", "en": "Country"},
    "export_check_strategic_region": {"zh": "战略区域", "en": "Strategic Region"},
    "export_check_continent": {"zh": "大陆", "en": "Continent"},
    "export_check_terrain": {"zh": "地形", "en": "Terrain"},
    "export_check_heightmap": {"zh": "高度图", "en": "Heightmap"},
    "export_check_assets": {"zh": "美术资产", "en": "Art Assets"},

    # 检查项详情 — 缺失
    "export_check_no_provinces": {"zh": "没有省份数据，请先画地图并生成省份", "en": "No province data. Please draw the map and generate provinces first"},
    "export_check_no_land": {"zh": "没有陆地像素，请先在 Land 模式画地图", "en": "No land pixels. Please draw the map in Land mode first"},
    "export_check_no_state": {"zh": "没有 State — 每个陆地省份必须属于一个 State，否则崩溃", "en": "No states — every land province must belong to a state, or the game will crash"},
    "export_check_no_country": {"zh": "没有国家 — 至少需要一个国家，否则无法进入游戏", "en": "No countries — at least one country is needed to enter the game"},
    "export_check_no_strategic_region": {"zh": "没有战略区域 — 每个省份必须属于一个战略区域，否则崩溃", "en": "No strategic regions — every province must belong to a strategic region, or the game will crash"},
    "export_check_no_continent": {"zh": "没有大陆定义 — 导出时使用默认大陆", "en": "No continent defined — default continent will be used on export"},
    "export_check_no_terrain": {"zh": "没有地形数据 — 导出时自动从 tile_map 生成", "en": "No terrain data — will be auto-generated from tile_map on export"},
    "export_check_no_heightmap": {"zh": "没有高度数据 — 导出时自动生成默认高度", "en": "No height data — default heightmap will be auto-generated on export"},

    # 检查项详情 — 正常
    "export_check_province_ok": {"zh": "共 {count} 个省份", "en": "{count} provinces total"},
    "export_check_state_ok": {"zh": "共 {count} 个 State", "en": "{count} states total"},
    "export_check_country_ok": {"zh": "共 {count} 个国家", "en": "{count} countries total"},
    "export_check_strategic_region_ok": {"zh": "共 {count} 个战略区域", "en": "{count} strategic regions total"},
    "export_check_continent_ok": {"zh": "共 {count} 个大陆", "en": "{count} continents total"},
    "export_check_terrain_ok": {"zh": "地形数据已设置", "en": "Terrain data is set"},
    "export_check_heightmap_ok": {"zh": "高度数据已设置", "en": "Height data is set"},

    # 检查项详情 — 警告
    "export_check_province_gaps": {"zh": "共 {total} 个省份，但 ID 有 {gaps} 个空洞（被吞并的省份需要用切割或增量生成补回来，否则导出后 HOI4 属性会错位）", "en": "{total} provinces total, but {gaps} ID gaps found (merged provinces need to be re-split or incrementally regenerated, otherwise HOI4 attributes will be misaligned)"},
    "export_check_state_orphans": {"zh": "有 {count} 个 State，但 {orphans} 个陆地省份未分配（导出时自动领养）", "en": "{count} states, but {orphans} land provinces unassigned (will be auto-adopted on export)"},
    "export_check_country_unowned": {"zh": "有 {count} 个国家，但 {unowned} 个 State 未分配所有者", "en": "{count} countries, but {unowned} states have no owner"},
    "export_check_assets_all_clean": {"zh": "共 {total} 个导入的原始资产全部保留（导出不会覆盖）", "en": "All {total} imported assets preserved (export will not overwrite)"},
    "export_check_assets_dirty": {"zh": "共 {total} 个导入资产：{clean} 个保留、{dirty} 个将重新生成\n（因为相关地图数据被编辑过）", "en": "{total} imported assets: {clean} preserved, {dirty} will be regenerated\n(related map data was edited)"},

    # 自动补全日志
    "export_auto_no_provinces": {"zh": "错误：没有省份数据，无法补全", "en": "Error: no province data, cannot auto-complete"},
    "export_auto_gen_states": {"zh": "自动生成 {count} 个 State（每组约15省份）", "en": "Auto-generated {count} states (~15 provinces each)"},
    "export_auto_create_country": {"zh": "自动创建默认国家 AAA", "en": "Auto-created default country AAA"},
    "export_auto_assign_states": {"zh": "将 {count} 个无主 State 分配给 {tag}", "en": "Assigned {count} unowned states to {tag}"},
    "export_auto_set_capital": {"zh": "国家 {tag} 自动设首都为省份 {pid}", "en": "Country {tag} auto-set capital to province {pid}"},
    "export_auto_gen_sr": {"zh": "自动生成 {count} 个战略区域", "en": "Auto-generated {count} strategic regions"},
    "export_auto_create_continent": {"zh": "自动创建默认大陆 default_continent", "en": "Auto-created default continent 'default_continent'"},

    # 导出工作线程
    "export_worker_pre_check": {"zh": "正在执行导出前检查和修复...", "en": "Running pre-export checks and fixes..."},

    # 对话框 UI
    "export_dlg_title": {"zh": "导出 MOD", "en": "Export MOD"},
    "export_pre_check_title": {"zh": "导出前检查", "en": "Pre-Export Check"},
    "export_project_readiness": {"zh": "项目完成度", "en": "Project Readiness"},
    "export_scope": {"zh": "导出范围", "en": "Export Scope"},
    "export_scope_map": {"zh": "地图文件 (BMP/CSV/positions/buildings)", "en": "Map files (BMP/CSV/positions/buildings)"},
    "export_scope_states": {"zh": "States (history/states/)", "en": "States (history/states/)"},
    "export_scope_countries": {"zh": "国家 (country_tags/countries/history)", "en": "Countries (country_tags/countries/history)"},
    "export_scope_strategic_regions": {"zh": "战略区域 (strategicregions/weatherpositions)", "en": "Strategic regions (strategicregions/weatherpositions)"},
    "export_scope_localisation": {"zh": "本地化 (localisation/)", "en": "Localisation (localisation/)"},
    "export_scope_supply": {"zh": "补给系统 (supply_nodes/railways/supply_areas)", "en": "Supply system (supply_nodes/railways/supply_areas)"},
    "export_scope_gfx": {"zh": "图形资源 (国旗/肖像)", "en": "Graphics (flags/portraits)"},
    "export_scope_replace_path": {"zh": "replace_path + descriptor.mod", "en": "replace_path + descriptor.mod"},
    "export_log": {"zh": "操作日志", "en": "Operation Log"},
    "export_btn_auto": {"zh": "自动补全并导出", "en": "Auto-Complete & Export"},
    "export_btn_direct": {"zh": "直接导出（不补全）", "en": "Export Directly (No Auto-Complete)"},
    "export_btn_export": {"zh": "导出", "en": "Export"},
    "export_can_auto": {"zh": "可自动补全", "en": "can be auto-completed"},
    "export_log_prefix": {"zh": "补全", "en": "Auto"},
    "export_separator": {"zh": "、", "en": ", "},
    "export_confirm_skip": {"zh": "以下数据缺失：{names}\n\n缺失的数据会导致 HOI4 加载崩溃。确定要跳过补全直接导出吗？", "en": "The following data is missing: {names}\n\nMissing data will cause HOI4 to crash on load. Are you sure you want to skip auto-complete and export anyway?"},
    "export_choose_dir": {"zh": "选择导出目录", "en": "Choose Export Directory"},
    "export_exporting": {"zh": "正在导出...", "en": "Exporting..."},
    "export_failed_title": {"zh": "导出失败", "en": "Export Failed"},

    # 导出结果
    "export_result_success": {"zh": "MOD 导出成功！\n路径: {path}\n", "en": "MOD exported successfully!\nPath: {path}\n"},
    "export_result_stats_header": {"zh": "── 统计 ──", "en": "── Statistics ──"},
    "export_stat_provinces": {"zh": "省份", "en": "Provinces"},
    "export_stat_states": {"zh": "State", "en": "States"},
    "export_stat_countries": {"zh": "国家", "en": "Countries"},
    "export_stat_files": {"zh": "文件", "en": "Files"},
    "export_result_fixed_header": {"zh": "\n── 自动修复 ──", "en": "\n── Auto-Fixed ──"},
    "export_result_fixed_tag": {"zh": "已修复", "en": "Fixed"},
    "export_result_warnings_header": {"zh": "\n── 导出警告 ──", "en": "\n── Export Warnings ──"},
    "export_result_warning_tag": {"zh": "警告", "en": "Warning"},
    "export_verify_header": {"zh": "\n── MOD 验证 ──", "en": "\n── MOD Verification ──"},
    "export_verify_all_pass": {"zh": "  ✅ 所有检查通过，可以进游戏了！", "en": "  ✅ All checks passed. Ready to play!"},
    "export_verify_errors_header": {"zh": "\n── MOD 验证：{count} 个错误（可能导致崩溃）──", "en": "\n── MOD Verification: {count} errors (may cause crash) ──"},
    "export_verify_warnings_header": {"zh": "\n── MOD 验证：{count} 个警告 ──", "en": "\n── MOD Verification: {count} warnings ──"},

    # === 后勤页面 (logistics/page.py) ===
    "logistics_rail_supply_section": {"zh": "铁路 / 补给", "en": "Railway / Supply"},
    "logistics_click_province_hint": {"zh": "选择工具后点击省份:", "en": "Select a tool then click a province:"},
    "logistics_rail_label": {"zh": "铁路", "en": "Rail"},
    "logistics_rail_erase_tip": {"zh": "擦除铁路", "en": "Erase railway"},
    "logistics_rail_level_tip": {"zh": "铁路等级 {0}", "en": "Railway level {0}"},
    "logistics_supply_label": {"zh": "补给", "en": "Supply"},
    "logistics_supply_place_tip": {"zh": "放置补给节点", "en": "Place supply node"},
    "logistics_supply_erase_tip": {"zh": "删除补给节点", "en": "Remove supply node"},

    # === 战略区域页面 (strategic_region/page.py) ===
    "sr_tip": {"zh": "在列表选中一个区域，然后点击地图省份分配。\n白色边界线 = State 边界。", "en": "Select a region from the list, then click map provinces to assign.\nWhite borders = State boundaries."},
    "sr_quick_section": {"zh": "快速开始", "en": "Quick Start"},
    "sr_edit_section": {"zh": "手动编辑", "en": "Manual Edit"},
    "sr_assign_drag_label": {"zh": "拖拽分配省份(陆地+海洋)", "en": "Drag-assign provinces (land+sea)"},
    "sr_from_states_btn_short": {"zh": "从州创建", "en": "From States"},
    "sr_from_states_confirm_btn_short": {"zh": "确认", "en": "Confirm"},
    "sr_list_section": {"zh": "区域列表", "en": "Region List"},
    "sr_props_section": {"zh": "选中区域属性", "en": "Selected Region Properties"},
    "sr_assign_mode_label": {"zh": "分配模式（点省份加入选中区域）", "en": "Assign mode (click province to add to selected region)"},

    # === 州页面 (state/page.py) ===
    "state_quick_section": {"zh": "快速开始", "en": "Quick Start"},
    "state_edit_section": {"zh": "手动编辑", "en": "Manual Edit"},
    "state_assign_drag_label": {"zh": "拖拽分配省份到州", "en": "Drag-assign provinces to state"},
    "state_batch_select_btn_short": {"zh": "框选建州", "en": "Lasso Create"},
    "state_batch_confirm_btn_short": {"zh": "确认建州", "en": "Confirm"},
    "state_assign_mode_label": {"zh": "✏ 分配模式（点省份加入选中州）", "en": "✏ Assign mode (click province to add to selected state)"},
    "state_assign_hint": {"zh": "💡 默认点击地图 = 查看州信息。勾选上面开关才能分配省份。", "en": "💡 Default click = view state info. Enable the toggle above to assign provinces."},
    "state_vp_hint": {"zh": "双击地图省份 = 设置胜利点(VP)", "en": "Double-click a province = set Victory Point (VP)"},

    # === 文件操作 (main_window_file_ops.py) ===
    "file_ops_new_confirm": {"zh": "新建项目将清除当前数据，是否继续？", "en": "Creating a new project will clear current data. Continue?"},
    "file_ops_map_size_title": {"zh": "选择地图尺寸", "en": "Select Map Size"},
    "file_ops_map_size_prompt": {"zh": "选择新项目的地图尺寸：", "en": "Choose a map size for the new project:"},
    "file_ops_new_created": {"zh": "新项目已创建 ({0}×{1})", "en": "New project created ({0}×{1})"},
    "file_ops_save_title": {"zh": "保存项目", "en": "Save Project"},
    "file_ops_open_title": {"zh": "打开项目", "en": "Open Project"},
    "file_ops_proj_filter": {"zh": "HOI4 项目 (*.hoi4proj);;All Files (*)", "en": "HOI4 Project (*.hoi4proj);;All Files (*)"},
    "file_ops_saved": {"zh": "项目已保存: {0}", "en": "Project saved: {0}"},
    "file_ops_save_fail": {"zh": "保存失败", "en": "Save Failed"},
    "file_ops_loaded": {"zh": "项目已加载: {0}", "en": "Project loaded: {0}"},
    "file_ops_loaded_gaps": {"zh": "项目已加载: {0} | ⚠ 项目自带 {1} 个省份 ID 空洞", "en": "Project loaded: {0} | ⚠ {1} province ID gaps found"},
    "file_ops_load_fail": {"zh": "加载失败", "en": "Load Failed"},
    "file_ops_vanilla_loaded": {"zh": "原版地图参考已加载: {0}", "en": "Vanilla map reference loaded: {0}"},
    "file_ops_vanilla_not_found": {"zh": "未找到原版地图文件\n检查路径: {0}", "en": "Vanilla map files not found\nCheck path: {0}"},
    "file_ops_ref_loaded": {"zh": "参考图已加载: {0}", "en": "Reference image loaded: {0}"},
    "file_ops_ref_fail": {"zh": "无法加载图片", "en": "Failed to load image"},
    "file_ops_landmask_title": {"zh": "选择陆海源图", "en": "Select Land/Sea Source Image"},
    "file_ops_threshold_title": {"zh": "陆海阈值", "en": "Land/Sea Threshold"},
    "file_ops_threshold_prompt": {"zh": "灰度阈值 (0-255)\n>= 阈值为陆地，< 阈值为海洋\n建议：高度图用 1；卫星图用 90 左右", "en": "Grayscale threshold (0-255)\n>= threshold = land, < threshold = sea\nSuggested: 1 for heightmaps; ~90 for satellite images"},
    "file_ops_invert_title": {"zh": "反转?", "en": "Invert?"},
    "file_ops_invert_prompt": {"zh": "勾选 Yes 表示：暗色为陆地、亮色为海洋（默认 No）", "en": "Select Yes to invert: dark = land, bright = sea (default No)"},
    "file_ops_img_read_fail": {"zh": "读取图片失败：{0}", "en": "Failed to read image: {0}"},
    "file_ops_landmask_done": {"zh": "陆海导入完成 — 陆地 {0}% / 海洋 {1}%", "en": "Land/sea import done — land {0}% / sea {1}%"},
    "file_ops_import_confirm": {"zh": "导入将替换当前地图数据，是否继续？", "en": "Import will replace current map data. Continue?"},
    "file_ops_select_mod_dir": {"zh": "选择 HOI4 MOD 或原版目录", "en": "Select HOI4 MOD or Vanilla Directory"},
    "file_ops_missing_files": {"zh": "目录缺少必需文件:\n", "en": "Directory is missing required files:\n"},
    "file_ops_import_fail": {"zh": "导入失败：{0}", "en": "Import failed: {0}"},
    "file_ops_mod_imported": {"zh": "MOD地图已导入 ({0}×{1}, {2} 省份, {3} 州, {4} 战略区域, {5} 美术资产)", "en": "MOD map imported ({0}×{1}, {2} provinces, {3} states, {4} strategic regions, {5} art assets)"},
    "file_ops_import_warnings": {"zh": "注意:\n", "en": "Warnings:\n"},
    "file_ops_import_done": {"zh": "导入完成", "en": "Import Complete"},
    "file_ops_test_dialog_title": {"zh": "渐进式测试导出", "en": "Progressive Test Export"},
    "file_ops_test_select_level": {"zh": "选择测试级别（从低到高，逐级排查崩溃原因）:", "en": "Select test level (low to high, debug crashes step by step):"},
    "file_ops_test_lv1_title": {"zh": "Lv1: 最小完整MOD（1国家）", "en": "Lv1: Minimal MOD (1 country)"},
    "file_ops_test_lv1_desc": {"zh": "地图 + State + 1国家(AAA) + 补给 + 战略区域 + replace_path\n最小可运行配置，测试基础文件格式是否正确", "en": "Map + State + 1 country (AAA) + supply + strategic regions + replace_path\nMinimal runnable config, test basic file format"},
    "file_ops_test_lv2_title": {"zh": "Lv2: +2个国家 +bookmark", "en": "Lv2: +2 countries +bookmark"},
    "file_ops_test_lv2_desc": {"zh": "在Lv1基础上加: 第2个国家(BBB) + bookmark选择界面\n测试多国家和bookmark", "en": "Lv1 + 2nd country (BBB) + bookmark selection\nTest multi-country and bookmark"},
    "file_ops_test_lv3_title": {"zh": "Lv3: +意识形态 +State类别", "en": "Lv3: +ideology +state categories"},
    "file_ops_test_lv3_desc": {"zh": "在Lv2基础上加: ideologies, state_category 定义文件\n测试自定义意识形态/State类别", "en": "Lv2 + ideologies, state_category definitions\nTest custom ideologies/state categories"},
    "file_ops_test_lv4_title": {"zh": "Lv4: +更多replace_path", "en": "Lv4: +more replace_path"},
    "file_ops_test_lv4_desc": {"zh": "在Lv3基础上加: 更多replace_path（清空原版国策/事件等）\n完整TC MOD", "en": "Lv3 + more replace_path (clear vanilla focus/events etc.)\nFull TC MOD"},
    "file_ops_test_output_dir": {"zh": "选择测试导出目录", "en": "Select Test Export Directory"},
    "file_ops_test_generating": {"zh": "正在生成 Lv{0} 测试MOD...", "en": "Generating Lv{0} test MOD..."},
    "file_ops_test_export_title": {"zh": "测试导出", "en": "Test Export"},
    "file_ops_test_export_ok": {"zh": "Lv{0} 测试MOD已导出到:\n{1}\n\n{2}\n\n启动游戏测试是否正常加载。\n如果崩溃，降低级别重试；如果能进，升高级别继续。", "en": "Lv{0} test MOD exported to:\n{1}\n\n{2}\n\nLaunch the game to test.\nIf it crashes, try a lower level; if it works, go higher."},
    "file_ops_export_fail": {"zh": "导出失败", "en": "Export Failed"},

    # === 战略区域对话框 ===
    "sr_dlg_title": {"zh": "战略区域编辑器", "en": "Strategic Region Editor"},
    "sr_dlg_auto_generate": {"zh": "自动生成 (按 State 分组)", "en": "Auto Generate (Group by State)"},
    "sr_dlg_new_region": {"zh": "新建空 Region", "en": "New Empty Region"},
    "sr_dlg_delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "sr_dlg_name_label": {"zh": "名字:", "en": "Name:"},
    "sr_dlg_weather_label": {"zh": "天气预设:", "en": "Weather Preset:"},
    "sr_dlg_province_count": {"zh": "省份: 0", "en": "Provinces: 0"},
    "sr_dlg_start_pick": {"zh": "开始拾取省份", "en": "Start Picking Provinces"},
    "sr_dlg_stop_pick": {"zh": "停止拾取", "en": "Stop Picking"},
    "sr_dlg_close": {"zh": "关闭", "en": "Close"},
    "sr_dlg_err_no_provinces": {"zh": "需要先生成省份", "en": "Provinces must be generated first"},
    "sr_dlg_auto_confirm": {"zh": "将按当前 State 分组自动生成战略区域，替换已有区域。继续？", "en": "Auto-generate strategic regions grouped by State, replacing existing ones. Continue?"},
    "sr_dlg_err_select_region": {"zh": "请先选中一个 Region", "en": "Please select a Region first"},
    "sr_dlg_region_list": {"zh": "区域列表", "en": "Region List"},
    "sr_dlg_naval_none": {"zh": "(无)", "en": "(None)"},
    "sr_dlg_list_item_fmt": {"zh": "{0} 省", "en": "{0} prov"},
    "sr_dlg_province_count_fmt": {"zh": "省份: {0}", "en": "Provinces: {0}"},
    "sr_dlg_generated_fmt": {"zh": "已生成 {0} 个区域", "en": "Generated {0} regions"},
    "sr_dlg_pick_status_fmt": {"zh": "点击主画布省份 → 加入 Region #{0}", "en": "Click province on canvas → add to Region #{0}"},
    "sr_dlg_assigned_fmt": {"zh": "已指派省份 {0} → Region #{1}", "en": "Assigned province {0} → Region #{1}"},

    # === 邻接关系对话框 ===
    "adj_dlg_title": {"zh": "相邻关系编辑器", "en": "Adjacency Editor"},
    "adj_dlg_delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "adj_dlg_from_placeholder": {"zh": "省份 ID", "en": "Province ID"},
    "adj_dlg_to_placeholder": {"zh": "省份 ID", "en": "Province ID"},
    "adj_dlg_type_sea": {"zh": "海峡/运河 (sea)", "en": "Strait/Canal (sea)"},
    "adj_dlg_type_impassable": {"zh": "不可通行 (impassable)", "en": "Impassable"},
    "adj_dlg_through_placeholder": {"zh": "途经海省 ID (sea 类型)", "en": "Through sea province ID (sea type)"},
    "adj_dlg_comment_placeholder": {"zh": "备注 (可选)", "en": "Comment (optional)"},
    "adj_dlg_clear_fields": {"zh": "清空字段", "en": "Clear Fields"},
    "adj_dlg_save": {"zh": "保存", "en": "Save"},
    "adj_dlg_err_invalid_id": {"zh": "起点/终点必须是整数省份 ID", "en": "From/To must be integer province IDs"},
    "adj_dlg_tip": {"zh": "海峡 (sea): 跨海连接两个省 (必须指定 through 海省)\n不可通行 (impassable): 阻塞两省的直接相邻\n使用流程: 填字段 → 拾取省份 → 保存", "en": "Strait (sea): cross-sea connection between two provinces (must specify through sea province)\nImpassable: blocks direct adjacency between two provinces\nWorkflow: fill fields → pick provinces → save"},
    "adj_dlg_edit_group": {"zh": "新建 / 编辑", "en": "New / Edit"},
    "adj_dlg_pick_from_canvas": {"zh": "从画布拾取", "en": "Pick from Canvas"},
    "adj_dlg_from_label": {"zh": "起点省份:", "en": "From Province:"},
    "adj_dlg_to_label": {"zh": "终点省份:", "en": "To Province:"},
    "adj_dlg_type_label": {"zh": "类型:", "en": "Type:"},
    "adj_dlg_through_label": {"zh": "途经省份:", "en": "Through Province:"},
    "adj_dlg_comment_label": {"zh": "备注:", "en": "Comment:"},
    "adj_dlg_saved_fmt": {"zh": "已保存: {0} → {1} ({2}){3}", "en": "Saved: {0} → {1} ({2}){3}"},
    "adj_dlg_pick_status_fmt": {"zh": "拾取模式: 点击主画布省份填入 {0}", "en": "Pick mode: click province on canvas to fill {0}"},
    "adj_dlg_filled_fmt": {"zh": "已填入 {0} = {1}", "en": "Filled {0} = {1}"},

    # === 大陆对话框 ===
    "cont_dlg_title": {"zh": "大陆编辑器", "en": "Continent Editor"},
    "cont_dlg_add": {"zh": "添加", "en": "Add"},
    "cont_dlg_rename": {"zh": "重命名", "en": "Rename"},
    "cont_dlg_delete": {"zh": "删除", "en": "Delete"},
    "cont_dlg_start_assign": {"zh": "开始指派省份", "en": "Start Assigning Provinces"},
    "cont_dlg_stop_assign": {"zh": "停止指派", "en": "Stop Assigning"},
    "cont_dlg_err_min_one": {"zh": "必须至少保留 1 个大陆", "en": "Must keep at least 1 continent"},
    "cont_dlg_err_select": {"zh": "请先选中一个大陆", "en": "Please select a continent first"},
    "cont_dlg_tip": {"zh": "用法：\n1. 添加大陆（每个 MOD 至少 1 个）\n2. 选中大陆后点『开始指派』\n3. 在主画布点击陆地省份 → 该省份归入该大陆\n4. 再次点击按钮结束指派", "en": "Usage:\n1. Add continents (at least 1 per MOD)\n2. Select a continent and click 'Start Assigning'\n3. Click land provinces on canvas → assigned to that continent\n4. Click the button again to stop"},
    "cont_dlg_list_item_fmt": {"zh": "{0} 省", "en": "{0} prov"},
    "cont_dlg_add_title": {"zh": "添加大陆", "en": "Add Continent"},
    "cont_dlg_add_prompt": {"zh": "大陆名 (英文, 不含空格):", "en": "Continent name (English, no spaces):"},
    "cont_dlg_rename_title": {"zh": "重命名大陆", "en": "Rename Continent"},
    "cont_dlg_rename_prompt": {"zh": "新名字:", "en": "New name:"},
    "cont_dlg_delete_title": {"zh": "删除大陆", "en": "Delete Continent"},
    "cont_dlg_delete_confirm_fmt": {"zh": "删除「{0}」? 指向它的省份会改回首个大陆.", "en": "Delete \"{0}\"? Provinces assigned to it will revert to the first continent."},
    "cont_dlg_assigning_fmt": {"zh": "正在指派到：{0} — 点击主画布省份", "en": "Assigning to: {0} — click provinces on canvas"},
    "cont_dlg_assigned_fmt": {"zh": "已指派省份 {0} → {1}", "en": "Assigned province {0} → {1}"},

    # === 邻接规则对话框 ===
    "rule_dlg_list_label": {"zh": "规则列表", "en": "Rule List"},
    "rule_dlg_new": {"zh": "新建...", "en": "New..."},
    "rule_dlg_delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "rule_dlg_name_label": {"zh": "名字:", "en": "Name:"},
    "rule_dlg_name_placeholder": {"zh": "如 SUEZ_CANAL", "en": "e.g. SUEZ_CANAL"},
    "rule_dlg_pick_add": {"zh": "从画布拾取添加", "en": "Pick from Canvas"},
    "rule_dlg_manual_add": {"zh": "手填省份 ID", "en": "Enter Province ID"},
    "rule_dlg_remove_selected": {"zh": "删除选中", "en": "Remove Selected"},
    "rule_dlg_icon_placeholder": {"zh": "省份 ID, -1 = 不设", "en": "Province ID, -1 = none"},
    "rule_dlg_pick_icon": {"zh": "从画布拾取", "en": "Pick from Canvas"},
    "rule_dlg_close": {"zh": "关闭", "en": "Close"},
    "rule_dlg_err_name_exists": {"zh": "规则名 {0} 已存在", "en": "Rule name {0} already exists"},
    "rule_dlg_err_icon_int": {"zh": "icon 必须是整数省份 ID", "en": "Icon must be an integer province ID"},
    "rule_dlg_status_select": {"zh": "先选中或新建一个规则", "en": "Select or create a rule first"},
    "rule_dlg_status_pick_province": {"zh": "点击主画布省份 → 加入 required_provinces", "en": "Click province on canvas → add to required_provinces"},
    "rule_dlg_status_pick_icon": {"zh": "点击主画布海省 → 设为 icon", "en": "Click sea province on canvas → set as icon"},
    "rule_dlg_title": {"zh": "Adjacency Rules 编辑器", "en": "Adjacency Rules Editor"},
    "rule_dlg_tip": {"zh": "通行表: 4 种关系 × 4 种通行类型. 勾上=允许通过.\nrequired_provinces: 控制者必须同时控制这些省份才有效.\nicon: 海军视图里图标显示在哪个海省.", "en": "Pass table: 4 relations × 4 pass types. Check = allow passage.\nrequired_provinces: controller must hold these provinces for the rule to apply.\nicon: which sea province shows the icon in naval view."},
    "rule_dlg_pass_group": {"zh": "通行权限", "en": "Passage Permissions"},
    "rule_dlg_pass_army": {"zh": "陆军", "en": "Army"},
    "rule_dlg_pass_navy": {"zh": "海军", "en": "Navy"},
    "rule_dlg_pass_submarine": {"zh": "潜艇", "en": "Submarine"},
    "rule_dlg_pass_trade": {"zh": "贸易", "en": "Trade"},
    "rule_dlg_rel_contested": {"zh": "争夺中", "en": "Contested"},
    "rule_dlg_rel_enemy": {"zh": "敌国", "en": "Enemy"},
    "rule_dlg_rel_friend": {"zh": "盟友", "en": "Friend"},
    "rule_dlg_rel_neutral": {"zh": "中立", "en": "Neutral"},
    "rule_dlg_icon_label": {"zh": "Icon 海省:", "en": "Icon Sea Province:"},
    "rule_dlg_loaded_fmt": {"zh": "已加载 {0}", "en": "Loaded {0}"},
    "rule_dlg_new_title": {"zh": "新建规则", "en": "New Rule"},
    "rule_dlg_new_prompt": {"zh": "规则名 (英文大写, 如 SUEZ_CANAL):", "en": "Rule name (UPPER_CASE, e.g. SUEZ_CANAL):"},
    "rule_dlg_delete_title": {"zh": "删除", "en": "Delete"},
    "rule_dlg_delete_confirm_fmt": {"zh": "删除规则 {0}?", "en": "Delete rule {0}?"},
    "rule_dlg_add_province_title": {"zh": "添加省份", "en": "Add Province"},
    "rule_dlg_add_province_prompt": {"zh": "省份 ID:", "en": "Province ID:"},
    "rule_dlg_added_req_fmt": {"zh": "加入 required: {0}", "en": "Added to required: {0}"},
    "rule_dlg_icon_set_fmt": {"zh": "icon 设为 {0}", "en": "Icon set to {0}"},

    # === 地图配置对话框 ===
    "dm_dlg_title": {"zh": "地图配置 (default.map)", "en": "Map Config (default.map)"},
    "dm_dlg_add_index": {"zh": "添加索引", "en": "Add Index"},
    "dm_dlg_delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "dm_dlg_reset_default": {"zh": "恢复默认", "en": "Reset to Default"},
    "dm_dlg_save": {"zh": "保存", "en": "Save"},
    "dm_dlg_cancel": {"zh": "取消", "en": "Cancel"},
    "dm_dlg_tip": {"zh": "default.map 是 HOI4 引擎的地图加载配置.\n大部分字段是文件名 (vanilla 标准, 不可改).\n可调的是树木调色板索引和河流上限.", "en": "default.map is the HOI4 engine map loading config.\nMost fields are file names (vanilla standard, not editable).\nAdjustable: tree palette indices and river max level."},
    "dm_dlg_prov_count_fmt": {"zh": "{0} (自动)", "en": "{0} (auto)"},
    "dm_dlg_prov_count_label": {"zh": "总省份数:", "en": "Total Provinces:"},
    "dm_dlg_river_max_label": {"zh": "河流最大等级:", "en": "Max River Level:"},
    "dm_dlg_tree_label": {"zh": "树木调色板索引", "en": "Tree Palette Indices"},
    "dm_dlg_tree_desc": {"zh": "(trees.bmp 这些 palette ID 算树):", "en": "(these palette IDs in trees.bmp count as trees):"},
    "dm_dlg_add_title": {"zh": "添加索引", "en": "Add Index"},
    "dm_dlg_add_prompt": {"zh": "Palette 索引 (1-13):", "en": "Palette index (1-13):"},

    # === 颜色贴图对话框 ===
    "cm_dlg_title": {"zh": "战略总览贴图颜色", "en": "Strategic Overview Map Colors"},
    "cm_dlg_reset_default": {"zh": "恢复默认", "en": "Reset to Default"},
    "cm_dlg_save": {"zh": "保存", "en": "Save"},
    "cm_dlg_cancel": {"zh": "取消", "en": "Cancel"},
    "cm_dlg_tip": {"zh": "缩到战略视角时显示的全图色调.\n默认是地球感土褐+靛蓝, 改成任何颜色让你的架空世界更独特.\n(只影响极远视角的总览, 近景仍用地形画刷)", "en": "Color tones shown at strategic zoom level.\nDefault is earth-like brown + indigo. Change to any color for your alternate world.\n(Only affects far zoom overview; close-up still uses terrain brushes)"},
    "cm_dlg_land": {"zh": "陆地", "en": "Land"},
    "cm_dlg_sea": {"zh": "海洋", "en": "Sea"},
    "cm_dlg_lake": {"zh": "湖泊", "en": "Lake"},
    "cm_dlg_pick_color": {"zh": "选择颜色", "en": "Pick Color"},

    # === 新大陆画笔页面 ===
    "new_land_size_label": {"zh": "大小", "en": "Size"},
    "new_land_pixel_count": {"zh": "已画: 0 像素", "en": "Painted: 0 pixels"},
    "new_land_pixel_count_fmt": {"zh": "已画: {0} 像素", "en": "Painted: {0} pixels"},
    "new_land_generate": {"zh": "生成省份", "en": "Generate Provinces"},
    "new_land_generate_tip": {"zh": "为新画的陆地区域生成省份", "en": "Generate provinces for newly painted land"},
    "new_land_clear": {"zh": "清空画笔", "en": "Clear Brush"},
    "new_land_clear_tip": {"zh": "清空已画的新陆地记录（不删除已画的陆地）", "en": "Clear painted land records (does not delete the land)"},

    # === 铁路对话框 ===
    "rail_dlg_title": {"zh": "铁路列表", "en": "Railway List"},
    "rail_dlg_hint": {"zh": "所有已画的铁路. 新建请用侧边栏的『启用铁路画笔』.", "en": "All drawn railways. Use sidebar 'Enable Railway Brush' to create new ones."},
    "rail_dlg_delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "rail_dlg_clear_all": {"zh": "清空所有", "en": "Clear All"},
    "rail_dlg_close": {"zh": "关闭", "en": "Close"},
    "rail_dlg_list_item_fmt": {"zh": "{0} 省", "en": "{0} prov"},

    # === State 详情对话框 ===
    "state_dlg_save": {"zh": "保存", "en": "Save"},
    "state_dlg_cancel": {"zh": "取消", "en": "Cancel"},
    "state_dlg_edit_prov_buildings": {"zh": "编辑省份级建筑 (bunker / 海防 / 海军基地)...", "en": "Edit Province Buildings (bunker / coastal / naval base)..."},
    "state_dlg_add": {"zh": "添加...", "en": "Add..."},
    "state_dlg_delete_selected": {"zh": "删除选中", "en": "Delete Selected"},
    "state_dlg_title_fmt": {"zh": "State 详情 — {0} (ID {1})", "en": "State Details — {0} (ID {1})"},
    "state_dlg_tab_basic": {"zh": "基础", "en": "Basic"},
    "state_dlg_vp_names": {"zh": "城市命名 (Victory Points)", "en": "City Names (Victory Points)"},
    "state_dlg_vp_province": {"zh": "省份ID", "en": "Province"},
    "state_dlg_vp_value": {"zh": "VP值", "en": "VP Value"},
    "state_dlg_vp_city_name": {"zh": "城市名", "en": "City Name"},
    "state_dlg_vp_none": {"zh": "(该州无胜利点)", "en": "(No victory points in this state)"},
    "state_dlg_tab_resources": {"zh": "资源", "en": "Resources"},
    "state_dlg_tab_buildings": {"zh": "建筑", "en": "Buildings"},
    "state_dlg_tab_cores": {"zh": "核心 / 宣称", "en": "Cores / Claims"},
    "state_dlg_name_label": {"zh": "名字:", "en": "Name:"},
    "state_dlg_manpower_label": {"zh": "人口:", "en": "Manpower:"},
    "state_dlg_impassable": {"zh": "不可通行 (impassable)", "en": "Impassable"},
    "state_dlg_controller_same": {"zh": "(同 owner)", "en": "(same as owner)"},
    "state_dlg_controller_label": {"zh": "初始控制者:", "en": "Initial Controller:"},
    "state_dlg_supplies_label": {"zh": "本地补给加成:", "en": "Local Supply Bonus:"},
    "state_dlg_resources_hint": {"zh": "6 种战略资源, 0 表示不写", "en": "6 strategic resources, 0 = omit"},
    "state_dlg_buildings_hint": {"zh": "State 级建筑等级", "en": "State-level Building Levels"},
    "state_dlg_buildings_sub": {"zh": "0 = 按 state_category 默认值; 其他值会覆盖默认", "en": "0 = use state_category default; other values override"},
    "state_dlg_cores_group": {"zh": "额外核心 (owner 自动是核心, 这里填其他国家)", "en": "Extra Cores (owner is auto-core, add other countries here)"},
    "state_dlg_claims_group": {"zh": "宣称 (add_claim_by)", "en": "Claims (add_claim_by)"},
    "state_dlg_select_tag": {"zh": "选择国家 TAG:", "en": "Select Country TAG:"},
    "state_dlg_input_tag": {"zh": "输入国家 TAG (3 字母):", "en": "Enter Country TAG (3 letters):"},
    "state_dlg_add_core_title": {"zh": "添加核心", "en": "Add Core"},
    "state_dlg_add_claim_title": {"zh": "添加宣称", "en": "Add Claim"},
    "state_dlg_res_oil": {"zh": "石油", "en": "Oil"},
    "state_dlg_res_aluminium": {"zh": "铝", "en": "Aluminium"},
    "state_dlg_res_rubber": {"zh": "橡胶", "en": "Rubber"},
    "state_dlg_res_tungsten": {"zh": "钨", "en": "Tungsten"},
    "state_dlg_res_steel": {"zh": "钢", "en": "Steel"},
    "state_dlg_res_chromium": {"zh": "铬", "en": "Chromium"},
    "state_dlg_bld_infrastructure": {"zh": "基础设施 (0-5)", "en": "Infrastructure (0-5)"},
    "state_dlg_bld_arms_factory": {"zh": "军工厂", "en": "Arms Factory"},
    "state_dlg_bld_industrial_complex": {"zh": "民用工厂", "en": "Industrial Complex"},
    "state_dlg_bld_dockyard": {"zh": "船坞", "en": "Dockyard"},
    "state_dlg_bld_air_base": {"zh": "空军基地 (0-10)", "en": "Air Base (0-10)"},
    "state_dlg_bld_anti_air": {"zh": "防空 (0-5)", "en": "Anti-Air (0-5)"},
    "state_dlg_bld_radar": {"zh": "雷达站 (0-4)", "en": "Radar Station (0-4)"},
    "state_dlg_bld_synthetic": {"zh": "合成炼油厂", "en": "Synthetic Refinery"},
    "state_dlg_bld_fuel_silo": {"zh": "燃料储存", "en": "Fuel Silo"},
    "state_dlg_bld_nuclear": {"zh": "核反应堆 (0-3)", "en": "Nuclear Reactor (0-3)"},
    "state_dlg_bld_rocket": {"zh": "火箭发射井 (0-10)", "en": "Rocket Site (0-10)"},
    "state_dlg_bld_mass_transit": {"zh": "大众运输 (0-3)", "en": "Mass Transit (0-3)"},
    "state_dlg_bld_supply_node": {"zh": "补给节点 (0-1)", "en": "Supply Node (0-1)"},

    # === 省份建筑对话框 ===
    "prov_bld_save": {"zh": "保存", "en": "Save"},
    "prov_bld_cancel": {"zh": "取消", "en": "Cancel"},
    "prov_bld_title_fmt": {"zh": "省份建筑 — {0} (ID {1})", "en": "Province Buildings — {0} (ID {1})"},
    "prov_bld_tip": {"zh": "为 state 内每个陆地省份单独配置防御建筑.\n0 = 不建. bunker 适用所有陆地, coastal_bunker 和 naval_base 应只给沿海省份.", "en": "Configure defensive buildings for each land province in this state.\n0 = none. Bunker applies to all land; coastal_bunker and naval_base should only be set for coastal provinces."},
    "prov_bld_province_id": {"zh": "省份 ID", "en": "Province ID"},
    "prov_bld_bunker": {"zh": "陆防", "en": "Bunker"},
    "prov_bld_coastal": {"zh": "海防", "en": "Coastal"},
    "prov_bld_naval": {"zh": "海军基地", "en": "Naval Base"},

    # === 状态栏信息 ===
    "status_no_new_land": {"zh": "没有画新陆地，先用画笔画。", "en": "No new land painted. Draw with the brush first."},
    "status_new_land_cleared": {"zh": "新大陆画笔已清空。", "en": "New land brush cleared."},

    # === 新大陆画笔页面 (补充) ===
    "new_land_hint": {"zh": "用画笔在海洋上画新陆地，画完后点「生成省份」。\n只为画的区域生成省份，旧大陆不受影响。", "en": "Paint new land on ocean with the brush, then click 'Generate Provinces'.\nOnly the painted area gets new provinces; existing land is unaffected."},
    "new_land_section_brush": {"zh": "画笔大小", "en": "Brush Size"},
    "new_land_section_status": {"zh": "状态", "en": "Status"},
    "new_land_section_actions": {"zh": "操作", "en": "Actions"},
    "new_land_pixel_painted_fmt": {"zh": "已画: {0} 像素", "en": "Painted: {0} pixels"},

    # === 快捷键对话框 ===
    "shortcut_dlg_title": {"zh": "快捷键设置", "en": "Shortcut Settings"},
    "shortcut_col_function": {"zh": "功能", "en": "Function"},
    "shortcut_col_current": {"zh": "当前快捷键", "en": "Current Shortcut"},
    "shortcut_col_new": {"zh": "新快捷键", "en": "New Shortcut"},
    "shortcut_undo": {"zh": "撤销", "en": "Undo"},
    "shortcut_redo": {"zh": "重做", "en": "Redo"},
    "shortcut_save": {"zh": "保存项目", "en": "Save Project"},
    "shortcut_open": {"zh": "打开项目", "en": "Open Project"},
    "shortcut_new": {"zh": "新建项目", "en": "New Project"},
    "shortcut_export": {"zh": "导出MOD", "en": "Export MOD"},
    "shortcut_mode_land": {"zh": "大陆模式", "en": "Land Mode"},
    "shortcut_mode_province": {"zh": "省份模式", "en": "Province Mode"},
    "shortcut_mode_terrain": {"zh": "地形模式", "en": "Terrain Mode"},
    "shortcut_mode_height": {"zh": "高度模式", "en": "Height Mode"},
    "shortcut_mode_river": {"zh": "河流模式", "en": "River Mode"},
    "shortcut_mode_state": {"zh": "State模式", "en": "State Mode"},
    "shortcut_mode_country": {"zh": "国家模式", "en": "Country Mode"},
    "shortcut_mode_continent": {"zh": "大洲模式", "en": "Continent Mode"},
    "shortcut_tool_brush": {"zh": "画笔工具", "en": "Brush Tool"},
    "shortcut_tool_eraser": {"zh": "橡皮擦", "en": "Eraser"},
    "shortcut_tool_fill": {"zh": "填充工具", "en": "Fill Tool"},
    "shortcut_tool_transform": {"zh": "变换工具", "en": "Transform Tool"},
    "shortcut_tool_pan": {"zh": "平移工具", "en": "Pan Tool"},
    "shortcut_delete": {"zh": "删除", "en": "Delete"},
    "shortcut_zoom_fit": {"zh": "适应窗口", "en": "Fit to Window"},

    # === 胜利点对话框 ===
    "dlg_vp_title_fmt": {"zh": "胜利点 — 省份 {0}", "en": "Victory Point — Province {0}"},
    "dlg_vp_prompt": {"zh": "VP 值 (0=删除):", "en": "VP Value (0=remove):"},

    # === 剩余硬编码 — 战略区域对话框 ===
    "sr_dlg_region_list": {"zh": "区域列表", "en": "Region List"},
    "sr_dlg_naval_terrain": {"zh": "Naval terrain:", "en": "Naval terrain:"},
    "sr_dlg_naval_none": {"zh": "(无)", "en": "(none)"},
    "sr_dlg_province_count_fmt": {"zh": "省份: {0}", "en": "Provinces: {0}"},
    "sr_dlg_generated_fmt": {"zh": "已生成 {0} 个区域", "en": "Generated {0} regions"},
    "sr_dlg_pick_status_fmt": {"zh": "点击主画布省份 → 加入 Region #{0}", "en": "Click province on canvas → add to Region #{0}"},
    "sr_dlg_assigned_fmt": {"zh": "已指派省份 {0} → Region #{1}", "en": "Assigned province {0} → Region #{1}"},
    "sr_dlg_list_item_fmt": {"zh": "{0} 省", "en": "{0} prov"},

    # === 剩余硬编码 — 邻接对话框 ===
    "adj_dlg_tip": {"zh": "海峡 (sea): 跨海连接两个省 (必须指定 through 海省)\n不可通行 (impassable): 阻塞两省的直接相邻\n使用流程: 填字段 → 拾取省份 → 保存", "en": "Strait (sea): Cross-sea connection between two provinces (must specify through sea province)\nImpassable: Block direct adjacency between two provinces\nWorkflow: Fill fields → Pick provinces → Save"},
    "adj_dlg_edit_group": {"zh": "新建 / 编辑", "en": "New / Edit"},
    "adj_dlg_pick_from_canvas": {"zh": "从画布拾取", "en": "Pick from Canvas"},
    "adj_dlg_from_label": {"zh": "起点省份:", "en": "From Province:"},
    "adj_dlg_to_label": {"zh": "终点省份:", "en": "To Province:"},
    "adj_dlg_type_label": {"zh": "类型:", "en": "Type:"},
    "adj_dlg_through_label": {"zh": "途经省份:", "en": "Through Province:"},
    "adj_dlg_comment_label": {"zh": "备注:", "en": "Comment:"},
    "adj_dlg_saved_fmt": {"zh": "已保存: {0} → {1} ({2}){3}", "en": "Saved: {0} → {1} ({2}){3}"},
    "adj_dlg_pick_status_fmt": {"zh": "拾取模式: 点击主画布省份填入 {0}", "en": "Pick mode: Click province on canvas to fill {0}"},
    "adj_dlg_filled_fmt": {"zh": "已填入 {0} = {1}", "en": "Filled {0} = {1}"},

    # === 剩余硬编码 — 大陆对话框 ===
    "cont_dlg_tip": {"zh": "用法：\n1. 添加大陆（每个 MOD 至少 1 个）\n2. 选中大陆后点『开始指派』\n3. 在主画布点击陆地省份 → 该省份归入该大陆\n4. 再次点击按钮结束指派", "en": "Usage:\n1. Add continents (at least 1 per MOD)\n2. Select a continent, click 'Start Assigning'\n3. Click land provinces on canvas → assign to continent\n4. Click button again to stop"},
    "cont_dlg_add_title": {"zh": "添加大陆", "en": "Add Continent"},
    "cont_dlg_add_prompt": {"zh": "大陆名 (英文, 不含空格):", "en": "Continent name (English, no spaces):"},
    "cont_dlg_rename_title": {"zh": "重命名大陆", "en": "Rename Continent"},
    "cont_dlg_rename_prompt": {"zh": "新名字:", "en": "New name:"},
    "cont_dlg_delete_title": {"zh": "删除大陆", "en": "Delete Continent"},
    "cont_dlg_delete_confirm_fmt": {"zh": "删除「{0}」? 指向它的省份会改回首个大陆.", "en": "Delete '{0}'? Provinces assigned to it will be moved to the first continent."},
    "cont_dlg_list_item_fmt": {"zh": "{0} 省", "en": "{0} prov"},
    "cont_dlg_assigning_fmt": {"zh": "正在指派到：{0} — 点击主画布省份", "en": "Assigning to: {0} — click provinces on canvas"},
    "cont_dlg_assigned_fmt": {"zh": "已指派省份 {0} → {1}", "en": "Assigned province {0} → {1}"},

    # === 剩余硬编码 — 规则对话框 ===
    "rule_dlg_title": {"zh": "Adjacency Rules 编辑器", "en": "Adjacency Rules Editor"},
    "rule_dlg_tip": {"zh": "通行表: 4 种关系 × 4 种通行类型. 勾上=允许通过.\nrequired_provinces: 控制者必须同时控制这些省份才有效.\nicon: 海军视图里图标显示在哪个海省.", "en": "Pass table: 4 relations × 4 pass types. Checked = allow passage.\nrequired_provinces: Controller must hold these provinces for the rule to apply.\nicon: Province where the icon appears in naval view."},
    "rule_dlg_pass_group": {"zh": "通行权限", "en": "Pass Permissions"},
    "rule_dlg_icon_label": {"zh": "Icon 海省:", "en": "Icon Sea Province:"},
    "rule_dlg_new_title": {"zh": "新建规则", "en": "New Rule"},
    "rule_dlg_new_prompt": {"zh": "规则名 (英文大写, 如 SUEZ_CANAL):", "en": "Rule name (uppercase, e.g. SUEZ_CANAL):"},
    "rule_dlg_delete_title": {"zh": "删除", "en": "Delete"},
    "rule_dlg_delete_confirm_fmt": {"zh": "删除规则 {0}?", "en": "Delete rule {0}?"},
    "rule_dlg_add_province_title": {"zh": "添加省份", "en": "Add Province"},
    "rule_dlg_add_province_prompt": {"zh": "省份 ID:", "en": "Province ID:"},
    "rule_dlg_loaded_fmt": {"zh": "已加载 {0}", "en": "Loaded {0}"},
    "rule_dlg_added_req_fmt": {"zh": "加入 required: {0}", "en": "Added to required: {0}"},
    "rule_dlg_icon_set_fmt": {"zh": "icon 设为 {0}", "en": "Icon set to {0}"},
    "rule_dlg_rel_contested": {"zh": "争夺中", "en": "Contested"},
    "rule_dlg_rel_enemy": {"zh": "敌国", "en": "Enemy"},
    "rule_dlg_rel_friend": {"zh": "盟友", "en": "Friend"},
    "rule_dlg_rel_neutral": {"zh": "中立", "en": "Neutral"},
    "rule_dlg_pass_army": {"zh": "陆军", "en": "Army"},
    "rule_dlg_pass_navy": {"zh": "海军", "en": "Navy"},
    "rule_dlg_pass_submarine": {"zh": "潜艇", "en": "Submarine"},
    "rule_dlg_pass_trade": {"zh": "贸易", "en": "Trade"},

    # === 剩余硬编码 — 地图配置对话框 ===
    "dm_dlg_tip": {"zh": "default.map 是 HOI4 引擎的地图加载配置.\n大部分字段是文件名 (vanilla 标准, 不可改).\n可调的是树木调色板索引和河流上限.", "en": "default.map is the HOI4 engine map loading config.\nMost fields are file names (vanilla standard, not editable).\nAdjustable: tree palette indices and river max level."},
    "dm_dlg_prov_count_fmt": {"zh": "{0} (自动)", "en": "{0} (auto)"},
    "dm_dlg_prov_count_label": {"zh": "总省份数:", "en": "Total Provinces:"},
    "dm_dlg_river_max_label": {"zh": "河流最大等级:", "en": "River Max Level:"},
    "dm_dlg_tree_label": {"zh": "树木调色板索引", "en": "Tree Palette Indices"},
    "dm_dlg_tree_desc": {"zh": "(trees.bmp 这些 palette ID 算树):", "en": "(these palette IDs in trees.bmp count as trees):"},
    "dm_dlg_add_title": {"zh": "添加索引", "en": "Add Index"},
    "dm_dlg_add_prompt": {"zh": "Palette 索引 (1-13):", "en": "Palette index (1-13):"},

    # === 剩余硬编码 — 颜色贴图对话框 ===
    "cm_dlg_tip": {"zh": "缩到战略视角时显示的全图色调.\n默认是地球感土褐+靛蓝, 改成任何颜色让你的架空世界更独特.\n(只影响极远视角的总览, 近景仍用地形画刷)", "en": "Color tint shown at strategic zoom level.\nDefault is earth-tone brown + indigo. Change to make your world unique.\n(Only affects far zoom overview, close-up still uses terrain brushes)"},
    "cm_dlg_land": {"zh": "陆地", "en": "Land"},
    "cm_dlg_sea": {"zh": "海洋", "en": "Sea"},
    "cm_dlg_lake": {"zh": "湖泊", "en": "Lake"},
    "cm_dlg_pick_color": {"zh": "选择颜色", "en": "Pick Color"},

    # === 剩余硬编码 — 铁路对话框 (补充) ===
    "rail_dlg_list_item_fmt": {"zh": "{0} 省", "en": "{0} prov"},

    # === 通用 ===
    "dlg_error": {"zh": "错误", "en": "Error"},
    "dlg_auto_generate": {"zh": "自动生成", "en": "Auto Generate"},

    # === 右键菜单 ===
    "context_province_info": {"zh": "省份 {} 信息", "en": "Province {} Info"},
    "context_set_terrain": {"zh": "设置地形", "en": "Set Terrain"},
    "context_belongs_state": {"zh": "所属 State: {}", "en": "Belongs to State: {}"},
    "context_set_vp": {"zh": "设置胜利点...", "en": "Set Victory Point..."},
    "context_belongs_country": {"zh": "所属国家: {}", "en": "Belongs to Country: {}"},
    "context_set_capital": {"zh": "设为首都", "en": "Set as Capital"},
    "context_unassigned_state": {"zh": "(未分配 State)", "en": "(Unassigned State)"},
    "context_copy_province_id": {"zh": "复制省份ID", "en": "Copy Province ID"},
    "context_set_vp_title": {"zh": "设置胜利点", "en": "Set Victory Point"},
    "context_set_vp_label": {"zh": "省份 {} 的 VP 分值\n(1=小镇, 5=中等, 10=城市, 20=首都):", "en": "VP value for province {}\n(1=town, 5=medium, 10=city, 20=capital):"},
}


def set_language(lang: str) -> None:
    """设置当前语言 ('zh' 或 'en')，同时保存到配置。"""
    global _current_lang
    if lang in ("zh", "en"):
        _current_lang = lang
        try:
            from PyQt5.QtCore import QSettings
            s = QSettings("HOI4MapMaker", "Settings")
            s.setValue("language", lang)
        except Exception:
            pass


def get_language() -> str:
    """获取当前语言"""
    return _current_lang


def tr(key: str, *args) -> str:
    """
    获取翻译文本。
    支持格式化参数，例如 tr("status_pos", 100, 200) → "位置: (100, 200)"
    """
    entry = _translations.get(key)
    if entry is None:
        return key
    text = entry.get(_current_lang, entry.get("zh", key))
    if args:
        return text.format(*args)
    return text
