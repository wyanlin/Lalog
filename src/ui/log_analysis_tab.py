# -*- coding: utf-8 -*-
"""日志分析 Tab：打开文件/文件夹，搜索"""
import os
import re

from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtGui import QColor, QFont, QKeySequence
from PyQt5.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..app_settings import get_log_background_color
from ..file_loader import FileLoadWorker
from .log_panel import _log_font_size


class LogAnalysisTab(QWidget):
    """日志分析：导入文件/文件夹，搜索查找，编辑保存"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file_path = None
        self._folder_path = None
        self._load_thread = None
        self._load_worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 6, 6, 6)

        toolbar = QWidget()
        toolbar.setMaximumHeight(36)
        tool_layout = QHBoxLayout(toolbar)
        tool_layout.setContentsMargins(0, 2, 0, 2)
        tool_layout.setSpacing(6)

        self._open_file_btn = QPushButton("打开")
        self._open_file_btn.setToolTip("打开文件")
        self._open_file_btn.clicked.connect(self._on_open_file)
        tool_layout.addWidget(self._open_file_btn)

        self._open_folder_btn = QPushButton("文件夹")
        self._open_folder_btn.setToolTip("打开文件夹")
        self._open_folder_btn.clicked.connect(self._on_open_folder)
        tool_layout.addWidget(self._open_folder_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.setToolTip("Ctrl+S")
        self._save_btn.clicked.connect(self._on_save)
        tool_layout.addWidget(self._save_btn)

        self._save_as_btn = QPushButton("另存为")
        self._save_as_btn.clicked.connect(self._on_save_as)
        tool_layout.addWidget(self._save_as_btn)

        tool_layout.addSpacing(8)

        tool_layout.addWidget(QLabel("查找:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("关键字 Ctrl+F")
        self._search_edit.setMaximumWidth(140)
        self._search_edit.returnPressed.connect(self._on_find_next)
        self._search_edit.textChanged.connect(self._update_count)
        tool_layout.addWidget(self._search_edit)

        self._regex_check = QCheckBox("正则")
        self._regex_check.stateChanged.connect(self._update_count)
        tool_layout.addWidget(self._regex_check)

        self._ignore_case_check = QCheckBox("大小写")
        self._ignore_case_check.setChecked(True)
        self._ignore_case_check.setToolTip("忽略大小写")
        self._ignore_case_check.stateChanged.connect(self._update_count)
        tool_layout.addWidget(self._ignore_case_check)

        self._wrap_check = QCheckBox("循环")
        self._wrap_check.setChecked(True)
        self._wrap_check.setToolTip("循环查找")
        tool_layout.addWidget(self._wrap_check)

        self._find_prev_btn = QPushButton("上一个")
        self._find_prev_btn.clicked.connect(self._on_find_prev)
        tool_layout.addWidget(self._find_prev_btn)

        self._find_next_btn = QPushButton("下一个")
        self._find_next_btn.clicked.connect(self._on_find_next)
        tool_layout.addWidget(self._find_next_btn)

        self._count_label = QLabel("")
        self._count_label.setMinimumWidth(55)
        self._count_label.setStyleSheet("color: gray; font-size: 11px;")
        tool_layout.addWidget(self._count_label)

        self._path_label = QLabel("未打开")
        self._path_label.setStyleSheet("color: gray; font-size: 11px;")
        self._path_label.setMaximumWidth(200)
        tool_layout.addWidget(self._path_label, 1)

        layout.addWidget(toolbar)

        self._file_list = QListWidget()
        self._file_list.setMinimumWidth(120)
        self._file_list.currentItemChanged.connect(self._on_file_list_selection)
        self._file_list_container = QWidget()
        file_list_layout = QVBoxLayout(self._file_list_container)
        file_list_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addWidget(QLabel("文件列表"))
        file_list_layout.addWidget(self._file_list)

        self._edit = QPlainTextEdit()
        self._edit.setReadOnly(False)
        self._edit.setFont(QFont("Consolas", _log_font_size()))
        self._apply_background_color(get_log_background_color())

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.addWidget(self._file_list_container)
        self._splitter.addWidget(self._edit)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._file_list_container.hide()
        layout.addWidget(self._splitter, 1)

        QShortcut(QKeySequence.Save, self).activated.connect(self._on_save)

    def _apply_background_color(self, color):
        """应用日志背景色（与实时抓取一致）"""
        if hasattr(color, "name"):
            c = color
            color_name = c.name()
            text_color = "#e0e0e0" if c.lightness() < 128 else "#333333"
        else:
            color_name = str(color)
            c = QColor(color_name)
            text_color = "#e0e0e0" if c.lightness() < 128 else "#333333"
        self._edit.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {color_name}; color: {text_color}; }}"
        )

    def set_background_color(self, color):
        """供主窗口连接设置变更时调用"""
        self._apply_background_color(color)

    def _on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择日志文件",
            "",
            "日志文件 (*.log *.txt);;所有文件 (*)",
        )
        if path:
            self._load_file(path)

    def _on_open_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择日志文件夹", "")
        if path:
            self._load_folder(path)

    def _apply_content_incremental(self, content, chunk_size=300000):
        """分块设置内容，避免一次 setPlainText 大文本阻塞 UI"""
        if len(content) <= chunk_size:
            self._edit.setPlainText(content)
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
        """后台加载文件，避免大文件阻塞 UI"""
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

        def on_chunk(chunk):
            self._chunks.append(chunk)

        def on_progress(read_bytes, total):
            if total > 0 and total > 1024 * 1024:
                mb_r = read_bytes / (1024 * 1024)
                mb_t = total / (1024 * 1024)
                self._path_label.setText(f"加载中 {mb_r:.1f} / {mb_t:.1f} MB")

        def on_finished(success, err_msg):
            if success and self._chunks:
                content = "".join(self._chunks)
                self._chunks = []
                self._apply_content_incremental(content)
            else:
                self._chunks = []
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
            self._update_count()
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
        path = current.data(Qt.UserRole)
        if path and os.path.isfile(path):
            self._current_file_path = path
            self._start_async_load(path)

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
            self,
            "另存为",
            self._current_file_path or "",
            "日志文件 (*.log *.txt);;所有文件 (*)",
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

    def _get_matches(self):
        """返回 [(start, end), ...] 匹配位置列表"""
        keyword = self._search_edit.text().strip()
        text = self._edit.toPlainText()
        if not keyword or not text:
            return []
        use_regex = self._regex_check.isChecked()
        flags = re.IGNORECASE if self._ignore_case_check.isChecked() else 0
        try:
            if use_regex:
                pattern = re.compile(keyword, flags)
            else:
                pattern = re.compile(re.escape(keyword), flags)
            return [(m.start(), m.end()) for m in pattern.finditer(text)]
        except re.error:
            return []

    def _update_count(self):
        matches = self._get_matches()
        n = len(matches)
        if self._search_edit.text().strip():
            self._count_label.setText(f"共 {n} 处" if n > 0 else "0 处")
        else:
            self._count_label.setText("")

    def _goto_match(self, matches, direction):
        """direction: 1=next, -1=prev. 根据循环查找决定是否 wrap"""
        if not matches:
            QMessageBox.information(self, "提示", "未找到匹配项")
            return
        cursor = self._edit.textCursor()
        pos = cursor.position()
        wrap = self._wrap_check.isChecked()
        if direction == 1:
            idx = next((i for i, (s, e) in enumerate(matches) if s > pos), None)
            if idx is None:
                if wrap:
                    idx = 0
                else:
                    QMessageBox.information(self, "提示", "未找到更多匹配项")
                    return
        else:
            idx = next((i for i in range(len(matches) - 1, -1, -1) if matches[i][1] < pos), None)
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
        matches = self._get_matches()
        self._goto_match(matches, 1)

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
        matches = self._get_matches()
        self._goto_match(matches, -1)

    def focus_search(self):
        """聚焦到搜索框（供 Ctrl+F 调用）"""
        self._search_edit.setFocus()
        self._search_edit.selectAll()
