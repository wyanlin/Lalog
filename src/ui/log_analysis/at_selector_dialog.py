# -*- coding: utf-8 -*-
"""AT 类型选择弹窗：用户勾选要显示的 AT 指令类型。"""
from typing import Dict, List, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .config_loader import list_rules
from .types import RuleDef


_DOMAIN_LABELS = {
    "status": "状态/入网",
    "voice": "语音",
    "data": "数据",
}


class AtSelectorDialog(QDialog):
    """
    AT 类型选择对话框。

    按域分组显示所有可用的 AT 规则，用户勾选后返回选中的规则 ID 列表。
    """

    def __init__(self, rules: List[RuleDef], selected_ids: Set[str], parent=None):
        super().__init__(parent)
        self._rules = rules
        self._selected_ids = set(selected_ids)
        self._checkboxes: Dict[str, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("选择显示的 AT 类型")
        self.setMinimumSize(400, 350)
        self.resize(450, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

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
                cb.setChecked(rule.id in self._selected_ids)
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

    def get_selected_ids(self) -> Set[str]:
        """返回用户选中的规则 ID 集合。"""
        return {rule_id for rule_id, cb in self._checkboxes.items() if cb.isChecked()}


def show_at_selector(
    system_id: str,
    module_id: str,
    selected_ids: Set[str],
    parent=None,
) -> Set[str]:
    """
    显示 AT 选择对话框并返回结果。

    Args:
        system_id: 当前解析方案 ID
        module_id: 当前模组 ID
        selected_ids: 当前已选中的规则 ID 集合
        parent: 父窗口

    Returns:
        用户确认后的选中规则 ID 集合，取消则返回原集合
    """
    rules = list_rules(system_id, module_id)
    if not rules:
        return selected_ids

    dlg = AtSelectorDialog(rules, selected_ids, parent)
    if dlg.exec_() == QDialog.Accepted:
        return dlg.get_selected_ids()
    return selected_ids