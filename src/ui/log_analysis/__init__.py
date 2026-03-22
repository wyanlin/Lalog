# -*- coding: utf-8 -*-
"""
log_analysis 子包：仅供 log_analysis_tab 使用。
对外导出的核心 API：
  - parse_log(text, system_id, module_id) -> List[ParsedAtRecord]
  - list_systems() -> List[(id, name)]
  - list_modules(system_id) -> List[(id, name)]
  - ParsedAtRecord（类型）
"""
from .config_loader import list_modules, list_systems
from .engine import parse_log, parse_log_lines
from .types import ParsedAtRecord

__all__ = ["parse_log", "parse_log_lines", "list_systems", "list_modules", "ParsedAtRecord"]
