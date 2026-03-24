# AGENTS.md - LynxLog Development Guide

## Project Overview

**LynxLog** is a Windows desktop application for real-time Android device log capture and analysis using ADB (Android Debug Bridge).

- **Framework**: PyQt5
- **Python**: 3.8+
- **Platform**: Windows 10/11

## Build & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Optional: Install openpyxl for Excel export feature
pip install openpyxl
```

## Testing

**No test suite exists.** If adding tests, place them in a `tests/` directory and run with:

```bash
# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_log_filter.py -v

# Run a single test function
python -m pytest tests/test_log_filter.py::TestLogFilter::test_matches -v
```

## Code Style Guidelines

### File Headers

Every Python file must include the encoding declaration and module docstring:

```python
# -*- coding: utf-8 -*-
"""Module name: brief description"""
```

### Imports

Organize imports in three groups with blank lines between them:

```python
# 1. Standard library
import os
import re
from typing import List, Optional

# 2. Third-party packages
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout

# 3. Local application modules
from .config_loader import load_profile
from .types import ParsedAtRecord
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `log_filter.py` |
| Classes | PascalCase | `LogFilter`, `MainWindow` |
| Functions | snake_case | `get_devices()`, `matches()` |
| Variables | snake_case | `device_id`, `line_count` |
| Private members | _underscore prefix | `_logcat_thread`, `_setup_ui()` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT` |

### Type Annotations

Use type hints for function parameters and return values:

```python
def get_devices(self) -> List[str]:
    ...

def matches(line: str, keyword: str, case_sensitive: bool, use_regex: bool) -> bool:
    ...
```

For PyQt classes, use `Optional[...]` for nullable parameters:

```python
def __init__(self, parent: Optional[QWidget] = None):
    super().__init__(parent)
```

### Dataclasses

Use `@dataclass` with `frozen=True` for immutable data structures:

```python
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

@dataclass(frozen=True)
class ColumnDef:
    key: str
    label: str
    decoder: Optional[str] = None
    numeric: bool = False
```

### PyQt Signal/Slot Pattern

Define signals as class attributes and use `pyqtSignal`:

```python
from PyQt5.QtCore import QObject, pyqtSignal

class AdbManager(QObject):
    line_received = pyqtSignal(str)
    logcat_finished = pyqtSignal(bool, str)

    def _on_logcat_finished(self, success: bool, message: str):
        self.logcat_finished.emit(success, message)
```

### Threading Pattern

For background work, use `QThread` with worker objects:

```python
class LogcatThread(QThread):
    line_received = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def run(self):
        # Do work here
        self.finished_signal.emit(True, "")
```

### Error Handling

- Use specific exception types when possible
- Return empty collections on failure (preferable) or emit error signals
- Let Qt dialogs handle user-facing error messages

```python
try:
    result = subprocess.run(...)
    return result.stdout.strip()
except (subprocess.SubprocessError, FileNotFoundError):
    return []
```

### Docstrings

Use Google-style docstrings for public methods:

```python
def matches(
    line: str, keyword: str, case_sensitive: bool, use_regex: bool
) -> bool:
    """
    Determine if a log line matches the filter criteria.

    Args:
        line: The log line content
        keyword: Filter keyword, empty matches all
        case_sensitive: Whether to match case
        use_regex: Whether to use regex matching

    Returns:
        True if the line matches, False otherwise
    """
```

### Private Methods

Use `_underscore` prefix for internal methods:

```python
class MainWindow(QMainWindow):
    def _setup_ui(self):
        ...

    def _connect_signals(self):
        ...

    def _refresh_devices(self):
        ...
```

### UI Layout

- Use `QVBoxLayout` and `QHBoxLayout` for layouts
- Set spacing and margins explicitly
- Use `QFrame` with `QFrame.HLine` for separators

```python
layout = QVBoxLayout(widget)
layout.setSpacing(10)
layout.setContentsMargins(12, 12, 12, 12)
```

## Project Structure

```
src/
├── __init__.py           # Package marker with description
├── version.py            # Version: __version__ = "x.y.z"
├── adb_manager.py        # ADB & logcat management
├── log_filter.py         # Log filtering logic
├── config_preset.py      # Preset storage (JSON to %APPDATA%)
├── app_settings.py       # App settings (QSettings registry)
├── file_loader.py        # Async file loading
└── ui/
    ├── main_window.py    # Main window (QMainWindow)
    ├── device_panel.py   # Device selection
    ├── log_panel.py      # Log display (QTextEdit)
    ├── control_panel.py  # Start/Stop/Clear buttons
    ├── filter_panel.py   # Filter settings
    ├── highlight_panel.py # Highlight rules
    ├── settings_dialog.py # Settings dialog
    ├── preset_panel.py   # Preset management
    ├── about_dialog.py   # About dialog
    ├── log_analysis_tab.py # File analysis tab
    └── log_analysis/     # AT log parsing engine
        ├── engine.py      # Core parsing engine
        ├── types.py       # Data structures
        ├── config_loader.py # Config loading
        └── config/        # JSON configs (systems, modules)
```

## Data Storage

- **Presets**: `%APPDATA%/LynxLog/presets.json`
- **Settings**: Windows Registry via QSettings (`HKEY_CURRENT_USER\Software\LynxLog`)

## Common Patterns

### Module-Level Exports

In `__init__.py`, explicitly define public API:

```python
__all__ = ["parse_log", "parse_log_lines", "list_systems", "list_modules", "ParsedAtRecord"]
```

### Context Managers for Resources

```python
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
```

### Lambda for Signal Connections

When connecting to signals with additional parameters:

```python
filter_edit.textChanged.connect(
    lambda text, d=domain_id: self._apply_filter(d, text)
)
```

## Key Dependencies

- `PyQt5>=5.15.0` - GUI framework
- `openpyxl` (optional) - Excel export