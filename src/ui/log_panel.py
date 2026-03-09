# -*- coding: utf-8 -*-
"""日志显示区域"""
from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QTextCursor


class LogPanel(QWidget):
    """日志文本显示、追加、彩色高亮、滚动"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._edit = QTextEdit()
        self._edit.setReadOnly(True)
        self._edit.setFont(QFont("Consolas", 9))
        layout.addWidget(self._edit)

    def append_line(self, line: str, color=None):
        """
        追加一行日志并滚动到底部。

        Args:
            line: 日志内容
            color: QColor，若提供则整行使用该颜色，否则使用默认黑色
        """
        cursor = self._edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        if color and color.isValid():
            fmt.setForeground(color)
        cursor.insertText(line + "\n", fmt)
        scrollbar = self._edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        """清空日志"""
        self._edit.clear()
