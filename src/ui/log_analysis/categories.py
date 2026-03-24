# -*- coding: utf-8 -*-
"""AT 指令手册章节类型（MSC06A 手册 V3.9 目录），用于规则分类与界面筛选。"""
from __future__ import annotations

from typing import Dict, List, Tuple

# (category_id, 显示名称) — 顺序与手册第 3～9 章一致，状态监控/其他殿后
# 手册：3 通用控制与状态 → 9 扩展命令；CPSTATE 状态监控见入网/维测流程
CATEGORY_DEFS: List[Tuple[str, str]] = [
    ("general", "3 通用控制与状态"),
    ("terminal", "4 终端控制与状态"),
    ("network", "5 网络服务相关"),
    ("call", "6 呼叫控制相关"),
    ("sms", "7 短信相关"),
    ("usim", "8 USIM与安全"),
    ("extension", "9 扩展命令"),
    ("monitor", "状态监控"),
    ("other", "其他"),
]

CATEGORY_LABELS: Dict[str, str] = dict(CATEGORY_DEFS)


def label_for(category_id: str) -> str:
    """返回类型 id 对应的中文标签；未知 id 原样返回。"""
    return CATEGORY_LABELS.get(category_id, category_id or "其他")
