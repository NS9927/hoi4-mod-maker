# HOI4 本地化与MOD结构

> 来源: Paradox Wiki — Localisation / Modding 页面精简编译。仅保留格式规范/字段定义/文件路径。

---

## 1. 本地化文件格式

### 编码/BOM/换行

| 项目 | 要求 |
|------|------|
| 编码 | **UTF-8 with BOM** (前 3 字节 `EF BB BF`) |
| 扩展名 | `.yml` (不是 `.yaml`) |
| 换行 | 游戏不强制 CRLF/LF, 但导出建议 CRLF |
| 缺少 BOM 后果 | log 报错; 未分配语言时崩溃 `0xC0000005` |

### 文件命名

```
<任意前缀>_l_<语言代码>.yml
```

### 语言代码

`l_english` `l_french` `l_german` `l_spanish` `l_braz_por` `l_polish` `l_russian` `l_japanese` `l_simp_chinese` `l_korean`

### 文件路径

```
localisation/<语言>/filename_l_<语言>.yml
```

### 文件结构

```yaml
l_english:                          # 第一行: 语言声明 (必须)
 key_name:0 "显示文本"              # 缩进 1 空格; :0 是可选版本号
 another_key: "也行, 不写版本号"
```

### key 命名规则

- 允许字符: `A-Z a-z 0-9 _ . -`
- **禁止**: 空格、变音符号、非 Latin 字符 → 会导致 `Expected colon(:)` 错误并中断后续解析

### value 规则

- 必须单行, 换行用 `\n` (反斜杠)
- `\n` 后不要跟空格 (游戏中会有偏移)
- 引号用 `\"` 转义
- 必须用 ASCII 直引号 `"` (U+0022), 不能用弯引号

### 版本号

`:` 后的数字必须是纯数字, 非数字会中断解析。

---

## 2. 本地化格式化代码

### 颜色 (§ 段落符)

语法: `§<代码>文本§!`

| 代码 | 颜色 | 代码 | 颜色 |
|------|------|------|------|
| `§R` | 红 (255,50,50) | `§G` | 绿 (0,159,3) |
| `§B` | 蓝 (0,0,255) | `§Y` | 黄 (255,189,0) |
| `§W` | 白 | `§H` | 黄/标题 |
| `§O` | 橙 (255,112,25) | `§C` | 青 (35,206,255) |
| `§L` | 淡紫 (195,176,145) | `§T` | 白/标题 |
| `§b` | 黑 | `§g` | 浅灰 |
| `§t` | 鲜红 (255,76,77) | `§!` | 结束颜色 |
| `§0`-`§9` | 数字色板 (紫/淡紫/蓝/灰蓝/浅蓝/暗青/绿松石/浅绿/橙黄/白橙) | | |

### 变量引用 ($)

```yaml
key:0 "文本 $OTHER_KEY$ 继续"     # 引用另一个 loc key
key:0 "花费 $$100"                  # 字面 $ 用 $$
```

### 文本图标 (£)

```yaml
key:0 "£army_experience 陆军经验"   # 对应 GFX_army_experience
key:0 "£icon|2"                     # 多帧图标, 帧号从 0 开始
```

图标需在 `interface/*.gfx` 定义:
```
spriteType = {
    name = "GFX_army_experience"
    texturefile = "gfx/texticons/army_experience.dds"
    legacy_lazy_load = no
}
```

### 国旗 (@)

```yaml
key:0 "@GER 德国"                   # 显示 gfx/flags/GER.tga
```

### 作用域函数 ([])

```yaml
key:0 "[ROOT.GetName] 已加入 [FROM.GetFactionName]"
```

常用函数: `GetName` `GetTag` `GetAdjective` `GetLeader` `GetRulingParty` `GetFlag` `GetNameWithFlag` `GetDateText` `GetYear`

### 变量格式化 ([?])

```yaml
key:0 "[?party_popularity@democracy|%G0]"
# % = ×100 加 %号; G = 绿色; 0 = 0位小数
```

格式符: `%`(×100+%) `%%`(仅加%) `=`(±前缀) `+`(正绿零黄负红) `-`(正红零黄负绿) `0-9`(小数位) `*`/`^`(SI 单位 K/M)

---

## 3. 本地化覆盖 (replace)

```
localisation/<语言>/replace/xxx_l_english.yml
```

`replace/` 子目录下的文件 **优先级高于** 标准目录, 可覆盖特定 key 而不需复制整个文件。

覆盖日志: `logs/text.log`

---

## 4. MOD 目录结构

```
mod/<modname>/
├── descriptor.mod          # MOD 描述文件 (必须)
├── common/                 # 数据库条目
│   ├── national_focus/
│   ├── technologies/
│   └── ...
├── events/
├── history/
│   ├── countries/
│   ├── states/
│   └── units/
├── localisation/
│   └── english/
│       └── *_l_english.yml
├── interface/              # GFX sprite 定义 (.gfx)
│   └── *.gfx
└── gfx/                    # 图片资源
    ├── flags/              # 国旗 (32-bit TGA, 无 RLE)
    ├── loadingscreens/
    └── interface/
```

---

## 5. descriptor.mod 格式

**存在两份**:
1. `<HOI4用户目录>/mod/modname.mod` — 包含本机路径, 文件名决定加载顺序
2. `<MOD根目录>/descriptor.mod` — 随 MOD 发布

### 必填字段

```
name = "MOD 名称"
version = "v1.0"
supported_version = "1.13.*"       # 支持通配符
tags = { "Gameplay" "Historical" }
```

### 仅用户描述文件

```
path = "mod/modname"               # 必须正斜杠, 仅 ASCII
```

### 可选字段

```
picture = "thumbnail.png"          # ≤1MB
remote_file_id = "1678247250"      # Steam Workshop ID
user_dir = "MySaveFolder"          # 隔离存档目录
dependencies = { "Other Mod" }     # 强制先加载, name 必须精确匹配
replace_path = "history/states"    # 可多行
```

### 路径规则

- **仅正斜杠** `/`, 反斜杠被当转义符
- **仅 ASCII 字符**, 非 ASCII 会静默加载失败

---

## 6. replace_path 规则

```
replace_path = "history/states"
replace_path = "gfx/loadingscreens"
```

- 卸载目标文件夹中 **所有之前加载的索引文件**
- **不改变**加载顺序 (用 `dependencies` 控制顺序)
- **必须同时写入两份** descriptor
- 如果 replace 后目标文件夹为空 → **崩溃**
- 直接文件链接 (如角色头像) 不受影响, 仍会加载

---

## 7. GFX / spriteTypes 基本格式

定义位置: `interface/*.gfx`

```
spriteTypes = {

    # 普通精灵
    spriteType = {
        name = GFX_sprite_name
        texturefile = gfx/folder/file.dds
    }

    # 平铺精灵
    corneredTileSpriteType = {
        name = GFX_tiled_name
        texturefile = gfx/interface/tile.dds
    }

    # 帧动画精灵
    frameAnimatedSpriteType = {
        name = GFX_animated_name
        texturefile = gfx/animation.dds
        noOfFrames = 4
    }
}
```

支持图片格式: **DDS** (ARGB8), TGA, PNG, BMP

国旗特殊要求: **32-bit TGA, 无 RLE 压缩**

无需 sprite 定义的例外:
- `gfx/flags/` 下的国旗
- `gfx/loadingscreens/` 下的加载图
- 角色头像 (可能用直接文件链接)

---

## 8. 加载顺序

优先级从低到高:
1. 基础游戏
2. DLC (按内部 ID)
3. 用户目录
4. MOD (按 `.mod` 描述文件名字母序)

**同路径文件**: 后加载的覆盖先加载的。只看文件名是否重叠。

---

## 9. 常见本地化错误

| 错误 | 原因 |
|------|------|
| 崩溃 `0xC0000005` | 缺少 UTF-8 BOM |
| `Expected colon(:) at line X` | key 中含空格/变音符/非 Latin 字符 |
| `Could not find coloring for character 'X'` | 无效颜色代码 (§ 后跟了不存在的字母) |
| `Could not find coloring for character id 'N'` | 多字节 UTF-8 字符只读最后一字节 |
| 颜色渗透到后续文本 | 缺少 `§!` 结束符 |
| 文件后半部分全部丢失 | 未闭合引号 / key 含非法字符 |
| value 换行消失 | 不支持多行 value, 用 `\n` |
| 版本号后解析中断 | `:` 后写了非数字字符 |

---

## 10. 常见 MOD 结构错误

| 错误 | 原因 |
|------|------|
| MOD 静默不加载 | 路径含非 ASCII 字符 或 用了反斜杠 |
| replace_path 后崩溃 | 目标文件夹被清空但没有新文件填充 |
| 依赖 MOD 未生效 | `dependencies` 中的名字与目标 MOD 的 `name` 不完全匹配 |
| 存档不兼容 | `user_dir` 设置不同导致存档隔离 |
| 启动器不显示 MOD | `launcher-v2.sqlite` 缓存, 删除后重新生成 |
