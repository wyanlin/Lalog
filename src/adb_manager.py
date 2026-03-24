# -*- coding: utf-8 -*-
"""ADB 设备与 logcat 管理模块"""
import subprocess
from typing import List

from PyQt5.QtCore import QObject, QThread, pyqtSignal


class LogcatThread(QThread):
    """在后台线程中运行 logcat 并逐行发送输出"""
    line_received = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)  # success, message

    def __init__(self, device_id: str, parent=None):
        super().__init__(parent)
        self._device_id = device_id
        self._process = None

    def run(self):
        try:
            cmd = ["adb", "-s", self._device_id, "logcat", "-v", "time"]
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                encoding="utf-8",
                errors="replace",
            )
            for line in iter(self._process.stdout.readline, ""):
                line = line.rstrip("\n\r")
                if line:
                    self.line_received.emit(line)
            self._process.wait()
            self.finished_signal.emit(True, "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            self._process = None

    def stop(self):
        """终止 logcat 进程"""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()


class AdbManager(QObject):
    """ADB 命令执行、设备列表、logcat 进程管理"""

    line_received = pyqtSignal(str)
    logcat_finished = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logcat_thread = None

    def get_devices(self) -> List[str]:
        """
        获取已连接的 Android 设备列表。

        Returns:
            设备 ID 列表（序列号或 IP:端口）
        """
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                encoding="utf-8",
                errors="replace",
            )
            devices = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("List of"):
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except (subprocess.SubprocessError, FileNotFoundError):
            return []

    def start_logcat(self, device_id: str) -> bool:
        """
        启动指定设备的 logcat 抓取。

        Args:
            device_id: 设备 ID

        Returns:
            是否成功启动
        """
        if self._logcat_thread and self._logcat_thread.isRunning():
            return False
        self._logcat_thread = LogcatThread(device_id, self)
        self._logcat_thread.line_received.connect(self.line_received.emit)
        self._logcat_thread.finished_signal.connect(self._on_logcat_finished)
        self._logcat_thread.start()
        return True

    def stop_logcat(self):
        """停止 logcat 抓取"""
        if self._logcat_thread:
            self._logcat_thread.stop()

    def is_capturing(self) -> bool:
        """是否正在抓取"""
        return self._logcat_thread is not None and self._logcat_thread.isRunning()

    def _on_logcat_finished(self, success: bool, message: str):
        self._logcat_thread = None
        self.logcat_finished.emit(success, message)
