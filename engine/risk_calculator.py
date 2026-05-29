"""感染概率计算与暗骰结算。"""

from __future__ import annotations

import random
from typing import Any, Optional

from config import (
    DISEASE_POOL_BY_DEPTH,
    INFECTION_RISK_SCALE,
    TEST_KIT_FALSE_NEGATIVE_CHANCE,
)


def calc_infection_probability(base_risk: float, risk_multiplier: float) -> float:
    """计算本次行动的感染概率（基础风险 × 系数 × 全局缩放）。"""
    raw = base_risk * risk_multiplier * INFECTION_RISK_SCALE
    return min(1.0, max(0.0, raw))


def get_action_infection_probability(action: dict, base_risk: float) -> float:
    """感染概率 = 该嘉宾基础风险 × 行动风险系数。"""
    return calc_infection_probability(base_risk, action.get("risk_multiplier", 0))


def format_infection_formula(base_risk: float, multiplier: float) -> str:
    """生成感染概率公式说明。"""
    prob = calc_infection_probability(base_risk, multiplier)
    return f"{base_risk:.0%} × {multiplier:.0%} = {prob * 100:.2f}%"


def roll_infection(probability: float) -> bool:
    """根据概率进行暗骰，返回是否感染。"""
    if probability <= 0:
        return False
    return random.random() < probability


def risk_to_tier(base_risk: float) -> str:
    """将基础风险映射为可读档位。"""
    if base_risk < 0.2:
        return "低风险"
    if base_risk < 0.5:
        return "中低风险"
    if base_risk < 0.75:
        return "中高风险"
    return "高风险"


def run_test_kit_reading(
    base_risk: float, *, is_trap: bool = False
) -> tuple[str, bool]:
    """
    四联试纸读数：返回（显示档位, 是否假阴性）。
    高风险与暗雷嘉宾更易出现假阴性。
    """
    tier = risk_to_tier(base_risk)
    false_negative = False
    fn_chance = TEST_KIT_FALSE_NEGATIVE_CHANCE
    if is_trap:
        fn_chance = min(0.55, fn_chance + 0.25)

    if base_risk >= 0.55 and random.random() < fn_chance:
        false_negative = True
        if base_risk >= 0.75:
            tier = "中低风险"
        else:
            tier = "低风险"

    return tier, false_negative


def pick_disease_for_depth(
    depth: str, diseases: dict[str, dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """根据感染深度从疾病池抽取一种疾病。"""
    pool_ids = DISEASE_POOL_BY_DEPTH.get(depth, [])
    candidates = [diseases[did] for did in pool_ids if did in diseases]
    if not candidates:
        return None
    return random.choice(candidates)


def get_initial_damage(disease: dict[str, Any]) -> int:
    """感染当轮首击伤害（单独配置，通常大于每轮持续伤害）。"""
    if disease.get("instant_game_over"):
        return 0
    return int(
        disease.get(
            "initial_damage",
            disease.get("damage_per_turn", 0),
        )
    )


def create_infection_record(
    disease: dict[str, Any], source_npc_name: str
) -> dict[str, Any]:
    """创建一条感染记录（潜伏期结束后才进入每轮持续扣血）。"""
    return {
        "disease_id": disease["id"],
        "disease_name": disease["name"],
        "incubation_remaining": disease["incubation_turns"],
        "initial_damage": get_initial_damage(disease),
        "damage_per_turn": disease["damage_per_turn"],
        "curable": disease.get("curable", True),
        "instant_game_over": disease.get("instant_game_over", False),
        "is_active": False,
        "initial_damage_applied": True,
        "source_npc": source_npc_name,
    }
