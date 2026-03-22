# -*- coding: utf-8 -*-
"""解码器注册表：将配置里的 decoder_id 映射为可调用函数。"""
from __future__ import annotations

from typing import Callable, Dict

REGISTRY: Dict[str, Callable[[str], str]] = {}


def register(name: str) -> Callable:
    """装饰器：将函数注册为解码器。"""
    def decorator(fn: Callable[[str], str]) -> Callable[[str], str]:
        REGISTRY[name] = fn
        return fn
    return decorator


def decode(name: str, value: str) -> str:
    """调用已注册解码器；未注册时原样返回。"""
    fn = REGISTRY.get(name)
    if fn is None:
        return value
    try:
        return fn(value)
    except Exception:
        return value


# ── 内置解码器 ─────────────────────────────────────────────────────────────────

@register("signal_state_range")
def _signal_state_range(v: str) -> str:
    """CPSTATE signal_state：文档范围 -90～-130 dBm；超出范围显示 —。"""
    s = v.strip()
    if not s:
        return "—"
    try:
        n = int(s)
        if -130 <= n <= -90:
            return str(n)
    except ValueError:
        pass
    return "—"


# ── CPSTATE mm_state 码表（来源：CPSTATE描述.docx，基准 20）──────────────────
# 推导：文档明确 mm_state=21 为「正在搜索」，故空闲=20，其余按段落顺序递增。
# 实测 log 中 36→正常服务、54→对端呼叫清除完成 等均吻合。
_MM_STATE_MAP: Dict[int, str] = {
    20: "空闲",
    21: "正在搜索",
    22: "搜网失败",
    23: "搜网成功",
    24: "正在鉴权",
    25: "鉴权失败",
    26: "鉴权成功",
    27: "位置更新请求",
    28: "位置更新拒绝",
    29: "位置更新成功",
    30: "连接建立",
    31: "无网络",
    32: "安全模式",
    33: "高穿透模式",
    34: "RRC建链失败",
    35: "CM拒绝",
    36: "正常服务",
    37: "限制服务",
    38: "USIM卡无效",
    39: "主叫SETUP",
    40: "呼叫处理中",
    41: "对方已振铃",
    42: "对方已接听(等待确认)",
    43: "呼叫确认(通话中)",
    44: "本端挂机",
    45: "本端发起呼叫清除",
    46: "本端呼叫清除完成",
    47: "收到呼叫建立",
    48: "本端呼叫确认",
    49: "本端振铃",
    50: "本端呼叫接听",
    51: "对端呼叫确认(通话中)",
    52: "对端挂机",
    53: "对端发起呼叫清除",
    54: "对端呼叫清除完成",
    55: "CC状态上报",
    56: "CC状态查询",
}

# ── CPSTATE rrc_state 码表（来源：CPSTATE描述.docx，基准 80）──────────────────
# 推导：文档明确 rrc_state=82 为「扫频搜索」，故空闲=80，其余按段落顺序递增。
# 实测 log 中 84→读取广播信息、85→发送RACH、92→直传数据 均吻合。
_RRC_STATE_MAP: Dict[int, str] = {
    80: "空闲",
    81: "正在搜索",
    82: "扫频搜索",
    83: "搜索失败",
    84: "读取广播信息",
    85: "发送RACH",
    86: "发送RACH失败",
    87: "收到AGCH",
    88: "RRC CONNECTION REQUEST",
    89: "RRC CONNECTION SETUP",
    90: "RRC CONNECTION SETUP COMPLETE",
    91: "发送失败",
    92: "直传数据",
    93: "直传失败",
    94: "高穿透模式",
    95: "建链拒绝",
    96: "RB建立完成",
    97: "RB建立失败",
    98: "RB重配消息",
    99: "RB重配完成",
    100: "RB重配失败",
    101: "RRC链接释放",
    102: "RB_SETUP",
    103: "RB建立完成",
}


def _lookup_state(code_map: Dict[int, str], v: str) -> str:
    """通用码表查找：找到则返回「名称(码值)」，未知码值原样返回。"""
    s = v.strip()
    if not s:
        return s
    try:
        code = int(s)
        name = code_map.get(code)
        return f"{name}({code})" if name else s
    except ValueError:
        return s


@register("mm_state_cpstate")
def _mm_state_cpstate(v: str) -> str:
    """CPSTATE mm_state：上层状态，范围 20-56。"""
    return _lookup_state(_MM_STATE_MAP, v)


@register("rrc_state_cpstate")
def _rrc_state_cpstate(v: str) -> str:
    """CPSTATE rrc_state：底层状态，范围 80-103。"""
    return _lookup_state(_RRC_STATE_MAP, v)
