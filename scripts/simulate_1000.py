"""多策略 × 千局自动模拟，打印平衡对比。"""

from __future__ import annotations

import random
import sys
import types
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

mock_st = MagicMock()
mock_components = types.ModuleType("streamlit.components.v1")
sys.modules["streamlit"] = mock_st
sys.modules["streamlit.components"] = types.ModuleType("streamlit.components")
sys.modules["streamlit.components.v1"] = mock_components


class SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e

    def __setattr__(self, key, value):
        self[key] = value


from config import (  # noqa: E402
    ACTIONS,
    HEALTH_START,
    REPRESSION_MAX,
    REPRESSION_START,
    WIN_TURN_TARGET,
)
from engine import event_system, game_state  # noqa: E402
from engine.npc_policy import get_action_policy, is_action_allowed  # noqa: E402

INTERACTION_KEYS = (
    "test_kit",
    "ask_history",
    "request_report",
    "observe",
    "discuss_protection",
)


@dataclass
class Strategy:
    id: str
    name: str
    pick_probes: Callable[[dict, random.Random], list[str]]
    pick_action: Callable[[dict, random.Random], str]
    auto_treat: bool = True


def _first_allowed(npc: dict, order: tuple[str, ...]) -> str:
    for key in order:
        if is_action_allowed(npc, key):
            return key
    return "D"


def _weighted_pick(npc: dict, rng: random.Random, weights: list[tuple[str, float]]) -> str:
    roll = rng.random()
    for key, w in weights:
        if not is_action_allowed(npc, key):
            continue
        if roll < w:
            return key
        roll -= w
    return _first_allowed(npc, ("A", "B", "C", "D"))


# —— 策略定义 ——


def probes_none(_npc: dict, _rng: random.Random) -> list[str]:
    return []


def probes_discuss_only(_npc: dict, _rng: random.Random) -> list[str]:
    return ["discuss_protection"]


def probes_cautious(_npc: dict, rng: random.Random) -> list[str]:
    keys = ["discuss_protection", "test_kit", "observe"]
    rng.shuffle(keys)
    return keys[: rng.randint(2, 3)]


def probes_aggressive(_npc: dict, rng: random.Random) -> list[str]:
    return ["test_kit"] if rng.random() < 0.3 else []


def action_always_safe(npc: dict, _rng: random.Random) -> str:
    return _first_allowed(npc, ("A", "D"))


def action_always_risky(npc: dict, _rng: random.Random) -> str:
    return _first_allowed(npc, ("C", "B", "D"))


def action_mostly_leave(npc: dict, rng: random.Random) -> str:
    if rng.random() < 0.45:
        return "D" if is_action_allowed(npc, "D") else "A"
    return _first_allowed(npc, ("A", "B", "C", "D"))


def action_policy_mixed(npc: dict, rng: random.Random) -> str:
    policy = get_action_policy(npc)
    if policy == "refuse_condom":
        return _weighted_pick(npc, rng, [("B", 0.55), ("C", 0.35), ("D", 0.10)])
    if policy == "refuse_raw":
        return _weighted_pick(npc, rng, [("A", 0.45), ("B", 0.40), ("D", 0.15)])
    return _weighted_pick(
        npc, rng, [("A", 0.28), ("B", 0.42), ("C", 0.22), ("D", 0.08)]
    )


def action_conservative(npc: dict, rng: random.Random) -> str:
    policy = get_action_policy(npc)
    if policy == "refuse_condom":
        return _weighted_pick(npc, rng, [("B", 0.25), ("D", 0.55), ("C", 0.20)])
    return _weighted_pick(npc, rng, [("A", 0.72), ("B", 0.18), ("D", 0.10)])


def action_aggressive(npc: dict, rng: random.Random) -> str:
    policy = get_action_policy(npc)
    if policy == "refuse_raw":
        return _weighted_pick(npc, rng, [("B", 0.65), ("A", 0.25), ("D", 0.10)])
    return _weighted_pick(npc, rng, [("C", 0.45), ("B", 0.40), ("D", 0.15)])


def action_yolo(npc: dict, rng: random.Random) -> str:
    return _weighted_pick(npc, rng, [("C", 0.70), ("B", 0.25), ("D", 0.05)])


def action_random(npc: dict, rng: random.Random) -> str:
    allowed = [k for k in ("A", "B", "C", "D") if is_action_allowed(npc, k)]
    return rng.choice(allowed) if allowed else "D"


STRATEGIES: list[Strategy] = [
    Strategy("mixed", "均衡型（先聊防护+按policy）", probes_discuss_only, action_policy_mixed),
    Strategy("conservative", "保守型（偏A，拒戴套时多离场）", probes_cautious, action_conservative),
    Strategy("aggressive", "激进型（偏B/C）", probes_aggressive, action_aggressive),
    Strategy("always_safe", "全安全（能A就A）", probes_discuss_only, action_always_safe),
    Strategy("always_risky", "全冒险（能C就C）", probes_none, action_always_risky),
    Strategy("yolo", "莽夫（70%冲C）", probes_none, action_yolo),
    Strategy("hermit", "社恐（常选D）", probes_none, action_mostly_leave, auto_treat=False),
    Strategy("blind", "盲选（不试探随机行动）", probes_none, action_random),
]


@dataclass
class SimStats:
    games: int = 0
    wins: int = 0
    end_hiv: int = 0
    end_repression: int = 0
    end_health: int = 0
    end_other: int = 0
    with_infection: int = 0
    clean_wins: int = 0
    total_turns: int = 0
    total_rep: int = 0
    total_hp: int = 0
    total_inf_events: int = 0
    total_fled: int = 0
    actions: Counter = field(default_factory=Counter)
    diseases: Counter = field(default_factory=Counter)


def try_treat(ss: SessionState) -> bool:
    if ss.health > 45 or ss.repression > REPRESSION_MAX - 15:
        return False
    for i, inf in enumerate(ss.infections):
        d = ss.diseases.get(inf["disease_id"], {})
        if d.get("curable") and not d.get("instant_game_over"):
            game_state.treat_disease(i)
            return True
    return False


def play_one_game(strategy: Strategy, seed: int) -> SimStats:
    rng = random.Random(seed)
    random.seed(seed)

    ss = SessionState()
    mock_st.session_state = ss
    game_state.init_session_state()
    game_state.load_game_data()

    st = SimStats(games=1)
    max_turns = WIN_TURN_TARGET + 10

    while not ss.game_over and ss.turn_count < max_turns:
        if strategy.auto_treat and ss.infections:
            try_treat(ss)

        event_system.begin_encounter()
        if ss.game_over:
            break

        npc = ss.current_npc
        if not npc or not ss.awaiting_action:
            break

        for key in strategy.pick_probes(npc, rng):
            if not ss.awaiting_action:
                break
            event_system.apply_interaction(key)
            if not ss.awaiting_action:
                st.total_fled += 1
                break

        if not ss.awaiting_action:
            continue

        action = strategy.pick_action(npc, rng)
        before_inf = len(ss.infections)
        event_system.resolve_action(action)
        st.actions[action] += 1
        if len(ss.infections) > before_inf:
            st.total_inf_events += 1
            for inf in ss.infections[before_inf:]:
                st.diseases[inf["disease_name"]] += 1

        if ss.game_over:
            break

    reason = str(ss.get("game_over_reason", ""))
    won = bool(ss.get("game_won"))

    if "确诊 HIV" in reason:
        st.end_hiv += 1
    elif won or "成功存活" in reason:
        st.wins += 1
    elif "健康值归零" in reason or "身体垮掉" in reason:
        st.end_health += 1
    elif "压抑值爆表" in reason or "精神崩溃" in reason:
        st.end_repression += 1
    else:
        st.end_other += 1

    if ss.infections:
        st.with_infection = 1
    if won and not ss.infections:
        st.clean_wins = 1

    st.total_turns = ss.turn_count
    st.total_rep = ss.repression
    st.total_hp = ss.health
    return st


def merge_stats(acc: SimStats, one: SimStats) -> None:
    acc.games += one.games
    acc.wins += one.wins
    acc.end_hiv += one.end_hiv
    acc.end_repression += one.end_repression
    acc.end_health += one.end_health
    acc.end_other += one.end_other
    acc.with_infection += one.with_infection
    acc.clean_wins += one.clean_wins
    acc.total_turns += one.total_turns
    acc.total_rep += one.total_rep
    acc.total_hp += one.total_hp
    acc.total_inf_events += one.total_inf_events
    acc.total_fled += one.total_fled
    acc.actions += one.actions
    acc.diseases += one.diseases


def run_strategy(strategy: Strategy, n: int, base_seed: int) -> SimStats:
    total = SimStats()
    for i in range(n):
        merge_stats(total, play_one_game(strategy, base_seed + i))
    return total


def pct(n: int, d: int) -> str:
    return f"{n / d * 100:.1f}%" if d else "—"


def print_report(strategy: Strategy, s: SimStats, n: int) -> None:
    g = s.games
    print(f"\n{'─' * 60}")
    print(f"【{strategy.name}】 id={strategy.id}  n={g}")
    print(f"  胜利 {s.wins} ({pct(s.wins, g)})  零感染胜 {s.clean_wins} ({pct(s.clean_wins, g)})")
    print(
        f"  失败 {g - s.wins}: HIV {s.end_hiv} ({pct(s.end_hiv, g)}) | "
        f"压抑 {s.end_repression} | 健康 {s.end_health} | 其他 {s.end_other}"
    )
    print(
        f"  感染≥1次 {s.with_infection} ({pct(s.with_infection, g)})  "
        f"场均感染事件 {s.total_inf_events / g:.2f}  病种 {dict(s.diseases)}"
    )
    print(
        f"  场均回合 {s.total_turns / g:.2f}  "
        f"压抑 {s.total_rep / g:.1f}  健康 {s.total_hp / g:.1f}  "
        f"跑路 {s.total_fled / g:.2f}/局"
    )
    acts = s.actions
    total_a = sum(acts.values()) or 1
    parts = []
    for k in ("A", "B", "C", "D"):
        c = acts.get(k, 0)
        parts.append(f"{k}{c / total_a * 100:.0f}%")
    print(f"  行动占比 {' '.join(parts)}")


def print_summary_table(rows: list[tuple[Strategy, SimStats]], n: int) -> None:
    print(f"\n{'=' * 72}")
    print(f"千局对比总表（每策略 {n} 局，目标存活 {WIN_TURN_TARGET} 回合）")
    print(f"{'=' * 72}")
    header = (
        f"{'策略':<14} {'胜率':>7} {'感染率':>7} {'HIV死':>7} "
        f"{'压抑死':>7} {'均回合':>7} {'均压抑':>7} {'均健康':>7} {'A%':>5} {'B%':>5} {'C%':>5}"
    )
    print(header)
    print("-" * len(header))
    for st, s in rows:
        g = s.games
        ta = sum(s.actions.values()) or 1
        print(
            f"{st.name:<14} "
            f"{pct(s.wins, g):>7} {pct(s.with_infection, g):>7} {pct(s.end_hiv, g):>7} "
            f"{pct(s.end_repression, g):>7} {s.total_turns / g:>7.2f} "
            f"{s.total_rep / g:>7.1f} {s.total_hp / g:>7.1f} "
            f"{s.actions.get('A', 0) / ta * 100:>5.0f} "
            f"{s.actions.get('B', 0) / ta * 100:>5.0f} "
            f"{s.actions.get('C', 0) / ta * 100:>5.0f}"
        )
    print(f"{'=' * 72}\n")


def main() -> None:
    n = 1000
    rows: list[tuple[Strategy, SimStats]] = []

    print(f"开始模拟：{len(STRATEGIES)} 种策略 × {n} 局 = {len(STRATEGIES) * n} 局")

    for idx, strategy in enumerate(STRATEGIES):
        base_seed = 10_000 + idx * 100_000
        stats = run_strategy(strategy, n, base_seed)
        rows.append((strategy, stats))
        print_report(strategy, stats, n)

    print_summary_table(rows, n)


if __name__ == "__main__":
    main()
