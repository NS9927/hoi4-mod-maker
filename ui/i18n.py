"""
国际化支持 — 中英文切换
"""

# 当前语言
_current_lang = "zh"

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
    "continent_add_dlg_title": {"zh": "添加大陆", "en": "Add Continent"},
    "continent_add_dlg_label": {"zh": "大陆名 (英文):", "en": "Continent name (English):"},
    "continent_rename_dlg_title": {"zh": "重命名", "en": "Rename"},
    "continent_rename_dlg_label": {"zh": "新名字:", "en": "New name:"},

    # === 战略区域页面 ===
    "sr_tip": {"zh": "战略区域: 省份分组 + 天气 + 海军地形.\n建议先点'自动生成'按 State 创建初始分组，\n再手动调整。每个区域可设天气和海军地形类型.\n用拾取模式点省份可移入选中的区域.", "en": "Strategic regions: province grouping + weather + naval terrain.\nSuggest clicking 'Auto Generate' to create initial groups by state,\nthen adjust manually. Each region can set weather and naval terrain.\nUse pick mode to move provinces into the selected region."},
    "sr_auto_btn": {"zh": "自动生成 (按 State 分组)", "en": "Auto Generate (Group by State)"},
    "sr_from_states_btn": {"zh": "选择州 → 创建战略区域", "en": "Select States → Create Strategic Region"},
    "sr_from_states_tip": {"zh": "开启后点击地图选择多个州，然后点确认合并为一个战略区域", "en": "Enable to select multiple states on map, then confirm to merge into one strategic region"},
    "sr_from_states_confirm_btn": {"zh": "确认创建战略区域", "en": "Confirm Create Strategic Region"},
    "sr_new_btn": {"zh": "新建", "en": "New"},
    "sr_delete_btn": {"zh": "删除", "en": "Delete"},
    "sr_name_label": {"zh": "名字:", "en": "Name:"},
    "sr_weather_label": {"zh": "天气:", "en": "Weather:"},
    "sr_naval_label": {"zh": "Naval:", "en": "Naval:"},
    "sr_naval_none": {"zh": "(无)", "en": "(None)"},
    "sr_prov_count": {"zh": "省份: {}", "en": "Provinces: {}"},
    "sr_pick_btn": {"zh": "开始拾取省份", "en": "Start Picking Provinces"},

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
    "height_section_ref": {"zh": "高度含义", "en": "Height Reference"},
    "land_btn_fit_map": {"zh": "铺满地图", "en": "Fit to Map"},
    "land_btn_generate": {"zh": "生成省份", "en": "Generate Provinces"},
    "land_btn_hide": {"zh": "隐藏", "en": "Hide"},
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
    "land_section_vanilla_ref": {"zh": "原版地图参考", "en": "Vanilla Map Reference"},
    "land_tool_brush": {"zh": "画笔", "en": "Brush"},
    "land_tool_eraser": {"zh": "橡皮", "en": "Eraser"},
    "land_tool_fill": {"zh": "填充", "en": "Fill"},
    "land_tool_fill_tip": {"zh": "点击一个区域，自动填满相同类型的连通区域", "en": "Click a region to flood-fill connected area of same type"},
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
    "province_hint_merge": {"zh": "合并模式：点第一个省份，再点第二个", "en": "Merge mode: click first province, then second"},
    "province_hint_regen": {"zh": "增量生成：点击省份选择区域（多选），然后点「重新生成」", "en": "Regen: click provinces to select (multi), then click Regenerate"},
    "province_info_coastal": {"zh": "沿海", "en": "Coastal"},
    "province_info_id": {"zh": "省份 ID", "en": "Province ID"},
    "province_info_pixels": {"zh": "像素数", "en": "Pixels"},
    "province_info_terrain": {"zh": "地形", "en": "Terrain"},
    "province_info_type": {"zh": "类型", "en": "Type"},
    "province_section_info": {"zh": "省份信息", "en": "Province Info"},
    "province_section_regen": {"zh": "增量生成", "en": "Incremental Regen"},
    "province_section_tools": {"zh": "省份操作", "en": "Province Tools"},
    "river_btn_validate": {"zh": "验证河流", "en": "Validate Rivers"},
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
    "sr_delete_btn": {"zh": "删除", "en": "Delete"},
    "sr_from_states_btn": {"zh": "选择州 → 创建战略区域", "en": "Select States → Create Strategic Region"},
    "sr_from_states_confirm_btn": {"zh": "确认创建战略区域", "en": "Confirm Create Strategic Region"},
    "sr_from_states_tip": {"zh": "开启后点击地图选择多个州，然后点确认合并为一个战略区域", "en": "Enable to select multiple states on map, then confirm to merge into one strategic region"},
    "sr_name_label": {"zh": "名字:", "en": "Name:"},
    "sr_naval_label": {"zh": "Naval:", "en": "Naval:"},
    "sr_naval_none": {"zh": "(无)", "en": "(None)"},
    "sr_new_btn": {"zh": "新建", "en": "New"},
    "sr_pick_btn": {"zh": "开始拾取省份", "en": "Start Picking Provinces"},
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
}


def set_language(lang: str) -> None:
    """设置当前语言 ('zh' 或 'en')"""
    global _current_lang
    if lang in ("zh", "en"):
        _current_lang = lang


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
