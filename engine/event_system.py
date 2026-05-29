"""遭遇事件生成、交互与行动结算。"""

from __future__ import annotations

import random
from typing import Any

import streamlit as st

from config import ACTIONS, INFECTION_NARRATIVES, INTERACTIONS, NPC_FLEE_REPRESSION_PENALTY, PROBING_INTERACTIONS
from engine.game_state import (
    add_infection,
    append_clue,
    append_history,
    after_encounter_resolved,
    apply_repression_delta,
    count_probing_interactions,
    get_flee_probe_limit,
    interaction_already_used,
    mark_interaction_used,
    reset_encounter_meta,
    start_new_event_turn,
    trigger_instant_game_over,
)
from engine.copy import pick_health_edu
from engine.risk_calculator import (
    create_infection_record,
    get_action_infection_probability,
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

    npc = random.choice(pool)
    st.session_state.met_npc_ids.append(npc["id"])
    st.session_state.current_npc = npc
    st.session_state.awaiting_action = True
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
    action = ACTIONS[action_key]
    diseases = st.session_state.diseases

    lines: list[str] = []
    if st.session_state.encounter_clues:
        lines.append("—— 本轮已收集线索 ——")
        lines.extend(f"· {c}" for c in st.session_state.encounter_clues)
        lines.append("—— 行动结算 ——")

    lines.append(f"你选择了【{action['label']}】，与 {npc['name']} 的互动结束。")

    old_rep = st.session_state.repression
    apply_repression_delta(action["repression_delta"])
    lines.append(
        f"压抑值 {old_rep} → {st.session_state.repression}（变化 {action['repression_delta']:+d}）。"
    )

    prob = get_action_infection_probability(action, _npc_risk(npc))

    if prob > 0:
        if roll_infection(prob):
            disease = pick_disease_for_depth(action["depth"], diseases)
            if disease:
                if disease.get("instant_game_over"):
                    trigger_instant_game_over("确诊 HIV，游戏结束。")
                    lines.append(
                        "确诊 **HIV**，精神与健康防线瞬间崩溃，游戏立刻结束。"
                    )
                    lines.append(
                        _infection_narrative(
                            disease["id"], npc["name"], action["label"]
                        )
                    )
                else:
                    record = create_infection_record(disease, npc["name"])
                    record["action_label"] = action["label"]
                    record["encounter_turn"] = st.session_state.turn_count
                    add_infection(record)
                    lines.append(
                        f"你已感染「{disease['name']}」，"
                        f"潜伏期 {disease['incubation_turns']} 轮（尚未扣血）。"
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
        # 未感染：不展示判定过程，保持悬念
    elif action_key == "D":
        lines.append("你明确婉拒并直接离场，孤独感加重了压抑。")
    # 全程安全保护且未感染：同样不额外提示

    lines.append(pick_health_edu())
    result = "\n".join(lines)
    _end_encounter()
    st.session_state.last_result = result
    append_history("亲密抉择", f"{action['label']} @ {npc['name']}", result)
    after_encounter_resolved()
    return result
