# -*- coding: utf-8 -*-
"""开始/停止抓取按钮区域"""
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import pyqtSignal


class ControlPanel(QWidget):
    """开始抓取、停止抓取、清除日志按钮"""
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        self._start_btn = QPushButton("开始抓取")
        self._start_btn.clicked.connect(self.start_clicked.emit)
        layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("停止抓取")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self._stop_btn)

        self._clear_btn = QPushButton("清除")
        self._clear_btn.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(self._clear_btn)

        layout.addStretch()

    def set_capturing(self, capturing: bool):
        """根据抓取状态更新按钮"""
        self._start_btn.setEnabled(not capturing)
        self._stop_btn.setEnabled(capturing)
