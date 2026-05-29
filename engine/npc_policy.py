"""嘉宾亲密选项策略：与 base_risk 可错位（掺雷），话术与选项一致。"""

from __future__ import annotations

import random
from typing import Any

# 仅用于生成时的「常理」映射，运行时以 JSON 的 action_policy 为准
RISK_REFUSE_RAW_MAX = 0.12
RISK_DEFAULT_MAX = 0.35

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

# 生成时：与 suggested 不一致则打 policy_mine 标签
POLICY_MINE_RATE = 0.16


def suggested_policy_from_risk(risk: float, tags: list[str] | None = None) -> str:
    """按风险推算的「表面常理」策略（可被生成器故意改雷）。"""
    if tags and "trap" in tags:
        return "refuse_condom"
    if risk <= RISK_REFUSE_RAW_MAX:
        return "refuse_raw"
    if risk <= RISK_DEFAULT_MAX:
        return "default"
    return "refuse_condom"


def is_policy_mine(npc: dict[str, Any]) -> bool:
    tags = npc.get("tags") or []
    if "policy_mine" in tags:
        return True
    risk = float(npc.get("base_risk", 0))
    stored = npc.get("action_policy")
    if not stored:
        return False
    return stored != suggested_policy_from_risk(risk, tags)


def ensure_npc_policy(npc: dict[str, Any]) -> str:
    """仅补齐缺失字段，不覆盖已生成的策略（保留掺雷）。"""
    policy = npc.get("action_policy")
    if policy not in ACTION_POLICIES:
        policy = suggested_policy_from_risk(
            float(npc.get("base_risk", 0)), npc.get("tags")
        )
        npc["action_policy"] = policy
    return policy


def get_action_policy(npc: dict[str, Any] | None) -> str:
    if not npc:
        return "default"
    return ensure_npc_policy(npc)


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


def _pick_stable(npc: dict[str, Any], options: list[str]) -> str:
    if not options:
        return ""
    idx = sum(ord(c) for c in (npc.get("id") or npc.get("name", ""))) % len(options)
    return options[idx]


# —— 防护态度：只跟 action_policy（与按钮一致）——


def dialogue_discuss_protection(npc: dict[str, Any]) -> str:
    name = npc.get("name", "对方")
    policy = get_action_policy(npc)

    if policy == "refuse_raw":
        return f"{name} 态度很明确：不接受无保护，希望全程做好防护。"
    if policy == "refuse_condom":
        return f"{name} 对戴套表现出抵触，说「别搞那么复杂」。"
    return _pick_stable(
        npc,
        [
            f"{name} 不反对聊防护，但不愿把气氛搞僵。",
            f"{name} 说「到时候再看」，态度模棱两可。",
            f"{name} 愿意听你说，但没给出明确承诺。",
        ],
    )


# —— 以下试探：只跟 base_risk（可与策略错位，形成「雷」）——


def dialogue_ask_history(npc: dict[str, Any]) -> str:
    name = npc.get("name", "对方")
    risk = _risk(npc)

    if risk < 0.25:
        return f"{name} 坦然提到近期体检正常，语气自然。"
    if risk < 0.55:
        return f"{name} 含糊其辞，称「上火吃过抗生素」但说不清药名。"
    return f"{name} 明显不耐烦，拒绝深谈病史。"


def dialogue_request_report(npc: dict[str, Any]) -> str:
    name = npc.get("name", "对方")
    risk = _risk(npc)
    roll = random.random()

    if risk < 0.3 and roll < 0.85:
        return f"{name} 主动出示近期阴性报告，看起来靠谱。"
    if risk < 0.65:
        if roll < 0.5:
            return f"{name} 推脱说报告忘带了，眼神闪躲。"
        return f"{name} 出示三个月前的报告，称「最近忙没复查」。"
    if roll < 0.35:
        return f"{name} 强硬拒绝：「不信就算了」。"
    return f"{name} 拿出模糊手机截图，日期看不清，可疑。"


def dialogue_observe(npc: dict[str, Any]) -> str:
    risk = _risk(npc)

    if risk < 0.25:
        return "你注意到对方精神状态稳定，体表无明显异常。"
    if risk < 0.55:
        return "你注意到遮瑕痕迹、旧抓痕或药物包装等疑点。"
    return "你注意到皮疹结痂、针眼旧痕或强烈异味等危险信号。"


def roll_action_policy_for_npc(
    risk: float, tags: list[str] | None = None
) -> tuple[str, bool]:
    """
    生成嘉宾策略：多数符合风险常理，约 POLICY_MINE_RATE 故意错位。
    返回 (policy, is_mine)。
    """
    tags = list(tags or [])
    suggested = suggested_policy_from_risk(risk, tags)

    if "trap" in tags:
        # 致命地雷：高感染风险 + 不要戴套；与常理一致，不算 policy 雷
        return "refuse_condom", False

    if random.random() >= POLICY_MINE_RATE:
        return suggested, False

    if suggested == "refuse_raw":
        alt = random.choice(["refuse_condom", "default"])
    elif suggested == "refuse_condom":
        alt = random.choice(["refuse_raw", "default"])
    else:
        alt = random.choice(["refuse_raw", "refuse_condom"])

    if alt == suggested:
        # 保底改成另一种
        alt = "refuse_condom" if suggested != "refuse_condom" else "refuse_raw"
    return alt, True
