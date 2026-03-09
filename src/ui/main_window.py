# -*- coding: utf-8 -*-
"""主窗口"""
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from ..app_settings import get_log_background_color

from ..adb_manager import AdbManager
from ..log_filter import LogFilter
from .device_panel import DevicePanel
from .log_panel import LogPanel
from .control_panel import ControlPanel
from .highlight_panel import HighlightPanel
from .settings_dialog import SettingsDialog
from .about_dialog import AboutDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._adb_manager = AdbManager(self)
        self._setup_ui()
        self._connect_signals()
        self._refresh_devices()

    def _setup_ui(self):
        self.setWindowTitle("LynxLog - Android 日志分析")

        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            w, h = geom.width(), geom.height()
            default_w = max(1000, int(w * 0.55))
            default_h = max(600, int(h * 0.6))
            self.setMinimumSize(max(900, int(w * 0.35)), max(500, int(h * 0.35)))
            self.resize(default_w, default_h)
        else:
            self.setMinimumSize(900, 500)
            self.resize(1100, 650)

        self._setup_toolbar()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setSpacing(12)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        self._device_panel = DevicePanel()
        self._control_panel = ControlPanel()
        first_row_layout.addWidget(self._device_panel)
        first_row_layout.addWidget(self._control_panel)
        layout.addWidget(first_row)

        self._log_panel = LogPanel()
        self._log_panel.set_background_color(get_log_background_color())
        layout.addWidget(self._log_panel, 1)

        self.setCentralWidget(central)
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")

        self._settings_dialog = SettingsDialog(self)
        self._filter_panel = self._settings_dialog.get_filter_panel()
        self._highlight_panel = self._settings_dialog.get_highlight_panel()
        self._settings_dialog.log_background_color_changed.connect(
            self._log_panel.set_background_color
        )

        self._about_dialog = AboutDialog(self)

    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._on_settings_clicked)
        toolbar.addAction(settings_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about_clicked)
        toolbar.addAction(about_action)

    def _on_settings_clicked(self):
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def _on_about_clicked(self):
        self._about_dialog.exec_()

    def _connect_signals(self):
        self._device_panel.refresh_clicked.connect(self._refresh_devices)
        self._device_panel.device_selected.connect(self._on_device_selected)
        self._control_panel.start_clicked.connect(self._on_start_clicked)
        self._control_panel.stop_clicked.connect(self._on_stop_clicked)
        self._control_panel.clear_clicked.connect(self._log_panel.clear)
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
