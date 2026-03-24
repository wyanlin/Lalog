# -*- coding: utf-8 -*-
"""LynxLog 程序入口"""
import os
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from src.ui.main_window import MainWindow


def _icon_path():
    """返回应用图标路径"""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources", "icon.png")


def main():
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("LynxLog")
    app.setApplicationDisplayName("LynxLog - Android 日志分析")
    icon_path = _icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
