"""月抛模拟器风格 UI（纯内联样式，兼容 Streamlit Cloud）。"""

from __future__ import annotations

import html

import streamlit as st

from config import ACTIONS, REPRESSION_MAX, WIN_TURN_TARGET

BG_IMAGE = (
    "https://images.unsplash.com/photo-1623949566270-3d23157e0573"
    "?q=80&w=2070&auto=format&fit=crop"
)

# 玻璃卡片容器
S_CARD = (
    "background:rgba(15,23,42,0.95);backdrop-filter:blur(24px);"
    "border:1px solid rgba(255,255,255,0.08);border-top:1px solid rgba(255,255,255,0.1);"
    "border-radius:1.5rem;box-shadow:0 25px 50px -12px rgba(0,0,0,0.8);"
    "overflow:hidden;margin-bottom:1rem;"
)


def inject_theme() -> None:
    """背景层用内联 style，避免 <style> 被当成正文显示。"""
    st.markdown(
        f'<div aria-hidden="true" style="position:fixed;inset:0;z-index:-2;pointer-events:none;'
        f"background:#020617 url('{BG_IMAGE}') center/cover fixed;\"></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div aria-hidden="true" style="position:fixed;inset:0;z-index:-1;pointer-events:none;'
        'background:rgba(0,0,0,0.88);"></div>',
        unsafe_allow_html=True,
    )


def _esc(text: str) -> str:
    return html.escape(str(text))


def open_card() -> None:
    st.markdown(f'<div style="{S_CARD}">', unsafe_allow_html=True)


def close_card() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_top_header(turn: int) -> None:
    turn_disp = f"{max(turn, 0):02d}"
    open_card()
    st.markdown(
        f"""
        <div style="padding:1rem 1.5rem;border-bottom:1px solid rgba(255,255,255,0.05);
            background:rgba(15,23,42,0.5);display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:1.25rem;font-weight:900;font-style:italic;
                    background:linear-gradient(90deg,#c084fc,#fb7185);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;line-height:1.2;">压抑模拟器</div>
                <div style="font-size:10px;font-weight:700;color:#64748b;
                    letter-spacing:0.15em;text-transform:uppercase;">Survival Edition</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;">Round</div>
                <div style="font-size:1.5rem;font-weight:700;font-family:ui-monospace,monospace;color:#fff;line-height:1;">{turn_disp}</div>
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
            '<p style="font-size:10px;color:#fca5a5;text-align:center;margin:0.35rem 0 0;">'
            "⚠️ 压抑过高：情绪濒临失控</p>"
        )
    st.markdown(
        f"""
        <div style="padding:1rem 1.5rem;background:rgba(15,23,42,0.3);">
            <div style="margin-bottom:0.75rem;">
                <div style="display:flex;justify-content:space-between;font-size:11px;
                    font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.25rem;">
                    <span style="color:#fb7185;">🔥 压抑值</span>
                    <span style="color:#fff;">{repression} / {REPRESSION_MAX}</span>
                </div>
                <div style="width:100%;background:#1e293b;border-radius:9999px;height:8px;padding:2px;
                    box-shadow:inset 0 1px 3px rgba(0,0,0,0.4);">
                    <div style="height:100%;border-radius:9999px;width:{rep_pct}%;
                        background:linear-gradient(90deg,#10b981,#f43f5e);"></div>
                </div>
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;font-size:11px;
                    font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.25rem;">
                    <span style="color:#a78bfa;">💚 健康值</span>
                    <span style="color:#fff;">{health} / 100</span>
                </div>
                <div style="width:100%;background:#1e293b;border-radius:9999px;height:8px;padding:2px;
                    box-shadow:inset 0 1px 3px rgba(0,0,0,0.4);">
                    <div style="height:100%;border-radius:9999px;width:{health_pct}%;
                        background:linear-gradient(90deg,#6366f1,#8b5cf6);"></div>
                </div>
            </div>
            {warn}
        </div>
        """,
        unsafe_allow_html=True,
    )


def close_glass_card() -> None:
    close_card()


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
        badges += (
            '<span style="display:inline-block;padding:0.2rem 0.55rem;margin:0.15rem;'
            'font-size:10px;font-weight:600;color:#cbd5e1;background:rgba(51,65,85,0.8);'
            'border:1px solid rgba(255,255,255,0.08);border-radius:9999px;">Coser</span>'
        )
    if "trap" in tags:
        badges += (
            '<span style="display:inline-block;padding:0.2rem 0.55rem;margin:0.15rem;'
            'font-size:10px;font-weight:600;color:#fda4af;background:rgba(51,65,85,0.8);'
            'border:1px solid rgba(244,63,94,0.4);border-radius:9999px;">地雷</span>'
        )
    desc = _esc(npc.get("description", ""))
    name = _esc(npc.get("name", "???"))
    st.markdown(
        f"""
        <div style="padding:1.5rem;text-align:center;">
            <div style="width:5rem;height:5rem;margin:0 auto 0.75rem;border-radius:50%;
                background:linear-gradient(135deg,#334155,#1e293b);border:2px solid #475569;
                display:flex;align-items:center;justify-content:center;font-size:2.25rem;
                box-shadow:0 10px 25px rgba(0,0,0,0.5);">{npc_avatar(npc)}</div>
            <h2 style="font-size:1.1rem;font-weight:700;color:#fff;margin:0 0 0.75rem;">
                潜在伴侣 · {name}</h2>
            <p style="font-size:15px;color:rgba(253,186,216,0.95);font-style:italic;line-height:1.75;
                margin:0;padding:0 0.5rem;text-align:left;font-family:Georgia,'Noto Serif SC',serif;">
                "{desc}"</p>
            <div style="margin-top:0.75rem;">{badges}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_clue_tags(clues: list[str]) -> None:
    if not clues:
        return
    tags_html = "".join(
        '<span style="display:inline-block;padding:0.2rem 0.55rem;margin:0.15rem;'
        "font-size:10px;font-weight:600;color:#cbd5e1;background:rgba(51,65,85,0.8);"
        'border:1px solid rgba(255,255,255,0.08);border-radius:9999px;">'
        f"{_esc(c[:28])}</span>"
        for c in clues
    )
    st.markdown(
        f'<div style="text-align:center;padding:0 1rem 0.5rem;">{tags_html}</div>',
        unsafe_allow_html=True,
    )


def action_button_label(key: str) -> str:
    act = ACTIONS[key]
    icons = {"A": "🛡️", "B": "🍬", "C": "🔥", "D": "👋"}
    icon = icons.get(key, "▪️")
    rep = act["repression_delta"]
    return f"{icon} {act['label']} · 压抑{rep:+d}"


def section_title(text: str) -> None:
    st.markdown(
        f'<p style="font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;'
        f'letter-spacing:0.08em;margin:0 0 0.5rem;padding:0 1.25rem;">{text}</p>',
        unsafe_allow_html=True,
    )


def render_intro_screen() -> None:
    st.markdown(
        f"""
        <div style="{S_CARD}text-align:center;padding:2rem 1.5rem;">
            <div style="font-size:4rem;margin-bottom:1rem;
                filter:drop-shadow(0 0 15px rgba(236,72,153,0.5));">💘</div>
            <div style="font-size:1.75rem;font-weight:900;color:#fff;margin-bottom:0.25rem;">压抑模拟器</div>
            <div style="font-size:10px;font-weight:700;color:#64748b;letter-spacing:0.15em;
                text-transform:uppercase;margin-bottom:1rem;">Survival Edition</div>
            <div style="text-align:left;font-size:14px;color:#cbd5e1;background:rgba(30,41,59,0.5);
                border:1px solid rgba(255,255,255,0.05);border-radius:0.75rem;padding:1.25rem;
                line-height:1.75;">
                <p>1. <b>延迟判决</b>：高危行为后，你<b>不会</b>立刻知道是否感染。</p>
                <p>2. <b>双条生存</b>：压抑爆表或健康归零都会失败。</p>
                <p>3. <b>试探取舍</b>：试纸与追问有用，但问太多对方可能离开。</p>
                <p>4. <b>目标</b>：存活 <b>{WIN_TURN_TARGET}</b> 回合，在欲望与风险间撑住。</p>
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
        f'<div style="padding:0 1.25rem 1rem;">'
        f'<div style="background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.06);'
        f"border-radius:0.75rem;padding:1rem;font-size:15px;line-height:1.75;color:#e2e8f0;"
        f'white-space:pre-wrap;">{body}</div></div>',
        unsafe_allow_html=True,
    )


def render_warn_banner(message: str, *, tone: str = "warn") -> None:
    if tone == "info":
        style = (
            "color:#93c5fd;border:1px solid rgba(59,130,246,0.25);"
            "background:rgba(30,58,138,0.2);"
        )
    else:
        style = (
            "color:#fcd34d;border:1px solid rgba(245,158,11,0.2);"
            "background:rgba(120,53,15,0.25);"
        )
    st.markdown(
        f'<div style="padding:0 1.25rem 1rem;"><div style="{style}font-size:12px;'
        f'padding:0.65rem 1rem;border-radius:0.75rem;text-align:center;">'
        f"{_esc(message)}</div></div>",
        unsafe_allow_html=True,
    )
