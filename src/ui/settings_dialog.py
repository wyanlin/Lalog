# -*- coding: utf-8 -*-
"""设置对话框"""
from PyQt5.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor

from ..app_settings import get_log_background_color, set_log_background_color
from .filter_panel import FilterPanel
from .highlight_panel import HighlightPanel
from .preset_panel import PresetPanel


class SettingsDialog(QDialog):
    """筛选与高亮设置弹窗"""
    log_background_color_changed = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")

        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            w, h = geom.width(), geom.height()
            min_w = max(520, int(w * 0.3))
            min_h = max(520, int(h * 0.35))
            self.setMinimumSize(min_w, min_h)
            self.resize(max(580, int(w * 0.4)), max(600, int(h * 0.45)))
        else:
            self.setMinimumSize(520, 520)
            self.resize(600, 620)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        self._filter_panel = FilterPanel(self)
        self._highlight_panel = HighlightPanel(self)
        self._preset_panel = PresetPanel(self._filter_panel, self._highlight_panel, self)
        self._preset_panel.preset_applied.connect(self._on_preset_applied)
        layout.addWidget(self._preset_panel)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        layout.addWidget(self._filter_panel)
        layout.addWidget(self._highlight_panel)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep2)

        appearance_layout = QHBoxLayout()
        appearance_layout.addWidget(QLabel("日志区域背景色："))
        self._log_bg_btn = QPushButton()
        self._log_bg_btn.setFixedWidth(100)
        self._log_bg_btn.clicked.connect(self._on_pick_log_bg_color)
        self._update_log_bg_button()
        appearance_layout.addWidget(self._log_bg_btn)
        appearance_layout.addStretch()
        layout.addLayout(appearance_layout)

    def _update_log_bg_button(self):
        color = get_log_background_color()
        if isinstance(color, str):
            color = QColor(color)
        self._log_bg_btn.setText(color.name())
        self._log_bg_btn.setStyleSheet(
            f"background-color: {color.name()}; "
            f"color: {'white' if color.lightness() < 128 else 'black'}"
        )

    def _on_preset_applied(self, config):
        """预设应用后，若包含背景色则同步到 UI 并通知主窗口"""
        if "log_background_color" in config:
            self._update_log_bg_button()
            self.log_background_color_changed.emit(
                QColor(config["log_background_color"])
            )

    def _on_pick_log_bg_color(self):
        color = get_log_background_color()
        if hasattr(color, "name"):
            old = color
        else:
            old = QColor(color)
        new_color = QColorDialog.getColor(old, self, "选择日志背景色")
        if new_color.isValid():
            set_log_background_color(new_color)
            self._update_log_bg_button()
            self.log_background_color_changed.emit(new_color)

    def get_filter_panel(self):
        return self._filter_panel

    def get_highlight_panel(self):
        return self._highlight_panel
