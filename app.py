"""压抑模拟器 — Streamlit 主入口。"""

import streamlit as st

from config import (
    ACTIONS,
    GAME_INTRO,
    INTERACTIONS,
    REPRESSION_MAX,
    TREATMENT_REPRESSION_PENALTY,
    WIN_TURN_TARGET,
)
from engine.copy import pick_health_edu
from engine.event_system import apply_interaction, begin_encounter, resolve_action
from engine.game_state import (
    check_game_over,
    get_disease_display,
    init_session_state,
    interaction_already_used,
    load_game_data,
    reset_game,
    treat_disease,
)

st.set_page_config(
    page_title="压抑模拟器",
    page_icon="🎭",
    layout="wide",
)

st.title("🎭 压抑模拟器")
st.caption(f"在压抑与健康之间寻找平衡 · 目标：存活 {WIN_TURN_TARGET} 回合")


def render_game_intro() -> None:
    """开局介绍（未开始遭遇时显示）。"""
    if st.session_state.turn_count == 0 and not st.session_state.current_npc:
        with st.expander("游戏介绍与性病防治提示", expanded=True):
            st.markdown(GAME_INTRO)


def render_sidebar() -> None:
    with st.sidebar:
        st.header("生存面板")

        rep = st.session_state.repression
        health = st.session_state.health

        st.subheader("压抑值")
        st.progress(rep / REPRESSION_MAX)
        st.write(f"{rep} / {REPRESSION_MAX}")
        if rep >= 80:
            st.error("情绪濒临失控！")

        st.subheader("健康值")
        st.progress(max(0, health) / 100)
        st.write(f"{health} / 100")

        st.divider()
        st.subheader("疾病状态")
        infections = st.session_state.infections
        if not infections:
            st.success("暂无感染")
        else:
            for i, inf in enumerate(infections):
                st.warning(get_disease_display(inf))
                diseases = st.session_state.diseases
                disease = diseases.get(inf["disease_id"], {})
                if disease.get("curable", True) and not disease.get(
                    "instant_game_over", False
                ):
                    if st.button(
                        f"治疗 {inf['disease_name']}（压抑+{TREATMENT_REPRESSION_PENALTY}）",
                        key=f"treat_{i}_{inf['disease_id']}",
                        disabled=st.session_state.game_over,
                    ):
                        msg = treat_disease(i)
                        st.session_state.last_result = msg + "\n" + pick_health_edu()
                        st.rerun()
                else:
                    st.caption(f"  · {inf['disease_name']}：无法治愈")

        st.divider()
        turn = st.session_state.turn_count
        st.caption(f"存活回合：{turn} / {WIN_TURN_TARGET}")
        st.progress(min(1.0, turn / WIN_TURN_TARGET))
        met = len(st.session_state.get("met_npc_ids", []))
        st.caption(f"本局已遇嘉宾：{met} 人")

        st.subheader("历史记录")
        history = st.session_state.get("history_log", [])
        if not history:
            st.caption("暂无记录")
        else:
            with st.expander(f"共 {len(history)} 条", expanded=False):
                for item in history[:30]:
                    detail = item.get("detail", "")
                    line = f"**回合 {item['turn']}** · {item['type']} · {item['summary']}"
                    st.markdown(line)
                    if detail:
                        st.caption(
                            detail[:120] + ("…" if len(detail) > 120 else "")
                        )

        if st.button("重新开始", type="secondary"):
            reset_game()
            st.rerun()


def render_history_main() -> None:
    history = st.session_state.get("history_log", [])
    with st.expander(f"📜 历史记录（{len(history)} 条）", expanded=False):
        if not history:
            st.caption("暂无记录，开始遭遇后会自动记录。")
        else:
            for item in history[:50]:
                st.markdown(
                    f"**回合 {item['turn']}** · `{item['type']}` · {item['summary']}"
                )
                if item.get("detail"):
                    st.caption(item["detail"][:200])


def render_interactions() -> None:
    st.markdown("**遭遇前互动**（每种每轮限 1 次）")

    keys = list(INTERACTIONS.keys())
    cols = st.columns(len(keys))

    for col, key in zip(cols, keys):
        cfg = INTERACTIONS[key]
        used = interaction_already_used(key)
        disabled = (
            not st.session_state.awaiting_action
            or used
            or st.session_state.game_over
        )
        with col:
            st.caption(cfg["description"])
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

    clues = st.session_state.encounter_clues
    if clues:
        with st.expander("本轮已收集线索", expanded=True):
            for c in clues:
                st.markdown(f"- {c}")


def render_actions() -> None:
    st.markdown("---")
    st.markdown("**亲密抉择**（选一项结束本轮）")

    cols = st.columns(4)
    for col, key in zip(cols, ["A", "B", "C", "D"]):
        act = ACTIONS[key]
        with col:
            st.markdown(f"**{key}**")
            st.caption(act.get("description") or act["label"])
            st.caption(f"压抑 {act['repression_delta']:+d}")
            if st.button(
                f"选择 {key}",
                key=f"action_{key}",
                use_container_width=True,
                disabled=not st.session_state.awaiting_action,
            ):
                resolve_action(key)
                st.rerun()


def render_last_settlement() -> None:
    """展示上一轮行动/跑路等结算文案。"""
    st.subheader("上一轮结算")
    if st.session_state.last_result:
        st.markdown(st.session_state.last_result.replace("\n", "\n\n"))
    else:
        st.caption("暂无结算，开始遭遇后将显示在这里。")


def render_game_over() -> None:
    won = st.session_state.get("game_won", False)
    if won:
        st.success(st.session_state.game_over_reason)
        st.info(
            "坚持到第 25 回合很不容易。现实中请继续保持：固定伴侣沟通、安全套、定期筛查、"
            "有症状尽早就医——这些习惯比任何一次侥幸都可靠。"
        )
    else:
        st.error(f"游戏结束：{st.session_state.game_over_reason}")
        st.warning(
            "无论胜负，真实性病感染都会带来身心代价。若你有过高危经历，请到正规医院皮肤性病科"
            "或疾控中心咨询检测；若已感染，规范治疗可控制多数病情，越早越好。"
        )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("最终压抑值", st.session_state.repression)
    with col2:
        st.metric("最终健康值", st.session_state.health)
    with col3:
        st.metric("存活回合", st.session_state.turn_count)
    if st.button("再来一局", type="primary"):
        reset_game()
        st.rerun()


def render_encounter() -> None:
    render_game_intro()

    npc = st.session_state.current_npc
    if not npc:
        between_encounters = (
            st.session_state.turn_count > 0 and not st.session_state.game_over
        )
        if between_encounters:
            if st.session_state.last_result:
                st.markdown("---")
                render_last_settlement()
            st.warning("本轮遭遇已结束。点击下方进入下一遭遇。")
        elif st.session_state.turn_count == 0:
            st.info("阅读上方介绍后，点击下方开始第一次遭遇。")

        if st.button(
            "开始 / 继续遭遇",
            type="primary",
            disabled=st.session_state.game_over or st.session_state.get("game_won"),
        ):
            begin_encounter()
            st.rerun()
        return

    tags = npc.get("tags") or []
    title = f"遭遇：{npc['name']}"
    if "coser" in tags:
        title += " 【Coser】"
    st.subheader(title)
    st.info(npc["description"])

    render_interactions()
    render_actions()

    if not st.session_state.awaiting_action:
        st.markdown("---")
        if st.button("进入下一遭遇 →", type="primary"):
            begin_encounter()
            st.rerun()


def main() -> None:
    init_session_state()
    load_game_data()
    from engine.game_state import check_victory

    check_game_over()
    check_victory()

    render_sidebar()

    if st.session_state.game_over:
        render_game_over()
        st.markdown("---")
        render_last_settlement()
        return

    render_encounter()

    st.markdown("---")
    render_history_main()
    # 遭遇进行中：底部保留上一轮结算；遭遇间隔已在上方展示，避免重复
    if st.session_state.current_npc:
        render_last_settlement()
    elif st.session_state.turn_count == 0 and not st.session_state.game_over:
        render_last_settlement()


if __name__ == "__main__":
    main()
