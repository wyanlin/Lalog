# -*- coding: utf-8 -*-
"""高亮规则配置区域"""
from PyQt5.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal


class HighlightPanel(QWidget):
    """关键字-颜色高亮规则配置"""
    rules_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("高亮规则（关键字 → 颜色，匹配整行显示对应颜色）："))
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["关键字", "颜色", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.setMinimumHeight(200)
        self._table.setMaximumHeight(350)
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("添加规则")
        self._add_btn.clicked.connect(self._add_rule)
        btn_layout.addWidget(self._add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _add_rule(self):
        color = QColorDialog.getColor(QColor(255, 200, 0), self, "选择颜色")
        if color.isValid():
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(""))
            color_btn = QPushButton(color.name())
            color_btn.setStyleSheet(
                f"background-color: {color.name()}; "
                f"color: {'white' if color.lightness() < 128 else 'black'}"
            )
            color_btn.clicked.connect(self._on_pick_color_clicked)
            self._table.setCellWidget(row, 1, color_btn)
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(self._on_delete_clicked)
            self._table.setCellWidget(row, 2, del_btn)
            self.rules_changed.emit()

    def _on_pick_color_clicked(self):
        btn = self.sender()
        if not btn:
            return
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 1) is btn:
                try:
                    old_color = QColor(btn.text())
                except Exception:
                    old_color = QColor("black")
                color = QColorDialog.getColor(old_color, self, "选择颜色")
                if color.isValid():
                    btn.setText(color.name())
                    btn.setStyleSheet(
                        f"background-color: {color.name()}; "
                        f"color: {'white' if color.lightness() < 128 else 'black'}"
                    )
                    self.rules_changed.emit()
                return

    def _on_delete_clicked(self):
        btn = self.sender()
        if not btn:
            return
        for row in range(self._table.rowCount()):
            if self._table.cellWidget(row, 2) is btn:
                self._table.removeRow(row)
                self.rules_changed.emit()
                return

    def get_rules(self):
        """返回 [(keyword, QColor), ...]，按顺序，仅返回非空关键字"""
        result = []
        for row in range(self._table.rowCount()):
            kw_item = self._table.item(row, 0)
            keyword = kw_item.text().strip() if kw_item else ""
            if not keyword:
                continue
            color_btn = self._table.cellWidget(row, 1)
            if color_btn:
                try:
                    color = QColor(color_btn.text())
                except Exception:
                    color = QColor("black")
            else:
                color = QColor("black")
            result.append((keyword, color))
        return result

    def set_rules(self, rules):
        """
        设置高亮规则，清空后填充。
        rules: [(keyword, QColor), ...] 或 [(keyword, str), ...]，str 为颜色名如 #ff0000
        """
        self._table.setRowCount(0)
        for keyword, color in rules:
            if not keyword:
                continue
            if isinstance(color, str):
                color = QColor(color)
            if not color.isValid():
                color = QColor("black")
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(keyword))
            color_btn = QPushButton(color.name())
            color_btn.setStyleSheet(
                f"background-color: {color.name()}; "
                f"color: {'white' if color.lightness() < 128 else 'black'}"
            )
            color_btn.clicked.connect(self._on_pick_color_clicked)
            self._table.setCellWidget(row, 1, color_btn)
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(self._on_delete_clicked)
            self._table.setCellWidget(row, 2, del_btn)
        self.rules_changed.emit()
