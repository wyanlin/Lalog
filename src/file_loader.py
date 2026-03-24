# -*- coding: utf-8 -*-
"""后台文件加载"""
import os

from PyQt5.QtCore import QObject, QThread, pyqtSignal


class FileLoadWorker(QObject):
    """在后台线程中读取文件，分块发送以保持 UI 响应"""
    chunk_ready = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # bytes_read, total
    finished = pyqtSignal(bool, str)  # success, error_message

    def __init__(self, path, chunk_size=524288):
        super().__init__()
        self._path = path
        self._chunk_size = chunk_size

    def do_load(self):
        try:
            total = os.path.getsize(self._path)
        except (OSError, TypeError):
            total = 0
        try:
            with open(self._path, "r", encoding="utf-8", errors="replace") as f:
                read = 0
                while True:
                    chunk = f.read(self._chunk_size)
                    if not chunk:
                        break
                    read += len(chunk.encode("utf-8", errors="replace"))
                    self.chunk_ready.emit(chunk)
                    self.progress.emit(min(read, total), total)
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

