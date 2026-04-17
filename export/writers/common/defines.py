"""
common/defines/01_mod_defines.lua 写入器.

全转换 MOD 必须覆盖部分 NDefines，否则 AI 在非标准地图上除零崩溃。
主要问题：
- 空军 AI 用 (像素数 * 系数) 做除数，战略区域过小时除零
- 海军 AI 尝试登陆/巡逻不存在的区域
- 补给系统引用不匹配的省份数

策略：保守覆盖，只改会崩的参数，不改游戏平衡。
"""

from __future__ import annotations

import os


def write_defines_lua(output_dir: str, province_count: int = 0) -> None:
    """生成 common/defines/01_mod_defines.lua。"""
    d = os.path.join(output_dir, "common", "defines")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "01_mod_defines.lua")

    with open(path, "w", encoding="utf-8") as f:
        f.write(_generate_defines(province_count))


def _generate_defines(province_count: int) -> str:
    return f"""\
NDefines.NGame.MAX_PROVINCES = {max(province_count + 100, 25000)}
NDefines.NAir.AIR_REGION_SUPERIORITY_PIXEL_SCALE = 0.01
NDefines.NSupply.RAILWAY_BASE_FLOW = 10.0
"""
