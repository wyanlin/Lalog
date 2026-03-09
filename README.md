# LynxLog

基于 Windows 的 Android 设备日志实时抓取与筛选工具。

## 功能

- 选择已连接的 ADB 设备
- 刷新设备列表
- 开始/停止实时 logcat 抓取
- 关键字筛选（支持匹配大小写、正则表达式）
- 抓取中可随时修改筛选条件
- 高亮规则：配置关键字与颜色，匹配的日志整行显示对应颜色

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
│   ├── adb_manager.py      # ADB 与 logcat 管理
│   ├── log_filter.py       # 日志筛选逻辑
│   └── ui/
│       ├── main_window.py  # 主窗口
│       ├── device_panel.py # 设备选择
│       ├── filter_panel.py # 筛选设置
│       ├── log_panel.py    # 日志显示
│       └── control_panel.py# 开始/停止按钮
└── README.md
```
