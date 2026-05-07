"""supply_nodes.txt / railways.txt / supply_areas/*.txt."""
import os
import numpy as np


def write_supply_nodes(states, province_map, output_dir):
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "supply_nodes.txt"), "w", encoding="utf-8") as f:
        # 按索引每5个State放一个补给节点
        state_list = [(sid, provs) for sid, provs in states.items() if provs]
        written = False
        for i, (sid, provs) in enumerate(state_list):
            if i % 5 == 0:
                f.write(f"1 {provs[0]}\n")
                written = True
        if not written and state_list:
            f.write(f"1 {state_list[0][1][0]}\n")
            written = True
        if not written:
            # 文件不能为空也不能写注释，写一个占位节点
            f.write("1 1\n")


def write_railways(states, province_map, output_dir):
    """fallback：没有用户铁路数据时，写最小占位。"""
    d = os.path.join(output_dir, "map")
    os.makedirs(d, exist_ok=True)
    fallback_pid = 1
    for sid, provs in states.items():
        if provs:
            fallback_pid = provs[0]
            break
    with open(os.path.join(d, "railways.txt"), "w", encoding="utf-8") as f:
        f.write(f"1 2 {fallback_pid} {fallback_pid}\n")


def write_supply_areas(states, output_dir, states_per_area: int = 15):
    """写 map/supplyareas/*.txt，每个补给区域包含 states_per_area 个 state。

    HOI4 要求每个 state 都属于一个 supply_area，否则报错。
    把所有 state 按 ID 排序后分组，每组写一个文件。
    """
    d = os.path.join(output_dir, "map", "supplyareas")
    os.makedirs(d, exist_ok=True)

    state_ids = sorted(states.keys())
    if not state_ids:
        # 至少写一个空补给区域文件，避免目录为空
        with open(os.path.join(d, "1-SupplyArea.txt"), "w", encoding="utf-8") as f:
            f.write("supply_area={\n\tid=1\n")
            f.write('\tname="SUPPLYAREA_WT_1"\n\tvalue=1\n')
            f.write("\tstates={\n\t\t1\n\t}\n}\n")
        return

    # 按 states_per_area 分组
    area_id = 0
    for i in range(0, len(state_ids), states_per_area):
        area_id += 1
        chunk = state_ids[i:i + states_per_area]
        # value 随 state 数量缩放（1-10），更多 state 的区域给更高补给值
        value = max(1, min(10, len(chunk)))
        with open(os.path.join(d, f"{area_id}-SupplyArea.txt"), "w", encoding="utf-8") as f:
            f.write("supply_area={\n")
            f.write(f"\tid={area_id}\n")
            f.write(f'\tname="SUPPLYAREA_WT_{area_id}"\n')
            f.write(f"\tvalue={value}\n")
            f.write("\tstates={\n\t\t")
            f.write(" ".join(str(s) for s in chunk))
            f.write("\n\t}\n}\n")

