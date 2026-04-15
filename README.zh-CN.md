[English](README.md) | [中文](README.zh-CN.md)

# HOI4 幻想世界 MOD 制作工具

**从零构建完整的钢铁雄心 IV 全转换 MOD，无需手动编辑任何游戏文件。**

HOI4 Map Maker 是一款基于 Python + PyQt5 的开源桌面地图编辑器。提供 12 种编辑模式，覆盖地图制作全流程：绘制大陆轮廓、生成省份、分配州和国家，一键导出 2000+ 游戏文件，导出即可启动 HOI4 进入游戏。

> **当前版本**：v1.0.1 &nbsp;|&nbsp; **技术栈**：Python 3.10 · PyQt5 · NumPy &nbsp;|&nbsp; **平台**：Windows

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)

### 界面预览

**欢迎页** — 新建、打开、导入项目，或查看新手引导：

<p align="center">
  <img src="docs/screenshots/welcome_page.png" width="600" alt="欢迎页">
</p>

**工具面板** — 12 种编辑模式，分组折叠导航：

<p align="center">
  <img src="docs/screenshots/tool_panel_land.png" width="300" alt="工具面板">
</p>

**新手引导** — 首次启动时分步引导，带你走完全流程：

<p align="center">
  <img src="docs/screenshots/guide_step1.png" width="480" alt="新手引导">
</p>

**模式提示条** — 每个编辑模式首次切换时显示操作提示：

<p align="center">
  <img src="docs/screenshots/hint_bar.png" width="380" alt="模式提示条">
</p>

---

## 功能一览

### 地图绘制
- **陆地 / 海洋 / 湖泊**画笔，支持画笔、橡皮、填充、变换、平移五种工具
- 加载原版地图参考叠加 + 自定义参考底图
- 4 种地图尺寸可选：2048×1024 / 3072×1536 / 4096×2048 / 5632×2048

### 省份系统
- Voronoi + Lloyd 松弛算法自动生成省份，海洋/湖泊密度独立可调
- **合并** / **切割** / **套索扩张**工具，精细调整省份边界
- 增量生成：框选区域重新生成省份
- 一键全图诊断：X-crossings、过小省份、不连通区域、沿海检测

### 地形 / 高度 / 河流
- 10 种地形画刷：平原、森林、丘陵、山地、沙漠、沼泽、丛林、城市、海洋、湖泊
- 智能地形生成：高度分层 + 噪声边界 + 散点斑点
- 智能高度图生成：海岸距离场 + Perlin 噪声山脉 + 高斯平滑
- 河流绘制：12 种类型，严格遵循 HOI4 调色板

### 州 / 国家 / 区域
- 从省份自动生成州，支持归属国家、人口、等级、胜利点设置
- 创建国家：TAG / 颜色 / 执政党 / 首都
- 大陆分区、战略区域管理
- 后勤系统：邻接关系、铁路、补给节点
- **一键初始化**：自动生成州 + 战略区域 + 默认国家，一步到位可导出

### 一键导出
- 生成 2000+ HOI4 文件：`provinces.bmp`、`definition.csv`、`heightmap.bmp`、`terrain.bmp`、`rivers.bmp`、州历史、国家定义、`buildings.txt`、补给网络等
- 导出前自动预检 + 自动补全缺失数据
- 智能 `replace_path` 生成，自动处理 vanilla 冲突
- 导出完成直接启动 HOI4，即可进入游戏

### 工程管理
- 保存 / 加载 `.hoi4proj` 工程文件（zip 格式）
- 撤销 / 重做（Command 模式，30 步历史）
- 中英文双语界面
- 支持导入已有 MOD 地图

---

## 快速开始

### 从源码运行

```bash
git clone https://github.com/AmonStreeling/hoi4-mod-maker.git
cd hoi4-mod-maker
pip install -r requirements.txt
python main.py
```

### 下载打包版

前往 [Releases](https://github.com/AmonStreeling/hoi4-mod-maker/releases) 下载最新 `.zip`，解压后运行 `HOI4MapMaker.exe`。

### 环境要求

- Python 3.10+（仅源码运行需要）
- Windows 10/11
- 依赖库：PyQt5、NumPy、Pillow、SciPy

---

## 项目架构

```
hoi4_map_maker/          224 个文件，26,000 行代码
├── model/               数据中心（Project + EventBus）
├── domain/              纯数据层（MapData + 8 个 Manager + 生成器/验证器）
├── commands/            Command 模式 undo/redo（25 个命令）
├── controllers/         13 个业务 Controller（零 Qt 依赖）
├── views/               主窗口 + 画布（输入路由 + 叠加层）
├── ui/                  工具面板 + 暗色主题 + 国际化
├── features/            12 个地图编辑模式 + 10 个内容模块（2.0 规划）
├── services/            导出 / 导入 / 项目服务
├── export/              MOD 导出器（writer 按 HOI4 目录结构分组）
├── data/                常量 + 地形定义
├── app/                 DI 容器 + Feature 注册
└── tests/               pytest 测试套件
```

**架构模式**：MVC + Command + EventBus

**数据流**：用户操作 → InputRouter → Controller → Command → MapData/Manager → EventBus → Feature 渲染器 → Canvas 刷新

---

## 版本路线

### v1.0 — 地图编辑器 ✅
- [x] 陆地 / 省份 / 地形 / 高度 / 河流编辑
- [x] 州 / 国家 / 大陆 / 战略区域管理
- [x] 后勤系统（邻接 / 铁路 / 补给节点）
- [x] 一键导出可玩 MOD
- [x] 导入已有 MOD 地图
- [x] 中英文双语界面
- [x] 打包 `.exe` 发布

### v2.0 — 内容编辑器（规划中）
- [ ] 科技树 / 国策树编辑器
- [ ] 顾问 / 将领 / 间谍系统
- [ ] 起始部队 OOB 编辑器
- [ ] 事件 / 决议编辑器
- [ ] Ideas / 命名列表 / 肖像

---

## 许可证

本项目采用 **GNU General Public License v3.0** 开源许可。

- ✅ 可自由使用、修改、分发
- ✅ 用本工具制作的 MOD **不受** GPL 约束
- ❌ 修改本工具代码后必须同样以 GPL 开源
- 详见 [LICENSE](LICENSE) 文件

---

## 参与贡献

欢迎提 Issue 和 Pull Request。

代码规范：
- 中文注释
- `snake_case` 函数名 / `CamelCase` 类名
- 单文件不超过 800 行
- NumPy 向量化处理像素，禁止 Python 循环
