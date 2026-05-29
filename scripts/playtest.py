"""无 UI 试玩：模拟多轮遭遇，检查逻辑与边界。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 在导入 engine 前注入 mock streamlit
mock_st = MagicMock()
mock_st.session_state = {}


class SessionState(dict):
    """兼容属性访问的 session_state。"""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e

    def __setattr__(self, key, value):
        self[key] = value


sys.modules["streamlit"] = mock_st

from config import (  # noqa: E402
    ACTIONS,
    MAX_PROBES_BEFORE_FLEE,
    NPC_FLEE_REPRESSION_PENALTY,
    PROBING_INTERACTIONS,
    REPRESSION_START,
)
from engine import game_state, event_system  # noqa: E402


def setup_fresh_game() -> SessionState:
    ss = SessionState()
    mock_st.session_state = ss
    game_state.init_session_state()
    game_state.load_game_data()
    return ss


def play_round(
    ss: SessionState,
    *,
    probes: list[str] | None = None,
    action: str = "A",
    label: str = "",
) -> dict:
    event_system.begin_encounter()
    if probes:
        for p in probes:
            event_system.apply_interaction(p)
            if not ss.get("awaiting_action"):
                break
    if ss.get("awaiting_action"):
        event_system.resolve_action(action)
    return {
        "label": label,
        "turn": ss.turn_count,
        "repression": ss.repression,
        "health": ss.health,
        "game_over": ss.game_over,
        "reason": ss.get("game_over_reason", ""),
        "infections": [i["disease_name"] for i in ss.infections],
        "awaiting": ss.awaiting_action,
        "history_len": len(ss.history_log),
    }


def main() -> None:
    issues: list[str] = []

    print("=== 试玩 1：安全路线 A × 3 ===")
    ss = setup_fresh_game()
    for i in range(3):
        r = play_round(ss, action="A", label=f"A-{i+1}")
        print(r)
        if ss.game_over:
            break
    if ss.repression >= 100:
        issues.append("连续 A 三轮压抑仍爆表？需核对数值")
    if not ss.history_log:
        issues.append("历史记录为空")

    print("\n=== 试玩 2：追问 3 次触发跑路 ===")
    ss = setup_fresh_game()
    event_system.begin_encounter()
    probe_keys = list(PROBING_INTERACTIONS)[:MAX_PROBES_BEFORE_FLEE]
    for k in probe_keys:
        msg = event_system.apply_interaction(k)
        print(f"  {k}: awaiting={ss.awaiting_action}, rep={ss.repression}")
    if ss.awaiting_action:
        issues.append("追问 3 次后应结束遭遇但未结束")
    if ss.repression < REPRESSION_START + 15 + NPC_FLEE_REPRESSION_PENALTY - 5:
        issues.append(f"跑路后压抑未正确 +25（当前 {ss.repression}）")
    flee_hist = [h for h in ss.history_log if h["type"] == "对方跑路"]
    if not flee_hist:
        issues.append("跑路未写入历史")

    print("\n=== 试玩 3：拒绝 D ===")
    ss = setup_fresh_game()
    r = play_round(ss, action="D", label="拒绝")
    print(r)
    if ss.repression <= REPRESSION_START + 15:
        issues.append("D 选项 +20 压抑可能未生效")

    print("\n=== 试玩 4：治疗 +50 压抑 ===")
    ss = setup_fresh_game()
    ss.infections.append(
        {
            "disease_id": "syphilis",
            "disease_name": "梅毒",
            "incubation_remaining": 2,
            "damage_per_turn": 8,
            "curable": True,
            "is_active": False,
            "source_npc": "测试",
        }
    )
    before = ss.repression
    game_state.treat_disease(0)
    if ss.repression != min(100, before + 50):
        issues.append(f"治疗后压抑应为 {before+50}，实际 {ss.repression}")

    print("\n=== 试玩 5：init 缺 history_log 兼容 ===")
    ss = SessionState({"initialized": True, "repression": 50, "health": 100})
    mock_st.session_state = ss
    game_state.append_history("测试", "摘要")
    if "history_log" not in ss:
        issues.append("旧存档无 history_log 时 append_history 失败")

    print("\n=== 问题汇总 ===")
    if issues:
        for i, x in enumerate(issues, 1):
            print(f"  {i}. {x}")
        sys.exit(1)
    print("  未发现逻辑问题。")


if __name__ == "__main__":
    main()
