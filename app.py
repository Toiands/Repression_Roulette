"""压抑模拟器 — Streamlit 主入口（月抛模拟器风格 UI）。"""

import streamlit as st

from config import (
    ACTIONS,
    GAME_INTRO,
    INTERACTIONS,
    REPRESSION_MAX,
    TREATMENT_REPRESSION_PENALTY,
    WIN_TURN_TARGET,
)
from engine.achievements import (
    render_achievements_sidebar,
    render_new_achievements_banner,
    show_achievement_toasts,
)
from engine.copy import pick_health_edu
from engine.event_system import apply_interaction, begin_encounter, resolve_action
from engine.npc_policy import action_disabled_hint, is_action_allowed
from engine.game_state import (
    check_game_over,
    get_disease_display,
    init_session_state,
    interaction_already_used,
    load_game_data,
    reset_game,
    treat_disease,
)
from ui.theme import (
    action_button_label,
    close_glass_card,
    game_layout,
    inject_theme,
    render_clue_tags,
    render_encounter_roster,
    render_intro_screen,
    render_partner_card,
    render_settlement_box,
    render_stat_bars,
    render_top_header,
    render_warn_banner,
    section_title,
)

st.set_page_config(
    page_title="压抑模拟器",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _ensure_ui_state() -> None:
    if "ui_started" not in st.session_state:
        st.session_state.ui_started = False


@st.dialog("游戏指南手册")
def show_help_dialog() -> None:
    st.markdown(GAME_INTRO)
    if st.button("知道了", type="primary", use_container_width=True):
        st.rerun()


def render_hospital_row() -> None:
    """侧边治疗改为卡片内「医院检查」行。"""
    infections = st.session_state.infections
    if not infections:
        return
    section_title("🏥 医院检查")
    diseases = st.session_state.diseases
    for i, inf in enumerate(infections):
        disease = diseases.get(inf["disease_id"], {})
        if disease.get("curable", True) and not disease.get("instant_game_over", False):
            if st.button(
                f"治疗 {inf['disease_name']}（压抑+{TREATMENT_REPRESSION_PENALTY}）",
                key=f"treat_{i}_{inf['disease_id']}",
                use_container_width=True,
                disabled=st.session_state.game_over,
            ):
                msg = treat_disease(i)
                st.session_state.last_result = msg + "\n" + pick_health_edu()
                st.rerun()
        else:
            st.caption(f"· {inf['disease_name']}：无法常规治疗")


def _interaction_button(key: str) -> None:
    cfg = INTERACTIONS[key]
    used = interaction_already_used(key)
    disabled = (
        not st.session_state.awaiting_action
        or used
        or st.session_state.game_over
    )
    label = cfg["label"] + (" ✓" if used else "")
    if st.button(
        label,
        key=f"interact_{key}",
        use_container_width=True,
        disabled=disabled,
    ):
        msg = apply_interaction(key)
        st.session_state.last_result = msg
        st.rerun()


def render_tool_row() -> None:
    """遭遇前互动：两行排布，避免五个按钮挤在一行。"""
    section_title("遭遇前试探")
    keys = list(INTERACTIONS.keys())
    row1 = st.columns(3)
    for col, key in zip(row1, keys[:3]):
        with col:
            _interaction_button(key)
    row2 = st.columns(2)
    for col, key in zip(row2, keys[3:]):
        with col:
            _interaction_button(key)


def render_action_grid() -> None:
    section_title("亲密抉择")
    npc = st.session_state.get("current_npc")
    base_disabled = not st.session_state.awaiting_action

    row1 = st.columns(2)
    for col, key in zip(row1, ["A", "B"]):
        with col:
            policy_disabled = not is_action_allowed(npc, key)
            if st.button(
                action_button_label(key),
                key=f"action_{key}",
                use_container_width=True,
                disabled=base_disabled or policy_disabled,
                help=action_disabled_hint(npc, key) if policy_disabled else None,
            ):
                resolve_action(key)
                st.rerun()

    row2 = st.columns(2)
    for col, key in zip(row2, ["C", "D"]):
        with col:
            policy_disabled = not is_action_allowed(npc, key)
            if st.button(
                action_button_label(key),
                key=f"action_{key}",
                use_container_width=True,
                disabled=base_disabled or policy_disabled,
                help=action_disabled_hint(npc, key) if policy_disabled else None,
            ):
                resolve_action(key)
                st.rerun()


def render_footer_panels() -> None:
    with st.expander("🏆 成就", expanded=False):
        render_achievements_sidebar(compact=True)
    with st.expander(f"📋 约会记录（{len(st.session_state.get('history_log', []))}）", expanded=False):
        history = st.session_state.get("history_log", [])
        if not history:
            st.caption("暂无记录")
        else:
            for item in history[:40]:
                st.markdown(
                    f"**回合 {item['turn']}** · {item['type']} · {item['summary']}"
                )
                if item.get("detail"):
                    st.caption(item["detail"][:160])
    if st.button("重新开始本局", type="secondary", use_container_width=True):
        reset_game()
        st.session_state.ui_started = True
        st.rerun()


def render_intro_flow() -> None:
    render_intro_screen()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("开始游戏", type="primary", use_container_width=True):
            st.session_state.ui_started = True
            st.rerun()
    with c2:
        if st.button("📖 游戏帮助", use_container_width=True):
            show_help_dialog()


def render_between_encounters() -> None:
    if st.session_state.last_result:
        section_title("上一轮结算")
        render_settlement_box(st.session_state.last_result)
    render_warn_banner("本轮遭遇已结束 · 点击下方继续")
    if st.button("继续下一遭遇 →", type="primary", use_container_width=True):
        begin_encounter()
        st.rerun()


def render_game_over() -> None:
    won = st.session_state.get("game_won", False)
    render_top_header(st.session_state.turn_count)
    render_stat_bars(st.session_state.repression, st.session_state.health)
    if won:
        st.success(st.session_state.game_over_reason)
        st.info(
            f"坚持到第 {WIN_TURN_TARGET} 回合很不容易。请继续保持：固定伴侣沟通、"
            "安全套、定期筛查、有症状尽早就医。"
        )
    else:
        st.error(f"游戏结束：{st.session_state.game_over_reason}")
    close_glass_card()

    if st.session_state.last_result:
        render_settlement_box(st.session_state.last_result)

    roster = st.session_state.get("encounter_roster", [])
    with st.expander(f"👥 本局嘉宾回顾（{len(roster)}）", expanded=True):
        render_encounter_roster(roster)

    render_new_achievements_banner()
    render_footer_panels()

    if st.button("再来一局", type="primary", use_container_width=True):
        reset_game()
        st.session_state.ui_started = True
        st.rerun()


def render_active_encounter() -> None:
    npc = st.session_state.current_npc
    turn = st.session_state.turn_count

    render_top_header(turn)
    render_stat_bars(st.session_state.repression, st.session_state.health)
    render_hospital_row()
    render_partner_card(npc)
    render_clue_tags(st.session_state.encounter_clues)
    render_tool_row()
    render_action_grid()
    close_glass_card()
    render_footer_panels()


def render_idle_start() -> None:
    render_top_header(0)
    render_stat_bars(st.session_state.repression, st.session_state.health)
    render_warn_banner("阅读规则后，点击下方开始第一次遭遇", tone="info")
    close_glass_card()
    if st.button("开始遭遇", type="primary", use_container_width=True):
        begin_encounter()
        st.rerun()
    render_footer_panels()


def main() -> None:
    inject_theme()
    _ensure_ui_state()
    init_session_state()
    load_game_data()

    from engine.game_state import check_victory

    check_game_over()
    check_victory()
    show_achievement_toasts()

    with game_layout():
        if not st.session_state.ui_started:
            render_intro_flow()
            return

        if st.session_state.game_over:
            render_game_over()
            return

        npc = st.session_state.current_npc
        if not npc:
            if st.session_state.turn_count > 0:
                render_top_header(st.session_state.turn_count)
                render_stat_bars(st.session_state.repression, st.session_state.health)
                render_hospital_row()
                close_glass_card()
                render_between_encounters()
                render_footer_panels()
            else:
                render_idle_start()
            return

        render_active_encounter()


if __name__ == "__main__":
    main()
