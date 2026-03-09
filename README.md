# LynxLog

基于 Windows 的 Android 设备日志实时抓取与筛选工具。

## 功能

### 核心功能

- **设备管理**：选择已连接的 ADB 设备、刷新设备列表
- **实时抓取**：开始/停止 logcat 抓取，日志实时显示
- **关键字筛选**：支持匹配大小写、正则表达式，抓取中可随时修改
- **高亮规则**：配置关键字与颜色，匹配的日志整行显示对应颜色
- **清除日志**：一键清空日志显示区域

### 日志分析（Tab 切换）

- **打开文件**：导入单个 .log / .txt 文件，可编辑
- **打开文件夹**：左侧显示文件列表，点击文件在右侧查看/编辑内容
- **大文件优化**：后台异步加载，显示进度，分块渲染减少卡顿
- **保存 / 另存为**：Ctrl+S 保存，单文件覆盖原路径，文件夹内容需另存为
- **搜索**：Ctrl+F 聚焦搜索框，支持：
  - 正则表达式、忽略大小写、循环查找（可勾选）
  - 上一个/下一个查找，回车查找下一个
  - 实时显示匹配数量（共 N 处）

### 配置与预设

- **设置**：筛选条件、高亮规则、日志背景色（工具栏进入）
- **配置预设**：一键保存/加载筛选 + 高亮 + 日志背景色
  - 保存：覆盖选中预设或创建新预设
  - 另存为：以新名称保存，若存在可覆盖
  - 应用：加载并应用选中预设
  - 删除：删除选中预设
- **日志背景色**：可配置，随预设保存与加载

### 其他

- **关于**：查看当前软件版本（工具栏进入）
- **界面适配**：默认窗口根据屏幕尺寸自动调整，支持高 DPI 缩放，日志字体随 DPI 适配

## 环境要求

- Windows 10/11
- Python 3.8+
- ADB 已安装并加入系统 PATH
- Android 设备已连接并开启 USB 调试

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 项目结构

```
LynxLog/
├── main.py                 # 程序入口
├── requirements.txt
├── docs/
│   └── 设计文档.md
├── src/
│   ├── __init__.py
│   ├── version.py          # 版本号
│   ├── adb_manager.py       # ADB 与 logcat 管理
│   ├── log_filter.py       # 日志筛选逻辑
│   ├── config_preset.py     # 配置预设存储
│   ├── app_settings.py     # 应用级设置（日志背景色等）
│   └── ui/
│       ├── main_window.py   # 主窗口
│       ├── device_panel.py  # 设备选择
│       ├── filter_panel.py # 筛选设置
│       ├── highlight_panel.py # 高亮规则
│       ├── log_panel.py    # 日志显示
│       ├── control_panel.py  # 开始/停止/清除
│       ├── log_analysis_tab.py  # 日志分析（文件/文件夹导入、搜索）
│       ├── preset_panel.py  # 配置预设
│       ├── settings_dialog.py # 设置对话框
│       └── about_dialog.py # 关于
└── README.md
```

## 数据存储

- **预设**：`%APPDATA%/LynxLog/presets.json`
- **应用设置**（日志背景色等）：系统注册表 / QSettings
