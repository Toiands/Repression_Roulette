"""本局遭遇嘉宾回顾（结局页展示）。"""

from __future__ import annotations

from typing import Any

import streamlit as st


def append_encounter_roster(
    *,
    outcome: str,
    summary: str,
    action_label: str = "",
    disease_name: str = "",
) -> None:
    """在遭遇结束时写入一条回顾（需在 current_npc 仍有效时调用）。"""
    npc = st.session_state.get("current_npc")
    if not npc:
        return
    if "encounter_roster" not in st.session_state or not isinstance(
        st.session_state.encounter_roster, list
    ):
        st.session_state.encounter_roster = []

    entry: dict[str, Any] = {
        "turn": st.session_state.get("turn_count", 0),
        "npc_id": npc.get("id", ""),
        "name": npc.get("name", "未知"),
        "outcome": outcome,
        "summary": summary,
        "action_label": action_label,
        "disease_name": disease_name,
    }
    st.session_state.encounter_roster.append(entry)


OUTCOME_LABELS: dict[str, str] = {
    "completed": "正常结束",
    "infected": "感染",
    "hiv": "确诊 HIV",
    "left": "婉拒离场",
    "fled": "对方离开",
    "refused": "选项不可用",
}
