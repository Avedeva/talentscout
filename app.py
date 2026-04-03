"""
app.py
TalentScout Hiring Assistant - Streamlit frontend.
Run with: streamlit run app.py
"""

import streamlit as st

from conversation import ConversationManager
from data_handler import format_candidate_summary, get_all_candidates


st.set_page_config(
    page_title="TalentScout | AI Hiring Assistant",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp {
    background: #09090f;
    background-image:
        radial-gradient(ellipse 80% 40% at 50% -10%, rgba(99,102,241,0.18), transparent),
        radial-gradient(ellipse 50% 30% at 85% 85%, rgba(16,185,129,0.07), transparent);
}

.ts-header {
    text-align: center;
    padding: 2rem 0 1.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 1.5rem;
}
.ts-logo {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #fff;
    letter-spacing: -0.02em;
}
.ts-logo em { color: #6366f1; font-style: normal; }
.ts-tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #4b5563;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

.ts-stage {
    display: inline-block;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.3);
    color: #a5b4fc;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    margin-bottom: 1rem;
}

.stChatMessage {
    background: transparent !important;
    border: none !important;
}

[data-testid="stChatMessageContent"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    padding: 0.9rem 1.1rem !important;
    color: #e5e7eb !important;
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
}

[data-testid="stChatMessageContent"] p { color: #e5e7eb !important; }
[data-testid="stChatMessageContent"] strong { color: #a5b4fc !important; }

[data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
    background: rgba(99,102,241,0.1) !important;
    border-color: rgba(99,102,241,0.2) !important;
}

.stChatInput textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #f9fafb !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
}
.stChatInput textarea:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}

.stProgress > div > div {
    background: linear-gradient(90deg, #6366f1, #818cf8) !important;
    border-radius: 4px !important;
}
.stProgress > div {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 4px !important;
}

.stSidebar { background: #0d0d16 !important; }
.stSidebar [data-testid="stMarkdownContainer"] p { color: #9ca3af !important; }

.cand-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.82rem;
    color: #9ca3af;
}
.cand-card strong { color: #c4b5fd; }

.stButton button {
    background: rgba(99,102,241,0.15) !important;
    border: 1px solid rgba(99,102,241,0.35) !important;
    color: #a5b4fc !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton button:hover {
    background: rgba(99,102,241,0.25) !important;
    border-color: rgba(99,102,241,0.6) !important;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


def init_session():
    if "manager" not in st.session_state:
        st.session_state.manager = ConversationManager()
        st.session_state.messages = []
        st.session_state.initialized = False
        st.session_state.show_summary = False


init_session()
manager: ConversationManager = st.session_state.manager


with st.sidebar:
    st.markdown("### 🎯 TalentScout")
    st.markdown("---")

    if manager.candidate:
        st.markdown("**Current Candidate**")
        summary_md = format_candidate_summary(manager.candidate)
        if summary_md:
            st.markdown(summary_md)
        else:
            st.caption("Gathering info...")
        st.markdown("---")

    st.markdown("**Past Candidates**")
    records = get_all_candidates()
    if records:
        for record in records[:5]:
            st.markdown(
                f'<div class="cand-card"><strong>{record.get("name", "-")}</strong><br>'
                f'{record.get("desired_position", "")}<br>'
                f'<span style="color:#6b7280;font-size:0.75rem">{record.get("timestamp", "")[:10]}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No candidates yet.")

    st.markdown("---")
    if st.button("🔄 New Session"):
        for key in ["manager", "messages", "initialized", "show_summary"]:
            st.session_state.pop(key, None)
        st.rerun()


st.markdown(
    """
<div class="ts-header">
    <div class="ts-logo">Talent<em>Scout</em></div>
    <div class="ts-tagline">AI Hiring Assistant · Powered by Claude</div>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([3, 1])
with col1:
    st.progress(manager.progress_pct / 100)
with col2:
    st.markdown(
        f'<div class="ts-stage">{manager.stage_label}</div>',
        unsafe_allow_html=True,
    )

st.caption("🔒 Your data is securely handled and not stored permanently.")

if not st.session_state.initialized:
    with st.spinner("Connecting..."):
        greeting = manager.get_greeting()
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.session_state.initialized = True

for msg in st.session_state.messages:
    avatar = "🎯" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if not manager.is_ended:
    placeholder_map = {
        "collect_name": "Type your full name...",
        "collect_email": "your@email.com",
        "collect_phone": "+1-234-567-8900 (or type 'skip')",
        "collect_location": "City, Country",
        "collect_experience": "e.g. 3 years",
        "collect_position": "e.g. Backend Engineer, ML Engineer...",
        "collect_techstack": "e.g. Python, FastAPI, PostgreSQL, Docker...",
        "technical_questions": "Type your answer...",
    }
    placeholder = placeholder_map.get(manager.stage, "Type your message...")

    if user_input := st.chat_input(placeholder):
        if not user_input.strip():
            st.warning("Please enter a response.")
            st.stop()

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant", avatar="🎯"):
            with st.spinner("Analyzing your response..."):
                try:
                    response = manager.process(user_input)
                except Exception:
                    response = "⚠️ Something went wrong. Please try again."
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()
else:
    st.success("✅ Interview complete! Your profile has been saved.")
    st.balloons()
    if st.button("Start a new interview"):
        for key in ["manager", "messages", "initialized", "show_summary"]:
            st.session_state.pop(key, None)
        st.rerun()
