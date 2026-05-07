"""localisation/*.yml 本地化.

规则（HOI4 标准）:
- state/strategic_region/city 的内部文件永远只写 **key**（如 STATE_123）
- 显示名走 yml，按语言分 english / simp_chinese 两份
- 用户输入的 `name` = 主显示名（任何语言）
- 用户输入的 `name_en` = 可选英文名（空则用默认 "State {id}"）
"""
import os


def _state_name_en(s, sid: int) -> str:
    """返回 state 英文 yml 显示名。
    优先 name_en; 没设就用 name (允许中文 — yml 是 utf-8 BOM, 比 "State X" fallback 强);
    都没设才默认.
    """
    name_en = (getattr(s, "name_en", "") or "").strip()
    if name_en:
        return name_en
    name = (getattr(s, "name", "") or "").strip()
    if name and name != f"STATE_{sid}":
        return name
    return f"State {sid}"


def _state_name_local(s, sid: int) -> str:
    """返回 state 主语言 yml 显示名（优先用户输入的 name）"""
    name = (getattr(s, "name", "") or "").strip()
    # 排除 key 形式（旧数据或默认 fallback）
    if name and name != f"STATE_{sid}":
        return name
    return _state_name_en(s, sid)


def _region_name_en(r, rid: int) -> str:
    name_en = (getattr(r, "name_en", "") or "").strip()
    if name_en:
        return name_en
    name = (getattr(r, "name", "") or "").strip()
    if name and name != f"STRATEGICREGION_{rid}":
        return name  # 中文也用 (yml 是 UTF-8 BOM, HOI4 能正确显示)
    return f"Region {rid}"


def _region_name_local(r, rid: int) -> str:
    name = (getattr(r, "name", "") or "").strip()
    if name and name != f"STRATEGICREGION_{rid}":
        return name
    return _region_name_en(r, rid)


def _city_name_en(s, pid: int, fallback_en: str, vp_idx: int) -> str:
    """VP 城市英文名。
    优先 vp_names_en；若空则回退 vp_names（如果是 ASCII）；再回退到 state 英文名。
    """
    custom_en = (getattr(s, "vp_names_en", {}) or {}).get(pid, "").strip()
    if custom_en:
        return custom_en
    custom = (s.vp_names or {}).get(pid, "").strip()
    if custom:
        return custom  # 中文 VP 名也用
    base = _state_name_en(s, s.id)
    if vp_idx == 0:
        return base
    return f"{base} City {vp_idx + 1}"


def _city_name_local(s, pid: int, vp_idx: int) -> str:
    """VP 城市本地显示名（优先用户输入）"""
    custom = (s.vp_names or {}).get(pid, "").strip()
    if custom:
        return custom
    base = _state_name_local(s, s.id)
    if vp_idx == 0:
        return base
    return f"{base} City {vp_idx + 1}"


def _escape_yml(text: str) -> str:
    """yml 字符串里的 `"` 会截断，替换成单引号。也剔除换行。"""
    return text.replace('"', "'").replace("\n", " ").replace("\r", "")


def write_localisation_simple(mod_name, tag, states, output_dir, region_count=24):
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")
    with open(os.path.join(d, f"{safe}_l_english.yml"), "w", encoding="utf-8-sig") as f:
        f.write("l_english:\n")
        for sid in states:
            # BUG-6: 用 WT_ 前缀避开 vanilla key
            f.write(f' STATE_WT_{sid}:0 "State {sid}"\n')
        for rid in range(1, region_count + 1):
            f.write(f' STRATEGICREGION_WT_{rid}:0 "Region {rid}"\n')
        f.write(f' SUPPLYAREA_WT_1:0 "Fantasy Supply"\n')
        f.write(f' FANTASY_BOOKMARK:0 "Fantasy World"\n')
        f.write(f' FANTASY_BOOKMARK_DESC:0 "A fantasy world awaits."\n')
        f.write(f' {tag}:0 "Fantasy Country"\n')
        f.write(f' {tag}_DEF:0 "Fantasy Country"\n')
        f.write(f' {tag}_ADJ:0 "Fantasy"\n')
        f.write(f' {tag}_BOOKMARK_DESC:0 "Play as Fantasy Country"\n')
        f.write(f' OTHER_BOOKMARK_DESC:0 "Other nations"\n')


def _open_yml(dir_path: str, safe: str, topic: str, lang: str):
    """打开一个按主题分的 yml 文件，已写好 `l_<lang>:` 头。调用方负责 close。

    文件名前缀 `zz_` 确保按字母序排在 vanilla 的 yml (state_names_l_*.yml 等) **之后**,
    HOI4 同 key 后加载覆盖前加载 → 我们 MOD 的 STATE_X 翻译能稳定盖过 vanilla.
    """
    path = os.path.join(dir_path, f"zz_{safe}_{topic}_l_{lang}.yml")
    f = open(path, "w", encoding="utf-8-sig")
    f.write(f"l_{lang}:\n")
    return f


def write_localisation_full(mod_name, state_mgr, country_mgr, states, output_dir,
                             region_count=24, region_mgr=None):
    """完整本地化。按主题拆成多个 yml（对齐 vanilla HOI4 风格），方便查找和编辑：

      <mod>_states_l_<lang>.yml             STATE_* / VICTORY_POINTS_*
      <mod>_strategic_regions_l_<lang>.yml  STRATEGICREGION_* / SUPPLYAREA_*
      <mod>_countries_l_<lang>.yml          {TAG} / {TAG}_DEF / {TAG}_ADJ / {TAG}_BOOKMARK_DESC
      <mod>_leaders_l_<lang>.yml            {TAG}_leader_* / field_marshal / general / admiral
      <mod>_ideas_l_<lang>.yml              national_spirit id / id_desc
      <mod>_bookmarks_l_<lang>.yml          bookmark / bookmark_desc / other_bookmark_desc

    英/中两份各一套，引擎会自动合并，效果和单文件等价。
    """
    d = os.path.join(output_dir, "localisation")
    os.makedirs(d, exist_ok=True)
    safe = mod_name.replace(" ", "_")

    def _write_yml(lang: str):
        """lang: 'english' or 'simp_chinese'"""
        is_en = (lang == "english")

        # ── states + VP 城市 ──
        # BUG-6: 用 WT_ 前缀避开 vanilla 命名空间 (STATE_142 撞 vanilla "Krakow" 等)
        with _open_yml(d, safe, "states", lang) as f:
            if state_mgr and state_mgr.states:
                for sid, s in state_mgr.states.items():
                    name = _state_name_en(s, sid) if is_en else _state_name_local(s, sid)
                    f.write(f' STATE_WT_{sid}:0 "{_escape_yml(name)}"\n')
                    for vp_idx, vpid in enumerate(s.victory_points.keys()):
                        if is_en:
                            city = _city_name_en(s, vpid, _state_name_en(s, sid), vp_idx)
                        else:
                            city = _city_name_local(s, vpid, vp_idx)
                        f.write(f' VICTORY_POINTS_{vpid}:0 "{_escape_yml(city)}"\n')
            else:
                for sid in states:
                    default = f"State {sid}" if is_en else f"状态 {sid}"
                    f.write(f' STATE_WT_{sid}:0 "{default}"\n')

        # ── strategic regions + supply area ──
        with _open_yml(d, safe, "strategic_regions", lang) as f:
            if region_mgr is not None and region_mgr.regions:
                for rid, r in sorted(region_mgr.regions.items()):
                    name = _region_name_en(r, rid) if is_en else _region_name_local(r, rid)
                    f.write(f' STRATEGICREGION_WT_{rid}:0 "{_escape_yml(name)}"\n')
            else:
                for rid in range(1, region_count + 1):
                    default = f"Region {rid}" if is_en else f"战区 {rid}"
                    f.write(f' STRATEGICREGION_WT_{rid}:0 "{default}"\n')
            supply_name = f"{mod_name} Supply" if is_en else f"{mod_name} 补给"
            f.write(f' SUPPLYAREA_WT_1:0 "{_escape_yml(supply_name)}"\n')

        # ── countries + leaders + ideas ──
        f_countries = _open_yml(d, safe, "countries", lang)
        f_leaders = _open_yml(d, safe, "leaders", lang)
        f_ideas = _open_yml(d, safe, "ideas", lang)
        try:
            if country_mgr and country_mgr.countries:
                for tag, c in country_mgr.countries.items():
                    cname = _escape_yml(c.name or tag)
                    f_countries.write(f' {tag}:0 "{cname}"\n')
                    f_countries.write(f' {tag}_DEF:0 "{cname}"\n')
                    f_countries.write(f' {tag}_ADJ:0 "{cname}"\n')
                    play_as = f"Play as {cname}" if is_en else f"扮演 {cname}"
                    f_countries.write(f' {tag}_BOOKMARK_DESC:0 "{play_as}"\n')

                    leader = f"{cname} Leader" if is_en else f"{cname} 领袖"
                    for ideology in ("despotism", "conservatism", "nazism", "marxism"):
                        f_leaders.write(f' {tag}_leader_{ideology}:0 "{leader}"\n')
                    marshal = f"{cname} Marshal" if is_en else f"{cname} 元帅"
                    general = f"{cname} General" if is_en else f"{cname} 将军"
                    admiral = f"{cname} Admiral" if is_en else f"{cname} 海军上将"
                    f_leaders.write(f' {tag}_field_marshal_1:0 "{marshal}"\n')
                    f_leaders.write(f' {tag}_general_1:0 "{general}"\n')
                    f_leaders.write(f' {tag}_admiral_1:0 "{admiral}"\n')
                    sci_label = "Scientist" if is_en else "科学家"
                    for i in range(1, 5):
                        f_leaders.write(f' {tag}_scientist_{i}:0 "{cname} {sci_label} {i}"\n')

                    for spirit in c.national_spirits:
                        nm = _escape_yml(spirit.name)
                        ds = _escape_yml(spirit.desc or spirit.name)
                        f_ideas.write(f' {spirit.id}:0 "{nm}"\n')
                        f_ideas.write(f' {spirit.id}_desc:0 "{ds}"\n')
            else:
                tag = "AAA"
                cname = "Fantasy Country" if is_en else "奇幻国度"
                f_countries.write(f' {tag}:0 "{cname}"\n')
                f_countries.write(f' {tag}_DEF:0 "{cname}"\n')
                f_countries.write(f' {tag}_ADJ:0 "{cname}"\n')
                f_countries.write(f' {tag}_BOOKMARK_DESC:0 "Play as {cname}"\n')
                for ideology in ("despotism", "conservatism", "nazism", "marxism"):
                    f_leaders.write(f' {tag}_leader_{ideology}:0 "{cname} Leader"\n')
                f_leaders.write(f' {tag}_field_marshal_1:0 "{cname} Marshal"\n')
                f_leaders.write(f' {tag}_general_1:0 "{cname} General"\n')
                f_leaders.write(f' {tag}_admiral_1:0 "{cname} Admiral"\n')
                for i in range(1, 5):
                    f_leaders.write(f' {tag}_scientist_{i}:0 "{cname} Scientist {i}"\n')
        finally:
            f_countries.close()
            f_leaders.close()
            f_ideas.close()

        # ── bookmarks ──
        with _open_yml(d, safe, "bookmarks", lang) as f:
            bm_safe = mod_name.replace(" ", "_").upper()
            f.write(f' {bm_safe}_BOOKMARK:0 "{_escape_yml(mod_name)}"\n')
            desc = f"A world of {mod_name} awaits." if is_en else f"{mod_name} 的世界正等待着你。"
            f.write(f' {bm_safe}_BOOKMARK_DESC:0 "{_escape_yml(desc)}"\n')
            other = "Other nations" if is_en else "其他国家"
            f.write(f' {bm_safe}_OTHER_BOOKMARK_DESC:0 "{other}"\n')
            if bm_safe != "FANTASY":
                f.write(f' FANTASY_BOOKMARK:0 "{_escape_yml(mod_name)}"\n')
                f.write(f' FANTASY_BOOKMARK_DESC:0 "{_escape_yml(desc)}"\n')
                f.write(f' OTHER_BOOKMARK_DESC:0 "{other}"\n')

    _write_yml("english")
    _write_yml("simp_chinese")
