"""
ui/components/chat_window.py — NayePankh AI Workforce
======================================================
Main conversational chat UI panel.
"""
import streamlit as st


ROLE_AVATARS = {
    "user":      "👤",
    "assistant": "🕊️",
}

AGENT_COLORS = {
    "volunteer":  "#22c55e",
    "internship": "#3b82f6",
    "content":    "#f59e0b",
    "analytics":  "#8b5cf6",
    "resource":   "#ef4444",
    "supervisor": "#64748b",
}


def render_chat_window(messages: list[dict]) -> None:
    """
    Render the full conversation history.

    Args:
        messages: List of {"role": str, "content": str, "agent"?: str} dicts
    """
    if not messages:
        _render_empty_state()
        return

    for msg in messages:
        role    = msg.get("role", "user")
        content = msg.get("content", "")
        agent   = msg.get("agent", "")
        avatar  = ROLE_AVATARS.get(role, "💬")

        with st.chat_message(role, avatar=avatar):
            if role == "assistant" and agent and agent in AGENT_COLORS:
                color = AGENT_COLORS[agent]
                st.markdown(
                    f'<span style="font-size:11px;color:{color};font-weight:600;">'
                    f'▶ {agent.replace("_"," ").title()} Agent</span>',
                    unsafe_allow_html=True,
                )
            st.markdown(content)


def render_chat_input() -> str | None:
    """Render the chat input box. Returns user input or None."""
    return st.chat_input("Ask anything about volunteers, interns, content, analytics, or funds...")


def render_thinking_indicator(agent_name: str = "AI") -> None:
    """Show a spinner while the agent is processing."""
    st.markdown(
        f'<div style="padding:8px 12px;border-radius:8px;background:#1e293b;'
        f'color:#94a3b8;font-size:13px;">🧠 {agent_name} is thinking...</div>',
        unsafe_allow_html=True,
    )


def _render_empty_state() -> None:
    """Render welcome screen when no messages exist."""
    st.markdown(
        """
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:64px;margin-bottom:16px;">🕊️</div>
            <h2 style="color:#f8fafc;margin-bottom:8px;">NayePankh AI Workforce</h2>
            <p style="color:#94a3b8;font-size:16px;max-width:480px;margin:0 auto 32px;">
                Your intelligent NGO operating system. Ask me anything about 
                volunteers, interns, content, analytics, or resources.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Example query cards
    examples = [
        ("🙋", "Register a new volunteer", "Register a new volunteer named Priya Sharma, email priya@example.com, skills: outreach, social_media"),
        ("🎓", "Check intern pipeline", "Show me all interns currently in 'reviewing' status"),
        ("✍️", "Generate content",       "Write an Instagram post celebrating our 100th volunteer milestone"),
        ("📊", "Analytics report",        "Generate the monthly impact report with all KPIs"),
    ]

    cols = st.columns(2)
    for i, (icon, label, prompt) in enumerate(examples):
        with cols[i % 2]:
            if st.button(f"{icon} {label}", use_container_width=True, key=f"eg_{i}"):
                st.session_state["quick_prompt"] = prompt
                st.rerun()
