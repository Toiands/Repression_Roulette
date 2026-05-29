"""月抛模拟器风格：暗色玻璃卡片 + 居中移动端布局。"""

from __future__ import annotations

import html
import streamlit as st

from config import ACTIONS, REPRESSION_MAX, WIN_TURN_TARGET

FONT_LINK = (
    "https://fonts.googleapis.com/css2?"
    "family=Noto+Sans+SC:wght@400;500;700;900&display=swap"
)

BG_IMAGE = (
    "https://images.unsplash.com/photo-1623949566270-3d23157e0573"
    "?q=80&w=2070&auto=format&fit=crop"
)


def inject_theme() -> None:
    st.markdown(
        f"""
        <link href="{FONT_LINK}" rel="stylesheet">
        <style>
        @import url('{FONT_LINK}');

        :root {{
            --bg-deep: #020617;
            --glass: rgba(15, 23, 42, 0.95);
            --border: rgba(255, 255, 255, 0.08);
            --rose: #fb7185;
            --violet: #a78bfa;
            --emerald: #34d399;
        }}

        .stApp {{
            background: var(--bg-deep) url('{BG_IMAGE}') center/cover fixed !important;
            font-family: 'Noto Sans SC', sans-serif !important;
        }}
        .stApp::before {{
            content: '';
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.9);
            backdrop-filter: blur(2px);
            z-index: 0;
            pointer-events: none;
        }}

        header[data-testid="stHeader"] {{ background: transparent !important; }}
        #MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
        section[data-testid="stSidebar"] {{ display: none; }}

        .block-container {{
            max-width: 28rem !important;
            padding: 1rem 1rem 2rem !important;
            margin: 0 auto !important;
            position: relative;
            z-index: 1;
        }}

        .glass-card {{
            background: var(--glass);
            backdrop-filter: blur(24px);
            border: 1px solid var(--border);
            border-top: 1px solid rgba(255,255,255,0.1);
            border-radius: 1.5rem;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8);
            overflow: hidden;
            margin-bottom: 1rem;
        }}

        .game-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            background: rgba(15,23,42,0.5);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .game-title {{
            font-size: 1.25rem;
            font-weight: 900;
            font-style: italic;
            letter-spacing: -0.02em;
            background: linear-gradient(90deg, #c084fc, #fb7185);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.2;
        }}
        .game-edition {{
            font-size: 10px;
            font-weight: 700;
            color: #64748b;
            letter-spacing: 0.15em;
            text-transform: uppercase;
        }}
        .round-badge {{
            text-align: right;
        }}
        .round-label {{
            font-size: 10px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
        }}
        .round-num {{
            font-size: 1.5rem;
            font-weight: 700;
            font-family: ui-monospace, monospace;
            color: #fff;
            line-height: 1;
        }}

        .stats-panel {{
            padding: 1rem 1.5rem;
            background: rgba(15,23,42,0.3);
        }}
        .stat-row {{ margin-bottom: 0.75rem; }}
        .stat-row:last-child {{ margin-bottom: 0; }}
        .stat-label {{
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }}
        .stat-bar-track {{
            width: 100%;
            background: #1e293b;
            border-radius: 9999px;
            height: 8px;
            padding: 2px;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.4);
        }}
        .stat-bar-fill {{
            height: 100%;
            border-radius: 9999px;
            transition: width 0.5s ease;
        }}
        .fill-repression {{
            background: linear-gradient(90deg, #10b981, #f43f5e);
        }}
        .fill-health {{
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
        }}

        .partner-zone {{
            padding: 1.5rem;
            text-align: center;
        }}
        .avatar-ring {{
            width: 5rem;
            height: 5rem;
            margin: 0 auto 0.75rem;
            border-radius: 50%;
            background: linear-gradient(135deg, #334155, #1e293b);
            border: 2px solid #475569;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.25rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            animation: avatar-float 6s ease-in-out infinite;
        }}
        @keyframes avatar-float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-5px); }}
        }}
        .partner-title {{
            font-size: 1rem;
            font-weight: 700;
            color: #fff;
            margin: 0 0 0.5rem;
        }}
        .partner-desc {{
            font-size: 11px;
            color: rgba(249, 168, 212, 0.9);
            font-style: italic;
            line-height: 1.6;
            margin: 0;
            font-family: Georgia, 'Noto Serif SC', serif;
        }}
        .tag-badge {{
            display: inline-block;
            padding: 0.2rem 0.55rem;
            margin: 0.15rem;
            font-size: 10px;
            font-weight: 600;
            color: #cbd5e1;
            background: rgba(51,65,85,0.8);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 9999px;
        }}

        .section-pad {{ padding: 0 1.25rem 1rem; }}
        .section-title {{
            font-size: 11px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0 0 0.5rem;
        }}
        .divider-line {{
            height: 1px;
            background: rgba(255,255,255,0.05);
            margin: 0.75rem 0;
        }}

        /* Streamlit 按钮统一为卡片内风格 */
        .block-container .stButton > button {{
            width: 100%;
            border-radius: 0.75rem !important;
            font-weight: 700 !important;
            font-size: 0.8rem !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            background: rgba(30, 41, 59, 0.9) !important;
            color: #e2e8f0 !important;
            padding: 0.65rem 0.5rem !important;
            transition: all 0.2s ease !important;
        }}
        .block-container .stButton > button:hover {{
            background: rgba(51, 65, 85, 0.95) !important;
            border-color: rgba(255,255,255,0.15) !important;
        }}
        .block-container .stButton > button[kind="primary"] {{
            background: linear-gradient(90deg, #db2777, #e11d48) !important;
            border: none !important;
            color: white !important;
            font-size: 0.95rem !important;
            padding: 0.85rem !important;
        }}
        .block-container .stButton > button[kind="primary"]:hover {{
            filter: brightness(1.08);
            transform: scale(1.01);
        }}
        .block-container .stButton > button:disabled {{
            opacity: 0.45;
            filter: grayscale(0.6);
        }}

        /* 行动按钮配色（按列） */
        div[data-testid="stHorizontalBlock"]:has(.action-grid-marker) {{
            gap: 0.5rem;
        }}
        .action-grid-marker + div [data-testid="column"]:nth-child(1) .stButton > button {{
            background: rgba(6, 78, 59, 0.45) !important;
            border-color: rgba(16, 185, 129, 0.25) !important;
            color: #a7f3d0 !important;
        }}
        .action-grid-marker + div [data-testid="column"]:nth-child(2) .stButton > button {{
            background: rgba(30, 41, 59, 0.9) !important;
            color: #cbd5e1 !important;
        }}
        .action-grid-marker + div [data-testid="column"]:nth-child(3) .stButton > button {{
            background: rgba(120, 53, 15, 0.35) !important;
            border-color: rgba(245, 158, 11, 0.2) !important;
            color: #fde68a !important;
        }}
        .action-grid-marker + div [data-testid="column"]:nth-child(4) .stButton > button {{
            background: rgba(136, 19, 55, 0.55) !important;
            border-color: rgba(244, 63, 94, 0.35) !important;
            color: #fecdd3 !important;
        }}

        .intro-wrap {{
            text-align: center;
            padding: 2rem 1.5rem;
        }}
        .intro-emoji {{ font-size: 4rem; margin-bottom: 1rem; filter: drop-shadow(0 0 15px rgba(236,72,153,0.5)); }}
        .intro-rules {{
            text-align: left;
            font-size: 12px;
            color: #cbd5e1;
            background: rgba(30,41,59,0.5);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin: 1rem 0 1.25rem;
            line-height: 1.7;
        }}
        .settlement-box {{
            background: rgba(30,41,59,0.5);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 0.75rem;
            padding: 1rem;
            font-size: 13px;
            line-height: 1.65;
            color: #e2e8f0;
            white-space: pre-wrap;
        }}
        .warn-banner {{
            background: rgba(120, 53, 15, 0.25);
            border: 1px solid rgba(245, 158, 11, 0.2);
            color: #fcd34d;
            font-size: 12px;
            padding: 0.65rem 1rem;
            border-radius: 0.75rem;
            margin: 0.5rem 0;
            text-align: center;
        }}
        .stAlert {{ border-radius: 0.75rem !important; }}
        [data-testid="stExpander"] {{
            background: rgba(15,23,42,0.6) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 0.75rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _esc(text: str) -> str:
    return html.escape(str(text))


def render_top_header(turn: int) -> None:
    turn_disp = f"{max(turn, 0):02d}"
    st.markdown(
        f"""
        <div class="glass-card">
        <div class="game-header">
            <div>
                <h1 class="game-title">压抑模拟器</h1>
                <div class="game-edition">Survival Edition</div>
            </div>
            <div class="round-badge">
                <div class="round-label">Round</div>
                <div class="round-num">{turn_disp}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_bars(repression: int, health: int) -> None:
    rep_pct = min(100, max(0, int(repression / REPRESSION_MAX * 100)))
    health_pct = min(100, max(0, int(health)))
    warn = ""
    if repression >= 80:
        warn = (
            '<p style="font-size:10px;color:#fca5a5;text-align:center;'
            'margin:0.35rem 0 0;animation:pulse 2s infinite">'
            "⚠️ 压抑过高：情绪濒临失控</p>"
        )
    st.markdown(
        f"""
        <div class="stats-panel">
            <div class="stat-row">
                <div class="stat-label">
                    <span style="color:#fb7185">🔥 压抑值</span>
                    <span style="color:#fff">{repression} / {REPRESSION_MAX}</span>
                </div>
                <div class="stat-bar-track">
                    <div class="stat-bar-fill fill-repression" style="width:{rep_pct}%"></div>
                </div>
            </div>
            <div class="stat-row">
                <div class="stat-label">
                    <span style="color:#a78bfa">💚 健康值</span>
                    <span style="color:#fff">{health} / 100</span>
                </div>
                <div class="stat-bar-track">
                    <div class="stat-bar-fill fill-health" style="width:{health_pct}%"></div>
                </div>
            </div>
            {warn}
        </div>
        """,
        unsafe_allow_html=True,
    )


def close_glass_card() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def npc_avatar(npc: dict | None) -> str:
    if not npc:
        return "🌚"
    tags = npc.get("tags") or []
    if "trap" in tags:
        return "⚠️"
    if "coser" in tags:
        return "📸"
    return "💘"


def render_partner_card(npc: dict) -> None:
    tags = npc.get("tags") or []
    badges = ""
    if "coser" in tags:
        badges += '<span class="tag-badge">Coser</span>'
    if "trap" in tags:
        badges += '<span class="tag-badge" style="border-color:rgba(244,63,94,0.4);color:#fda4af">地雷</span>'
    desc = _esc(npc.get("description", ""))
    name = _esc(npc.get("name", "???"))
    st.markdown(
        f"""
        <div class="partner-zone">
            <div class="avatar-ring">{npc_avatar(npc)}</div>
            <h2 class="partner-title">潜在伴侣 · {name}</h2>
            <p class="partner-desc">"{desc}"</p>
            <div style="margin-top:0.75rem">{badges}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_clue_tags(clues: list[str]) -> None:
    if not clues:
        return
    tags_html = "".join(f'<span class="tag-badge">{_esc(c[:24])}</span>' for c in clues)
    st.markdown(
        f'<div style="text-align:center;padding:0 1rem 0.5rem">{tags_html}</div>',
        unsafe_allow_html=True,
    )


def action_button_label(key: str) -> str:
    act = ACTIONS[key]
    icons = {"A": "🛡️", "B": "🍬", "C": "🔥", "D": "👋"}
    icon = icons.get(key, "▪️")
    sub = act.get("description") or act["label"]
    rep = act["repression_delta"]
    return f"{icon} {act['label']}\n压抑 {rep:+d} · {sub[:12]}"


def render_intro_screen() -> None:
    st.markdown(
        """
        <div class="glass-card intro-wrap">
            <div class="intro-emoji">💘</div>
            <h1 class="game-title" style="font-size:1.75rem;-webkit-text-fill-color:#fff;
                background:none;margin-bottom:0.25rem">压抑模拟器</h1>
            <div class="game-edition" style="margin-bottom:1rem">Survival Edition</div>
            <div class="intro-rules">
                <p>1. <b>延迟判决</b>：高危行为后，你<b>不会</b>立刻知道是否感染。</p>
                <p>2. <b>双条生存</b>：压抑爆表或健康归零都会失败。</p>
                <p>3. <b>试探取舍</b>：试纸与追问有用，但问太多对方可能离开。</p>
                <p>4. <b>目标</b>：存活 <b>"""
        + str(WIN_TURN_TARGET)
        + """</b> 回合，在欲望与风险间撑住。</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_settlement_box(text: str) -> None:
    if not text:
        return
    body = _esc(text)
    st.markdown(
        f'<div class="section-pad"><div class="settlement-box">{body}</div></div>',
        unsafe_allow_html=True,
    )
