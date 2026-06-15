"""
ui/components/sidebar.py — NayePankh AI Workforce
===================================================
Streamlit sidebar: session management, quick actions, nav.
"""
import streamlit as st
from memory.db import execute_query
from config import APP_TITLE, PAGE_ICON, AGENTS


def render_sidebar() -> None:
    """Render the full left sidebar."""
    with st.sidebar:
        # ── Logo / Title ─────────────────────────────────────
        st.markdown(f"## {PAGE_ICON} {APP_TITLE}")
        st.markdown("*Powered by Agno + Ollama qwen3:8b*")
        st.divider()

        # ── New Conversation ──────────────────────────────────
        if st.button("➕ New Conversation", use_container_width=True, type="primary"):
            _start_new_session()

        st.divider()

        # ── Agent Status Indicators ───────────────────────────
        st.markdown("**🤖 Agent Status**")
        for key, label in AGENTS.items():
            st.markdown(f"🟢 `{label}`")

        st.divider()

        # ── Quick Actions ─────────────────────────────────────
        st.markdown("**⚡ Quick Actions**")
        quick_actions = {
            "📊 Monthly KPI Report":    "Generate the monthly KPI impact report for this month",
            "🙋 List Active Volunteers": "Show me all currently active volunteers",
            "🎓 Active Interns":         "Show me all currently active interns",
            "💰 Budget Status":          "Show budget utilization across all categories",
            "✍️ Draft Instagram Post":   "Create an Instagram post about our recent impact",
        }
        for label, prompt in quick_actions.items():
            if st.button(label, use_container_width=True):
                st.session_state["quick_prompt"] = prompt
                st.rerun()

        st.divider()

        # ── Past Sessions ─────────────────────────────────────
        st.markdown("**🕐 Recent Sessions**")
        try:
            sessions = execute_query(
                "SELECT id, title, created_at FROM sessions "
                "ORDER BY created_at DESC LIMIT 8",
            )
            for s in sessions:
                label = s.get("title") or f"Session {s['id'][:8]}..."
                created = s["created_at"][:10] if s.get("created_at") else ""
                if st.button(f"📝 {label}\n{created}", key=f"sess_{s['id']}",
                             use_container_width=True):
                    st.session_state["session_id"] = s["id"]
                    st.session_state["messages"] = _load_session_messages(s["id"])
                    st.rerun()
        except Exception:
            st.caption("No past sessions found.")

        st.divider()
        st.caption("© 2025 NayePankh Foundation")


def _start_new_session():
    """Initialize a fresh session in state and DB."""
    import uuid
    session_id = str(uuid.uuid4())
    try:
        execute_query(
            "INSERT INTO sessions (id, agent, user_id, title) VALUES (?, 'supervisor', 'default', ?)",
            (session_id, "New Conversation"),
            fetch="none",
        )
    except Exception:
        pass
    st.session_state["session_id"] = session_id
    st.session_state["messages"] = []
    st.rerun()


def _load_session_messages(session_id: str) -> list[dict]:
    """Load messages for a session into state format."""
    try:
        rows = execute_query(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp",
            (session_id,),
        )
        return [{"role": r["role"], "content": r["content"]}
                for r in rows if r["role"] in ("user", "assistant")]
    except Exception:
        return []
