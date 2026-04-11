"""
default.map 配置.

HOI4 用 map/default.map 告诉引擎从哪里找各种地图文件 + 树木调色板等配置.
参考 参考/Map modding.txt §Default.map (行 56-83).

我们的工具自动生成 BMP/CSV 用 vanilla 标准文件名, 不改路径.
但用户可以自定义:
- tree_palette_indices: 哪些 trees.bmp 调色板索引算"树"
- river_max_level: 河流最大宽度等级 (默认 5)
- max_provinces 自动 = 实际省份数 + 1 (HOI4 必需)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DefaultMapSettings:
    """default.map 配置."""

    # 树木调色板索引: trees.bmp 这些索引会被算作树木 (默认 vanilla 值)
    # 参考 Map modding.txt §Trees: 0=无树, 1-13 是不同密度/类型
    tree_palette_indices: list[int] = field(default_factory=lambda: [3, 4, 7, 10])

    # 河流最大宽度 (1-5, vanilla 默认 5)
    river_max_level: int = 5

    # 这些字段不可编辑, 写死 vanilla 文件名 (改了 HOI4 找不到)
    # 但暴露在 settings 里方便未来扩展
    definitions: str = "definition.csv"
    provinces: str = "provinces.bmp"
    positions: str = "positions.txt"
    terrain: str = "terrain.bmp"
    rivers: str = "rivers.bmp"
    heightmap: str = "heightmap.bmp"
    tree_definition: str = "trees.bmp"
    continent: str = "continent.txt"
    adjacency_rules: str = "adjacency_rules.txt"
    adjacencies: str = "adjacencies.csv"
    ambient_object: str = "ambient_object.txt"
    seasons: str = "seasons.txt"

    @classmethod
    def default(cls) -> "DefaultMapSettings":
        return cls()

    def to_dict(self) -> dict:
        return {
            "tree_palette_indices": list(self.tree_palette_indices),
            "river_max_level": int(self.river_max_level),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DefaultMapSettings":
        return cls(
            tree_palette_indices=list(data.get("tree_palette_indices", [3, 4, 7, 10])),
            river_max_level=int(data.get("river_max_level", 5)),
        )
