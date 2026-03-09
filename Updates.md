# 更新记录

| 时间 | 变更内容 |
|------|----------|
| 2025-03-09 | 新增设计文档 `docs/设计文档.md`，涵盖 LynxLog 功能需求、技术架构、模块划分、界面设计及实现要点 |
| 2025-03-09 | 完成代码实现：AdbManager、LogFilter、DevicePanel、FilterPanel、LogPanel、ControlPanel、MainWindow、main.py、requirements.txt、README.md |
| 2025-03-09 | 新增高亮功能：HighlightPanel 支持配置关键字-颜色规则，LogPanel 支持彩色文本，匹配关键字整行显示对应颜色 |
| 2025-03-09 | 设置与关于：筛选/高亮配置移至设置弹窗，工具栏添加「设置」「关于」，关于弹窗显示版本号 v1.0.0 |
| 2025-03-09 | 一键配置预设：可保存/应用/删除筛选+高亮配置，存储于 %APPDATA%/LynxLog/presets.json |
| 2025-03-09 | 清除按钮与日志背景色：ControlPanel 增加清除按钮，设置中可配置日志区域背景色并持久化 |
