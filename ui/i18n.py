"""
国际化支持 — 中英文切换
"""

# 当前语言
_current_lang = "zh"

# 翻译字典
_translations: dict[str, dict[str, str]] = {
    # === 主窗口 ===
    "app_title": {
        "zh": "HOI4 幻想世界 MOD 制作工具",
        "en": "HOI4 Fantasy World MOD Maker",
    },
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

    # === 通用 ===
    "btn_ok": {"zh": "确定", "en": "OK"},
    "btn_apply": {"zh": "应用", "en": "Apply"},
    "btn_close": {"zh": "关闭", "en": "Close"},
    "btn_yes": {"zh": "是", "en": "Yes"},
    "btn_no": {"zh": "否", "en": "No"},
    "dlg_confirm": {"zh": "确认", "en": "Confirm"},
    "dlg_warning": {"zh": "警告", "en": "Warning"},
    "dlg_error": {"zh": "错误", "en": "Error"},
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
