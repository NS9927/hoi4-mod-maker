"""
map/railways.txt 写入器.

参考: 参考/Map modding.txt 行 534-540
格式: Level Count ProvId1 ProvId2 ... (空格分隔, 每行一条)
- 不能空 (CLAUDE.md 约束, 空文件会崩)
- 无 BOM, LF 换行
"""

from __future__ import annotations

import os


def write_railways_txt(output_dir: str, railway_mgr=None, fallback_pid: int = 1) -> None:
    """生成 map/railways.txt.

    railway_mgr: RailwayManager 实例, None 或空时写一条 placeholder (必须非空).
    fallback_pid: 当 mgr 为空时, placeholder 用的省份 ID (必须是合法的陆地省份).
    """
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "railways.txt")

    lines: list[str] = []
    if railway_mgr is not None:
        for entry in railway_mgr.get_all():
            lines.append(entry.to_line())

    # 必须非空 — vanilla 约束
    if not lines:
        # 单省份退化铁路 (level 1, 只经过 1 个省) — HOI4 接受 但可能警告
        # 为保险起见用 2 个相同 ID 组成最小合法条目
        lines.append(f"1 2 {fallback_pid} {fallback_pid}")

    content = "\n".join(lines) + "\n"
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
