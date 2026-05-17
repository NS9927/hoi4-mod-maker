"""
map/ambient_object.txt 写入器.

vanilla 用 frame_border_entity_top/bottom 3D 模型挡住地图上下边界空白。
位置根据地图高度计算。

参考: Map modding.txt §Ambient objects (行 557-606)
"""

from __future__ import annotations

import os

# 注意: 用 import as 而非 from import — set_map_size 改的是模块属性,
# from import 复制了值, 后续不会跟着更新.
import data.constants as _const


def write_ambient_object_txt(output_dir: str) -> None:
    """生成 map/ambient_object.txt — 地图边框 + 风效果."""
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)

    # vanilla: top z ≈ MAP_HEIGHT + 142, bottom z = -140
    map_h = _const.MAP_HEIGHT
    top_z = map_h + 142
    bottom_z = -140
    logo_z = map_h + 82

    path = os.path.join(d, "ambient_object.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"""type={{
\ttype="frame_border_entity"
\tuse_animation=no
\tscale=100.000000
\talways_visible=yes
\tobject={{
\t\tname="frame_border_entity_top"
\t\tposition={{
\t\t\t0 0 {top_z}
\t\t}}
\t\trotation={{
\t\t\t0 0 0
\t\t}}
\t}}
}}
type={{
\ttype="frame_border_bottom_entity"
\tuse_animation=no
\tscale=100.000000
\talways_visible=yes
\tobject={{
\t\tname="frame_border_bottom_entity_bottom"
\t\tposition={{
\t\t\t0 0 {bottom_z}
\t\t}}
\t\trotation={{
\t\t\t0 0 0
\t\t}}
\t}}
}}
type={{
\ttype="frame_border_logo_entity"
\tuse_animation=no
\tscale=300.000000
\talways_visible=yes
\tobject={{
\t\tname="frame_border_logo_entity_top"
\t\tposition={{
\t\t\t3000 -1 {logo_z}
\t\t}}
\t\trotation={{
\t\t\t0 0 0
\t\t}}
\t}}
}}
""")
