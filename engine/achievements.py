"""成就定义、统计与解锁（会话内跨「重新开始」保留，并写入浏览器 localStorage）。"""

from __future__ import annotations

import json
from typing import Any, Callable

import streamlit as st
import streamlit.components.v1 as components

from config import HEALTH_START, WIN_TURN_TARGET

STORAGE_KEY = "repression_roulette_ach_v1"

ACHIEVEMENTS: dict[str, dict[str, str]] = {
    "win_game": {
        "title": "幸存者",
        "desc": "成功存活至胜利回合",
        "icon": "🏁",
    },
    "clean_win": {
        "title": "洁身自好",
        "desc": "全程零感染通关",
        "icon": "✨",
    },
    "full_health": {
        "title": "体魄完好",
        "desc": "满血通关",
        "icon": "💪",
    },
    "wounded_win": {
        "title": "带伤突围",
        "desc": "通关时健康值不高于 30",
        "icon": "🩹",
    },
    "wire_mood": {
        "title": "钢丝心情",
        "desc": "通关时压抑值不低于 85",
        "icon": "😰",
    },
    "iron_refusal": {
        "title": "柳下惠",
        "desc": "通关时从未选择中度/高危亲密选项",
        "icon": "🧘",
    },
    "all_in": {
        "title": "孤注一掷",
        "desc": "曾选全程无套并完成通关",
        "icon": "🎲",
    },
    "hiv_end": {
        "title": "红线",
        "desc": "确诊 HIV，游戏结束",
        "icon": "🛑",
    },
    "first_infection": {
        "title": "栽了",
        "desc": "首次感染可治愈性病",
        "icon": "🦠",
    },
    "trap_hit": {
        "title": "踩雷了",
        "desc": "感染来自带陷阱标签的嘉宾",
        "icon": "💣",
    },
    "npc_fled": {
        "title": "把人问跑了",
        "desc": "追问过多导致对方离场",
        "icon": "🏃",
    },
    "hospital": {
        "title": "跑医院",
        "desc": "接受过医院治疗",
        "icon": "🏥",
    },
    "coser_fan": {
        "title": "漫展夜",
        "desc": "与 Coser 嘉宾完成一整轮遭遇",
        "icon": "📸",
    },
    "speed_run": {
        "title": "节奏大师",
        "desc": f"单局遇见至少 {WIN_TURN_TARGET} 位不同嘉宾",
        "icon": "⚡",
    },
}


def default_game_stats() -> dict[str, Any]:
    return {
        "actions": [],
        "infected": False,
        "infection_disease_ids": [],
        "from_trap": False,
        "treated": False,
        "npc_fled": False,
        "met_coser": False,
    }


def init_achievement_state() -> None:
    if "achievements_persistent" not in st.session_state:
        st.session_state.achievements_persistent = []
    if "achievements_new" not in st.session_state:
        st.session_state.achievements_new = []
    if "achievements_at_run_start" not in st.session_state:
        st.session_state.achievements_at_run_start = []
    if "game_stats" not in st.session_state:
        st.session_state.game_stats = default_game_stats()


def begin_new_run_achievements() -> None:
    """重新开始一局时调用：保留历史成就，重置本局统计。"""
    init_achievement_state()
    st.session_state.achievements_at_run_start = list(
        st.session_state.achievements_persistent
    )
    st.session_state.game_stats = default_game_stats()
    st.session_state.achievements_new = []


def _persistent_set() -> set[str]:
    return set(st.session_state.get("achievements_persistent", []))


def _unlock(aid: str) -> bool:
    if aid not in ACHIEVEMENTS or aid in _persistent_set():
        return False
    st.session_state.achievements_persistent.append(aid)
    st.session_state.achievements_new.append(aid)
    _save_to_browser_storage()
    return True


def _save_to_browser_storage() -> None:
    payload = json.dumps(
        list(st.session_state.achievements_persistent), ensure_ascii=False
    )
    components.html(
        f"<script>try{{localStorage.setItem({json.dumps(STORAGE_KEY)}, "
        f"{json.dumps(payload)});}}catch(e){{}}</script>",
        height=0,
    )


def record_action(action_key: str) -> None:
    st.session_state.game_stats["actions"].append(action_key)


def record_npc_encounter(npc: dict[str, Any]) -> None:
    if "coser" in (npc.get("tags") or []):
        st.session_state.game_stats["met_coser"] = True


def record_infection(disease_id: str, npc: dict[str, Any]) -> None:
    stats = st.session_state.game_stats
    stats["infected"] = True
    stats["infection_disease_ids"].append(disease_id)
    if "trap" in (npc.get("tags") or []):
        stats["from_trap"] = True
    check_achievements()


def record_npc_fled() -> None:
    st.session_state.game_stats["npc_fled"] = True
    check_achievements()


def record_treatment() -> None:
    st.session_state.game_stats["treated"] = True
    check_achievements()


def record_hiv_game_over() -> None:
    check_achievements()


def _checkers() -> dict[str, Callable[[], bool]]:
    stats = st.session_state.game_stats
    actions = set(stats.get("actions", []))
    won = bool(st.session_state.get("game_won"))
    met = len(st.session_state.get("met_npc_ids", []))
    reason = str(st.session_state.get("game_over_reason", ""))

    return {
        "win_game": lambda: won,
        "clean_win": lambda: won and not stats.get("infected"),
        "full_health": lambda: won and st.session_state.health >= HEALTH_START,
        "wounded_win": lambda: won and st.session_state.health <= 30,
        "wire_mood": lambda: won and st.session_state.repression >= 85,
        "iron_refusal": lambda: won and actions.isdisjoint({"B", "C"}),
        "all_in": lambda: won and "C" in actions,
        "hiv_end": lambda: st.session_state.game_over
        and not won
        and ("HIV" in reason or "hiv" in reason.lower()),
        "first_infection": lambda: bool(stats.get("infected")),
        "trap_hit": lambda: bool(stats.get("from_trap")),
        "npc_fled": lambda: bool(stats.get("npc_fled")),
        "hospital": lambda: bool(stats.get("treated")),
        "coser_fan": lambda: bool(stats.get("met_coser")),
        "speed_run": lambda: met >= WIN_TURN_TARGET,
    }


def check_achievements() -> list[str]:
    init_achievement_state()
    newly: list[str] = []
    for aid, fn in _checkers().items():
        if aid in _persistent_set():
            continue
        try:
            if fn() and _unlock(aid):
                newly.append(aid)
        except Exception:
            continue
    return newly


def show_achievement_toasts() -> None:
    for aid in st.session_state.get("achievements_new", []):
        meta = ACHIEVEMENTS.get(aid, {})
        st.toast(
            f"{meta.get('icon', '🏆')} 成就解锁：{meta.get('title', aid)}",
            icon="🏆",
        )
    st.session_state.achievements_new = []


def achievements_new_this_run() -> list[str]:
    start = set(st.session_state.get("achievements_at_run_start", []))
    return [a for a in st.session_state.achievements_persistent if a not in start]


def render_achievements_sidebar(*, compact: bool = False) -> None:
    init_achievement_state()
    unlocked = _persistent_set()
    total = len(ACHIEVEMENTS)
    if not compact:
        st.subheader("成就")
    st.caption(f"已解锁 {len(unlocked)} / {total}（同浏览器可保留）")

    with st.expander("查看全部成就", expanded=False):
        for aid, meta in ACHIEVEMENTS.items():
            if aid in unlocked:
                st.markdown(
                    f"{meta['icon']} **{meta['title']}** — {meta['desc']} ✓"
                )
            else:
                st.markdown(f"🔒 ~~{meta['title']}~~ — ???")


def render_new_achievements_banner() -> None:
    check_achievements()
    new = achievements_new_this_run()
    if not new:
        return
    st.subheader("🏆 本局新解锁成就")
    for aid in new:
        meta = ACHIEVEMENTS[aid]
        st.success(f"{meta['icon']} **{meta['title']}** — {meta['desc']}")
