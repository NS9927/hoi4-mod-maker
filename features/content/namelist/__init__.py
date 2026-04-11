"""
名字表编辑器 (2.0 功能, 空壳).

未来用来编辑 common/names/*.txt 和单位命名.
读 1.0 的 map 数据 (state_mgr / country_mgr 等), 实现时按 Feature 协议扩展.
"""

from features.base import BaseFeature


class NamelistFeature(BaseFeature):
    id = "content.namelist"
    display_name = "名字表"
    category = "content"
    # 空壳: 暂无实现, 仅让 FeatureRegistry 列出可用 2.0 功能
