"""
Railway 管理器 — 铁路线数据.

HOI4 用 map/railways.txt 定义初始铁路.
参考: 参考/Map modding.txt 行 534-540

每行格式 (空格分隔, 无分号):
Level Amount_of_provinces List_of_provinces

示例:
4 4 693 1444 12 11   # level 4, 4 个省份, 依次经过 693/1444/12/11

Level 上限 5 (默认, 见 NDefines.NSupply.MAX_RAILWAY_LEVEL).
无效定义会导致 HOI4 崩溃:
- 经过不存在的省份
- 经过 stateless 省份
- 严重不连续的定义
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RailwayEntry:
    """一条铁路."""
    level: int  # 1-5
    province_ids: list[int] = field(default_factory=list)

    def to_line(self) -> str:
        """序列化为 railways.txt 一行."""
        ids_str = " ".join(str(p) for p in self.province_ids)
        return f"{self.level} {len(self.province_ids)} {ids_str}"


class RailwayManager:
    """管理所有铁路线. 按顺序存储, 允许重复路径."""

    MAX_LEVEL = 5

    def __init__(self) -> None:
        self._entries: list[RailwayEntry] = []

    # ─────────── CRUD ───────────

    def add(self, level: int, province_ids: list[int]) -> int:
        """添加一条铁路, 返回索引."""
        if not (1 <= level <= self.MAX_LEVEL):
            raise ValueError(f"level 必须在 1-{self.MAX_LEVEL}, 传入 {level}")
        if len(province_ids) < 2:
            raise ValueError(f"铁路至少经过 2 个省份, 传入 {len(province_ids)}")
        self._entries.append(RailwayEntry(level=level, province_ids=list(province_ids)))
        return len(self._entries) - 1

    def remove_at(self, index: int) -> bool:
        if 0 <= index < len(self._entries):
            self._entries.pop(index)
            return True
        return False

    def update_level(self, index: int, level: int) -> None:
        if not (1 <= level <= self.MAX_LEVEL):
            raise ValueError(f"level 必须在 1-{self.MAX_LEVEL}")
        if 0 <= index < len(self._entries):
            self._entries[index].level = level

    def get_all(self) -> list[RailwayEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries = []

    def find_by_province(self, province_id: int) -> list[int]:
        """返回所有经过指定省份的铁路索引."""
        return [
            i for i, e in enumerate(self._entries)
            if province_id in e.province_ids
        ]

    # ─────────── 数据同步 ───────────

    def drop_provinces(self, pids: set[int]) -> None:
        """删除引用了被删省份的铁路 (整条丢弃)."""
        self._entries = [
            e for e in self._entries
            if not any(p in pids for p in e.province_ids)
        ]

    def remap_provinces(self, old_to_new: dict[int, int]) -> None:
        """按旧→新 ID 映射重写. 任一省份找不到新 ID 就丢弃整条."""
        new_entries: list[RailwayEntry] = []
        for e in self._entries:
            new_ids = []
            broken = False
            for p in e.province_ids:
                new_p = old_to_new.get(p)
                if new_p is None:
                    broken = True
                    break
                new_ids.append(new_p)
            if not broken and len(new_ids) >= 2:
                new_entries.append(RailwayEntry(level=e.level, province_ids=new_ids))
        self._entries = new_entries

    # ─────────── 序列化 ───────────

    def to_dict(self) -> dict:
        return {
            "entries": [
                {"level": e.level, "province_ids": list(e.province_ids)}
                for e in self._entries
            ]
        }

    def from_dict(self, data: dict) -> None:
        self._entries = []
        for d in data.get("entries", []):
            self._entries.append(
                RailwayEntry(
                    level=int(d["level"]),
                    province_ids=[int(p) for p in d.get("province_ids", [])],
                )
            )
