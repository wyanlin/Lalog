# -*- coding: utf-8 -*-
"""应用级设置持久化"""
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QColor

_KEY_LOG_BG = "log_background_color"
_DEFAULT_LOG_BG = "#1e1e1e"  # 深色背景，便于长时间看日志


def get_log_background_color():
    """获取日志背景色，默认深色"""
    s = QSettings("LynxLog", "LynxLog")
    val = s.value(_KEY_LOG_BG, _DEFAULT_LOG_BG)
    if isinstance(val, QColor):
        return val
    return QColor(val) if val else QColor(_DEFAULT_LOG_BG)


def set_log_background_color(color):
    """保存日志背景色"""
    s = QSettings("LynxLog", "LynxLog")
    s.setValue(_KEY_LOG_BG, color.name() if hasattr(color, "name") else str(color))
