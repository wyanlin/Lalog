# -*- coding: utf-8 -*-
"""主窗口"""
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..adb_manager import AdbManager
from ..log_filter import LogFilter
from .device_panel import DevicePanel
from .filter_panel import FilterPanel
from .log_panel import LogPanel
from .control_panel import ControlPanel
from .highlight_panel import HighlightPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._adb_manager = AdbManager(self)
        self._setup_ui()
        self._connect_signals()
        self._refresh_devices()

    def _setup_ui(self):
        self.setWindowTitle("LynxLog - Android 日志分析")
        self.setMinimumSize(800, 500)
        self.resize(1000, 600)

        central = QWidget()
        layout = QVBoxLayout(central)

        toolbar = QWidget()
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        self._device_panel = DevicePanel()
        self._control_panel = ControlPanel()
        first_row_layout.addWidget(self._device_panel)
        first_row_layout.addWidget(self._control_panel)
        toolbar_layout.addWidget(first_row)

        self._filter_panel = FilterPanel()
        toolbar_layout.addWidget(self._filter_panel)

        self._highlight_panel = HighlightPanel()
        toolbar_layout.addWidget(self._highlight_panel)

        layout.addWidget(toolbar)
        self._log_panel = LogPanel()
        layout.addWidget(self._log_panel)

        self.setCentralWidget(central)
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")

    def _connect_signals(self):
        self._device_panel.refresh_clicked.connect(self._refresh_devices)
        self._device_panel.device_selected.connect(self._on_device_selected)
        self._control_panel.start_clicked.connect(self._on_start_clicked)
        self._control_panel.stop_clicked.connect(self._on_stop_clicked)
        self._adb_manager.line_received.connect(self._on_line_received)
        self._adb_manager.logcat_finished.connect(self._on_logcat_finished)

    def _refresh_devices(self):
        devices = self._adb_manager.get_devices()
        self._device_panel.set_devices(devices)
        if devices:
            self._status_bar.showMessage(f"已发现 {len(devices)} 台设备")
        else:
            self._status_bar.showMessage("未发现设备，请连接 Android 设备并开启 USB 调试")
        self._update_start_button_state()

    def _on_device_selected(self, device_id: str):
        self._update_start_button_state()

    def _update_start_button_state(self):
        has_device = bool(self._device_panel.get_selected_device())
        capturing = self._adb_manager.is_capturing()
        self._control_panel._start_btn.setEnabled(has_device and not capturing)

    def _on_start_clicked(self):
        device_id = self._device_panel.get_selected_device()
        if not device_id:
            QMessageBox.warning(self, "提示", "请先选择设备")
            return
        self._log_panel.clear()
        if self._adb_manager.start_logcat(device_id):
            self._control_panel.set_capturing(True)
            self._status_bar.showMessage(f"正在抓取设备 {device_id} 的日志...")
        else:
            QMessageBox.warning(self, "错误", "启动 logcat 失败")

    def _on_stop_clicked(self):
        self._adb_manager.stop_logcat()
        self._status_bar.showMessage("已停止抓取")

    def _resolve_highlight_color(self, line: str):
        """根据高亮规则返回匹配的颜色，无匹配返回 None"""
        for keyword, color in self._highlight_panel.get_rules():
            if keyword and keyword.lower() in line.lower():
                return color
        return None

    def _on_line_received(self, line: str):
        keyword, case_sensitive, use_regex = self._filter_panel.get_filter()
        if LogFilter.matches(line, keyword, case_sensitive, use_regex):
            color = self._resolve_highlight_color(line)
            self._log_panel.append_line(line, color)

    def _on_logcat_finished(self, success: bool, message: str):
        self._control_panel.set_capturing(False)
        self._update_start_button_state()
        if success:
            self._status_bar.showMessage("抓取已结束")
        else:
            self._status_bar.showMessage(f"抓取异常: {message}")
            QMessageBox.warning(self, "错误", f"logcat 异常退出: {message}")
