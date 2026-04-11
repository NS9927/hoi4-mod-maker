"""
map/supply_nodes.txt 写入器.

参考: 参考/Map modding.txt 行 528-532
格式: Level ProvinceID (每行一条, 空格分隔)
- 不能空, 空文件崩 (CLAUDE.md)
- UTF-8 无 BOM, LF 换行
"""

from __future__ import annotations

import os


def write_supply_nodes_txt(
    output_dir: str,
    supply_mgr=None,
    fallback_pid: int = 1,
) -> None:
    """生成 map/supply_nodes.txt.

    supply_mgr: SupplyNodeManager 实例. None 或空时写 placeholder.
    fallback_pid: 空时用的兜底省份 ID.
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "supply_nodes.txt")

    lines: list[str] = []
    if supply_mgr is not None:
        for node in supply_mgr.get_all():
            lines.append(node.to_line())

    if not lines:
        lines.append(f"1 {fallback_pid}")

    content = "\n".join(lines) + "\n"
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
