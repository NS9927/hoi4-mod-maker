# HOI4 State 规则

> 编译自 Paradox Wiki "State modding" 页面

## State 文件格式

路径: `/history/states/*.txt`

```
state = {
    id = 123                    # 必须, 整数, 从1开始连续
    name = STATE_123            # 必须, 本地化key
    manpower = 500000           # 必须, 总人口
    state_category = large_town # 必须, 决定建筑槽位
    provinces = { 123 456 789 } # 必须, 省份列表(空格分隔)

    impassable = yes            # 可选, 不可通行
    resources = { steel = 10 aluminium = 20 }  # 注意: aluminium 英式拼写!
    local_supplies = 8.3        # 可选, 基础补给

    history = {
        owner = POL
        victory_points = { 1234 10 }  # 每条只能一个省份
        victory_points = { 5678 5 }   # 多个VP写多条
        add_core_of = POL
        buildings = {
            infrastructure = 3
            7777 = {            # 省份级建筑套省份ID
                naval_base = 10
            }
        }
    }
}
```

## 致命规则

| 规则 | 违反后果 |
|------|----------|
| **State ID 必须连续** (从1开始, 不能有间隔) | 非 debug 模式 **[崩溃]** |
| **无 owner 的 state** 执行任何 effect | **[崩溃]** (右键/转让/AI空袭评估) |
| State 省份跨 strategic region | **[崩溃]** (非 debug) |
| VP 引用不存在的省份 | **[崩溃]** 加载阶段 |
| 内陆 state 定义沿海建筑(即使=0) | **[错误]** |

## State Category (建筑槽位)

| 名称 | 内部名 | 共享槽位 |
|------|--------|---------|
| Wasteland | wasteland | 0 |
| Enclave | enclave | 0 |
| Tiny island | tiny_island | 0 |
| Pastoral | pastoral | 1 |
| Small island | small_island | 1 |
| Rural | rural | 2 |
| Town | town | 4 |
| Large town | large_town | 5 |
| City | city | 6 |
| Large city | large_city | 8 |
| Metropolis | metropolis | 10 |
| Megalopolis | megalopolis | 12 |

## 资源列表

`oil`, `aluminium` (英式拼写!), `rubber`, `tungsten`, `steel`, `chromium`
