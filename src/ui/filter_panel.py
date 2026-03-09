# -*- coding: utf-8 -*-
"""筛选设置区域"""
from PyQt5.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import pyqtSignal


class FilterPanel(QWidget):
    """关键字输入、匹配大小写、正则表达式勾选"""
    filter_changed = pyqtSignal(str, bool, bool)  # keyword, case_sensitive, use_regex

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        options_layout = QHBoxLayout()
        self._case_check = QCheckBox("匹配大小写")
        self._case_check.stateChanged.connect(self._emit_filter)
        options_layout.addWidget(self._case_check)

        self._regex_check = QCheckBox("正则表达式")
        self._regex_check.stateChanged.connect(self._emit_filter)
        options_layout.addWidget(self._regex_check)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("关键字："))
        self._keyword_edit = QLineEdit()
        self._keyword_edit.setPlaceholderText("输入关键字，留空则显示全部")
        self._keyword_edit.textChanged.connect(self._emit_filter)
        keyword_layout.addWidget(self._keyword_edit)
        layout.addLayout(keyword_layout)

    def get_filter(self):
        """返回 (keyword, case_sensitive, use_regex)"""
        return (
            self._keyword_edit.text().strip(),
            self._case_check.isChecked(),
            self._regex_check.isChecked(),
        )

    def _emit_filter(self):
        self.filter_changed.emit(*self.get_filter())
