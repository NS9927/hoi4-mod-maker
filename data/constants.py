"""
HOI4 地图 MOD 工具 — 全局常量定义
"""

# 地图尺寸（HOI4 原版标准）
MAP_WIDTH = 5632
MAP_HEIGHT = 2048

# 省份数量范围
MIN_PROVINCES = 3000
MAX_PROVINCES = 8000
DEFAULT_PROVINCES = 5000

# 省份最小像素数
MIN_PROVINCE_PIXELS = 8

# 省份数量上限（HOI4 引擎限制）
ENGINE_MAX_PROVINCES = 19000

# 高度图参数
SEA_LEVEL = 95          # 海平面灰度值
OCEAN_HEIGHT = 40       # 深海灰度值
LAND_BASE_HEIGHT = 120  # 陆地基础灰度值
MOUNTAIN_HEIGHT = 220   # 山地灰度值

# 画布缩放范围
ZOOM_MIN = 0.05
ZOOM_MAX = 10.0
ZOOM_STEP = 1.2

# 画笔大小范围
BRUSH_MIN = 1
BRUSH_MAX = 100
BRUSH_DEFAULT = 10

# 地块类型（内部表示）
TILE_UNDEFINED = 0
TILE_LAND = 1
TILE_SEA = 2
TILE_LAKE = 3

# 地块类型名称映射
TILE_TYPE_NAMES = {
    TILE_UNDEFINED: "undefined",
    TILE_LAND: "land",
    TILE_SEA: "sea",
    TILE_LAKE: "lake",
}

# HOI4 definition.csv 类型名
PROVINCE_TYPE_LAND = "land"
PROVINCE_TYPE_SEA = "sea"
PROVINCE_TYPE_LAKE = "lake"

# 禁用颜色（HOI4 不允许使用）
FORBIDDEN_COLOR = (0, 0, 0)

# BMP 文件常量
BMP_HEADER_SIZE = 14
BMP_INFO_HEADER_SIZE = 40
BMP_BITS_24 = 24
BMP_BITS_8 = 8

# 默认 MOD 信息
DEFAULT_MOD_NAME = "Fantasy World"
DEFAULT_MOD_VERSION = "0.1"
DEFAULT_SUPPORTED_VERSION = "1.17.*"

# HOI4 路径（用户可配置）
DEFAULT_HOI4_PATH = "G:/SteamLibrary/steamapps/common/Hearts of Iron IV/"
DEFAULT_MOD_OUTPUT_PATH = "D:/Documents/Paradox Interactive/Hearts of Iron IV/mod/"

# 全转换 MOD 替换路径
# 只替换我们实际提供内容的目录，避免清空引擎必需文件导致崩溃
# 未替换的目录会使用原版内容（bookmarks、game_rules、modifiers 等）
REPLACE_PATHS = [
    # 参照 Kaiserreich MOD 的 77 个 replace_path（已验证能正常运行）
    # 我们的目录
    "history/countries", "history/states", "history/units", "history/general",
    "map/strategicregions", "map/supplyareas",
    "common/countries", "common/country_tags", "common/bookmarks",
    # KR 替换的所有目录（空目录不会崩溃，KR已验证）
    "common/abilities",
    "common/ai_areas", "common/ai_equipment", "common/ai_focuses",
    "common/ai_navy/fleet", "common/ai_navy/goals", "common/ai_navy/taskforce",
    "common/ai_strategy", "common/ai_strategy_plans", "common/ai_templates",
    "common/autonomous_states",
    "common/bop",
    "common/characters",
    "common/collections",
    "common/continuous_focus",
    "common/country_leader", "common/country_tag_aliases",
    "common/decisions", "common/decisions/categories",
    "common/difficulty_settings",
    "common/dynamic_modifiers",
    "common/factions/goals", "common/factions/rules", "common/factions/templates",
    "common/focus_inlay_windows",
    "common/game_rules",
    "common/idea_tags", "common/ideas", "common/ideologies",
    "common/military_industrial_organization/organizations",
    "common/modifier_definitions", "common/modifiers",
    "common/names",
    "common/national_focus",
    "common/on_actions",
    "common/operations", "common/opinion_modifiers",
    "common/peace_conference/ai_peace", "common/peace_conference/cost_modifiers",
    "common/raids",
    "common/scripted_diplomatic_actions", "common/scripted_effects",
    "common/scripted_guis", "common/scripted_localisation", "common/scripted_triggers",
    "common/special_projects/projects",
    "common/state_category",
    "common/technologies", "common/technology_sharing", "common/technology_tags",
    "common/units/codenames_operatives",
    "common/units/names", "common/units/names_divisions",
    "common/units/names_railway_guns", "common/units/names_ships",
    "common/unit_leader",
    "common/unit_medals",
    "common/factions/rules/groups",
    "common/scorers/country",
    "common/ai_faction_theaters",
    "events",
    "tests",
]
