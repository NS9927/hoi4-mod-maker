"""Project — 项目数据中心，持有所有 manager 和地图数据。

一个 Project = 一个 .hoi4proj 文件的全部内容。
所有 controller 通过 Project 访问数据，不直接持有 manager 引用。
"""
from __future__ import annotations

import time
import threading

from model.events import EventBus
from domain.map_data import MapData
from domain.managers.state import StateManager
from domain.managers.country import CountryManager
from domain.managers.continent import ContinentManager
from domain.managers.adjacency import AdjacencyManager
from domain.managers.railway import RailwayManager
from domain.managers.supply_node import SupplyNodeManager
from domain.managers.adjacency_rule import AdjacencyRuleManager
from domain.managers.strategic_region import StrategicRegionManager
from domain.managers.colormap_settings import ColormapSettings
from domain.managers.default_map_settings import DefaultMapSettings


class Project:
    """项目数据中心。"""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus or EventBus()
        self.map_data = MapData()
        self.state_mgr = StateManager()
        self.country_mgr = CountryManager()
        self.continent_mgr = ContinentManager()
        self.adjacency_mgr = AdjacencyManager()
        self.railway_mgr = RailwayManager()
        self.supply_mgr = SupplyNodeManager()
        self.adjacency_rule_mgr = AdjacencyRuleManager()
        self.strategic_region_mgr = StrategicRegionManager()
        self.colormap_settings = ColormapSettings.default()
        self.default_map_settings = DefaultMapSettings()

        self._path: str | None = None  # current save path
        self._dirty = False  # unsaved changes
        self._autosave_interval = 300  # seconds (5 min)
        self._autosave_timer: threading.Timer | None = None
        self._last_save_time = 0.0

    @property
    def path(self) -> str | None:
        return self._path

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def mark_dirty(self) -> None:
        """标记有未保存的修改。"""
        self._dirty = True

    def mark_clean(self) -> None:
        self._dirty = False

    def new_project(self, width: int, height: int) -> None:
        """创建新项目。"""
        from data.constants import set_map_size

        set_map_size(width, height)
        self.map_data = MapData()
        self.state_mgr = StateManager()
        self.country_mgr = CountryManager()
        self.continent_mgr = ContinentManager()
        self.adjacency_mgr = AdjacencyManager()
        self.railway_mgr = RailwayManager()
        self.supply_mgr = SupplyNodeManager()
        self.adjacency_rule_mgr = AdjacencyRuleManager()
        self.strategic_region_mgr = StrategicRegionManager()
        self.colormap_settings = ColormapSettings.default()
        self.default_map_settings = DefaultMapSettings()
        self._path = None
        self._dirty = False

    def save(self, path: str | None = None) -> None:
        """保存项目到文件。"""
        save_path = path or self._path
        if not save_path:
            raise ValueError("没有指定保存路径")
        from domain.project_io import save_project

        save_project(
            save_path,
            tile_map=self.map_data.tile_map,
            province_map=self.map_data.province_map,
            terrain_map=self.map_data.terrain_map,
            height_map=self.map_data.height_map,
            state_mgr=self.state_mgr,
            country_mgr=self.country_mgr,
            river_map=self.map_data.river_map,
            continent_mgr=self.continent_mgr,
            adjacency_mgr=self.adjacency_mgr,
            railway_mgr=self.railway_mgr,
            supply_mgr=self.supply_mgr,
            adjacency_rule_mgr=self.adjacency_rule_mgr,
            strategic_region_mgr=self.strategic_region_mgr,
            provincial_terrain=self.map_data.provincial_terrain,
        )
        self._path = save_path
        self._dirty = False
        self._last_save_time = time.time()

    def load(self, path: str) -> None:
        """加载项目文件。"""
        from domain.project_io import load_project

        result = load_project(
            path,
            state_mgr=self.state_mgr,
            country_mgr=self.country_mgr,
            continent_mgr=self.continent_mgr,
            adjacency_mgr=self.adjacency_mgr,
            railway_mgr=self.railway_mgr,
            supply_mgr=self.supply_mgr,
            adjacency_rule_mgr=self.adjacency_rule_mgr,
            strategic_region_mgr=self.strategic_region_mgr,
        )
        # load_project returns (tile_map, province_map, terrain_map, height_map, river_map, provincial_terrain)
        tile_map, province_map, terrain_map, height_map, river_map, provincial_terrain = result

        # Update map size from loaded data
        from data.constants import set_map_size

        h, w = tile_map.shape
        set_map_size(w, h)

        self.map_data = MapData()
        self.map_data.replace_all(
            tile_map=tile_map,
            province_map=province_map,
            terrain_map=terrain_map,
            height_map=height_map,
        )
        if river_map is not None:
            self.map_data.river_map[:] = river_map
        self.map_data.provincial_terrain = provincial_terrain or {}

        self._path = path
        self._dirty = False

    def start_autosave(self) -> None:
        """启动自动保存定时器。"""
        self._stop_autosave()
        if self._path and self._autosave_interval > 0:
            self._autosave_timer = threading.Timer(
                self._autosave_interval, self._do_autosave
            )
            self._autosave_timer.daemon = True
            self._autosave_timer.start()

    def _stop_autosave(self) -> None:
        if self._autosave_timer:
            self._autosave_timer.cancel()
            self._autosave_timer = None

    def _do_autosave(self) -> None:
        """自动保存回调。"""
        if self._dirty and self._path:
            try:
                # Save to autosave path (not overwrite main file)
                autosave_path = self._path + ".autosave"
                self.save(autosave_path)
                self._path = self._path.replace(".autosave", "")  # restore original path
                self.event_bus.emit("status_message", text="自动保存完成")
            except Exception:
                pass  # autosave failure is silent
        # Reschedule
        self.start_autosave()

    def close(self) -> None:
        """关闭项目，清理资源。"""
        self._stop_autosave()
