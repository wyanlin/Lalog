# -*- coding: utf-8 -*-
"""
扫描引擎：根据 EffectiveProfile 对 log 全文逐行解析，产出 ParsedAtRecord 列表。
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

from .config_loader import load_profile
from .decoders.registry import decode
from .types import ColumnDef, EffectiveProfile, ParsedAtRecord, RuleDef

_LOG_TIME_RE = re.compile(r"^\S+\s+(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})")
_TAG_RE = re.compile(r"\s([A-Za-z0-9_/.-]+):\s")


def _extract_time(line: str) -> str:
    m = _LOG_TIME_RE.match(line)
    return m.group(1) if m else ""


def _extract_payload(line: str, urc_prefix: str) -> Optional[str]:
    idx = line.find(urc_prefix)
    if idx == -1:
        return None
    return line[idx + len(urc_prefix):].strip()


def _split_payload(payload: str, separator: str, n_cols: int, max_fields: int) -> List[str]:
    """拆分 payload；多余部分合并到最后一列。"""
    limit = max_fields if max_fields > 0 else n_cols
    parts = [p.strip() for p in payload.split(separator)]
    if len(parts) <= limit:
        while len(parts) < limit:
            parts.append("")
        return parts[:limit]
    return parts[: limit - 1] + [separator.join(parts[limit - 1:])]


def _apply_rule(line: str, tag: str, rule: RuleDef,
                system_id: str, module_id: str,
                line_no: int) -> Optional[ParsedAtRecord]:
    if rule.urc_prefix not in line:
        return None
    payload = _extract_payload(line, rule.urc_prefix)
    if payload is None:
        return None

    n = len(rule.columns)
    if n == 0:
        return None

    raw_parts = _split_payload(payload, rule.separator, n, rule.max_fields)
    raw_cols: Dict[str, str] = {}
    disp_cols: Dict[str, str] = {}
    for i, col_def in enumerate(rule.columns):
        raw_val = raw_parts[i] if i < len(raw_parts) else ""
        raw_cols[col_def.key] = raw_val
        disp_cols[col_def.key] = decode(col_def.decoder, raw_val) if col_def.decoder else raw_val

    return ParsedAtRecord(
        line_no=line_no,
        time_str=_extract_time(line),
        tag=tag,
        system_id=system_id,
        module_id=module_id,
        rule_id=rule.id,
        domain=rule.domain,
        column_defs=rule.columns,
        columns=disp_cols,
        raw_columns=raw_cols,
        raw_line=line,
        rule_category=rule.category,
    )


def _extract_tag(line: str, allowed_tags: Tuple[str, ...]) -> Optional[str]:
    """从行中提取匹配的 logcat TAG；返回第一个匹配的允许 TAG，否则 None。"""
    for tag in allowed_tags:
        if f" {tag}:" in line or f"\t{tag}:" in line:
            return tag
    return None


def parse_log_lines(
    lines: Iterable[str],
    system_id: str,
    module_id: str = "generic",
) -> List[ParsedAtRecord]:
    """
    接受行迭代器（不含换行符），逐行解析并返回所有命中记录。
    调用方可以直接传入文件对象、str.splitlines() 或跨分块的行生成器，
    避免在调用侧将整个文本 join 后再 splitlines() 造成的双份内存峰值。
    """
    profile = load_profile(system_id, module_id)
    if profile is None or not profile.rules:
        return []

    # 前缀越长越先匹配，避免短前缀误抢（若将来存在包含关系）
    rules = tuple(
        sorted(profile.rules, key=lambda r: (-len(r.urc_prefix), r.id))
    )

    allowed_tags = profile.system.tags
    results: List[ParsedAtRecord] = []

    for line_no, raw in enumerate(lines, start=1):
        line = raw.rstrip("\r\n")
        tag = _extract_tag(line, allowed_tags)
        if tag is None:
            continue
        for rule in rules:
            rec = _apply_rule(line, tag, rule, system_id, module_id, line_no)
            if rec is not None:
                results.append(rec)
                break  # 一行只取第一条命中的规则

    return results


def parse_log(text: str, system_id: str, module_id: str = "generic") -> List[ParsedAtRecord]:
    """
    对全文按行解析（向后兼容接口）。
    内部直接将迭代器传给 parse_log_lines，避免先 splitlines 再复制整个列表。
    """
    return parse_log_lines(iter(text.splitlines()), system_id, module_id)
