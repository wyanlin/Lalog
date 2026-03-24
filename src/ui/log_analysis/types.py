# -*- coding: utf-8 -*-
"""公共数据结构，仅供 log_analysis 子包内部与 log_analysis_tab 使用。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class ColumnDef:
    """一列的定义：内部 key、展示标签、可选解码器 id、是否数值（供图表使用）。"""
    key: str
    label: str
    decoder: Optional[str] = None
    numeric: bool = False


@dataclass(frozen=True)
class RuleDef:
    """一条 AT/URC 解析规则。"""
    id: str
    name: str             # 显示名称，如 "CPSTATE"
    desc: str             # 描述，如 "卫星信号状态上报"
    domain: str           # "status" | "voice" | "data"
    urc_prefix: str       # 行内子串快速匹配，例如 "^CPSTATE:"
    category: str = "other"  # 手册章节类型 id，见 categories.CATEGORY_DEFS
    separator: str = ","
    max_fields: int = 0   # 0 表示无限制，取前 len(columns) 个
    columns: Tuple[ColumnDef, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SystemDef:
    """解析方案（天通 / 星网 等）。"""
    id: str
    name: str
    tags: Tuple[str, ...]
    default_module: str = "generic"
    modules: Tuple[str, ...] = ("generic",)


@dataclass(frozen=True)
class EffectiveProfile:
    """合并 system + module 后的完整解析配置。"""
    system: SystemDef
    module_id: str
    rules: Tuple[RuleDef, ...]


@dataclass
class ParsedAtRecord:
    """引擎产出的单条解析记录。"""
    line_no: int
    time_str: str
    tag: str
    system_id: str
    module_id: str
    rule_id: str
    domain: str
    column_defs: Tuple[ColumnDef, ...]        # 有序列定义（来自规则）
    columns: Dict[str, str]                   # key -> 解码后显示值
    raw_columns: Dict[str, str]               # key -> 原始字符串值（供图表用）
    raw_line: str
    rule_category: str = "other"              # 与 RuleDef.category 一致，供类型筛选与展示
