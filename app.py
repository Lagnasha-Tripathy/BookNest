"""
streamlit_app.py — BookNest "Reading Room" chatbot frontend.

Enhancements over the previous version:
  - Temperature slider removed (it was disabled/unused anyway)
  - Richer, higher-contrast two-tone card palette (user vs. assistant)
  - Live connection status indicator (API key set / not set)
  - Session stats (message count, session start time) in the sidebar
  - Quick-start suggestion chips for a first-time user (real-chatbot UX)
  - Per-message timestamps
  - Export the whole conversation as a Markdown file
  - Small code cleanups: helpers instead of repeated blocks
"""

from datetime import datetime

import streamlit as st
from booknest_chatbot import BookNestChatBot

st.set_page_config(
    page_title="BookNest — Reading Room",
    page_icon="📖",
    layout="wide",
)

# =====================================================================
# Session State
# =====================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []          # [{"role", "content", "time"}]
if "bot" not in st.session_state:
    st.session_state.bot = None
if "session_started" not in st.session_state:
    st.session_state.session_started = datetime.now().strftime("%I:%M %p")
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

QUICK_PROMPTS = [
    "📚 Recommend a mystery novel",
    "🔎 Do you have any Stephen King books?",
    "🧾 Has Ananya returned her book yet?",
    "🚚 What's your standard shipping time?",
]

# =====================================================================
# DESIGN: "The Reading Room" — v2
# Deep reading-room green + brass hardware, now with two-tone catalog
# cards (warm wine-paper for the patron, cool green-paper for BookyBot)
# so the conversation reads at a glance, plus a live status lamp.
# =====================================================================
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Lora:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --reading-green: #1B3A2F;
    --reading-green-deep: #0F211B;
    --green-tint: #E9EFE4;
    --paper: #F6F1E4;
    --paper-shadow: #E4D9BE;
    --wine-tint: #F5E7DD;
    --brass: #B08D57;
    --brass-light: #D8B87E;
    --wine: #7A2E2E;
    --wine-light: #9C4A3C;
    --ink: #2A2620;
    --ink-soft: #6B6355;
    --ok: #4C7A5A;
    --bad: #A6453C;
}

html, body, [class*="css"] { font-family: 'Lora', serif; color: var(--ink); }

.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(176,141,87,0.12), transparent 45%),
        radial-gradient(circle at 100% 100%, rgba(122,46,46,0.06), transparent 40%),
        var(--paper);
}

.block-container { max-width: 880px; margin: auto; padding-top: 2rem; }

/* ---------- header ---------- */
.catalog-header {
    background: var(--paper);
    border: 1px solid var(--ink-soft);
    border-top: 6px solid var(--wine);
    box-shadow: 4px 4px 0 var(--paper-shadow);
    padding: 22px 28px 18px 28px;
    margin-bottom: 22px;
    position: relative;
}
.catalog-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--brass); margin-bottom: 6px;
    display: flex; align-items: center; gap: 8px;
}
.status-dot {
    width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}
.status-dot.on { background: var(--ok); box-shadow: 0 0 6px var(--ok); }
.status-dot.off { background: var(--bad); box-shadow: 0 0 6px var(--bad); }
.chat-title {
    font-family: 'Fraunces', serif; font-weight: 700; font-size: 40px;
    color: var(--reading-green-deep); line-height: 1.1; margin: 0 0 6px 0;
}
.chat-subtitle {
    font-family: 'Lora', serif; font-style: italic; color: var(--ink-soft); font-size: 15px; margin: 0;
}
.catalog-header::after {
    content: "No. 0001"; position: absolute; top: 18px; right: 24px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    color: var(--ink-soft); letter-spacing: 1px;
}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
    background: var(--reading-green);
    border-right: 3px solid var(--brass);
}
section[data-testid="stSidebar"] * { color: var(--paper) !important; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12.5px !important; letter-spacing: 3px; text-transform: uppercase;
    color: var(--brass-light) !important;
    border-bottom: 1px solid rgba(176,141,87,0.4); padding-bottom: 8px; margin-top: 18px;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: var(--reading-green-deep) !important;
    border: 1px solid var(--brass) !important;
    color: var(--paper) !important; border-radius: 3px !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: var(--brass) !important; color: var(--reading-green-deep) !important;
    border: none !important; border-radius: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 12px !important;
    letter-spacing: 1.3px; text-transform: uppercase; font-weight: 600;
    padding: 9px 0 !important; transition: background 0.15s ease;
}
section[data-testid="stSidebar"] .stButton button:hover { background: var(--brass-light) !important; }
section[data-testid="stSidebar"] .stDownloadButton button {
    background: transparent !important; color: var(--paper) !important;
    border: 1px solid var(--brass) !important; border-radius: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 11.5px !important;
    letter-spacing: 1px; text-transform: uppercase;
}
section[data-testid="stSidebar"] .stDownloadButton button:hover {
    border-color: var(--brass-light) !important; color: var(--brass-light) !important;
}
section[data-testid="stSidebar"] hr { border-color: rgba(176,141,87,0.3) !important; }
.sidebar-stat {
    font-family: 'IBM Plex Mono', monospace; font-size: 12px;
    color: var(--paper); opacity: 0.85; margin: 2px 0;
}
.sidebar-stat b { color: var(--brass-light); }

/* ---------- quick-start chips ---------- */
div[data-testid="stHorizontalBlock"] .stButton button {
    background: var(--paper) !important;
    border: 1px solid var(--brass) !important;
    color: var(--reading-green-deep) !important;
    border-radius: 20px !important;
    font-family: 'Lora', serif !important;
    font-size: 13.5px !important;
    padding: 8px 14px !important;
    box-shadow: 2px 2px 0 var(--paper-shadow);
    transition: all 0.15s ease;
}
div[data-testid="stHorizontalBlock"] .stButton button:hover {
    background: var(--brass) !important; color: var(--paper) !important;
    transform: translateY(-1px);
}

/* ---------- chat bubbles ---------- */
div[data-testid="stChatMessage"] {
    border: 1px solid var(--ink-soft);
    border-radius: 3px;
    box-shadow: 3px 3px 0 var(--paper-shadow);
    padding: 4px 6px;
    margin-bottom: 16px;
    position: relative;
}
div[data-testid="stChatMessage"]::before {
    content: "";
    position: absolute; top: -1px; left: 0; right: 0; height: 6px;
    background-image: radial-gradient(circle, var(--paper) 2.5px, transparent 2.6px);
    background-size: 14px 14px; background-position: 4px -3px;
}
div[data-testid="stChatMessageContent"] p {
    font-family: 'Lora', serif; font-size: 15.5px; line-height: 1.6; color: var(--ink);
}

/* assistant = cool green-tinted card */
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
    background: var(--green-tint) !important;
    border-left: 4px solid var(--reading-green);
}
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"])::after {
    content: "BOOKY · REF. DESK";
    position: absolute; bottom: 6px; right: 10px;
    font-family: 'IBM Plex Mono', monospace; font-size: 9px; letter-spacing: 1.4px;
    color: var(--reading-green); opacity: 0.75; transform: rotate(-2deg);
}

/* user = warm wine-tinted card */
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
    background: var(--wine-tint) !important;
    border-left: 4px solid var(--wine);
}
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"])::after {
    content: "PATRON REQUEST";
    position: absolute; bottom: 6px; right: 10px;
    font-family: 'IBM Plex Mono', monospace; font-size: 9px; letter-spacing: 1.4px;
    color: var(--wine); opacity: 0.75; transform: rotate(-2deg);
}

.msg-time {
    font-family: 'IBM Plex Mono', monospace; font-size: 10px;
    color: var(--ink-soft); opacity: 0.7; margin-top: 2px;
}

/* ---------- chat input ---------- */
div[data-testid="stChatInput"] {
    background: var(--paper) !important;
    border: 1.5px solid var(--reading-green) !important;
    border-radius: 3px !important;
}
div[data-testid="stChatInput"] textarea {
    font-family: 'Lora', serif !important; color: var(--ink) !important;
}

.stAlert { border-radius: 3px !important; font-family: 'Lora', serif; }

</style>
""", unsafe_allow_html=True)


# =====================================================================
# Helpers
# =====================================================================
def add_message(role: str, content: str):
    st.session_state.messages.append(
        {"role": role, "content": content, "time": datetime.now().strftime("%I:%M %p")}
    )


def render_message(role: str, content: str, msg_time: str):
    avatar = "📖" if role == "assistant" else "🎫"
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)
        st.markdown(f'<div class="msg-time">{msg_time}</div>', unsafe_allow_html=True)


def export_conversation_md() -> str:
    lines = ["# BookNest Reading Room — Conversation\n"]
    for m in st.session_state.messages:
        speaker = "Patron" if m["role"] == "user" else "BookyBot"
        lines.append(f"**{speaker}** _{m['time']}_\n\n{m['content']}\n")
    return "\n".join(lines)


def ask_bot(prompt: str, api_key: str, model: str):
    add_message("user", prompt)
    render_message("user", prompt, st.session_state.messages[-1]["time"])

    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
        st.stop()

    if st.session_state.bot is None or st.session_state.bot.model != model:
        st.session_state.bot = BookNestChatBot(api_key=api_key, model=model)

    try:
        with st.chat_message("assistant", avatar="📖"):
            with st.spinner("Checking the card catalog..."):
                reply = st.session_state.bot.send(prompt)
            st.markdown(reply)
            stamp = datetime.now().strftime("%I:%M %p")
            st.markdown(f'<div class="msg-time">{stamp}</div>', unsafe_allow_html=True)
        add_message("assistant", reply)
    except Exception as e:
        st.error(f"Error: {e}")


# =====================================================================
# Sidebar
# =====================================================================
with st.sidebar:
    st.markdown("## Connection")

    api_key = st.text_input("Gemini API Key", type="password")

    model = st.selectbox(
        "Model",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
    )

    st.markdown("## Session")
    st.markdown(f'<div class="sidebar-stat">Started &nbsp;<b>{st.session_state.session_started}</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-stat">Messages &nbsp;<b>{len(st.session_state.messages)}</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-stat">Model &nbsp;<b>{model}</b></div>', unsafe_allow_html=True)

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ New Chat", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.bot is not None:
                st.session_state.bot.reset()
            st.rerun()
    with col_b:
        st.download_button(
            "⬇️ Export",
            data=export_conversation_md() if st.session_state.messages else "No messages yet.",
            file_name="booknest_conversation.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=not st.session_state.messages,
        )

# =====================================================================
# Header
# =====================================================================
status_class = "on" if api_key else "off"
status_text = "Connected" if api_key else "No API key"
st.markdown(
    f"""
    <div class="catalog-header">
        <div class="catalog-eyebrow">
            <span class="status-dot {status_class}"></span> BookNest &middot; Reading Room &middot; {status_text}
        </div>
        <div class="chat-title">Ask BookyBot</div>
        <p class="chat-subtitle">Books, borrow records, orders, shipping &amp; returns — all in one card catalog.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# Chat history
# =====================================================================
for message in st.session_state.messages:
    render_message(message["role"], message["content"], message.get("time", ""))

# =====================================================================
# Quick-start chips (only shown before the first message)
# =====================================================================
if not st.session_state.messages:
    st.markdown(
        '<p style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
        'letter-spacing:1.5px;text-transform:uppercase;color:#6B6355;margin-bottom:8px;">'
        'Try asking</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(QUICK_PROMPTS))
    for col, suggestion in zip(cols, QUICK_PROMPTS):
        with col:
            if st.button(suggestion, use_container_width=True, key=f"quick_{suggestion}"):
                st.session_state.pending_prompt = suggestion.split(" ", 1)[1]
                st.rerun()

# =====================================================================
# Chat input
# =====================================================================
typed_prompt = st.chat_input("Type your message...")
prompt = typed_prompt or st.session_state.pending_prompt
st.session_state.pending_prompt = None

if prompt:
    ask_bot(prompt, api_key, model)