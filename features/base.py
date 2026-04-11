"""
Feature 基类 — 一个功能模块的统一接口.

每个 feature (map/land, map/state, content/tech_tree 等) 实现这个接口,
在 app/container.py 注册. 加新功能 = 建新 feature 目录 + 注册一行, 其他地方零改动.

接口约定:
- id: 全局唯一标识, 例 'map.land' 'content.tech_tree'
- display_name: 用户可见名
- category: 'map' 或 'content', 对应顶部模式切换
- build_page(parent) -> QWidget | None: 侧边栏 tab 内容, 返回 None 表示该功能不在侧边栏暴露
- build_renderer() -> object | None: canvas 渲染器, 返回 None 表示复用上一个 feature
- build_tools() -> list[Tool]: 该功能用的 canvas 工具
- register_menu(menu_bar): 可选, 在菜单栏注册动作
- on_activate(ctx) / on_deactivate(ctx): 切换到/离开该 feature 时的钩子
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class FeatureContext:
    """Feature 能访问的所有应用级对象. 由 container 注入."""
    # 数据管理器 (domain 层)
    map_data: object = None
    state_mgr: object = None
    country_mgr: object = None
    continent_mgr: object = None
    river_mgr: object = None
    undo_mgr: object = None
    # UI 根对象 (供 feature 需要时弹对话框/取状态栏)
    main_window: object = None
    canvas: object = None
    # 未来可加: strategic_region_mgr, railway_mgr, command_bus 等
    extras: dict = field(default_factory=dict)


class Feature(Protocol):
    """Feature 协议 — 每个功能模块必须实现."""

    id: str
    display_name: str
    category: str  # 'map' | 'content'

    def build_page(self, ctx: FeatureContext):
        """返回侧边栏 QWidget, 或 None 表示无 UI 面板."""
        ...

    def build_renderer(self, ctx: FeatureContext):
        """返回 canvas Renderer, 或 None 表示复用默认."""
        ...

    def build_tools(self, ctx: FeatureContext) -> list:
        """返回该功能用的画布 Tool 列表."""
        ...

    def on_activate(self, ctx: FeatureContext) -> None:
        """切换到该 feature 时调用 (刷新 UI, 连信号等)."""
        ...

    def on_deactivate(self, ctx: FeatureContext) -> None:
        """离开该 feature 时调用 (清理临时状态)."""
        ...


class BaseFeature:
    """Feature 的默认空实现, 子类按需 override."""

    id: str = ""
    display_name: str = ""
    category: str = "map"

    def build_page(self, ctx: FeatureContext):
        return None

    def build_renderer(self, ctx: FeatureContext):
        return None

    def build_tools(self, ctx: FeatureContext) -> list:
        return []

    def on_activate(self, ctx: FeatureContext) -> None:
        pass

    def on_deactivate(self, ctx: FeatureContext) -> None:
        pass
