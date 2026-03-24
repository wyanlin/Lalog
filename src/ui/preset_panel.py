# -*- coding: utf-8 -*-
"""配置预设面板"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..app_settings import get_log_background_color, set_log_background_color
from ..config_preset import (
    apply_config_to_panels,
    config_from_panels,
    delete_preset,
    load_presets,
    save_preset,
)


class PresetPanel(QWidget):
    """一键保存/加载配置预设"""
    preset_applied = pyqtSignal(dict)

    def __init__(self, filter_panel, highlight_panel, parent=None):
        super().__init__(parent)
        self._filter_panel = filter_panel
        self._highlight_panel = highlight_panel
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(
            QLabel("配置预设（保存/加载 筛选条件 + 高亮规则 + 日志背景色）：")
        )
        row = QHBoxLayout()
        row.addWidget(QLabel("预设："))
        self._combo = QComboBox()
        self._combo.setMinimumWidth(180)
        self._combo.setEditable(False)
        row.addWidget(self._combo)

        self._apply_btn = QPushButton("应用")
        self._apply_btn.clicked.connect(self._on_apply)
        row.addWidget(self._apply_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.setToolTip("覆盖选中的预设，未选中则创建新预设")
        self._save_btn.clicked.connect(self._on_save)
        row.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("另存为")
        self._save_as_btn.setToolTip("以新名称保存当前配置")
        self._save_as_btn.clicked.connect(self._on_save_as)
        row.addWidget(self._save_as_btn)

        self._delete_btn = QPushButton("删除")
        self._delete_btn.clicked.connect(self._on_delete)
        row.addWidget(self._delete_btn)

        row.addStretch()
        layout.addLayout(row)

        self._refresh_combo()

    def _refresh_combo(self):
        presets = load_presets()
        names = sorted(presets.keys())
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem("-- 选择预设 --", None)
        for name in names:
            self._combo.addItem(name, name)
        self._combo.blockSignals(False)

    def _on_apply(self):
        name = self._combo.currentData()
        if not name:
            QMessageBox.information(self, "提示", "请先选择要应用的预设")
            return
        presets = load_presets()
        if name not in presets:
            QMessageBox.warning(self, "错误", f"预设「{name}」不存在")
            return
        config = presets[name]
        apply_config_to_panels(config, self._filter_panel, self._highlight_panel)
        if "log_background_color" in config:
            set_log_background_color(config["log_background_color"])
        self.preset_applied.emit(config)

    def _on_save(self):
        """保存：选中预设则覆盖，未选中则提示输入名称创建"""
        name = self._combo.currentData()
        if name:
            reply = QMessageBox.question(
                self,
                "覆盖保存",
                f"确定用当前配置覆盖预设「{name}」吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        else:
            name, ok = QInputDialog.getText(self, "保存预设", "请输入预设名称：")
            if not ok or not name.strip():
                return
            name = name.strip()
        try:
            log_bg = get_log_background_color()
            config = config_from_panels(
                self._filter_panel,
                self._highlight_panel,
                log_background_color=log_bg,
            )
            save_preset(name, config)
            self._refresh_combo()
            idx = self._combo.findData(name)
            if idx >= 0:
                self._combo.setCurrentIndex(idx)
            QMessageBox.information(self, "提示", f"已保存预设「{name}」")
        except RuntimeError as e:
            QMessageBox.warning(self, "错误", str(e))

    def _on_save_as(self):
        """另存为：始终提示输入名称，若已存在则确认后覆盖"""
        name, ok = QInputDialog.getText(
            self, "另存为", "请输入预设名称：", text=self._combo.currentData() or ""
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        presets = load_presets()
        if name in presets:
            reply = QMessageBox.question(
                self,
                "覆盖确认",
                f"预设「{name}」已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        try:
            log_bg = get_log_background_color()
            config = config_from_panels(
                self._filter_panel,
                self._highlight_panel,
                log_background_color=log_bg,
            )
            save_preset(name, config)
            self._refresh_combo()
            idx = self._combo.findData(name)
            if idx >= 0:
                self._combo.setCurrentIndex(idx)
            QMessageBox.information(self, "提示", f"已保存预设「{name}」")
        except RuntimeError as e:
            QMessageBox.warning(self, "错误", str(e))

    def _on_delete(self):
        name = self._combo.currentData()
        if not name:
            QMessageBox.information(self, "提示", "请先选择要删除的预设")
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除预设「{name}」吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            delete_preset(name)
            self._refresh_combo()
            QMessageBox.information(self, "提示", f"已删除预设「{name}」")
        except RuntimeError as e:
            QMessageBox.warning(self, "错误", str(e))
