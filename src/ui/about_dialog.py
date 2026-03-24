# -*- coding: utf-8 -*-
"""关于对话框"""
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

from ..version import __version__


class AboutDialog(QDialog):
    """关于 LynxLog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 LynxLog")
        self.setFixedSize(320, 180)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("LynxLog"))
        layout.addWidget(QLabel("Android 日志分析工具"))
        layout.addWidget(QLabel(f"版本：{__version__}"))
        layout.addStretch()
