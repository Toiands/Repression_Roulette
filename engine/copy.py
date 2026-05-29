"""文案与教育提示。"""

from __future__ import annotations

import random

from config import HEALTH_EDU_TIPS


def pick_health_edu() -> str:
    return random.choice(HEALTH_EDU_TIPS)
