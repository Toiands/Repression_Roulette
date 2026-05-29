"""封装 Streamlit session_state 的初始化与更新。"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from config import (
    DISEASES_FILE,
    EVENT_REPRESSION_INCREASE,
    HEALTH_EDU_TIPS,
    HEALTH_MIN,
    HEALTH_START,
    NPCS_FILE,
    REPRESSION_MAX,
    REPRESSION_START,
    TREATMENT_REPRESSION_PENALTY,
    WIN_TURN_TARGET,
)


def _load_json(path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_game_data() -> tuple[list[dict], dict[str, dict]]:
    """加载 NPC 与疾病数据（缓存于 session）。"""
    st.session_state.npcs = _load_json(NPCS_FILE)
    raw = _load_json(DISEASES_FILE)
    st.session_state.diseases = {d["id"]: d for d in raw}
    return st.session_state.npcs, st.session_state.diseases


def reset_encounter_meta() -> None:
    """新遭遇开始时清空本轮交互记录，并随机本局跑路阈值。"""
    import random

    from config import PROBE_FLEE_MAX, PROBE_FLEE_MIN

    st.session_state.encounter_clues = []
    st.session_state.interactions_used = []
    st.session_state.flee_probe_limit = random.randint(
        PROBE_FLEE_MIN, PROBE_FLEE_MAX
    )


def init_session_state() -> None:
    """首次进入时初始化全部游戏状态。"""
    defaults: dict[str, Any] = {
        "initialized": True,
        "repression": REPRESSION_START,
        "health": HEALTH_START,
        "current_npc": None,
        "infections": [],
        "encounter_clues": [],
        "interactions_used": [],
        "last_result": "",
        "game_over": False,
        "game_over_reason": "",
        "awaiting_action": False,
        "turn_count": 0,
        "history_log": [],
        "met_npc_ids": [],
        "game_won": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # 兼容旧存档：补齐新增字段
    if not isinstance(st.session_state.get("history_log"), list):
        st.session_state.history_log = []
    if not isinstance(st.session_state.get("interactions_used"), list):
        st.session_state.interactions_used = []
    if not isinstance(st.session_state.get("encounter_clues"), list):
        st.session_state.encounter_clues = []
    if not isinstance(st.session_state.get("met_npc_ids"), list):
        st.session_state.met_npc_ids = []
    if "game_won" not in st.session_state:
        st.session_state.game_won = False
    load_game_data()


def reset_game() -> None:
    """重置游戏。"""
    keys_to_clear = list(st.session_state.keys())
    for key in keys_to_clear:
        del st.session_state[key]
    init_session_state()


def clamp_repression(value: int) -> int:
    return max(0, min(REPRESSION_MAX, value))


def clamp_health(value: int) -> int:
    return max(HEALTH_MIN, value)


def apply_repression_delta(delta: int) -> None:
    st.session_state.repression = clamp_repression(
        st.session_state.repression + delta
    )


def apply_health_delta(delta: int) -> None:
    st.session_state.health = clamp_health(st.session_state.health + delta)


def add_infection(record: dict[str, Any]) -> None:
    st.session_state.infections.append(record)


def interaction_already_used(key: str) -> bool:
    return key in st.session_state.interactions_used


def mark_interaction_used(key: str) -> None:
    if key not in st.session_state.interactions_used:
        st.session_state.interactions_used.append(key)


def append_clue(text: str) -> None:
    st.session_state.encounter_clues.append(text)


def append_history(event_type: str, summary: str, detail: str = "") -> None:
    """写入全局历史记录（最新在前）。"""
    if "history_log" not in st.session_state:
        st.session_state.history_log = []
    entry = {
        "turn": st.session_state.get("turn_count", 0),
        "type": event_type,
        "summary": summary,
        "detail": detail,
    }
    st.session_state.history_log.insert(0, entry)


def count_probing_interactions() -> int:
    from config import PROBING_INTERACTIONS

    used = st.session_state.interactions_used
    return sum(1 for key in used if key in PROBING_INTERACTIONS)


def tick_infections() -> list[str]:
    """每轮新事件开始时推进疾病，返回日志。"""
    logs: list[str] = []
    for inf in st.session_state.infections:
        if not inf["is_active"]:
            if inf["incubation_remaining"] > 0:
                inf["incubation_remaining"] -= 1
            if inf["incubation_remaining"] <= 0:
                inf["is_active"] = True
                logs.append(f"「{inf['disease_name']}」潜伏期结束，开始发作！")
            continue

        damage = inf["damage_per_turn"]
        apply_health_delta(-damage)
        logs.append(
            f"「{inf['disease_name']}」发作中，健康值 -{damage}（剩余 {st.session_state.health}）"
        )
    return logs


def start_new_event_turn() -> list[str]:
    """开启新遭遇：压抑值自动增加，推进疾病。"""
    logs: list[str] = []
    st.session_state.turn_count += 1
    apply_repression_delta(EVENT_REPRESSION_INCREASE)
    logs.append(f"新遭遇开始，压抑值自动 +{EVENT_REPRESSION_INCREASE}。")
    logs.extend(tick_infections())
    return logs


def get_flee_probe_limit() -> int:
    return int(st.session_state.get("flee_probe_limit", 3))


def check_victory() -> bool:
    """存活达到目标回合数即胜利。"""
    if st.session_state.get("game_won") or st.session_state.game_over:
        return st.session_state.get("game_won", False)

    if st.session_state.turn_count >= WIN_TURN_TARGET:
        st.session_state.game_won = True
        st.session_state.game_over = True
        import random

        edu = random.choice(HEALTH_EDU_TIPS)
        st.session_state.game_over_reason = (
            f"你成功存活 {WIN_TURN_TARGET} 回合，在压抑与风险之间撑了过来。{edu}"
        )
        return True
    return False


def check_game_over() -> bool:
    """检测并设置 Game Over 状态（失败）。"""
    if st.session_state.game_over:
        return True

    import random

    edu = random.choice(HEALTH_EDU_TIPS)

    if st.session_state.repression >= REPRESSION_MAX:
        st.session_state.game_over = True
        st.session_state.game_over_reason = f"压抑值爆表，精神崩溃…… {edu}"
        return True

    if st.session_state.health <= HEALTH_MIN:
        st.session_state.game_over = True
        st.session_state.game_over_reason = (
            f"健康值归零，身体垮掉…… {edu} 请牢记：早发现、早治疗，可显著改善预后。"
        )
        return True

    return False


def after_encounter_resolved() -> None:
    """一轮遭遇结束后的统一结算（胜负检测）。"""
    check_game_over()
    if not st.session_state.game_over:
        check_victory()


def trigger_instant_game_over(reason: str) -> None:
    st.session_state.game_over = True
    st.session_state.game_over_reason = reason


def treat_disease(index: int) -> str:
    """医院治疗：清除可治愈感染，但压抑值大幅上升。"""
    infections = st.session_state.infections
    if index < 0 or index >= len(infections):
        return "无效的疾病索引。"

    inf = infections[index]
    diseases = st.session_state.diseases
    disease = diseases.get(inf["disease_id"])
    if not disease:
        return "疾病数据异常。"

    if disease.get("instant_game_over") or not disease.get("curable", True):
        return f"「{disease['name']}」无法通过常规治疗解除。"

    removed = infections.pop(index)
    old_rep = st.session_state.repression
    apply_repression_delta(TREATMENT_REPRESSION_PENALTY)
    msg = (
        f"已在医院治疗「{removed['disease_name']}」。"
        f"压抑值 {old_rep} → {st.session_state.repression}（治疗代价 +{TREATMENT_REPRESSION_PENALTY}）。"
    )
    append_history("治疗", f"治愈 {removed['disease_name']}", msg)
    check_game_over()
    return msg


def get_disease_display(inf: dict[str, Any]) -> str:
    """格式化单条感染状态用于侧栏展示。"""
    if inf["is_active"]:
        status = "爆发中"
        detail = f"每轮 -{inf['damage_per_turn']} 健康"
    else:
        status = "潜伏中"
        detail = f"剩余 {inf['incubation_remaining']} 轮潜伏期"
    return f"{inf['disease_name']}（{status}，{detail}）"
