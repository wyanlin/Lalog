# 更新记录

| 时间 | 变更内容 |
|------|----------|
| 2026-03-22 | 新增 AT^SATSIGNAL 通用解析规则（base.json satsignal）：URC ^SATSIGNAL: &lt;rscp&gt;,&lt;snr&gt;，解码器 satsignal_rscp / satsignal_snr（0 显示 —） |
| 2026-03-22 | 日志分析 AT 解析重构：引入 `src/ui/log_analysis/` 子包（可扩展方案×模组×规则）；工具栏新增解析方案/模组双下拉；结果区改为状态/语音/数据三域 QTabWidget；支持实时过滤、导出 CSV/Excel（openpyxl 可选）、图表（matplotlib 可选）；旧 `cpstate_parser.py` 迁入子包并删除 |
| 2025-03-09 | 新增设计文档 `docs/设计文档.md`，涵盖 LynxLog 功能需求、技术架构、模块划分、界面设计及实现要点 |
| 2025-03-09 | 完成代码实现：AdbManager、LogFilter、DevicePanel、FilterPanel、LogPanel、ControlPanel、MainWindow、main.py、requirements.txt、README.md |
| 2025-03-09 | 新增高亮功能：HighlightPanel 支持配置关键字-颜色规则，LogPanel 支持彩色文本，匹配关键字整行显示对应颜色 |
| 2025-03-09 | 设置与关于：筛选/高亮配置移至设置弹窗，工具栏添加「设置」「关于」，关于弹窗显示版本号 v1.0.0 |
| 2025-03-09 | 一键配置预设：可保存/应用/删除筛选+高亮配置，存储于 %APPDATA%/LynxLog/presets.json |
| 2025-03-09 | 清除按钮与日志背景色：ControlPanel 增加清除按钮，设置中可配置日志区域背景色并持久化 |
