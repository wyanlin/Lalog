# LynxLog

基于 Windows 的 Android 设备日志实时抓取与筛选工具。

## 功能

### 核心功能

- **设备管理**：选择已连接的 ADB 设备，刷新设备列表
- **实时抓取**：开始/停止 logcat 抓取，日志实时显示
- **关键字筛选**：支持匹配大小写、正则表达式，抓取中可随时修改
- **高亮规则**：配置关键字与颜色，匹配的日志整行显示对应颜色

### 配置预设

- **保存**：覆盖选中预设，或创建新预设
- **另存为**：以新名称保存，若已存在则确认后覆盖
- **应用**：一键加载预设（筛选 + 高亮规则 + 日志背景色）
- **删除**：移除不需要的预设
- 预设存储于 `%APPDATA%/LynxLog/presets.json`

### 外观与显示

- **清除**：一键清空日志区域
- **日志背景色**：在设置中配置，支持深色/浅色主题，自动适配文字颜色
- **关于**：查看软件版本号

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
├── main.py
├── requirements.txt
├── docs/
│   └── 设计文档.md
├── src/
│   ├── version.py           # 版本号
│   ├── adb_manager.py       # ADB 与 logcat 管理
│   ├── log_filter.py        # 日志筛选逻辑
│   ├── app_settings.py      # 应用设置（如日志背景色）
│   ├── config_preset.py     # 配置预设存储
│   └── ui/
│       ├── main_window.py   # 主窗口
│       ├── device_panel.py  # 设备选择
│       ├── filter_panel.py  # 筛选设置
│       ├── highlight_panel.py   # 高亮规则
│       ├── log_panel.py     # 日志显示
│       ├── control_panel.py # 开始/停止/清除按钮
│       ├── preset_panel.py  # 配置预设
│       ├── settings_dialog.py   # 设置弹窗
│       └── about_dialog.py  # 关于弹窗
└── README.md
```

## License

MIT
