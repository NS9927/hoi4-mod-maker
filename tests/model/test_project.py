"""Project 单元测试。"""
import pytest
from model.events import EventBus
from model.project import Project
from domain.managers.state import StateManager
from domain.managers.country import CountryManager


@pytest.fixture(autouse=True)
def _restore_map_size():
    """测试后恢复全局 MAP_WIDTH / MAP_HEIGHT，避免污染其他测试。"""
    import data.constants as _c
    orig_w, orig_h = _c.MAP_WIDTH, _c.MAP_HEIGHT
    yield
    _c.MAP_WIDTH = orig_w
    _c.MAP_HEIGHT = orig_h


class TestProject:
    """Project 基本功能。"""

    def test_new_project_creates_fresh_managers(self) -> None:
        """new_project 后所有 manager 是新实例。"""
        proj = Project()
        old_state_mgr = proj.state_mgr
        old_country_mgr = proj.country_mgr
        proj.new_project(256, 128)
        assert proj.state_mgr is not old_state_mgr
        assert proj.country_mgr is not old_country_mgr
        assert not proj.is_dirty

    def test_mark_dirty_and_clean(self) -> None:
        """mark_dirty / mark_clean / is_dirty 状态切换。"""
        proj = Project()
        assert not proj.is_dirty
        proj.mark_dirty()
        assert proj.is_dirty
        proj.mark_clean()
        assert not proj.is_dirty

    def test_holds_all_managers(self) -> None:
        """Project 持有所有必要的 manager。"""
        proj = Project()
        assert isinstance(proj.state_mgr, StateManager)
        assert isinstance(proj.country_mgr, CountryManager)
        assert proj.map_data is not None
        assert proj.adjacency_mgr is not None
        assert proj.railway_mgr is not None
        assert proj.supply_mgr is not None
        assert proj.adjacency_rule_mgr is not None
        assert proj.strategic_region_mgr is not None
        assert proj.continent_mgr is not None
        assert proj.colormap_settings is not None
        assert proj.default_map_settings is not None

    def test_path_initially_none(self) -> None:
        """新建 Project 的 path 为 None。"""
        proj = Project()
        assert proj.path is None

    def test_save_without_path_raises(self) -> None:
        """没有路径时 save 抛异常。"""
        proj = Project()
        import pytest
        with pytest.raises(ValueError):
            proj.save()

    def test_event_bus_default(self) -> None:
        """不传 event_bus 时自动创建一个。"""
        proj = Project()
        assert proj.event_bus is not None

    def test_event_bus_injected(self) -> None:
        """可以注入 event_bus。"""
        bus = EventBus()
        proj = Project(event_bus=bus)
        assert proj.event_bus is bus

    def test_close_stops_autosave(self) -> None:
        """close 后 autosave timer 被清理。"""
        import threading
        proj = Project()
        # 创建一个不会真正触发的 timer
        timer = threading.Timer(9999, lambda: None)
        proj._autosave_timer = timer
        proj.close()
        assert proj._autosave_timer is None
