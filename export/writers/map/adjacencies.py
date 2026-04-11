"""
map/adjacencies.csv 写入器.

参考 参考/Map modding.txt 行 485-502:
- 10 字段, 分号分隔
- 末尾哨兵: -1;-1;-1;-1;-1;-1;-1;-1;-1 (行 502, 必需, 没有会 hangup)
- UTF-8 无 BOM (行 505 adjacency_rules 提到这个要求, adjacencies.csv 同理)
- LF 换行
"""

from __future__ import annotations

import os


def write_adjacencies_csv(output_dir: str, adjacency_mgr=None) -> None:
    """生成 map/adjacencies.csv.

    adjacency_mgr: AdjacencyManager 实例, 可为 None (写只含 header + 哨兵).
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "adjacencies.csv")

    lines: list[str] = []
    lines.append(
        "From;To;Type;Through;start_x;start_y;stop_x;stop_y;"
        "adjacency_rule_name;Comment"
    )

    if adjacency_mgr is not None:
        for entry in adjacency_mgr.get_all():
            lines.append(entry.to_csv_line())

    # 哨兵 (必须)
    lines.append("-1;-1;-1;-1;-1;-1;-1;-1;-1")

    # 用 binary 模式写, LF 换行, UTF-8 无 BOM
    content = "\n".join(lines) + "\n"
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
