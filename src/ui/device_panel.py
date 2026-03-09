# -*- coding: utf-8 -*-
"""设备选择区域"""
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import pyqtSignal


class DevicePanel(QWidget):
    """设备下拉框与刷新按钮"""
    device_selected = pyqtSignal(str)
    refresh_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        self._combo = QComboBox()
        self._combo.setMinimumWidth(260)
        self._combo.setEditable(False)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self._combo)

        self._refresh_btn = QPushButton("刷新设备")
        self._refresh_btn.clicked.connect(self.refresh_clicked.emit)
        layout.addWidget(self._refresh_btn)

        layout.addStretch()

    def set_devices(self, devices: list):
        """设置设备列表"""
        self._combo.blockSignals(True)
        self._combo.clear()
        if not devices:
            self._combo.addItem("无设备", None)
        else:
            for dev in devices:
                self._combo.addItem(dev, dev)
        self._combo.blockSignals(False)
        self._on_selection_changed()

    def get_selected_device(self):
        """获取当前选中的设备 ID，无设备时返回 None"""
        data = self._combo.currentData()
        return data if data else None

    def _on_selection_changed(self):
        self.device_selected.emit(self.get_selected_device() or "")
