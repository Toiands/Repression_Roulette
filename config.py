"""游戏全局配置常量。"""

from pathlib import Path

# 路径
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
NPCS_FILE = DATA_DIR / "npcs.json"
DISEASES_FILE = DATA_DIR / "diseases.json"

# 初始数值
REPRESSION_START = 50
REPRESSION_MAX = 100
HEALTH_START = 100
HEALTH_MIN = 0

# 医院治疗导致的压抑值上升
TREATMENT_REPRESSION_PENALTY = 50

# 每轮新事件自动增加的压抑值（随回合略升，见 game_state.repression_increase_for_turn）
EVENT_REPRESSION_INCREASE = 10
EVENT_REPRESSION_SCALE_EVERY = 4  # 每满 N 回合，自动压抑额外 +2
EVENT_REPRESSION_SCALE_STEP = 2

# 胜利条件：存活回合数
WIN_TURN_TARGET = 10

# 中后期嘉宾池更偏高危（仍不重复）
SPAWN_HIGH_RISK_BIAS_AFTER_TURN = 3
SPAWN_HIGH_RISK_WEIGHT_FACTOR = 2.8

# 全程安全保护：无法无脑通关
CONDOM_BREACH_CHANCE = 0.12  # 有套仍可能疏漏，按更高系数重算感染
CONDOM_BREACH_RISK_MULTIPLIER = 0.22
SAFE_STREAK_LONELINESS_START = 3  # 连续第 N 次选安全保护起算孤独惩罚
SAFE_STREAK_LONELINESS_BASE = 6
SAFE_STREAK_LONELINESS_STEP = 4

# 遭遇前「追问/试探」类互动累计过多，对方跑路（每轮随机阈值，不对玩家显示）
PROBING_INTERACTIONS = (
    "ask_history",
    "request_report",
    "observe",
    "discuss_protection",
)
PROBE_FLEE_MIN = 2
PROBE_FLEE_MAX = 4
NPC_FLEE_REPRESSION_PENALTY = 25

# 遭遇前交互（每轮每种最多使用一次）
INTERACTIONS = {
    "test_kit": {
        "key": "test_kit",
        "label": "性病四联试纸",
        "description": "快检对方体液样本（不限次数，可能假阴性）",
    },
    "ask_history": {
        "key": "ask_history",
        "label": "旁敲侧击问病史",
        "description": "试探病史（追问过多对方可能离开）",
    },
    "request_report": {
        "key": "request_report",
        "label": "要求出示体检报告",
        "description": "要求看报告（追问过多对方可能离开）",
    },
    "observe": {
        "key": "observe",
        "label": "仔细观察细节",
        "description": "观察体表线索（追问过多对方可能离开）",
    },
    "discuss_protection": {
        "key": "discuss_protection",
        "label": "坦诚沟通防护态度",
        "description": "了解防护态度（追问过多对方可能离开）",
    },
}

# 亲密行动选项
ACTIONS = {
    "A": {
        "key": "A",
        "label": "全程安全保护",
        "description": "相对稳妥，但并非零风险；连续选择会累积孤独",
        "repression_delta": -6,
        "risk_multiplier": 0.06,
        "risk_coefficient_label": "6%",
        "depth": "shallow",
    },
    "B": {
        "key": "B",
        "label": "无套口角+保护插入",
        "repression_delta": -15,
        "risk_multiplier": 0.25,
        "risk_coefficient_label": "25%",
        "depth": "shallow",
    },
    "C": {
        "key": "C",
        "label": "全程无套",
        "repression_delta": -30,
        "risk_multiplier": 1.0,
        "risk_coefficient_label": "100%",
        "depth": "deep",
    },
    "D": {
        "key": "D",
        "label": "明确婉拒，直接离场",
        "description": "结束今晚；压抑 +20（孤独代价）",
        "repression_delta": 20,
        "risk_multiplier": 0.0,
        "depth": "none",
    },
}

# 感染深度 -> 可能抽到的疾病 ID
DISEASE_POOL_BY_DEPTH = {
    "shallow": ["syphilis", "genital_warts"],
    "deep": ["syphilis", "genital_warts", "hiv"],
}

# 四联试纸：高风险 NPC 假阴性概率
TEST_KIT_FALSE_NEGATIVE_CHANCE = 0.28

# 嘉宾基础风险四阶梯（游戏内数值保密）
RISK_TIERS = {
    "low": {"count": 65, "min": 0.01, "max": 0.10, "label": "低危泛众"},
    "active": {"count": 20, "min": 0.15, "max": 0.30, "label": "活跃玩家"},
    "high": {"count": 12, "min": 0.40, "max": 0.70, "label": "高危盲盒"},
    "deadly": {"count": 3, "min": 0.85, "max": 0.95, "label": "致命地雷"},
}

# 开局介绍
GAME_INTRO = """
**压抑模拟器**是一款文字生存决策游戏。你要在「压抑值」与「健康值」之间找平衡：压抑爆表或健康归零都会失败，**存活 10 回合**即胜利。界面为居中暗色卡片式布局。

每轮你会遇到一位陌生女嘉宾。可先试探（试纸、问病史、看报告等），再选择亲密程度——**嘉宾的基础风险档位决定其防护态度与可选行动**（低风险更坚持戴套，高风险更抵触戴套）。感染性病后**当轮就会受到较大健康冲击**，潜伏期结束后还会持续扣血。越到后期越难遇到「看起来安全」的人；一味全程保护能保命，但压抑会缓慢爬升，孤独也会叠加。侧边栏可查看**成就**（同一浏览器会尽量保留解锁记录）。谁更安全只能靠自己判断，后果常在事后才显现。通关或失败时可在**本局嘉宾回顾**中查看遇到过的人。

**健康提示：** 正确使用安全套、减少无保护行为、有疑虑时先做检测、尽早治疗，是预防梅毒、尖锐湿疣与 HIV 的关键。本游戏为虚构模拟，请勿替代真实医疗建议。
"""

# 防治教育短句（随机插入结算）
HEALTH_EDU_TIPS = [
    "【健康提示】发生高危行为后，应在窗口期到正规医疗机构做梅毒、HIV 等筛查，不要凭「看起来没事」自行判断。",
    "【健康提示】安全套能显著降低多数性病传播风险，但无法覆盖所有接触方式；口交、破损皮肤接触同样存在风险。",
    "【健康提示】「对方说没事」不等于医学上的安全；体检报告也有窗口期，过期报告参考价值有限。",
    "【健康提示】若出现皮疹、溃疡、异常分泌物或持续低烧，请尽快就诊，拖延会让治疗更复杂。",
    "【健康提示】HIV 目前虽可控制，但仍会改变生活轨迹；事前预防远比事后焦虑成本更低。",
    "【健康提示】追问病史、使用试纸、坚持保护措施，不是不信任，而是对自己和对方负责。",
]

# 感染后叙事（按疾病，随机抽取一条）
INFECTION_NARRATIVES: dict[str, list[str]] = {
    "syphilis": [
        "几天后你在浴室镜前停顿——有些症状让人无法假装无事发生。你想起那晚与【{npc}】的接触，后悔与侥幸交替涌上来。",
        "手机弹出搜索记录推荐，你盯着屏幕发呆。和【{npc}】有关的那个夜晚，像一根刺卡在记忆里。",
        "你开始刻意回避体检 App 的推送，却知道这件事不会自己消失。【{npc}】走后的安静，比当时更吵。",
    ],
    "genital_warts": [
        "皮肤上的变化小而顽固，你不敢再拖延。脑海里反复闪回【{npc}】当时含糊的解释和你的心软。",
        "你删掉了几条聊天记录，又忍不住翻回去看。那晚的选择并不浪漫，只是你不愿承认。",
        "镜子里陌生的细节提醒你：风险从不因为「看起来没问题」而消失。【{npc}】的笑容此刻显得遥远。",
    ],
    "hiv": [
        "化验单上的字母像一记闷雷。【{npc}】、那个夜晚、所有侥幸，在同一瞬间坍缩成废墟。",
        "你坐在走廊长椅上很久，周围人声变得遥远。与【{npc}】有关的故事，到此为止。",
        "手机反复亮起又熄灭，你没有回复任何人。关于【{npc}】的最后一丝幻想，被报告单彻底掐灭。",
    ],
}
