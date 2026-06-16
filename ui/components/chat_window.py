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
    "volunteer":  "#10b981",
    "internship": "#3b82f6",
    "content":    "#f59e0b",
    "analytics":  "#8b5cf6",
    "resource":   "#ef4444",
    "supervisor": "#00f0ff",
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
            if role == "assistant":
                if agent:
                    color = AGENT_COLORS.get(agent, "#00f0ff")
                    st.markdown(
                        f'<div class="agent-badge" style="color: {color}; border-color: {color}44; background: {color}15;">'
                        f'🤖 {agent.replace("_"," ").title()} Agent</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="agent-badge" style="color: #00f0ff; border-color: #00f0ff44; background: rgba(0,240,255,0.08);">'
                        '🧠 Supervisor Agent</div>',
                        unsafe_allow_html=True,
                    )
            st.markdown(content)


def render_chat_input() -> str | None:
    """Render the chat input box. Returns user input or None."""
    return st.chat_input("Command the AI OS to run volunteer campaigns, log funds, analyze intern pipelines...")


def render_thinking_indicator(agent_name: str = "AI") -> None:
    """Show a spinner while the agent is processing."""
    st.markdown(
        f'<div style="display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-radius: 12px; background: rgba(0, 240, 255, 0.05); border: 1px dashed rgba(0, 240, 255, 0.2); margin-bottom: 12px;">'
        f'<span style="font-size: 16px; animation: spin 2s linear infinite; display: inline-block;">🧠</span>'
        f'<span style="color: var(--primary); font-size: 13px; font-weight: 600; font-family: \'JetBrains Mono\', monospace;">'
        f'{agent_name.replace("_"," ").title()} Agent is active and processing...</span>'
        f'</div>'
        f'<style>'
        f'@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}'
        f'</style>',
        unsafe_allow_html=True,
    )


def _render_empty_state() -> None:
    """Render welcome screen when no messages exist."""
    st.markdown(
        """
        <div style="text-align:center;padding:40px 20px;">
            <div style="font-size:64px;margin-bottom:16px; animation: float 3s ease-in-out infinite;">🕊️</div>
            <h2 class="gradient-text" style="font-size: 2.2rem; margin-bottom:8px;">AI Workforce Chat Terminal</h2>
            <p style="color:var(--text-muted);font-size:16px;max-width:550px;margin:0 auto 32px; line-height: 1.6;">
                Directly communicate with the supervisor agent, which plans multi-agent tasks, coordinates specialists, and delivers reports.
            </p>
        </div>
        <style>
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
        </style>
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
            st.markdown(
                f"""
                <div style="padding: 2px 0;">
                """,
                unsafe_allow_html=True
            )
            if st.button(f"{icon} {label}", use_container_width=True, key=f"eg_{i}"):
                st.session_state["quick_prompt"] = prompt
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
