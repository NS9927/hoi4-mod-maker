"""美术资产导出辅助 — 决定是写回原字节还是重新生成。

导入 MOD 时，工具把 colormap / world_normal 等非结构性文件读入 project.assets。
用户编辑画布时相关资产被标 dirty。导出时：
  clean → 直接写回原字节（保留原美术）
  dirty 或不在 assets → 调 generator_fn 生成新版本
"""
from __future__ import annotations

import os
from typing import Callable


def write_or_restore(
    rel_path: str,
    output_dir: str,
    assets: dict[str, bytes] | None,
    dirty_assets: set[str] | None,
    generator_fn: Callable[[], None],
) -> str:
    """按 dirty 状态决定写回原 asset 还是生成新文件。

    参数:
        rel_path: MOD 相对路径，如 "map/terrain/colormap_rgb_cityemissivemask_a.dds"
                  （斜杠分隔，与 project.assets 的 key 一致）
        output_dir: 导出根目录（MOD 根）
        assets: project.assets（可能为 None，表示没有导入资产）
        dirty_assets: project.dirty_assets（可能为 None）
        generator_fn: 当需要重新生成时调用的函数（无参数，内部自行写文件）

    返回:
        "restored" | "generated" | "skipped"
    """
    if assets is None:
        assets = {}
    if dirty_assets is None:
        dirty_assets = set()

    # clean asset → 写回原字节
    if rel_path in assets and rel_path not in dirty_assets:
        dst = os.path.join(output_dir, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(assets[rel_path])
        return "restored"

    # 否则执行生成
    generator_fn()
    return "generated"


def classify_assets(
    rel_paths: list[str],
    assets: dict[str, bytes] | None,
    dirty_assets: set[str] | None,
) -> tuple[int, int, int]:
    """统计：(restored, generated, total_paths)。

    用于 UI 显示"保留 X 个 / 重生 Y 个"。
    """
    if assets is None:
        assets = {}
    if dirty_assets is None:
        dirty_assets = set()
    restored = 0
    generated = 0
    for p in rel_paths:
        if p in assets and p not in dirty_assets:
            restored += 1
        else:
            generated += 1
    return restored, generated, len(rel_paths)
