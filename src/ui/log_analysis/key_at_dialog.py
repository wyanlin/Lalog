# -*- coding: utf-8 -*-
"""关键 AT 管理弹窗：用户勾选标记为"关键"的 AT 指令。"""
from typing import Dict, List, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .types import RuleDef


_DOMAIN_LABELS = {
    "status": "状态/入网",
    "voice": "语音",
    "data": "数据",
}


class KeyAtDialog(QDialog):
    """
    关键 AT 管理对话框。

    用户勾选的 AT 规则会被标记为"关键"，在分析表格中展开参数列并以淡黄色背景显示。
    """

    def __init__(self, rules: List[RuleDef], key_ids: Set[str], parent=None):
        super().__init__(parent)
        self._rules = rules
        self._key_ids = set(key_ids)
        self._checkboxes: Dict[str, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("管理关键 AT")
        self.setMinimumSize(450, 400)
        self.resize(500, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        hint_label = QLabel(
            "勾选的 AT 将在分析表格中展开参数列，并以淡黄色背景显示。\n"
            "未勾选的 AT 仅显示原始行内容。"
        )
        hint_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        rules_by_domain: Dict[str, List[RuleDef]] = {}
        for rule in self._rules:
            domain = rule.domain
            if domain not in rules_by_domain:
                rules_by_domain[domain] = []
            rules_by_domain[domain].append(rule)

        for domain in ["status", "voice", "data"]:
            if domain not in rules_by_domain:
                continue
            domain_rules = rules_by_domain[domain]
            group = QGroupBox(_DOMAIN_LABELS.get(domain, domain))
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(4)
            group_layout.setContentsMargins(8, 8, 8, 8)

            for rule in domain_rules:
                display_text = f"{rule.name} - {rule.desc}" if rule.desc else rule.name
                cb = QCheckBox(display_text)
                cb.setChecked(rule.id in self._key_ids)
                cb.setProperty("rule_id", rule.id)
                self._checkboxes[rule.id] = cb
                group_layout.addWidget(cb)

            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

        select_all_btn = btn_box.addButton("全选", QDialogButtonBox.ActionRole)
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn = btn_box.addButton("全不选", QDialogButtonBox.ActionRole)
        deselect_all_btn.clicked.connect(self._deselect_all)

        layout.addWidget(btn_box)

    def _select_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def get_key_ids(self) -> Set[str]:
        """返回用户选中的关键 AT 规则 ID 集合。"""
        return {rule_id for rule_id, cb in self._checkboxes.items() if cb.isChecked()}


def show_key_at_dialog(
    rules: List[RuleDef],
    key_ids: Set[str],
    parent=None,
) -> Set[str]:
    """
    显示关键 AT 管理对话框并返回结果。

    Args:
        rules: 当前可用的规则列表
        key_ids: 当前已标记的关键 AT ID 集合
        parent: 父窗口

    Returns:
        用户确认后的关键 AT ID 集合，取消则返回原集合
    """
    if not rules:
        return key_ids

    dlg = KeyAtDialog(rules, key_ids, parent)
    if dlg.exec_() == QDialog.Accepted:
        return dlg.get_key_ids()
    return key_ids