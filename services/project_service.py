"""
项目 IO 服务 — 保存/加载 .hoi4proj 的业务逻辑.

UI 层 (MainWindow) 只负责弹文件对话框 + 显示错误,
实际的 save_project/load_project 调用 + 数据同步都在这里.
"""

from __future__ import annotations


def save_project(
    path: str,
    canvas,
    state_mgr,
    country_mgr,
    continent_mgr,
    adjacency_mgr=None,
    railway_mgr=None,
    supply_mgr=None,
    adjacency_rule_mgr=None,
    strategic_region_mgr=None,
) -> None:
    """保存项目到 .hoi4proj. 失败抛异常, UI 层捕获显示."""
    from domain.project_io import save_project as _save
    _save(
        path,
        canvas.tile_map,
        canvas.province_map,
        canvas.terrain_map,
        canvas.height_map,
        state_mgr,
        country_mgr,
        canvas.river_map,
        continent_mgr=continent_mgr,
        adjacency_mgr=adjacency_mgr,
        railway_mgr=railway_mgr,
        supply_mgr=supply_mgr,
        adjacency_rule_mgr=adjacency_rule_mgr,
        strategic_region_mgr=strategic_region_mgr,
        provincial_terrain=canvas.map_data.provincial_terrain,
        tile_snapshot=canvas.map_data.tile_snapshot,
    )


def load_project(
    path: str,
    canvas,
    state_mgr,
    country_mgr,
    continent_mgr,
    adjacency_mgr=None,
    railway_mgr=None,
    supply_mgr=None,
    adjacency_rule_mgr=None,
    strategic_region_mgr=None,
) -> None:
    """从 .hoi4proj 加载, 原地更新 canvas 和 manager. 失败抛异常."""
    from domain.project_io import load_project as _load
    tm, pm, terrain, hm, rm, pt, tile_snapshot = _load(
        path, state_mgr, country_mgr,
        continent_mgr=continent_mgr,
        adjacency_mgr=adjacency_mgr,
        railway_mgr=railway_mgr,
        supply_mgr=supply_mgr,
        adjacency_rule_mgr=adjacency_rule_mgr,
        strategic_region_mgr=strategic_region_mgr,
    )
    canvas.tile_map = tm
    canvas.province_map = pm
    canvas.terrain_map = terrain
    canvas.height_map = hm
    if rm is not None:
        canvas.river_map = rm
    # 省份级地形 (Feature A)
    canvas.map_data.provincial_terrain = pt if pt else {}
    # tile_snapshot（省份生成时的 tile_map 快照）
    # 旧项目没有快照 → 用当前 tile_map 作为快照（假设保存时 tile_map 未被修改过）
    canvas.map_data.tile_snapshot = tile_snapshot if tile_snapshot is not None else tm.copy()


def create_mod_skeleton(output_dir: str) -> None:
    """在项目导出目录创建 HOI4 MOD 基本空目录结构。"""
    import os
    dirs = [
        "common/countries",
        "common/country_tags",
        "common/national_focus",
        "common/ideas",
        "common/technologies",
        "common/units",
        "history/countries",
        "history/states",
        "history/units",
        "map/strategicregions",
        "gfx/flags",
        "gfx/leaders",
        "localisation",
        "events",
    ]
    for d in dirs:
        os.makedirs(os.path.join(output_dir, d), exist_ok=True)
