# -*- coding: utf-8 -*-
"""配置预设存储"""
import json
import os

from PyQt5.QtCore import QStandardPaths


def _presets_path():
    """预设文件路径"""
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".lynxlog")
    else:
        base = os.path.join(base, "LynxLog")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "presets.json")


def load_presets():
    """
    加载所有预设。

    Returns:
        dict: { "预设名": { "filter_keyword", "filter_case_sensitive", "filter_use_regex", "highlight_rules": [{"keyword", "color"}, ...] } }
    """
    path = _presets_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("presets", {})
    except (json.JSONDecodeError, IOError):
        return {}


def save_preset(name: str, config: dict):
    """
    保存预设。

    Args:
        name: 预设名称
        config: { "filter_keyword", "filter_case_sensitive", "filter_use_regex", "highlight_rules": [{"keyword", "color"}, ...] }
    """
    presets = load_presets()
    presets[name] = config
    path = _presets_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"presets": presets}, f, ensure_ascii=False, indent=2)
    except IOError:
        raise RuntimeError("保存预设失败")


def delete_preset(name: str):
    """删除预设"""
    presets = load_presets()
    if name in presets:
        del presets[name]
        path = _presets_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"presets": presets}, f, ensure_ascii=False, indent=2)
        except IOError:
            raise RuntimeError("删除预设失败")


def config_from_panels(filter_panel, highlight_panel, log_background_color=None):
    """
    从 FilterPanel 和 HighlightPanel 获取当前配置 dict。
    log_background_color: 可选，QColor 或颜色名字符串，保存到预设中
    """
    keyword, case_sensitive, use_regex = filter_panel.get_filter()
    rules = [(kw, c.name()) for kw, c in highlight_panel.get_rules()]
    cfg = {
        "filter_keyword": keyword,
        "filter_case_sensitive": case_sensitive,
        "filter_use_regex": use_regex,
        "highlight_rules": [{"keyword": kw, "color": color} for kw, color in rules],
    }
    if log_background_color is not None:
        cfg["log_background_color"] = (
            log_background_color.name()
            if hasattr(log_background_color, "name")
            else str(log_background_color)
        )
    return cfg


def apply_config_to_panels(config: dict, filter_panel, highlight_panel):
    """将配置应用到 FilterPanel 和 HighlightPanel"""
    filter_panel.set_filter(
        config.get("filter_keyword", ""),
        config.get("filter_case_sensitive", False),
        config.get("filter_use_regex", False),
    )
    rules_data = config.get("highlight_rules", [])
    rules = [(r.get("keyword", ""), r.get("color", "#000000")) for r in rules_data]
    highlight_panel.set_rules(rules)
