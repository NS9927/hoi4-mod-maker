"""
HOI4 地图 MOD 工具 — 全局常量定义
"""

# 地图尺寸（必须是 256 的倍数，否则 HOI4 崩溃 — 见 参考/Troubleshooting.txt:100）
# 原版 5632×2048
MAP_WIDTH = 5632
MAP_HEIGHT = 2048

# 地图尺寸预设
MAP_SIZE_PRESETS = {
    "小 (2048×1024)": (2048, 1024),
    "中 (3072×1536)": (3072, 1536),
    "大 (4096×2048)": (4096, 2048),
    "原版 (5632×2048)": (5632, 2048),
}


def set_map_size(width: int, height: int) -> None:
    """更新全局地图尺寸。必须在初始化画布数组之前调用。"""
    import data.constants as _mod
    _mod.MAP_WIDTH = width
    _mod.MAP_HEIGHT = height

# 省份数量范围 (vanilla 13382, HOI4 上限 21000, 14000 以上警告)
MIN_PROVINCES = 1000
MAX_PROVINCES = 15000
DEFAULT_PROVINCES = 12000

# 省份最小像素数
# HOI4 硬性最低 8 像素，但 <50 像素的省份会导致 buildings.txt 坐标问题
# 生成时合并阈值设 50，确保每个省份足够大
MIN_PROVINCE_PIXELS = 50

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

# ════════════════════════════════════════════════════════════
# HOI4 合法意识形态白名单
# ════════════════════════════════════════════════════════════
# 主意识形态（用于 set_politics.ruling_party 和 set_popularities 的键）
# 来源：vanilla common/ideologies/00_ideologies.txt
VALID_MAIN_IDEOLOGIES = ("neutrality", "democratic", "fascism", "communism")

# 意识形态子类型（用于 country_leader.ideology 字段）
# 每个主意识形态对应一个默认子类型，保证 leader 定义一定合法
DEFAULT_IDEOLOGY_SUBTYPE = {
    "neutrality": "despotism",
    "democratic": "conservatism",
    "fascism": "nazism",
    "communism": "marxism",
}

# ════════════════════════════════════════════════════════════
# HOI4 合法 3D 建筑类型白名单（buildings.txt 可用类型）
# ════════════════════════════════════════════════════════════
# 来源：vanilla common/buildings/00_buildings.txt 中 spawn_point / has_pop_center = yes 的实体建筑
# 关键：infrastructure / air_base / supply_hub 等 state-level 统计建筑【不能】写入 buildings.txt
# 只有这些"有 3D 模型的点位建筑"合法，否则引擎会 MAP_ERROR 崩溃
VALID_3D_BUILDING_TYPES = frozenset({
    "arms_factory", "industrial_complex", "air_base", "anti_air_building",
    "bunker", "coastal_bunker", "dockyard", "naval_base", "naval_base_spawn",
    "supply_node", "rocket_site", "rocket_site_spawn",
    "synthetic_refinery", "radar_station", "fuel_silo", "nuclear_reactor",
    "floating_harbor",
})

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
    # ════════════════════════════════════════════════════════════
    # 最小集合 — 只替换"我们必须自己定义"的目录
    # 其他全部保留 vanilla（包括 ideas/scripted_effects/decisions 等）
    #
    # 关键认识：vanilla 的 GER_xxx idea/bop/decision 会被【定义】
    # 但永远【不会被应用】（因为 GER 国家不存在）。on_actions 引用
    # 它们时找得到定义，触发器失败时静默跳过，不会崩溃。
    #
    # 反之，如果我们把这些目录清空（哪怕放占位），vanilla on_actions
    # 调用具体ID时找不到定义就会触发 +878973 ACCESS_VIOLATION 崩溃。
    # ════════════════════════════════════════════════════════════

    # --- 地图子目录（必须替换，引用我们的省份ID）---
    "map/strategicregions",
    "map/supplyareas",

    # --- 历史（必须替换，引用我们的省份ID/state ID）---
    "history/states",
    "history/countries",
    "history/units",
    "history/general",

    # --- 国家定义（必须替换，我们要定义自己的TAG）---
    "common/country_tags",
    "common/countries",

    # --- 全部 AI 系统（必须替换，vanilla 引用 ENG/GER/JAP 等已删国家
    # + 引用 ENG_INF_01 等不存在的 division template → AI 初始化时
    # ACCESS_VIOLATION 崩溃。EaW 全替换确认可行）
    "common/ai_equipment",
    "common/ai_focuses",
    "common/ai_peace",
    "common/ai_strategy",
    "common/ai_strategy_plans",
    "common/ai_templates",
    "common/ai_navy/fleet",
    "common/ai_navy/goals",
    "common/ai_navy/taskforce",

    # --- 单位/师/船/铁路炮命名（必须替换，否则 vanilla 的 names_*.txt fallback
    # 同时匹配我们 75 个 dynamic tag，"Multiple name groups for D01..D75" → 崩）
    "common/units/names",
    "common/units/names_divisions",
    "common/units/names_ships",
    "common/units/names_railway_guns",
    "common/units/codenames_operatives",

    # --- 2026-04-09 移除 scripted_effects / scripted_triggers / dynamic_modifiers ---
    # 参考: 参考/Troubleshooting.txt 行 87
    # "A variety of crash types are caused by recklessly unloading folders with
    #  replace_path, leading to the game detecting there not being any database
    #  entries of a certain type. It's best practice to port over generic files..."
    # 正确策略: 保留 vanilla (符号定义完整, 事件触发不匹配 AAA-EEE 就静默).

    # --- events / common/national_focus 不 replace ---
    # 2026-04-09 实测: replace 整个目录会破坏 load_focus_tree = generic_focus,
    # 即使放 placeholder 也会因语法/namespace 缺失导致游戏无法加载.
    # 真正危险的只有 1 个文件: events/GOE_Raj.txt 硬编码 733.controller.
    # 解决方案: 文件级覆盖 (scrubber 里写同名空文件), 不用 replace_path.

    # --- raids / decisions 必须 replace ---
    # 不 replace → vanilla decisions 引用 state 1032/1035/1036 等不存在的 ID,
    # 每 tick 刷几万行错误 → 走时间崩溃 (LastRead=client_ping).
    # replace 后导出器必须同时拷贝 vanilla 的 decisions/categories/ 目录,
    # 否则加载时找不到 decision category 定义 → 加载崩溃.
    "common/raids",
    "common/decisions",

    # ════════════════════════════════════════════════════════════
    # 阶段 5 "Nuke AI" 已回退（2026-04-08 实测）
    # 原计划加 7 条 replace_path：characters/names/ideas/national_focus/
    # decisions/scripted_localisation/events。结果 vanilla 的 common/on_actions/*.txt
    # 里所有 country_event/add_ideas/dynamic_modifier 调用全部指向被清空的目标，
    # error.log 暴涨 9000+ 行 → 初始化阶段崩，连菜单都进不去。
    # 保留原 24 条（能进菜单），AI tick 崩溃用别的路径解决（见 ai_tick_crash_rootcauses.md）。
    # ════════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════════
    # 不替换的目录（保留 vanilla，不会崩溃）
    # ════════════════════════════════════════════════════════════
    # common/ideas        → vanilla idea 定义保留，触发条件失败静默
    # common/scripted_effects → on_actions 依赖
    # common/scripted_triggers
    # common/scripted_localisation
    # common/decisions    → on_actions 调用具体 decision ID
    # common/bop          → on_actions 引用 FIN_power_balance 等
    # common/national_focus → on_actions 检查 has_completed_focus
    # common/dynamic_modifiers
    # common/autonomous_states
    # common/peace_conference/*
    # common/intelligence_agencies, common/factions/*, common/military_industrial_organization
    # common/technology_sharing
    # common/units/*
    # common/ai_* (产生警告但不崩溃)
    # common/technologies  → 用原版科技树
    # common/ideologies, common/state_category → 用原版
    # common/on_actions, common/modifiers 等 → 引擎核心
    # events              → 引用原版国家但不崩溃
    #
    # ════════════════════════════════════════════════════════════
    # 文件级覆盖（不需要 replace_path）
    # ════════════════════════════════════════════════════════════
    # map/*.bmp, map/definition.csv → 按文件名覆盖
    # map/unitstacks.txt → 空文件覆盖（避免 prov -1 错误）
    # common/bookmarks/the_gathering_storm.txt → 空文件覆盖
    # common/bookmarks/blitzkrieg.txt → 空文件覆盖
    # common/bookmarks/z_fantasy.txt → 我们的 bookmark
    # portraits/AAA.txt → ★崩溃根因★ 必须有，否则 character_manager 崩溃
    # common/scripted_effects      → on_actions 依赖它，清空即 +878973 崩溃
    # common/scripted_triggers     → 同上
    # common/scripted_localisation → 同上
    # common/dynamic_modifiers     → on_actions 依赖它
    # common/characters            → ideas/decisions 依赖它
    # common/national_focus        → decisions/on_actions 依赖它
    # common/decisions             → on_actions 触发它
    # common/ai_*                  → 产生 warning 不崩溃
    # common/technologies          → 用户明确要保留原版科技
    # common/ideas, common/idea_tags → 引擎核心
    # common/modifiers, common/modifier_definitions → 引擎核心
    # common/bop, common/abilities, common/names → 引擎核心
    # common/operations, common/occupation_laws → 引擎核心
    # common/game_rules, common/difficulty_settings → 引擎核心
    # common/on_actions            → 引擎事件触发核心
    # common/ideologies            → 保留原版意识形态
    # common/state_category        → 保留原版
    # common/bookmarks             → 用同名文件屏蔽原版 bookmark + 加 z_fantasy
    # events                       → 引用原版国家但不崩溃
    # ...以及所有 vanilla 的音乐/UI/脚本/music 等
]
