# -*- coding: utf-8 -*-
"""
CPSTATE 规则专属辅助函数。
主规则定义在 config/base.json；解码器在 decoders/registry.py。
此模块保留函数入口供其他代码直接调用（向后兼容）。
"""
from ..decoders.registry import decode


def format_signal_state_display(raw: str) -> str:
    """将 signal_state 原始值格式化为展示字符串（文档范围 -90～-130 dBm）。"""
    return decode("signal_state_range", raw)
