"""
Colormap DDS 颜色设置.

控制 map/terrain/colormap_rgb_cityemissivemask_a.dds 的陆/海/湖三色.
HOI4 缩到战略视角时显示这张总览贴图. 用户可自定义颜色让架空世界
看起来不像地球.

存的是 RGB (用户友好), 写 DDS 时再转 BGRA.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ColormapColor:
    """RGB 0-255 三个分量."""
    r: int
    g: int
    b: int

    def to_bgra(self) -> tuple[int, int, int, int]:
        """转 DDS 用的 (B, G, R, A)."""
        return (self.b, self.g, self.r, 0)


@dataclass
class ColormapSettings:
    """战略总览贴图的三色配置."""
    land: ColormapColor
    sea: ColormapColor
    lake: ColormapColor

    @classmethod
    def default(cls) -> "ColormapSettings":
        # 暖土褐 / 深靛蓝 / 浅蓝灰 (与原 colormap_dds.py 硬编码值一致)
        return cls(
            land=ColormapColor(95, 90, 60),
            sea=ColormapColor(30, 55, 90),
            lake=ColormapColor(70, 110, 140),
        )

    def to_dict(self) -> dict:
        return {
            "land": {"r": self.land.r, "g": self.land.g, "b": self.land.b},
            "sea":  {"r": self.sea.r,  "g": self.sea.g,  "b": self.sea.b},
            "lake": {"r": self.lake.r, "g": self.lake.g, "b": self.lake.b},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ColormapSettings":
        def _c(d):
            return ColormapColor(int(d["r"]), int(d["g"]), int(d["b"]))
        return cls(
            land=_c(data.get("land", {"r": 95, "g": 90, "b": 60})),
            sea=_c(data.get("sea", {"r": 30, "g": 55, "b": 90})),
            lake=_c(data.get("lake", {"r": 70, "g": 110, "b": 140})),
        )
