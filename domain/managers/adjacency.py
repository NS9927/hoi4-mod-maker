"""
Adjacency 管理器 — 省份间特殊连接关系.

HOI4 用 map/adjacencies.csv 定义三种关系:
- sea: 海峡/运河 (两个省份跨海相连)
- impassable: 不可通行 (屏蔽直接相邻的边界)
- (未明确 type): 默认 sea

参考: 参考/Map modding.txt 行 485-502

每行 10 字段:
Start;End;Type;Through;start_x;start_y;stop_x;stop_y;rule;Comment

末尾必须有哨兵行: -1;-1;-1;-1;-1;-1;-1;-1;-1 (行 502)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


AdjacencyType = Literal["sea", "impassable"]


@dataclass
class AdjacencyEntry:
    """一条邻接关系."""
    from_id: int
    to_id: int
    type: AdjacencyType = "sea"
    through_id: int = -1  # sea 类型才用, impassable 保持 -1
    start_x: int = -1
    start_y: int = -1
    stop_x: int = -1
    stop_y: int = -1
    rule_name: str = ""  # adjacency_rules.txt 里定义的 rule name, 空=无规则
    comment: str = ""

    def to_csv_line(self) -> str:
        """序列化为 CSV 行 (10 字段, ; 分隔).

        注意: impassable 类型必须把 rule/坐标全置 -1 (行 497).
        """
        if self.type == "impassable":
            return (
                f"{self.from_id};{self.to_id};impassable;-1;"
                f"-1;-1;-1;-1;;{self.comment}"
            )
        return (
            f"{self.from_id};{self.to_id};{self.type};{self.through_id};"
            f"{self.start_x};{self.start_y};{self.stop_x};{self.stop_y};"
            f"{self.rule_name};{self.comment}"
        )


class AdjacencyManager:
    """管理所有 adjacency 条目. 按 (from,to) 去重."""

    def __init__(self) -> None:
        self._entries: list[AdjacencyEntry] = []

    # ─────────── CRUD ───────────

    def add(self, entry: AdjacencyEntry) -> None:
        """添加. 重复 (from,to,type) 会覆盖旧的."""
        self.remove(entry.from_id, entry.to_id, entry.type)
        self._entries.append(entry)

    def remove(self, from_id: int, to_id: int, type: AdjacencyType | None = None) -> bool:
        """删除指定条目. type=None 表示删除所有匹配的 (from,to). 返回是否删掉."""
        before = len(self._entries)
        if type is None:
            self._entries = [
                e for e in self._entries
                if not ((e.from_id == from_id and e.to_id == to_id)
                        or (e.from_id == to_id and e.to_id == from_id))
            ]
        else:
            self._entries = [
                e for e in self._entries
                if not ((e.from_id == from_id and e.to_id == to_id and e.type == type)
                        or (e.from_id == to_id and e.to_id == from_id and e.type == type))
            ]
        return len(self._entries) < before

    def get_all(self) -> list[AdjacencyEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries = []

    def find_by_province(self, province_id: int) -> list[AdjacencyEntry]:
        """返回涉及指定省份的所有 adjacency (无论起点终点)."""
        return [
            e for e in self._entries
            if e.from_id == province_id or e.to_id == province_id
        ]

    # ─────────── 数据同步 (供 compact_with_references) ───────────

    def drop_provinces(self, pids: set[int]) -> None:
        """删除引用了被删省份的 adjacency."""
        self._entries = [
            e for e in self._entries
            if e.from_id not in pids
               and e.to_id not in pids
               and e.through_id not in pids
        ]

    def remap_provinces(self, old_to_new: dict[int, int]) -> None:
        """按旧→新 ID 映射重写."""
        new_entries: list[AdjacencyEntry] = []
        for e in self._entries:
            new_from = old_to_new.get(e.from_id)
            new_to = old_to_new.get(e.to_id)
            if new_from is None or new_to is None:
                continue  # 任一端被删就丢弃
            new_through = old_to_new.get(e.through_id, e.through_id) if e.through_id >= 0 else -1
            new_entries.append(
                AdjacencyEntry(
                    from_id=new_from,
                    to_id=new_to,
                    type=e.type,
                    through_id=new_through,
                    start_x=e.start_x, start_y=e.start_y,
                    stop_x=e.stop_x, stop_y=e.stop_y,
                    rule_name=e.rule_name,
                    comment=e.comment,
                )
            )
        self._entries = new_entries

    # ─────────── 序列化 ───────────

    def to_dict(self) -> dict:
        return {
            "entries": [
                {
                    "from_id": e.from_id,
                    "to_id": e.to_id,
                    "type": e.type,
                    "through_id": e.through_id,
                    "start_x": e.start_x,
                    "start_y": e.start_y,
                    "stop_x": e.stop_x,
                    "stop_y": e.stop_y,
                    "rule_name": e.rule_name,
                    "comment": e.comment,
                }
                for e in self._entries
            ]
        }

    def from_dict(self, data: dict) -> None:
        self._entries = []
        for d in data.get("entries", []):
            self._entries.append(
                AdjacencyEntry(
                    from_id=int(d["from_id"]),
                    to_id=int(d["to_id"]),
                    type=d.get("type", "sea"),
                    through_id=int(d.get("through_id", -1)),
                    start_x=int(d.get("start_x", -1)),
                    start_y=int(d.get("start_y", -1)),
                    stop_x=int(d.get("stop_x", -1)),
                    stop_y=int(d.get("stop_y", -1)),
                    rule_name=d.get("rule_name", ""),
                    comment=d.get("comment", ""),
                )
            )
