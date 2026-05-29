"""遭遇事件生成、交互与行动结算。"""

from __future__ import annotations

import random
from typing import Any

import streamlit as st

from config import (
    ACTIONS,
    CONDOM_BREACH_CHANCE,
    CONDOM_BREACH_RISK_MULTIPLIER,
    INFECTION_NARRATIVES,
    INTERACTIONS,
    NPC_FLEE_REPRESSION_PENALTY,
    PROBING_INTERACTIONS,
    SAFE_STREAK_LONELINESS_BASE,
    SAFE_STREAK_LONELINESS_START,
    SAFE_STREAK_LONELINESS_STEP,
    SPAWN_HIGH_RISK_BIAS_AFTER_TURN,
    SPAWN_HIGH_RISK_WEIGHT_FACTOR,
)
from engine.game_state import (
    add_infection,
    append_clue,
    append_history,
    after_encounter_resolved,
    apply_health_delta,
    apply_repression_delta,
    check_game_over,
    count_probing_interactions,
    get_flee_probe_limit,
    interaction_already_used,
    mark_interaction_used,
    reset_encounter_meta,
    start_new_event_turn,
    trigger_instant_game_over,
)
from engine.roster import append_encounter_roster
from engine.copy import pick_health_edu
from engine.npc_policy import is_action_allowed
from engine.risk_calculator import (
    calc_infection_probability,
    create_infection_record,
    get_action_infection_probability,
    get_initial_damage,
    pick_disease_for_depth,
    roll_infection,
    run_test_kit_reading,
)


def spawn_npc() -> dict[str, Any]:
    """随机抽取未在本局出现过的嘉宾；全员见过后洗牌重来。"""
    all_npcs = st.session_state.npcs
    met: set[str] = set(st.session_state.get("met_npc_ids", []))
    pool = [n for n in all_npcs if n["id"] not in met]

    if not pool:
        st.session_state.met_npc_ids = []
        met = set()
        pool = list(all_npcs)
        append_history("嘉宾轮换", "本局嘉宾已全部登场，池子重新洗牌", "")

    turn = st.session_state.turn_count
    if turn > SPAWN_HIGH_RISK_BIAS_AFTER_TURN:
        weights = [
            1.0 + float(n["base_risk"]) * SPAWN_HIGH_RISK_WEIGHT_FACTOR for n in pool
        ]
        npc = random.choices(pool, weights=weights, k=1)[0]
    else:
        npc = random.choice(pool)
    st.session_state.met_npc_ids.append(npc["id"])
    st.session_state.current_npc = npc
    st.session_state.awaiting_action = True
    from engine.achievements import record_npc_encounter

    record_npc_encounter(npc)
    return npc


def _end_encounter() -> None:
    st.session_state.awaiting_action = False
    st.session_state.current_npc = None
    st.session_state.encounter_clues = []
    st.session_state.interactions_used = []


def _infection_narrative(disease_id: str, npc_name: str, action_label: str) -> str:
    templates = INFECTION_NARRATIVES.get(disease_id, [])
    if not templates:
        return f"—— 感染叙事 ——\n与【{npc_name}】那晚的「{action_label}」，在你心里留下无法抹去的痕迹。"
    body = random.choice(templates).format(npc=npc_name)
    return (
        f"—— 感染叙事 ——\n{body}\n"
        f"（记录：第 {st.session_state.turn_count} 回合 · 行动「{action_label}」）\n"
        f"{pick_health_edu()}"
    )


def trigger_npc_flee(npc_name: str) -> str:
    """追问过多，对方跑路并结束本轮遭遇。"""
    old_rep = st.session_state.repression
    apply_repression_delta(NPC_FLEE_REPRESSION_PENALTY)
    lines = [
        f"【{npc_name}】被你问得不耐烦，抓起外套夺门而出。",
        f"压抑值 {old_rep} → {st.session_state.repression}（被爽约 +{NPC_FLEE_REPRESSION_PENALTY}）。",
        "本轮遭遇结束，未发生亲密关系。",
    ]
    lines.append(pick_health_edu())
    result = "\n".join(lines)
    _end_encounter()
    st.session_state.last_result = result
    append_history("对方跑路", f"{npc_name} 因追问过多离开", result)
    append_encounter_roster(
        outcome="fled",
        summary="追问过多，对方离开",
    )
    from engine.achievements import record_npc_fled

    record_npc_fled()
    after_encounter_resolved()
    return result


def begin_encounter() -> None:
    """生成新遭遇。"""
    if st.session_state.get("game_over"):
        return

    turn_logs = start_new_event_turn()
    reset_encounter_meta()
    npc = spawn_npc()
    intro_lines = turn_logs + [
        f"你遇到了【{npc['name']}】，可先试探，再做出抉择。",
        pick_health_edu(),
    ]
    st.session_state.last_result = "\n".join(intro_lines)
    append_history("遭遇开始", f"遇到 {npc['name']}", npc["description"][:120])


def _npc_risk(npc: dict[str, Any]) -> float:
    return float(npc["base_risk"])


def _run_interaction_body(interaction_key: str, npc: dict[str, Any], risk: float) -> list[str]:
    lines: list[str] = []
    name = npc["name"]

    if interaction_key == "test_kit":
        tier, false_negative = run_test_kit_reading(
            risk, is_trap="trap" in (npc.get("tags") or [])
        )
        msg = f"试纸显示：{tier}。"
        if false_negative:
            msg += "（读数偏低，存在假阴性可能。）"
        else:
            msg += "（读数与样本一致。）"
        lines.append(msg)

    elif interaction_key == "ask_history":
        if risk < 0.25:
            lines.append(f"{name} 坦然提到近期体检正常，语气自然。")
        elif risk < 0.55:
            lines.append(f"{name} 含糊其辞，称「上火吃过抗生素」但说不清药名。")
        else:
            lines.append(f"{name} 明显不耐烦，拒绝深谈病史。")

    elif interaction_key == "request_report":
        roll = random.random()
        if risk < 0.3 and roll < 0.85:
            lines.append(f"{name} 主动出示近期阴性报告，看起来靠谱。")
        elif risk < 0.65:
            if roll < 0.5:
                lines.append(f"{name} 推脱说报告忘带了，眼神闪躲。")
            else:
                lines.append(f"{name} 出示三个月前的报告，称「最近忙没复查」。")
        else:
            if roll < 0.35:
                lines.append(f"{name} 强硬拒绝：「不信就算了」。")
            else:
                lines.append(f"{name} 拿出模糊手机截图，日期看不清，可疑。")

    elif interaction_key == "observe":
        if risk < 0.25:
            lines.append("你注意到对方精神状态稳定，体表无明显异常。")
        elif risk < 0.55:
            lines.append("你注意到遮瑕痕迹、旧抓痕或药物包装等疑点。")
        else:
            lines.append("你注意到皮疹结痂、针眼旧痕或强烈异味等危险信号。")

    elif interaction_key == "discuss_protection":
        if risk < 0.3:
            lines.append(f"{name} 主动提出全程做好防护，态度配合。")
        elif risk < 0.65:
            lines.append(f"{name} 口头答应，但对具体措施显得敷衍。")
        else:
            lines.append(f"{name} 对安全措施抵触，倾向「别那么多事」。")

    return lines


def apply_interaction(interaction_key: str) -> str:
    if not st.session_state.awaiting_action or not st.session_state.current_npc:
        return "当前没有进行中的遭遇。"

    if interaction_already_used(interaction_key):
        return "本轮已使用过该互动。"

    npc = st.session_state.current_npc
    risk = _npc_risk(npc)
    cfg = INTERACTIONS[interaction_key]
    body = _run_interaction_body(interaction_key, npc, risk)
    lines = [f"【{cfg['label']}】", *body]

    result = " ".join(lines)
    append_clue(result)
    mark_interaction_used(interaction_key)
    append_history("遭遇前互动", f"{cfg['label']} → {npc['name']}", result)

    flee_limit = get_flee_probe_limit()
    probes = count_probing_interactions()
    if interaction_key in PROBING_INTERACTIONS and probes >= flee_limit:
        flee_msg = trigger_npc_flee(npc["name"])
        return result + "\n\n" + flee_msg

    st.session_state.last_result = result
    return result


def resolve_action(action_key: str) -> str:
    if not st.session_state.awaiting_action or not st.session_state.current_npc:
        return "当前没有可处理的遭遇。"

    npc = st.session_state.current_npc
    if not is_action_allowed(npc, action_key):
        return "对方不接受该选项。"

    action = ACTIONS[action_key]
    diseases = st.session_state.diseases

    lines: list[str] = []
    if st.session_state.encounter_clues:
        lines.append("—— 本轮已收集线索 ——")
        lines.extend(f"· {c}" for c in st.session_state.encounter_clues)
        lines.append("—— 行动结算 ——")

    lines.append(f"你选择了【{action['label']}】，与 {npc['name']} 的互动结束。")

    from engine.achievements import check_achievements, record_action, record_infection

    record_action(action_key)

    old_rep = st.session_state.repression
    apply_repression_delta(action["repression_delta"])

    if action_key == "A":
        streak = int(st.session_state.get("safe_streak", 0)) + 1
        st.session_state.safe_streak = streak
        if streak >= SAFE_STREAK_LONELINESS_START:
            extra = SAFE_STREAK_LONELINESS_BASE + (
                streak - SAFE_STREAK_LONELINESS_START
            ) * SAFE_STREAK_LONELINESS_STEP
            apply_repression_delta(extra)
            lines.append(f"一再克制让今晚更空（压抑额外 +{extra}）。")
    else:
        st.session_state.safe_streak = 0

    lines.append(
        f"压抑值 {old_rep} → {st.session_state.repression}（含行动与额外变化）。"
    )

    risk = _npc_risk(npc)
    prob = get_action_infection_probability(action, risk)
    breach = False
    if action_key == "A" and prob > 0 and random.random() < CONDOM_BREACH_CHANCE:
        breach = True
        prob = calc_infection_probability(risk, CONDOM_BREACH_RISK_MULTIPLIER)

    roster_outcome = "left" if action_key == "D" else "completed"
    roster_summary = action["label"]
    roster_disease = ""

    if prob > 0:
        if roll_infection(prob):
            if breach:
                lines.append("你明明做了防护，仍出了难以预料的疏漏……")
            disease = pick_disease_for_depth(action["depth"], diseases)
            if disease:
                if disease.get("instant_game_over"):
                    trigger_instant_game_over("确诊 HIV，游戏结束。")
                    from engine.achievements import record_hiv_game_over

                    record_hiv_game_over()
                    roster_outcome = "hiv"
                    roster_summary = f"{action['label']} · 确诊 HIV"
                    lines.append(
                        "确诊 **HIV**，精神与健康防线瞬间崩溃，游戏立刻结束。"
                    )
                    lines.append(
                        _infection_narrative(
                            disease["id"], npc["name"], action["label"]
                        )
                    )
                else:
                    initial = get_initial_damage(disease)
                    old_health = st.session_state.health
                    apply_health_delta(-initial)
                    record = create_infection_record(disease, npc["name"])
                    record["action_label"] = action["label"]
                    record["encounter_turn"] = st.session_state.turn_count
                    add_infection(record)
                    record_infection(disease["id"], npc)
                    roster_outcome = "infected"
                    roster_disease = disease["name"]
                    roster_summary = f"{action['label']} · 感染{disease['name']}"
                    lines.append(
                        f"你已感染「{disease['name']}」，身体立刻受到冲击，"
                        f"健康值 {old_health} → {st.session_state.health}（首击 -{initial}）。"
                    )
                    if disease["incubation_turns"] > 0:
                        lines.append(
                            f"症状仍在潜伏期（剩余 {disease['incubation_turns']} 轮），"
                            f"发作后每轮还将持续 -{disease['damage_per_turn']} 健康。"
                        )
                    lines.append(
                        _infection_narrative(
                            disease["id"], npc["name"], action["label"]
                        )
                    )
                    append_history(
                        "感染",
                        f"「{disease['name']}」← {npc['name']}",
                        lines[-1],
                    )
                    check_game_over()
        # 未感染：不展示判定过程，保持悬念
    elif action_key == "D":
        lines.append("你明确婉拒并直接离场，孤独感加重了压抑。")
        roster_summary = "婉拒离场"
    # 全程安全保护且未感染：同样不额外提示

    lines.append(pick_health_edu())
    result = "\n".join(lines)
    append_encounter_roster(
        outcome=roster_outcome,
        summary=roster_summary,
        action_label=action["label"],
        disease_name=roster_disease,
    )
    _end_encounter()
    st.session_state.last_result = result
    append_history("亲密抉择", f"{action['label']} @ {npc['name']}", result)
    check_achievements()
    after_encounter_resolved()
    return result
