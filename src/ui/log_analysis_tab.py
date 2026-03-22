# -*- coding: utf-8 -*-
"""日志分析 Tab：打开文件/文件夹、搜索、卫星 AT 日志解析（可扩展方案×模组）"""
import csv
import os
import re
from typing import Dict, List

from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtGui import QColor, QFont, QKeySequence, QTextCursor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..app_settings import get_log_background_color
from ..file_loader import FileLoadWorker
from .log_analysis import ParsedAtRecord, list_modules, list_systems, parse_log, parse_log_lines
from .log_analysis.categories import CATEGORY_DEFS, label_for
from .log_analysis.chart_dialog import ChartDialog
from .log_panel import _log_font_size

# 域定义：(domain_id, 显示名称)
_DOMAINS = [
    ("status", "状态/入网"),
    ("voice",  "语音"),
    ("data",   "数据"),
]


class LogAnalysisTab(QWidget):
    """日志分析：导入文件/文件夹、搜索查找、编辑保存、AT 卫星解析。"""

    # 搜索「共 n 处」：防抖避免每键全表扫描；计数上限避免海量匹配卡死 UI
    _SEARCH_DEBOUNCE_MS = 220
    _SEARCH_COUNT_CAP = 10000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file_path = None
        self._folder_path = None
        self._load_thread = None
        self._load_worker = None
        self._chunks = []
        self._all_records: List[ParsedAtRecord] = []
        # domain -> {table, filter_edit, summary, col_keys, col_labels, records}
        self._domain_ui: Dict[str, dict] = {}
        # 搜索文本缓存：文件加载完毕后缓存全文，避免每次搜索调用 toPlainText() 产生副本
        self._search_text_cache: str = ""
        self._search_count_timer = QTimer(self)
        self._search_count_timer.setSingleShot(True)
        self._search_count_timer.timeout.connect(self._flush_search_count)
        self._setup_ui()

    # ── UI 搭建 ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)

        layout.addWidget(self._build_file_toolbar())
        layout.addWidget(self._build_analysis_bar())
        layout.addWidget(self._build_category_bar())

        # 文件列表容器
        self._file_list = QListWidget()
        self._file_list.setMinimumWidth(120)
        self._file_list.currentItemChanged.connect(self._on_file_list_selection)
        self._file_list_container = QWidget()
        fl_layout = QVBoxLayout(self._file_list_container)
        fl_layout.setContentsMargins(0, 0, 0, 0)
        fl_layout.addWidget(QLabel("文件列表"))
        fl_layout.addWidget(self._file_list)

        # 文本编辑器
        self._edit = QPlainTextEdit()
        self._edit.setReadOnly(False)
        self._edit.setFont(QFont("Consolas", _log_font_size()))
        self._apply_background_color(get_log_background_color())
        self._edit.document().contentsChanged.connect(self._on_editor_contents_changed)

        # 横向分割（文件列表 | 编辑器）
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.addWidget(self._file_list_container)
        self._splitter.addWidget(self._edit)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._file_list_container.hide()

        # 结果 TabWidget（按解析域分页）
        self._result_tabs = QTabWidget()
        for domain_id, domain_label in _DOMAINS:
            self._result_tabs.addTab(self._build_domain_tab(domain_id), domain_label)

        # 纵向分割（编辑区 | 解析结果区）
        self._outer_splitter = QSplitter(Qt.Vertical)
        self._outer_splitter.addWidget(self._splitter)
        self._outer_splitter.addWidget(self._result_tabs)
        self._outer_splitter.setStretchFactor(0, 1)
        self._outer_splitter.setStretchFactor(1, 0)
        self._outer_splitter.setSizes([480, 240])
        layout.addWidget(self._outer_splitter, 1)

        QShortcut(QKeySequence.Save, self).activated.connect(self._on_save)

    def _build_file_toolbar(self) -> QWidget:
        """文件操作 + 搜索工具栏（与原版保持一致）。"""
        toolbar = QWidget()
        toolbar.setMaximumHeight(36)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(0, 2, 0, 2)
        tl.setSpacing(6)

        self._open_file_btn = QPushButton("打开")
        self._open_file_btn.setToolTip("打开文件")
        self._open_file_btn.clicked.connect(self._on_open_file)
        tl.addWidget(self._open_file_btn)

        self._open_folder_btn = QPushButton("文件夹")
        self._open_folder_btn.setToolTip("打开文件夹")
        self._open_folder_btn.clicked.connect(self._on_open_folder)
        tl.addWidget(self._open_folder_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.setToolTip("Ctrl+S")
        self._save_btn.clicked.connect(self._on_save)
        tl.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("另存为")
        self._save_as_btn.clicked.connect(self._on_save_as)
        tl.addWidget(self._save_as_btn)

        tl.addSpacing(8)

        tl.addWidget(QLabel("查找:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("关键字 Ctrl+F")
        self._search_edit.setMaximumWidth(140)
        self._search_edit.returnPressed.connect(self._on_find_next)
        self._search_edit.textChanged.connect(self._schedule_search_count_update)
        tl.addWidget(self._search_edit)

        self._regex_check = QCheckBox("正则")
        self._regex_check.stateChanged.connect(self._schedule_search_count_update)
        tl.addWidget(self._regex_check)

        self._ignore_case_check = QCheckBox("大小写")
        self._ignore_case_check.setChecked(True)
        self._ignore_case_check.setToolTip("忽略大小写")
        self._ignore_case_check.stateChanged.connect(self._schedule_search_count_update)
        tl.addWidget(self._ignore_case_check)

        self._wrap_check = QCheckBox("循环")
        self._wrap_check.setChecked(True)
        self._wrap_check.setToolTip("循环查找")
        tl.addWidget(self._wrap_check)

        self._find_prev_btn = QPushButton("上一个")
        self._find_prev_btn.clicked.connect(self._on_find_prev)
        tl.addWidget(self._find_prev_btn)

        self._find_next_btn = QPushButton("下一个")
        self._find_next_btn.clicked.connect(self._on_find_next)
        tl.addWidget(self._find_next_btn)

        self._count_label = QLabel("")
        self._count_label.setMinimumWidth(55)
        self._count_label.setStyleSheet("color: gray; font-size: 11px;")
        tl.addWidget(self._count_label)

        self._path_label = QLabel("未打开")
        self._path_label.setStyleSheet("color: gray; font-size: 11px;")
        self._path_label.setMaximumWidth(200)
        tl.addWidget(self._path_label, 1)

        return toolbar

    def _build_analysis_bar(self) -> QWidget:
        """解析方案 + 模组选择条。"""
        bar = QWidget()
        bar.setMaximumHeight(36)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(0, 2, 0, 2)
        bl.setSpacing(6)

        bl.addWidget(QLabel("解析方案:"))
        self._system_combo = QComboBox()
        self._system_combo.setMinimumWidth(80)
        self._system_combo.setToolTip("选择卫星系统解析方案")
        for sid, sname in list_systems():
            self._system_combo.addItem(sname, sid)
        self._system_combo.currentIndexChanged.connect(self._on_system_changed)
        bl.addWidget(self._system_combo)

        bl.addWidget(QLabel("模组:"))
        self._module_combo = QComboBox()
        self._module_combo.setMinimumWidth(70)
        self._module_combo.setToolTip("选择芯片/模组（通用=默认规则集）")
        bl.addWidget(self._module_combo)

        self._parse_btn = QPushButton("解析")
        self._parse_btn.setToolTip("按当前方案 + 模组重新解析 AT 日志")
        self._parse_btn.clicked.connect(self._on_parse_clicked)
        bl.addWidget(self._parse_btn)

        bl.addStretch()
        hint = QLabel("切换方案/模组后点「解析」更新结果")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        bl.addWidget(hint)

        self._refresh_module_combo()
        return bar

    def _build_category_bar(self) -> QWidget:
        """手册章节类型：勾选要显示的 AT 解析结果（与各行 rule_category 对应）。"""
        bar = QWidget()
        bar.setMaximumHeight(72)
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(2)

        bl = QHBoxLayout()
        bl.setSpacing(4)
        bl.addWidget(QLabel("显示手册分类:"))
        self._category_checks = {}
        for cid, clabel in CATEGORY_DEFS:
            cb = QCheckBox(clabel)
            cb.setChecked(True)
            cb.setToolTip(
                f"勾选：显示手册章节「{clabel}」对应的解析行；"
                f"取消：隐藏该类。"
                f"若「类型」列几乎全是「状态监控」，多为日志里命中 ^CPSTATE，或此处只勾选了状态监控。"
            )
            cb.stateChanged.connect(lambda _s: self._on_category_filter_changed())
            self._category_checks[cid] = cb
            bl.addWidget(cb)

        btn_all = QPushButton("全选")
        btn_all.setToolTip("勾选全部类型")
        btn_all.clicked.connect(self._category_select_all)
        bl.addWidget(btn_all)

        btn_none = QPushButton("全不选")
        btn_none.setToolTip("取消全部类型（表格为空）")
        btn_none.clicked.connect(self._category_select_none)
        bl.addWidget(btn_none)
        bl.addStretch()
        outer.addLayout(bl)

        hint = QLabel(
            "说明：未勾选的分类会隐藏对应行（与 Tab 内「过滤」叠加）。"
            "「类型」列来自每条命中的规则所属手册章节；若几乎全是「状态监控」，说明解析命中多为 cpstate（^CPSTATE:）规则。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 11px;")
        outer.addWidget(hint)
        return bar

    def _category_select_all(self):
        for cb in self._category_checks.values():
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
        self._on_category_filter_changed()

    def _category_select_none(self):
        for cb in self._category_checks.values():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self._on_category_filter_changed()

    def _on_category_filter_changed(self):
        for domain_id, _ in _DOMAINS:
            ui = self._domain_ui.get(domain_id)
            if ui:
                self._apply_filter(domain_id, ui["filter_edit"].text())

    def _is_category_visible(self, rule_category: str) -> bool:
        cid = rule_category if rule_category in self._category_checks else "other"
        cb = self._category_checks.get(cid)
        return bool(cb.isChecked()) if cb else True

    def _build_domain_tab(self, domain_id: str) -> QWidget:
        """构建单个解析域（status/voice/data）的 Tab 页。"""
        widget = QWidget()
        vl = QVBoxLayout(widget)
        vl.setContentsMargins(2, 4, 2, 2)
        vl.setSpacing(4)

        # 控制行
        ctrl = QWidget()
        ctrl.setMaximumHeight(30)
        cl = QHBoxLayout(ctrl)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        cl.addWidget(QLabel("过滤:"))
        filter_edit = QLineEdit()
        filter_edit.setPlaceholderText("任意关键字实时过滤行")
        filter_edit.setMaximumWidth(200)
        cl.addWidget(filter_edit)

        summary_label = QLabel("未解析")
        summary_label.setStyleSheet("color: gray; font-size: 11px;")
        cl.addWidget(summary_label)

        cl.addStretch()

        csv_btn = QPushButton("导出 CSV")
        csv_btn.setToolTip("将过滤后可见行导出为 CSV（UTF-8 BOM）")
        cl.addWidget(csv_btn)

        excel_btn = QPushButton("导出 Excel")
        excel_btn.setToolTip("将过滤后可见行导出为 .xlsx（需安装 openpyxl）")
        cl.addWidget(excel_btn)

        chart_btn = QPushButton("图表")
        chart_btn.setToolTip("对过滤后可见行的数值列生成图表")
        cl.addWidget(chart_btn)

        vl.addWidget(ctrl)

        # 数据表格
        table = QTableWidget(0, 0)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setFont(QFont("Consolas", max(9, _log_font_size() - 1)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        vl.addWidget(table, 1)

        self._domain_ui[domain_id] = {
            "table": table,
            "filter_edit": filter_edit,
            "summary": summary_label,
            "col_keys": [],
            "col_labels": [],
            "records": [],
        }

        filter_edit.textChanged.connect(
            lambda text, d=domain_id: self._apply_filter(d, text)
        )
        table.cellDoubleClicked.connect(
            lambda row, _col, d=domain_id: self._on_table_double_click(d, row)
        )
        csv_btn.clicked.connect(lambda _=False, d=domain_id: self._export_csv(d))
        excel_btn.clicked.connect(lambda _=False, d=domain_id: self._export_excel(d))
        chart_btn.clicked.connect(lambda _=False, d=domain_id: self._show_chart(d))

        return widget

    # ── 方案/模组组合框 ──────────────────────────────────────────────────────────

    def _on_system_changed(self):
        self._refresh_module_combo()

    def _refresh_module_combo(self):
        self._module_combo.blockSignals(True)
        self._module_combo.clear()
        sid = self._system_combo.currentData() or ""
        for mid, mname in list_modules(sid):
            self._module_combo.addItem(mname, mid)
        self._module_combo.blockSignals(False)

    def _current_system_id(self) -> str:
        return self._system_combo.currentData() or ""

    def _current_module_id(self) -> str:
        return self._module_combo.currentData() or "generic"

    # ── 解析 ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _iter_lines_from_chunks(chunks: list):
        """
        将分块字符串列表按行产出，正确处理跨块的行边界。
        使用生成器避免 ''.join(chunks) + splitlines() 带来的双份内存峰值。
        """
        leftover = ""
        for chunk in chunks:
            data = leftover + chunk
            last_nl = data.rfind("\n")
            if last_nl == -1:
                leftover = data
            else:
                for line in data[: last_nl].splitlines():
                    yield line
                leftover = data[last_nl + 1 :]
        if leftover:
            yield leftover

    def _on_editor_contents_changed(self):
        """编辑器内容变化时，失效搜索文本缓存（保证搜索结果实时准确）。"""
        self._search_text_cache = ""

    def _on_parse_clicked(self):
        # 优先使用已缓存文本（文件加载后设置），避免 toPlainText() 额外复制
        text = self._search_text_cache or self._edit.toPlainText()
        if not text:
            return
        self._run_parse(text)

    def _run_parse(self, source):
        """
        source 可以是：
          - str：直接使用 parse_log（来自 toPlainText 或缓存）
          - Iterable[str]：行迭代器，使用 parse_log_lines（来自加载时的 chunks）
        """
        sid = self._current_system_id()
        mid = self._current_module_id()
        if not sid:
            return
        if isinstance(source, str):
            records = parse_log(source, sid, mid)
        else:
            records = parse_log_lines(source, sid, mid)
        self._all_records = records
        self._fill_results(records)

    def _fill_results(self, records: List[ParsedAtRecord]):
        """按域分组，填入各 Tab 表格。"""
        for domain_id, _ in _DOMAINS:
            domain_recs = [r for r in records if r.domain == domain_id]
            self._fill_domain_table(domain_id, domain_recs)

    def _fill_domain_table(self, domain_id: str, records: List[ParsedAtRecord]):
        ui = self._domain_ui[domain_id]
        table: QTableWidget = ui["table"]
        ui["records"] = records

        if not records:
            ui["col_keys"] = []
            ui["col_labels"] = []
            table.setRowCount(0)
            table.setColumnCount(0)
            sid = self._current_system_id()
            ui["summary"].setText("0 条（当前方案/模组下无此域记录）" if sid else "未解析")
            return

        # 按出现顺序收集所有列 key
        seen_keys: dict = {}
        seen_labels: dict = {}
        for rec in records:
            for cd in rec.column_defs:
                if cd.key not in seen_keys:
                    seen_keys[cd.key] = True
                    seen_labels[cd.key] = cd.label
        col_keys = list(seen_keys.keys())
        col_labels = [seen_labels[k] for k in col_keys]
        ui["col_keys"] = col_keys
        ui["col_labels"] = col_labels

        std_hdrs = ["行号", "时间", "TAG", "规则", "类型"]
        all_hdrs = std_hdrs + col_labels + ["原始行"]
        raw_col_idx = len(std_hdrs) + len(col_keys)

        table.setUpdatesEnabled(False)
        table.setRowCount(len(records))
        table.setColumnCount(len(all_hdrs))
        table.setHorizontalHeaderLabels(all_hdrs)

        for row, rec in enumerate(records):
            raw_display = rec.raw_line[:160] + "…" if len(rec.raw_line) > 160 else rec.raw_line
            cells = [
                str(rec.line_no),
                rec.time_str,
                rec.tag,
                rec.rule_id,
                label_for(rec.rule_category),
            ]
            for key in col_keys:
                cells.append(rec.columns.get(key, ""))
            cells.append(raw_display)
            for col, cell_text in enumerate(cells):
                it = QTableWidgetItem(cell_text)
                if col == 0:
                    it.setData(Qt.UserRole, rec.line_no)
                table.setItem(row, col, it)

        table.setUpdatesEnabled(True)
        table.horizontalHeader().setSectionResizeMode(raw_col_idx, QHeaderView.Stretch)
        for c in range(raw_col_idx):
            table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)

        ui["summary"].setText(f"共 {len(records)} 条")
        self._apply_filter(domain_id, ui["filter_edit"].text())

    # ── 过滤 ─────────────────────────────────────────────────────────────────────

    def _apply_filter(self, domain_id: str, text: str):
        ui = self._domain_ui[domain_id]
        table: QTableWidget = ui["table"]
        records: List[ParsedAtRecord] = ui["records"]
        needle = text.strip().lower()
        visible = 0
        total = table.rowCount()
        for row in range(total):
            if row < len(records) and not self._is_category_visible(records[row].rule_category):
                table.hideRow(row)
                continue
            if not needle:
                table.showRow(row)
                visible += 1
            else:
                matched = any(
                    (table.item(row, c) and needle in table.item(row, c).text().lower())
                    for c in range(table.columnCount())
                )
                if matched:
                    table.showRow(row)
                    visible += 1
                else:
                    table.hideRow(row)
        n_total = len(ui["records"])
        if n_total == 0:
            ui["summary"].setText(
                "0 条（当前方案/模组下无此域记录）" if self._current_system_id() else "未解析"
            )
        elif needle:
            ui["summary"].setText(f"共 {n_total} 条，过滤后 {visible} 条")
        else:
            ui["summary"].setText(f"共 {n_total} 条")

    # ── 双击跳转原文 ──────────────────────────────────────────────────────────────

    def _on_table_double_click(self, domain_id: str, row: int):
        table: QTableWidget = self._domain_ui[domain_id]["table"]
        item = table.item(row, 0)
        if not item:
            return
        line_no = item.data(Qt.UserRole)
        if line_no is None:
            return
        block = self._edit.document().findBlockByLineNumber(int(line_no) - 1)
        if not block.isValid():
            return
        c = self._edit.textCursor()
        c.setPosition(block.position())
        c.select(QTextCursor.LineUnderCursor)
        self._edit.setTextCursor(c)
        self._edit.setFocus()

    # ── 导出 ─────────────────────────────────────────────────────────────────────

    def _get_visible_rows(self, domain_id: str):
        """返回 (headers, rows) 仅含未隐藏行数据。"""
        table: QTableWidget = self._domain_ui[domain_id]["table"]
        n = table.columnCount()
        headers = [
            (table.horizontalHeaderItem(c).text() if table.horizontalHeaderItem(c) else "")
            for c in range(n)
        ]
        rows = [
            [(table.item(row, c).text() if table.item(row, c) else "") for c in range(n)]
            for row in range(table.rowCount())
            if not table.isRowHidden(row)
        ]
        return headers, rows

    def _export_csv(self, domain_id: str):
        headers, rows = self._get_visible_rows(domain_id)
        if not rows:
            QMessageBox.information(self, "提示", "当前无可导出的数据")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "", "CSV 文件 (*.csv);;所有文件 (*)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(headers)
                csv.writer(f).writerows(rows)
            QMessageBox.information(self, "提示", f"已导出 {len(rows)} 行到:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败：{e}")

    def _export_excel(self, domain_id: str):
        headers, rows = self._get_visible_rows(domain_id)
        if not rows:
            QMessageBox.information(self, "提示", "当前无可导出的数据")
            return
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            QMessageBox.warning(
                self, "缺少依赖",
                "导出 Excel 需要 openpyxl 库。\n"
                "请执行：pip install openpyxl\n"
                "安装后重启程序，或改用「导出 CSV」。"
            )
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "", "Excel 文件 (*.xlsx);;所有文件 (*)")
        if not path:
            return
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(headers)
            for row in rows:
                ws.append(row)
            wb.save(path)
            QMessageBox.information(self, "提示", f"已导出 {len(rows)} 行到:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败：{e}")

    # ── 图表 ─────────────────────────────────────────────────────────────────────

    def _show_chart(self, domain_id: str):
        ui = self._domain_ui[domain_id]
        table: QTableWidget = ui["table"]
        all_records: List[ParsedAtRecord] = ui["records"]
        visible_records = [
            rec for row, rec in enumerate(all_records) if not table.isRowHidden(row)
        ]
        if not visible_records:
            QMessageBox.information(self, "提示", "当前无可绘制的数据")
            return
        ChartDialog(visible_records, parent=self).exec_()

    # ── 背景色（供主窗口信号连接）────────────────────────────────────────────────

    def _apply_background_color(self, color):
        if hasattr(color, "name"):
            c = color
            color_name = c.name()
        else:
            color_name = str(color)
            c = QColor(color_name)
        text_color = "#e0e0e0" if c.lightness() < 128 else "#333333"
        self._edit.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {color_name}; color: {text_color}; }}"
        )

    def set_background_color(self, color):
        """供主窗口连接设置变更时调用。"""
        self._apply_background_color(color)

    # ── 文件操作 ─────────────────────────────────────────────────────────────────

    def _on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择日志文件", "", "日志文件 (*.log *.txt);;所有文件 (*)"
        )
        if path:
            self._load_file(path)

    def _on_open_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择日志文件夹", "")
        if path:
            self._load_folder(path)

    def _apply_content_incremental(self, content, chunk_size=300000):
        if len(content) <= chunk_size:
            self._edit.setPlainText(content)
            # setPlainText 触发 contentsChanged → 缓存已被清空，在此之后重设
            self._search_text_cache = content
            return
        self._edit.setUpdatesEnabled(False)
        self._edit.clear()
        pos = [0]

        def append_next():
            end = min(pos[0] + chunk_size, len(content))
            self._edit.insertPlainText(content[pos[0]:end])
            pos[0] = end
            if pos[0] < len(content):
                QTimer.singleShot(0, append_next)
            else:
                self._edit.setUpdatesEnabled(True)
                # 最后一块 insertPlainText 触发 contentsChanged 清空了缓存，
                # 在此之后重设（content 已在闭包中，不增加额外内存）
                self._search_text_cache = content

        QTimer.singleShot(0, append_next)

    def _load_file(self, path):
        self._file_list.blockSignals(True)
        self._file_list.clear()
        self._file_list.blockSignals(False)
        self._folder_path = None
        self._file_list_container.hide()
        self._current_file_path = path
        self._start_async_load(path)

    def _start_async_load(self, path):
        if self._load_thread and self._load_thread.isRunning():
            return
        self._open_file_btn.setEnabled(False)
        self._open_folder_btn.setEnabled(False)
        self._save_btn.setEnabled(False)
        self._save_as_btn.setEnabled(False)
        self._file_list.setEnabled(False)
        self._path_label.setText("加载中...")
        self._edit.clear()
        self._chunks = []
        for domain_id, _ in _DOMAINS:
            self._domain_ui[domain_id]["table"].setRowCount(0)
            self._domain_ui[domain_id]["summary"].setText("加载中…")

        def on_chunk(chunk):
            self._chunks.append(chunk)

        def on_progress(read_bytes, total):
            if total > 0 and total > 1024 * 1024:
                mb_r = read_bytes / (1024 * 1024)
                mb_t = total / (1024 * 1024)
                self._path_label.setText(f"加载中 {mb_r:.1f} / {mb_t:.1f} MB")

        def on_finished(success, err_msg):
            if success and self._chunks:
                # ① 先用行迭代器解析 chunks（不 join、不 splitlines，节省 1× 文件大小峰值）
                self._run_parse(LogAnalysisTab._iter_lines_from_chunks(self._chunks))
                # ② 再 join 用于显示（join 时有 2× 峰值，完成后释放 chunks）
                content = "".join(self._chunks)
                self._chunks = []
                self._apply_content_incremental(content)
            else:
                self._chunks = []
                self._fill_results([])
            self._open_file_btn.setEnabled(True)
            self._open_folder_btn.setEnabled(True)
            self._save_btn.setEnabled(True)
            self._save_as_btn.setEnabled(True)
            self._file_list.setEnabled(True)
            if success:
                self._path_label.setText(path)
            else:
                self._path_label.setText("加载失败")
                QMessageBox.warning(self, "错误", f"无法读取文件：{err_msg}")
                self._current_file_path = None
            self._flush_search_count()
            self._load_thread.quit()

        self._load_worker = FileLoadWorker(path)
        self._load_thread = QThread()
        self._load_worker.moveToThread(self._load_thread)
        self._load_thread.started.connect(self._load_worker.do_load)
        self._load_worker.chunk_ready.connect(on_chunk)
        self._load_worker.progress.connect(on_progress)
        self._load_worker.finished.connect(on_finished)
        self._load_thread.start()

    def _load_folder(self, path):
        files = []
        for name in sorted(os.listdir(path)):
            fp = os.path.join(path, name)
            if not os.path.isfile(fp):
                continue
            _, ext = os.path.splitext(name)
            if ext.lower() in (".log", ".txt") or ext == "":
                files.append(fp)
        if not files:
            QMessageBox.information(self, "提示", "该文件夹下没有找到 .log 或 .txt 文件")
            return
        self._folder_path = path
        self._file_list.blockSignals(True)
        self._file_list.clear()
        for fp in files:
            item = QListWidgetItem(os.path.basename(fp))
            item.setData(Qt.UserRole, fp)
            self._file_list.addItem(item)
        self._file_list.blockSignals(False)
        self._file_list_container.show()
        self._splitter.setSizes([200, 600])
        self._path_label.setText(f"{path} ({len(files)} 个文件)")
        self._file_list.setCurrentRow(0)

    def _on_file_list_selection(self, current, previous):
        if not current:
            return
        fp = current.data(Qt.UserRole)
        if fp and os.path.isfile(fp):
            self._current_file_path = fp
            self._start_async_load(fp)

    def _on_save(self):
        if not self._edit.toPlainText() and not self._current_file_path:
            return
        if self._current_file_path:
            try:
                with open(self._current_file_path, "w", encoding="utf-8") as f:
                    f.write(self._edit.toPlainText())
                self._path_label.setText(self._current_file_path)
                QMessageBox.information(self, "提示", "保存成功")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败：{e}")
        else:
            self._on_save_as()

    def _on_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", self._current_file_path or "",
            "日志文件 (*.log *.txt);;所有文件 (*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._edit.toPlainText())
                self._current_file_path = path
                self._path_label.setText(path)
                QMessageBox.information(self, "提示", "保存成功")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败：{e}")

    # ── 搜索（与原版完全一致）────────────────────────────────────────────────────

    def _schedule_search_count_update(self, *_args):
        """输入防抖：停止输入后再统计「共 n 处」，避免每键对整篇日志 finditer 卡 UI。"""
        keyword = self._search_edit.text().strip()
        if not keyword:
            self._search_count_timer.stop()
            self._count_label.setText("")
            return
        self._search_count_timer.start(self._SEARCH_DEBOUNCE_MS)

    def _count_matches_bounded(self) -> int:
        """
        统计匹配次数，最多数到 _SEARCH_COUNT_CAP+1；返回值 > CAP 表示「至少 CAP+1 处」用于显示「CAP+」。
        不构建全部匹配位置列表，避免大日志 + 高频匹配时内存与 CPU 爆炸。
        """
        keyword = self._search_edit.text().strip()
        text = self._search_text_cache or self._edit.toPlainText()
        if not keyword or not text:
            return 0
        flags = re.IGNORECASE if self._ignore_case_check.isChecked() else 0
        try:
            pattern = re.compile(
                keyword if self._regex_check.isChecked() else re.escape(keyword), flags
            )
        except re.error:
            return 0
        cap = self._SEARCH_COUNT_CAP
        count = 0
        pos = 0
        while True:
            m = pattern.search(text, pos)
            if not m:
                return count
            count += 1
            if count > cap:
                return cap + 1
            pos = m.end()
            if pos <= m.start():
                pos += 1

    def _flush_search_count(self):
        n = self._count_matches_bounded()
        if not self._search_edit.text().strip():
            self._count_label.setText("")
            return
        cap = self._SEARCH_COUNT_CAP
        if n > cap:
            self._count_label.setText(f"共 {cap}+ 处")
        elif n > 0:
            self._count_label.setText(f"共 {n} 处")
        else:
            self._count_label.setText("0 处")

    def _get_matches(self):
        keyword = self._search_edit.text().strip()
        # 优先使用加载时缓存的文本，避免 toPlainText() 对大文件每次按键都产生一个全量字符串副本
        text = self._search_text_cache or self._edit.toPlainText()
        if not keyword or not text:
            return []
        flags = re.IGNORECASE if self._ignore_case_check.isChecked() else 0
        try:
            pattern = re.compile(
                keyword if self._regex_check.isChecked() else re.escape(keyword), flags
            )
            return [(m.start(), m.end()) for m in pattern.finditer(text)]
        except re.error:
            return []

    def _goto_match(self, matches, direction):
        if not matches:
            QMessageBox.information(self, "提示", "未找到匹配项")
            return
        cursor = self._edit.textCursor()
        pos = cursor.position()
        wrap = self._wrap_check.isChecked()
        if direction == 1:
            idx = next((i for i, (s, _) in enumerate(matches) if s > pos), None)
            if idx is None:
                if wrap:
                    idx = 0
                else:
                    QMessageBox.information(self, "提示", "未找到更多匹配项")
                    return
        else:
            idx = next(
                (i for i in range(len(matches) - 1, -1, -1) if matches[i][1] < pos), None
            )
            if idx is None:
                if wrap:
                    idx = len(matches) - 1
                else:
                    QMessageBox.information(self, "提示", "未找到更多匹配项")
                    return
        start, end = matches[idx]
        cursor.setPosition(start)
        cursor.setPosition(end, cursor.KeepAnchor)
        self._edit.setTextCursor(cursor)
        self._edit.ensureCursorVisible()

    def _on_find_next(self):
        if not self._edit.toPlainText():
            return
        if not self._search_edit.text().strip():
            QMessageBox.information(self, "提示", "请输入搜索关键字")
            return
        if self._regex_check.isChecked():
            try:
                re.compile(self._search_edit.text())
            except re.error:
                QMessageBox.warning(self, "错误", "正则表达式无效")
                return
        self._goto_match(self._get_matches(), 1)

    def _on_find_prev(self):
        if not self._edit.toPlainText():
            return
        if not self._search_edit.text().strip():
            QMessageBox.information(self, "提示", "请输入搜索关键字")
            return
        if self._regex_check.isChecked():
            try:
                re.compile(self._search_edit.text())
            except re.error:
                QMessageBox.warning(self, "错误", "正则表达式无效")
                return
        self._goto_match(self._get_matches(), -1)

    def focus_search(self):
        """聚焦到搜索框（供主窗口 Ctrl+F 调用）。"""
        self._search_edit.setFocus()
        self._search_edit.selectAll()
