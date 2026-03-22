# -*- coding: utf-8 -*-
"""
图表对话框：对 ParsedAtRecord 列表的数值列做折线/散点图。
依赖 matplotlib（可选）；未安装时显示安装提示。
"""
from __future__ import annotations

from typing import List

from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .types import ParsedAtRecord

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
    from matplotlib.figure import Figure
    _MPL_OK = True
except ImportError:
    _MPL_OK = False


def _to_float(s: str):
    try:
        return float(s.strip())
    except (ValueError, AttributeError):
        return None


class ChartDialog(QDialog):
    """
    图表对话框，接受已过滤的 ParsedAtRecord 列表。
    - X 轴：「时间」（尝试解析日志时间字段）或「行序」（记录在列表中的顺序）
    - Y 轴：所有出现过的数值列（numeric=True 的列，或原始值可解析为 float 的列）
    """

    def __init__(self, records: List[ParsedAtRecord], parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("图表")
        self.resize(900, 560)
        self._records = records
        self._setup_ui()

    # ── 构建 UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        if not _MPL_OK:
            layout.addWidget(QLabel(
                "未检测到 matplotlib。\n"
                "请在命令行执行：pip install matplotlib\n"
                "安装后重启程序即可使用图表功能。"
            ))
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(self.close)
            layout.addWidget(close_btn)
            return

        # 控制栏
        ctrl = QWidget()
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(8)

        ctrl_layout.addWidget(QLabel("X 轴:"))
        self._x_combo = QComboBox()
        self._x_combo.addItem("时间", "time")
        self._x_combo.addItem("行序", "index")
        ctrl_layout.addWidget(self._x_combo)

        ctrl_layout.addWidget(QLabel("Y 轴:"))
        self._y_combo = QComboBox()
        self._populate_y_combo()
        ctrl_layout.addWidget(self._y_combo)

        ctrl_layout.addWidget(QLabel("分组:"))
        self._group_combo = QComboBox()
        self._group_combo.addItem("不分组", "none")
        self._group_combo.addItem("按 TAG", "tag")
        self._group_combo.addItem("按规则", "rule_id")
        ctrl_layout.addWidget(self._group_combo)

        update_btn = QPushButton("更新图表")
        update_btn.clicked.connect(self._plot)
        ctrl_layout.addWidget(update_btn)
        ctrl_layout.addStretch()
        layout.addWidget(ctrl)

        # matplotlib canvas
        self._fig = Figure(figsize=(9, 5), tight_layout=True)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas, 1)

        if self._y_combo.count() > 0:
            self._plot()

    def _populate_y_combo(self):
        """扫描所有记录，收集可作为 Y 轴的列。"""
        seen: dict = {}  # key -> label
        for rec in self._records:
            for col_def in rec.column_defs:
                if col_def.key in seen:
                    continue
                if col_def.numeric:
                    seen[col_def.key] = col_def.label
                    continue
                # 非 numeric 声明时，检查 raw_columns 是否可解析为 float
                raw = rec.raw_columns.get(col_def.key, "")
                if _to_float(raw) is not None:
                    seen[col_def.key] = col_def.label
        for key, label in seen.items():
            self._y_combo.addItem(label, key)

    # ── 绘图 ────────────────────────────────────────────────────────────────────

    def _plot(self):
        if not _MPL_OK or self._y_combo.count() == 0:
            return

        x_mode: str = self._x_combo.currentData()
        y_key: str = self._y_combo.currentData()
        group_by: str = self._group_combo.currentData()
        y_label: str = self._y_combo.currentText()

        # 分组
        groups: dict = {}
        for idx, rec in enumerate(self._records):
            raw_y = rec.raw_columns.get(y_key, "")
            y_val = _to_float(raw_y)
            if y_val is None:
                continue
            group_key = (
                rec.tag if group_by == "tag"
                else rec.rule_id if group_by == "rule_id"
                else "全部"
            )
            if group_key not in groups:
                groups[group_key] = ([], [])
            # X 轴值
            if x_mode == "time":
                x_val = rec.time_str or str(idx)
            else:
                x_val = idx
            groups[group_key][0].append(x_val)
            groups[group_key][1].append(y_val)

        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.set_title(y_label)
        ax.set_ylabel(y_label)
        ax.set_xlabel("时间" if x_mode == "time" else "行序")

        for gname, (xs, ys) in groups.items():
            ax.plot(xs, ys, marker=".", markersize=3, linewidth=1, label=gname)

        if x_mode == "time" and groups:
            # 只显示部分 X tick 避免过密
            ax.figure.autofmt_xdate(rotation=30)
            all_xs = next(iter(groups.values()))[0]
            if len(all_xs) > 20:
                step = max(1, len(all_xs) // 15)
                ax.set_xticks(all_xs[::step])

        if len(groups) > 1:
            ax.legend(fontsize=8)

        self._canvas.draw()
