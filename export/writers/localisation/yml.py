"""localisation/*.yml 本地化."""
import os


def write_localisation_simple(mod_name, tag, states, output_dir, region_count=24):
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")
    with open(os.path.join(d, f"{safe}_l_english.yml"), "w", encoding="utf-8-sig") as f:
        f.write("l_english:\n")
        for sid in states:
            f.write(f' STATE_{sid}:0 "State {sid}"\n')
        for rid in range(1, region_count + 1):
            f.write(f' STRATEGICREGION_{rid}:0 "Region {rid}"\n')
        f.write(f' SUPPLYAREA_1:0 "Fantasy Supply"\n')
        f.write(f' FANTASY_BOOKMARK:0 "Fantasy World"\n')
        f.write(f' FANTASY_BOOKMARK_DESC:0 "A fantasy world awaits."\n')
        f.write(f' {tag}:0 "Fantasy Country"\n')
        f.write(f' {tag}_DEF:0 "Fantasy Country"\n')
        f.write(f' {tag}_ADJ:0 "Fantasy"\n')
        f.write(f' {tag}_BOOKMARK_DESC:0 "Play as Fantasy Country"\n')
        f.write(f' OTHER_BOOKMARK_DESC:0 "Other nations"\n')


def write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir,
                             region_count=24):
    """完整本地化。同时生成英文和简体中文版本（HOI4 按语言加载对应yml）。"""
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")

    def _write_yml(lang):
        """lang: 'english' or 'simp_chinese'"""
        with open(os.path.join(d, f"{safe}_l_{lang}.yml"), "w", encoding="utf-8-sig") as f:
            f.write(f"l_{lang}:\n")
            # State 名称 + VP（城市）名称
            if state_mgr and state_mgr.states:
                for sid, s in state_mgr.states.items():
                    f.write(f' STATE_{sid}:0 "{s.name}"\n')
                    # 每个 VP 省份生成独立城市名
                    for vp_idx, vpid in enumerate(s.victory_points.keys()):
                        # 优先用用户自定义的城市名
                        custom_name = s.vp_names.get(vpid, "").strip()
                        if custom_name:
                            city_name = custom_name
                        elif vp_idx == 0:
                            city_name = s.name
                        else:
                            city_name = f"{s.name} City {vp_idx + 1}"
                        f.write(f' VICTORY_POINTS_{vpid}:0 "{city_name}"\n')
            else:
                for sid in states:
                    f.write(f' STATE_{sid}:0 "State {sid}"\n')
            # 国家名称（完整：TAG、TAG_DEF、TAG_ADJ、TAG_leader_despotism等）
            if country_mgr and country_mgr.countries:
                for tag, c in country_mgr.countries.items():
                    f.write(f' {tag}:0 "{c.name}"\n')
                    f.write(f' {tag}_DEF:0 "{c.name}"\n')
                    f.write(f' {tag}_ADJ:0 "{c.name}"\n')
                    f.write(f' {tag}_BOOKMARK_DESC:0 "Play as {c.name}"\n')
                    f.write(f' {tag}_leader_despotism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_leader_conservatism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_leader_nazism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_leader_marxism:0 "{c.name} Leader"\n')
                    f.write(f' {tag}_field_marshal_1:0 "{c.name} Marshal"\n')
                    f.write(f' {tag}_general_1:0 "{c.name} General"\n')
                    f.write(f' {tag}_admiral_1:0 "{c.name} Admiral"\n')
                    # 民族精神本地化
                    for spirit in c.national_spirits:
                        nm = spirit.name.replace('"', "'")
                        ds = (spirit.desc or spirit.name).replace('"', "'")
                        f.write(f' {spirit.id}:0 "{nm}"\n')
                        f.write(f' {spirit.id}_desc:0 "{ds}"\n')
            else:
                # 默认国家（无 country_mgr）
                tag = "AAA"
                f.write(f' {tag}:0 "Fantasy Country"\n')
                f.write(f' {tag}_DEF:0 "Fantasy Country"\n')
                f.write(f' {tag}_ADJ:0 "Fantasy"\n')
                f.write(f' {tag}_BOOKMARK_DESC:0 "Play as Fantasy Country"\n')
                f.write(f' {tag}_leader_despotism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_leader_conservatism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_leader_nazism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_leader_marxism:0 "Fantasy Leader"\n')
                f.write(f' {tag}_field_marshal_1:0 "Fantasy Marshal"\n')
                f.write(f' {tag}_general_1:0 "Fantasy General"\n')
                f.write(f' {tag}_admiral_1:0 "Fantasy Admiral"\n')
            for rid in range(1, region_count + 1):
                f.write(f' STRATEGICREGION_{rid}:0 "Region {rid}"\n')
            f.write(f' SUPPLYAREA_1:0 "{mod_name} Supply"\n')
            # bookmark 本地化 — 用 mod_name 的 UPPER 形式作 key
            bm_safe = mod_name.replace(" ", "_").upper()
            f.write(f' {bm_safe}_BOOKMARK:0 "{mod_name}"\n')
            f.write(f' {bm_safe}_BOOKMARK_DESC:0 "A world of {mod_name} awaits."\n')
            f.write(f' {bm_safe}_OTHER_BOOKMARK_DESC:0 "Other nations"\n')
            # 兼容旧 key (FANTASY_BOOKMARK)
            if bm_safe != "FANTASY":
                f.write(f' FANTASY_BOOKMARK:0 "{mod_name}"\n')
                f.write(f' FANTASY_BOOKMARK_DESC:0 "A world of {mod_name} awaits."\n')
                f.write(f' OTHER_BOOKMARK_DESC:0 "Other nations"\n')

    # 同时生成英文和简中两个版本
    _write_yml("english")
    _write_yml("simp_chinese")

