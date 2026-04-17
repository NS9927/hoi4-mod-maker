"""
replace_path 目录生成 + vanilla 文件清洗.

HOI4 的 replace_path 机制让 MOD 可以整个替换 vanilla 的某些目录.
对于 TC MOD, 大部分 vanilla 目录需要替换掉, 但完全空又会导致 AI 崩溃.
这里的策略是"最小可工作"集: 复制一部分 generic 文件 + 清洗掉引用已删 TAG
的内容, 其余写占位.

所有 vanilla 崩溃根因调试记录在 memory/ai_tick_crash_rootcauses.md.
"""

import os
import re
import shutil as _sh

from data.constants import REPLACE_PATHS, DEFAULT_HOI4_PATH


def _build_division_names_with_phantoms() -> str:
    """生成 names_divisions 文件内容: 符合原版格式的最小 generic fallback。"""
    return (
        'GENERIC_INF_01 = {\n'
        '\tname = "Infantry Division"\n'
        '\n'
        '\tfor_countries = { AAA }\n'
        '\n'
        '\tcan_use = { always = yes }\n'
        '\n'
        '\tdivision_types = { "infantry" }\n'
        '\n'
        '\tfallback_name = "%d Infantry Division"\n'
        '\n'
        '\tordered = {\n'
        '\t\t1 = { "1st Infantry Division" }\n'
        '\t\t2 = { "2nd Infantry Division" }\n'
        '\t\t3 = { "3rd Infantry Division" }\n'
        '\t}\n'
        '}\n'
    )


def write_replace_path_dirs(output_dir: str) -> None:
    """为所有 replace_path 创建目录并填充内容.

    精简策略: 所有 REPLACE_PATHS 里的目录我们都自己生成了内容
    (history/*, common/country_tags, common/countries, common/characters,
    common/names, map/strategicregions, map/supplyareas).
    history/general 里没有内容, 放一个空占位文件避免空目录.
    """
    for p in REPLACE_PATHS:
        os.makedirs(os.path.join(output_dir, p), exist_ok=True)

    # 空目录放占位文件
    for empty_dir in ("history/general", "common/strategic_locations"):
        d = os.path.join(output_dir, empty_dir.replace("/", os.sep))
        if os.path.isdir(d) and not os.listdir(d):
            with open(os.path.join(d, "00_placeholder.txt"), "w") as f:
                f.write("# Empty\n")

    ai_full_copy_dirs = (
        "common/ai_strategy",
        "common/ai_focuses",
        "common/ai_equipment",
        "common/ai_strategy_plans",
        "common/ai_navy/fleet",
        "common/ai_navy/taskforce",
    )
    TAG_TOKEN = re.compile(r"(?:^|[_.])[A-Z]{3,4}(?:[_.]|$)")
    FILENAME_BLACKLIST = {
        "zz_debug_effects.txt",
    }

    def _is_generic(filename):
        if filename in FILENAME_BLACKLIST:
            return False
        if filename.startswith("_") or "documentation" in filename.lower():
            return True
        return not TAG_TOKEN.search(filename)

    _BLOCKED_FOR_RE = re.compile(r"blocked_for\s*=\s*\{[^{}]*\}", re.DOTALL)
    _DEAD_TAG_RE = re.compile(
        r"\b(ENG|FRA|GER|ITA|JAP|SOV|USA|CHI|POL|HUN|ROM|YUG|BUL|TUR|GRE|"
        r"MEX|CAN|FIN|NOR|SWE|DEN|CZE|SIA|RAJ|AST|NZL|SAF)\b"
    )
    _AVAILABLE_FOR_RE = re.compile(r"available_for\s*=\s*\{[^{}]*\}", re.DOTALL)

    def _scrub_file(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
        except Exception:
            return
        new = _BLOCKED_FOR_RE.sub("blocked_for = {}", txt)

        def _av_sub(m):
            return "available_for = {}" if _DEAD_TAG_RE.search(m.group(0)) else m.group(0)
        new = _AVAILABLE_FOR_RE.sub(_av_sub, new)
        if new != txt:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)

    for sub in ai_full_copy_dirs:
        dst = os.path.join(output_dir, *sub.split("/"))
        src = os.path.join(DEFAULT_HOI4_PATH, *sub.split("/"))
        os.makedirs(dst, exist_ok=True)
        if os.path.isdir(src):
            for fn in os.listdir(src):
                if not _is_generic(fn):
                    continue
                sp = os.path.join(src, fn)
                if os.path.isfile(sp):
                    dp = os.path.join(dst, fn)
                    _sh.copy2(sp, dp)
                    _scrub_file(dp)
        if not os.listdir(dst):
            with open(os.path.join(dst, "00_placeholder.txt"), "w") as f:
                f.write(f"# Empty — no vanilla generic files for {sub}\n")

    # 2026-04-09: scripted_effects / scripted_triggers / dynamic_modifiers
    # 不再清空 (参考 Troubleshooting.txt 行 87). vanilla 保留, 符号查找完整,
    # 避免 vanilla events/focuses 17773 条 "trigger.cpp:700 Invalid trigger" 累积
    # → AI tick tbb race → 走时间崩溃.

    # common/achievements.txt 顶级覆盖
    ach_path = os.path.join(output_dir, "common", "achievements.txt")
    os.makedirs(os.path.dirname(ach_path), exist_ok=True)
    with open(ach_path, "w", encoding="utf-8") as f:
        f.write("# Empty — TC MOD disables vanilla achievements\n")

    # common/decisions replace — 清空决议但保留 vanilla categories
    # 决议本体清空 (vanilla 硬编码 state ID 每 tick 报错)
    # categories 必须从 vanilla 拷贝 (否则加载崩溃)
    dec_dir = os.path.join(output_dir, "common", "decisions")
    os.makedirs(dec_dir, exist_ok=True)
    with open(os.path.join(dec_dir, "00_placeholder.txt"), "w", encoding="utf-8") as f:
        f.write("# Empty — TC MOD replaces vanilla decisions\n")
    dcat_dir = os.path.join(dec_dir, "categories")
    os.makedirs(dcat_dir, exist_ok=True)
    # 拷贝 vanilla 的 decision categories (加载必需)
    van_dcat = os.path.join(DEFAULT_HOI4_PATH, "common", "decisions", "categories")
    if os.path.isdir(van_dcat):
        for fn in os.listdir(van_dcat):
            src = os.path.join(van_dcat, fn)
            if os.path.isfile(src):
                _sh.copy2(src, os.path.join(dcat_dir, fn))

    # events/*.txt 文件级覆盖 (周期性 tick 报错)
    # vanilla 事件文件引用了 TC MOD 不存在的 state ID 和 controller scope,
    # 导致游戏每周期 tick 报 "State X not found" / "invalid event target: controller"
    # 保留 add_namespace 声明避免其他文件 ID 引用失效, 清空所有 event 体.
    ev_dir = os.path.join(output_dir, "events")
    os.makedirs(ev_dir, exist_ok=True)

    # 需要覆盖的 vanilla event 文件 → namespaces 列表
    _VANILLA_EVENTS_TO_EMPTY = {
        "GOE_Raj.txt": [
            "GOE_RAJ", "GOE_RAJ_partition", "GOE_RAJ_famine", "GOE_RAJ_eic",
            "GOE_RAJ_princely", "GOE_RAJ_navy", "GOE_RAJ_goa",
            "GOE_RAJ_generals", "GOE_RAJ_mughals_peace_deal",
            "GOE_RAJ_loyalist", "GOE_RAJ_news",
        ],
        # NewsEvents.txt: 引用 state 1032/1035/1036 (TC MOD 没有)
        "NewsEvents.txt": ["news"],
        # SEA_Japan.txt: 引用 controller scope 但事件触发时无对象
        "SEA_Japan.txt": [
            "SEA_japan", "SEA_japan_foreign_policy", "SEA_japan_popup_events",
            "SEA_japan_tokko_arrest_events", "SEA_japan_news_events",
            "SEA_japan_hidden_events", "SEA_japan_air_accidents_events",
            "SEA_border_incidents_events", "SEA_imperial_influence_events",
        ],
    }

    for filename, namespaces in _VANILLA_EVENTS_TO_EMPTY.items():
        with open(os.path.join(ev_dir, filename), "w", encoding="utf-8") as f:
            f.write(f"# Emptied — TC MOD overrides vanilla {filename}\n")
            f.write("# Reason: references state IDs or scope targets not in TC MOD\n")
            f.write("# Keep add_namespace declarations so other files' ID refs don't break\n")
            for ns in namespaces:
                f.write(f"add_namespace = {ns}\n")

    # 所有 vanilla on_actions 文件空覆盖
    # 原因: 00_on_actions.txt on_startup 硬编码 canal 省份 6389/7617 + state 58/685,
    # 07/08/09 引用已删国家 dynamic_modifier, 01-10 引用 vanilla state ID.
    # TC MOD 自己的 on_actions 需要时再写新文件.
    oa_dir = os.path.join(output_dir, "common", "on_actions")
    os.makedirs(oa_dir, exist_ok=True)
    _VANILLA_ON_ACTIONS = (
        "00_on_actions.txt",
        "00_testing_on_actions.txt",
        "01_tfv_on_actions.txt",
        "02_dod_on_actions.txt",
        "03_wtt_on_actions.txt",
        "04_mtg_on_actions.txt",
        "05_lar_on_actions.txt",
        "06_bftb_on_actions.txt",
        "07_nsb_on_actions.txt",
        "08_bba_on_actions.txt",
        "09_aat_on_actions.txt",
        "10_toa_on_actions.txt",
        "12_wuw_on_actions.txt",
        "13_goe_on_actions.txt",
        "14_sea_on_actions.txt",
    )
    for fn in _VANILLA_ON_ACTIONS:
        with open(os.path.join(oa_dir, fn), "w", encoding="utf-8") as f:
            f.write(f"# Empty — TC MOD overrides vanilla {fn}\n")
            f.write("on_actions = {\n}\n")

    # common/raids replace — 清空 raids 但保留 vanilla categories
    raids_dir = os.path.join(output_dir, "common", "raids")
    os.makedirs(raids_dir, exist_ok=True)
    with open(os.path.join(raids_dir, "00_placeholder.txt"), "w", encoding="utf-8") as f:
        f.write("# Empty — TC MOD disables vanilla raids system\n")
    cat_dir = os.path.join(raids_dir, "categories")
    os.makedirs(cat_dir, exist_ok=True)
    # 拷贝 vanilla 的 raids categories
    van_rcat = os.path.join(DEFAULT_HOI4_PATH, "common", "raids", "categories")
    if os.path.isdir(van_rcat):
        for fn in os.listdir(van_rcat):
            src = os.path.join(van_rcat, fn)
            if os.path.isfile(src):
                _sh.copy2(src, os.path.join(cat_dir, fn))
    if not os.listdir(cat_dir):
        with open(os.path.join(cat_dir, "00_categories.txt"), "w", encoding="utf-8") as f:
            f.write("categories = {\n}\n")

    # 自建 ai_templates, 无 allowed 过滤
    at_dir = os.path.join(output_dir, "common", "ai_templates")
    os.makedirs(at_dir, exist_ok=True)
    for fn in os.listdir(at_dir):
        os.remove(os.path.join(at_dir, fn))
    with open(os.path.join(at_dir, "00_generic_templates.txt"), "w", encoding="utf-8") as f:
        f.write("""# Generic AI templates — no allowed filter, matches all countries
infantry_generic = {
\trole = infantry
\tupgrade_prio = { base = 2 }
\tinfantry_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tinfantry = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
garrison_generic = {
\trole = garrison
\tupgrade_prio = { base = 1 }
\tgarrison_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tinfantry = 4
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
cavalry_generic = {
\trole = cavalry
\tupgrade_prio = { base = 1 }
\tcavalry_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tcavalry = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
motorized_generic = {
\trole = motorized
\tupgrade_prio = { base = 1 }
\tmotorized_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tmotorized = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
mechanized_generic = {
\trole = mechanized
\tupgrade_prio = { base = 1 }
\tmechanized_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tmechanized = 6
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
armor_generic = {
\trole = armor
\tupgrade_prio = { base = 2 }
\tarmor_default = {
\t\tupgrade_prio = { base = 1 }
\t\ttarget_template = {
\t\t\tregiments = {
\t\t\t\tlight_armor = 4
\t\t\t\tmotorized = 4
\t\t\t}
\t\t}
\t\ttarget_min_match = 0.5
\t}
}
""")

    # ai_navy/goals/goals_generic.txt 自建
    ang_dst_dir = os.path.join(output_dir, "common", "ai_navy", "goals")
    os.makedirs(ang_dst_dir, exist_ok=True)
    with open(os.path.join(ang_dst_dir, "goals_generic.txt"), "w", encoding="utf-8") as f:
        f.write("""# Self-built generic naval goals — NO blocked_for TAG references
# (vanilla lists ENG/FRA/GER/ITA/JAP/SOV/USA which crash our TC MOD)
generic_naval_invasion_support = { objective_type = naval_invasion_support
\tmin_priority = 4  max_priority = 14 }
generic_mine_sweeping = { objective_type = mines_sweeping
\tmin_priority = 2  max_priority = 8 }
generic_invasion_defense = { objective_type = naval_invasion_defense
\tmin_priority = 15 max_priority = 25 }
generic_coast_defense = { objective_type = coast_defense
\tmin_priority = 1  max_priority = 16 }
generic_convoy_protection = { objective_type = convoy_protection
\tmin_priority = 1  max_priority = 5 }
generic_convoy_raiding = { objective_type = convoy_raiding
\tmin_priority = 3  max_priority = 7 }
generic_naval_dominance = { objective_type = naval_dominance
\tmin_priority = 1  max_priority = 13 }
generic_mine_laying = { objective_type = mines_planting
\tmin_priority = 2  max_priority = 8 }
generic_training = { objective_type = training
\tmin_priority = 10 max_priority = 20 }
generic_naval_blockade = { objective_type = naval_blockade
\tmin_priority = 10 max_priority = 20 }
generic_strike_force = { objective_type = strike_force_objective
\tmin_priority = 10 max_priority = 20 }
""")

    # ai_peace 无 generic 文件, 写占位
    apd = os.path.join(output_dir, "common", "ai_peace")
    os.makedirs(apd, exist_ok=True)
    if not os.listdir(apd):
        with open(os.path.join(apd, "00_placeholder.txt"), "w") as f:
            f.write("# Empty — vanilla has no generic ai_peace\n")

    # common/units/names* 必须 replace 掉 vanilla — 提供单一全局 fallback.
    # 2026-04-09 修: 之前的占位符缺 unique/ordered 块和 BOM, HOI4 解析崩.
    # 参考 vanilla generic_opertive_codenames.txt 等格式, 每个 entry 必须:
    #   - UTF-8 BOM
    #   - 完整结构 (name/type/fallback_name)
    #   - unique = { "name1" "name2" ... } 或 ordered 块
    _UNITS_FALLBACK_FILES = {
        "names_railway_guns": (
            "RG_COMMON_FALLBACK = {\n"
            '\tname = "Railway Gun"\n'
            "\tfor_countries = { }\n"
            "\tcan_use = { always = yes }\n"
            "\ttype = railway_gun\n"
            '\tfallback_name = "Railway Gun %d"\n'
            "\tunique = {\n"
            '\t\t"Big Gun" "Heavy Gun" "Long Gun" "Siege Gun"\n'
            "\t}\n"
            "}\n"
        ),
        "names_divisions": _build_division_names_with_phantoms(),
        "names_ships": (
            "GENERIC_SHIPS = {\n"
            '\tname = "Generic Ships"\n'
            "\tfor_countries = { }\n"
            "\ttype = ship\n"
            '\tprefix = ""\n'
            "\tunique = {\n"
            '\t\t"Hope" "Victory" "Glory" "Honor" "Liberty" "Dawn"\n'
            '\t\t"Valiant" "Courage" "Pride" "Endeavor" "Triumph" "Conquest"\n'
            "\t}\n"
            '\tfallback_name = "Ship %d"\n'
            "}\n"
        ),
        "codenames_operatives": (
            "GENERIC_OPERATIVES = {\n"
            '\tname = "Generic Operatives"\n'
            "\tfor_countries = { }\n"
            "\ttype = codename\n"
            '\tfallback_name = "Agent %d"\n'
            "\tunique = {\n"
            '\t\t"Wolf" "Sparrow" "Hawk" "Eagle" "Snake" "Bear"\n'
            '\t\t"Tiger" "Condor" "Magpie" "Shark" "Hornet" "Dragon"\n'
            "\t}\n"
            "}\n"
        ),
        "names": "# Empty — regiment-level unit names (optional)\n",
    }
    for sub, content in _UNITS_FALLBACK_FILES.items():
        d2 = os.path.join(output_dir, "common", "units", sub)
        os.makedirs(d2, exist_ok=True)
        if not os.listdir(d2):
            # UTF-8 with BOM (匹配 vanilla), HOI4 parser 对 BOM 敏感
            with open(os.path.join(d2, "00_generic_fallback.txt"), "wb") as f:
                f.write(b"\xef\xbb\xbf")  # UTF-8 BOM
                f.write(content.encode("utf-8"))
