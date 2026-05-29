"""月抛模拟器风格：暗色玻璃卡片 + 居中移动端布局。"""

from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from config import ACTIONS, REPRESSION_MAX, WIN_TURN_TARGET

_CSS_FILE = Path(__file__).resolve().parent / "game.css"

FONT_LINK = (
    "https://fonts.googleapis.com/css2?"
    "family=Noto+Sans+SC:wght@400;500;700;900&display=swap"
)

BG_IMAGE = (
    "https://images.unsplash.com/photo-1623949566270-3d23157e0573"
    "?q=80&w=2070&auto=format&fit=crop"
)


def _load_css() -> str:
    return _CSS_FILE.read_text(encoding="utf-8").replace("{{BG_IMAGE}}", BG_IMAGE)


def inject_theme() -> None:
    """Streamlit Cloud 会剥离 markdown 里的 <style>，故注入到父页面 head。"""
    if st.session_state.get("_theme_injected"):
        return
    st.session_state._theme_injected = True

    css = _load_css()
    css_json = json.dumps(css)
    components.html(
        f"""
        <div class="repression-theme-anchor"></div>
        <script>
        (function() {{
            const css = {css_json};
            const docs = [document, window.parent.document];
            for (const doc of docs) {{
                try {{
                    let node = doc.getElementById("repression-game-theme");
                    if (!node) {{
                        node = doc.createElement("style");
                        node.id = "repression-game-theme";
                        doc.head.appendChild(node);
                    }}
                    node.textContent = css;
                }} catch (e) {{}}
            }}
        }})();
        </script>
        """,
        height=0,
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
    rep = act["repression_delta"]
    return f"{icon} {act['label']} · 压抑{rep:+d}"


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
