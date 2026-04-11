"""
战略总览贴图颜色 feature.

控制 map/terrain/colormap_rgb_cityemissivemask_a.dds 的陆/海/湖颜色,
让架空 MOD 不再像地球. 通过菜单"工具 → 总览贴图颜色..." 打开对话框.
"""

from features.base import BaseFeature


class ColormapFeature(BaseFeature):
    id = "map.colormap"
    display_name = "总览贴图"
    category = "map"
    # 通过菜单触发, 不在 mode tab 暴露
