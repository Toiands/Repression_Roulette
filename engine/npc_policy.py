"""嘉宾亲密选项策略：与 base_risk 强绑定，并驱动试探类文案。"""

from __future__ import annotations

import random
from typing import Any

# base_risk → action_policy（全游戏唯一口径）
RISK_REFUSE_RAW_MAX = 0.12  # ≤ 此值：坚持防护，禁 B/C
RISK_DEFAULT_MAX = 0.35  # ≤ 此值且 > RAW：四选项可谈；> 此值：抵触戴套，禁 A

ACTION_POLICIES: dict[str, dict[str, Any]] = {
    "default": {
        "blocked": [],
        "hint": "",
    },
    "refuse_raw": {
        "blocked": ["B", "C"],
        "hint": "对方不接受无保护或半保护行为",
    },
    "refuse_condom": {
        "blocked": ["A"],
        "hint": "对方抵触全程戴套，此选项不可用",
    },
}


def policy_from_risk(risk: float, tags: list[str] | None = None) -> str:
    """由基础风险（+ 地雷标签）唯一决定策略，与 JSON 字段无关。"""
    if tags and "trap" in tags:
        return "refuse_condom"
    if risk <= RISK_REFUSE_RAW_MAX:
        return "refuse_raw"
    if risk <= RISK_DEFAULT_MAX:
        return "default"
    return "refuse_condom"


def sync_npc_policy(npc: dict[str, Any]) -> str:
    """写回并返回与 base_risk 一致的 action_policy。"""
    policy = policy_from_risk(float(npc.get("base_risk", 0)), npc.get("tags"))
    npc["action_policy"] = policy
    return policy


def get_action_policy(npc: dict[str, Any] | None) -> str:
    if not npc:
        return "default"
    return policy_from_risk(float(npc.get("base_risk", 0)), npc.get("tags"))


def get_blocked_actions(npc: dict[str, Any] | None) -> set[str]:
    policy = get_action_policy(npc)
    return set(ACTION_POLICIES[policy]["blocked"])


def is_action_allowed(npc: dict[str, Any] | None, action_key: str) -> bool:
    return action_key not in get_blocked_actions(npc)


def action_disabled_hint(npc: dict[str, Any] | None, action_key: str) -> str | None:
    if is_action_allowed(npc, action_key):
        return None
    policy = get_action_policy(npc)
    base = ACTION_POLICIES[policy]["hint"]
    if base:
        return base
    return "对方不接受此选项"


def _risk(npc: dict[str, Any]) -> float:
    return float(npc.get("base_risk", 0))


def dialogue_discuss_protection(npc: dict[str, Any]) -> str:
    name = npc.get("name", "对方")
    policy = get_action_policy(npc)
    risk = _risk(npc)

    if policy == "refuse_raw":
        return f"{name} 态度很明确：不接受无保护，希望全程做好防护。"
    if policy == "refuse_condom":
        return f"{name} 对戴套表现出抵触，说「别搞那么复杂」。"
    # default：中低风险，话术随 risk 微调
    if risk < 0.22:
        return f"{name} 愿意聊具体防护方式，整体态度配合。"
    if risk < 0.32:
        return f"{name} 口头答应会注意防护，但对细节有点敷衍。"
    return f"{name} 态度暧昧，防护要看当时气氛。"


def dialogue_ask_history(npc: dict[str, Any]) -> str:
    name = npc.get("name", "对方")
    policy = get_action_policy(npc)
    risk = _risk(npc)

    if policy == "refuse_raw":
        return f"{name} 坦然提到近期筛查正常，愿意多聊一点。"
    if policy == "refuse_condom":
        return f"{name} 明显不耐烦，拒绝深谈病史。"
    if risk < 0.22:
        return f"{name} 回答还算自然，没有明显闪躲。"
    if risk < 0.32:
        return f"{name} 含糊其辞，称「上火吃过抗生素」但说不清药名。"
    return f"{name} 三两句就想把话题岔开。"


def dialogue_request_report(npc: dict[str, Any]) -> str:
    name = npc.get("name", "对方")
    policy = get_action_policy(npc)
    risk = _risk(npc)
    roll = random.random()

    if policy == "refuse_raw":
        if roll < 0.85:
            return f"{name} 主动出示近期阴性报告，看起来靠谱。"
        return f"{name} 出示稍早的报告，称「最近忙没复查」。"

    if policy == "refuse_condom":
        if roll < 0.4:
            return f"{name} 强硬拒绝：「不信就算了」。"
        return f"{name} 拿出模糊手机截图，日期看不清，可疑。"

    if risk < 0.22 and roll < 0.8:
        return f"{name} 愿意出示报告，日期还算新。"
    if risk < 0.32:
        if roll < 0.5:
            return f"{name} 推脱说报告忘带了，眼神闪躲。"
        return f"{name} 出示三个月前的报告，称「最近忙没复查」。"
    if roll < 0.5:
        return f"{name} 推脱说报告忘带了，眼神闪躲。"
    return f"{name} 出示的报告信息不全，难以判断。"


def dialogue_observe(npc: dict[str, Any]) -> str:
    policy = get_action_policy(npc)
    risk = _risk(npc)

    if policy == "refuse_raw":
        return "你注意到对方精神状态稳定，体表无明显异常，边界感清晰。"
    if policy == "refuse_condom":
        return "你注意到皮疹结痂、针眼旧痕或强烈异味等危险信号。"
    if risk < 0.22:
        return "你注意到对方精神状态稳定，体表无明显异常。"
    if risk < 0.32:
        return "你注意到遮瑕痕迹、旧抓痕或药物包装等疑点。"
    return "你注意到一些令人不安的细节，但对方不愿多解释。"
