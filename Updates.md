# 更新记录

| 时间 | 变更内容 |
|------|----------|
| 2026-03-22 | 日志分析 Tab 搜索：「共 n 处」改为防抖 + 有界计数（不再每键对全文 finditer 建表）；超过 10000 处显示「10000+」 |
| 2026-03-22 | `categories.py` 显示名与 MSC06A 手册第 3～9 章对齐；`06a.delta.json` 各规则 `category` 按手册章节重映射（如 +COPS 属第 4 章终端控制） |
| 2026-03-22 | AT 指令规则增加 `category`（手册章节类型）；`categories.py`；解析结果表「类型」列；日志分析「指令类型」勾选 + 全选/全不选 |
| 2026-03-22 | MSC06A 芯片 AT 命令手册 V3.9：在 `config/modules/06a.delta.json` 增加约 50 条 URC/响应解析规则（^DSCI/^DCPI/+CREG/+CSQ/^TTLOG/^MESINFO 等）；天通+模组 06A 时与 base 合并 |
| 2026-03-22 | 设计文档更新：补充日志分析（F5）、AT 解析配置、规则合并顺序、项目结构 |
| 2026-03-22 | 规则合并顺序改为 base → module → system：同一 chip（06A/1881）在天通与星网下可由 system 的 rules_override 区分 AT 指令；星网支持 06a、1881 模组 |
| 2026-03-22 | 新增 AT^SATSIGNAL 通用解析规则（base.json satsignal）：URC ^SATSIGNAL: &lt;rscp&gt;,&lt;snr&gt;，解码器 satsignal_rscp / satsignal_snr（0 显示 —） |
| 2026-03-22 | 日志分析 AT 解析重构：引入 `src/ui/log_analysis/` 子包（可扩展方案×模组×规则）；工具栏新增解析方案/模组双下拉；结果区改为状态/语音/数据三域 QTabWidget；支持实时过滤、导出 CSV/Excel（openpyxl 可选）、图表（matplotlib 可选）；旧 `cpstate_parser.py` 迁入子包并删除 |
| 2025-03-09 | 新增设计文档 `docs/设计文档.md`，涵盖 LynxLog 功能需求、技术架构、模块划分、界面设计及实现要点 |
| 2025-03-09 | 完成代码实现：AdbManager、LogFilter、DevicePanel、FilterPanel、LogPanel、ControlPanel、MainWindow、main.py、requirements.txt、README.md |
| 2025-03-09 | 新增高亮功能：HighlightPanel 支持配置关键字-颜色规则，LogPanel 支持彩色文本，匹配关键字整行显示对应颜色 |
| 2025-03-09 | 设置与关于：筛选/高亮配置移至设置弹窗，工具栏添加「设置」「关于」，关于弹窗显示版本号 v1.0.0 |
| 2025-03-09 | 一键配置预设：可保存/应用/删除筛选+高亮配置，存储于 %APPDATA%/LynxLog/presets.json |
| 2025-03-09 | 清除按钮与日志背景色：ControlPanel 增加清除按钮，设置中可配置日志区域背景色并持久化 |
