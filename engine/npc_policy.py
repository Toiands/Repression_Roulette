"""嘉宾亲密选项策略：哪些行动可用、灰显说明。"""

from __future__ import annotations

from typing import Any

# default: 四选项均可
# refuse_raw: 不接受无套（禁 B、C）
# refuse_condom: 不要戴套（禁 A）
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


def get_action_policy(npc: dict[str, Any] | None) -> str:
    if not npc:
        return "default"
    policy = npc.get("action_policy") or "default"
    if policy not in ACTION_POLICIES:
        return "default"
    return policy


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
