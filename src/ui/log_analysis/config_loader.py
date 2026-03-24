# -*- coding: utf-8 -*-
"""
配置加载器：读取 config/ 目录中的 JSON，合并 base + module + system，
返回 EffectiveProfile 与系统/模组列表。

合并顺序（后者覆盖前者中同 id 的规则）：
  1. base.json  ── 通用规则集
  2. modules/<module>.delta.json  ── module 级 rules_override（chip 差异，module=generic 时跳过）
  3. systems/<system>.json  ── system 级 rules_override（制式差异，同一 chip 在天通/星网下 AT 不同）

语义：同一芯片（如 06A）在天通与星网下可能用不同 AT 指令，system 覆盖 module，以制式为最终依据。
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

from .types import ColumnDef, EffectiveProfile, RuleDef, SystemDef

_CFG_DIR = os.path.join(os.path.dirname(__file__), "config")


def _cfg(*parts: str) -> str:
    return os.path.join(_CFG_DIR, *parts)


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 原始 dict → 数据类 ──────────────────────────────────────────────────────────

def _col_from_dict(d: dict) -> ColumnDef:
    return ColumnDef(
        key=d["key"],
        label=d.get("label", d["key"]),
        decoder=d.get("decoder") or None,
        numeric=bool(d.get("numeric", False)),
    )


def _rule_from_dict(d: dict) -> RuleDef:
    return RuleDef(
        id=d["id"],
        name=d.get("name", d["id"].upper()),
        desc=d.get("desc", ""),
        domain=d.get("domain", "status"),
        urc_prefix=d["urc_prefix"],
        category=d.get("category", "other"),
        separator=d.get("separator", ","),
        max_fields=int(d.get("max_fields", 0)),
        columns=tuple(_col_from_dict(c) for c in d.get("columns", [])),
    )


def _merge_rules(base: List[dict], overrides: List[dict]) -> List[dict]:
    """用 overrides 替换 base 中同 id 的规则；overrides 中新 id 追加到末尾。"""
    merged = {r["id"]: dict(r) for r in base}
    for ov in overrides:
        rid = ov["id"]
        if rid in merged:
            merged[rid].update(ov)
        else:
            merged[rid] = dict(ov)
    return list(merged.values())


# ── 对外接口 ────────────────────────────────────────────────────────────────────

def list_systems() -> List[Tuple[str, str]]:
    """返回 [(system_id, display_name), ...] 列表，按文件名排序。"""
    sys_dir = _cfg("systems")
    result = []
    for fname in sorted(os.listdir(sys_dir)):
        if not fname.endswith(".json"):
            continue
        try:
            data = _load_json(os.path.join(sys_dir, fname))
            result.append((data["id"], data["name"]))
        except Exception:
            pass
    return result


def list_modules(system_id: str) -> List[Tuple[str, str]]:
    """返回该 system 支持的 [(module_id, display_name), ...]，generic 始终首位。"""
    sys_file = _cfg("systems", f"{system_id}.json")
    if not os.path.isfile(sys_file):
        return [("generic", "通用")]
    data = _load_json(sys_file)
    module_ids: List[str] = data.get("modules", ["generic"])
    result = []
    for mid in module_ids:
        if mid == "generic":
            result.append(("generic", "通用"))
            continue
        delta_file = _cfg("modules", f"{mid}.delta.json")
        if os.path.isfile(delta_file):
            try:
                ddata = _load_json(delta_file)
                result.append((mid, ddata.get("name", mid)))
                continue
            except Exception:
                pass
        result.append((mid, mid))
    return result if result else [("generic", "通用")]


def list_rules(system_id: str, module_id: str = "generic") -> List[RuleDef]:
    """返回当前方案/模组下所有规则列表，供AT类型选择弹窗使用。"""
    profile = load_profile(system_id, module_id)
    if profile is None:
        return []
    return list(profile.rules)


def load_profile(system_id: str, module_id: str) -> Optional[EffectiveProfile]:
    """合并配置并返回 EffectiveProfile；失败时返回 None。"""
    # 1. 基底规则
    base_file = _cfg("base.json")
    if not os.path.isfile(base_file):
        return None
    base_data = _load_json(base_file)
    rule_dicts: List[dict] = list(base_data.get("rules", []))

    sys_file = _cfg("systems", f"{system_id}.json")
    if not os.path.isfile(sys_file):
        return None
    sys_data = _load_json(sys_file)
    sys_overrides: List[dict] = sys_data.get("rules_override", [])
    if sys_overrides:
        rule_dicts = _merge_rules(rule_dicts, sys_overrides)

    sys_def = SystemDef(
        id=sys_data["id"],
        name=sys_data["name"],
        tags=tuple(sys_data.get("tags", [])),
        default_module=sys_data.get("default_module", "generic"),
        modules=tuple(sys_data.get("modules", ["generic"])),
    )

    # 2. module 级 rules_override（chip 差异，generic 跳过）
    if module_id and module_id != "generic":
        delta_file = _cfg("modules", f"{module_id}.delta.json")
        if os.path.isfile(delta_file):
            delta_data = _load_json(delta_file)
            mod_overrides: List[dict] = delta_data.get("rules_override", [])
            if mod_overrides:
                rule_dicts = _merge_rules(rule_dicts, mod_overrides)

    # 3. system 级 rules_override（制式差异，同一 chip 在天通/星网下 AT 可不同）
    sys_overrides: List[dict] = sys_data.get("rules_override", [])
    if sys_overrides:
        rule_dicts = _merge_rules(rule_dicts, sys_overrides)

    rules = tuple(_rule_from_dict(r) for r in rule_dicts)
    return EffectiveProfile(system=sys_def, module_id=module_id or "generic", rules=rules)
