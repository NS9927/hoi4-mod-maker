"""DefaultMapController — default.map 配置控制器。

处理河流等级和树木调色板索引配置。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controllers.base import BaseController

if TYPE_CHECKING:
    from model.project import Project
    from commands.history import CommandHistory


class DefaultMapController(BaseController):
    """default.map 配置编辑。"""

    def __init__(self, project: "Project", command_history: "CommandHistory") -> None:
        super().__init__(project, command_history)

    def set_river_level(self, level: int) -> None:
        """设置河流最大等级。"""
        self.project.default_map_settings.river_max_level = level
        self.project.mark_dirty()

    def add_tree_index(self, index: int) -> bool:
        """添加树木调色板索引。返回是否成功。"""
        settings = self.project.default_map_settings
        if index in settings.tree_palette_indices:
            return False
        settings.tree_palette_indices.append(index)
        settings.tree_palette_indices.sort()
        self.project.mark_dirty()
        return True

    def remove_tree_index(self, position: int) -> bool:
        """按位置删除树木调色板索引。"""
        settings = self.project.default_map_settings
        if 0 <= position < len(settings.tree_palette_indices):
            settings.tree_palette_indices.pop(position)
            self.project.mark_dirty()
            return True
        return False

    def reset_tree_indices(self) -> None:
        """重置树木调色板索引为默认值。"""
        self.project.default_map_settings.tree_palette_indices = [3, 4, 7, 10]
        self.project.mark_dirty()
