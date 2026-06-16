"""
app.py — NayePankh AI Workforce
================================
Main Streamlit entry point.

Layout:
  ├── Sidebar  (session nav, quick actions, agent status)
  └── Main Area
      ├── Tab 1: 🏠 OS Overview (landing dashboard, active agent directory, architecture flowchart)
      ├── Tab 2: 💬 Chat Terminal (conversational UI + execution timeline monitor)
      ├── Tab 3: 📊 Live Dashboard (real-time charity KPIs, Plotly charts)
      └── Tab 4: 📋 Task Log (task history)
"""
import logging
import uuid
from pathlib import Path

import streamlit as st

# ── Page config MUST be the first Streamlit call ─────────────
st.set_page_config(
    page_title="NayePankh AI Operating System",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject custom CSS ─────────────────────────────────────────
_css_path = Path(__file__).parent / "ui" / "styles" / "custom.css"
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Initialise DB & Logging ───────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from memory.db import init_db
init_db()

# ── Import UI Components ──────────────────────────────────────
from ui.components.sidebar      import render_sidebar
from ui.components.overview     import render_overview
from ui.components.chat_window  import render_chat_window, render_chat_input
from ui.components.timeline     import render_workflow_timeline
from ui.components.dashboard    import render_dashboard
from ui.components.task_tracker import render_task_tracker
from tools.db_tools             import save_message, get_session_messages

# ── Session State Bootstrap ───────────────────────────────────
def _init_session():
    if "session_id" not in st.session_state:
        session_id = str(uuid.uuid4())
        st.session_state["session_id"] = session_id
        # Create session record in DB
        from memory.db import execute_query
        try:
            execute_query(
                "INSERT INTO sessions (id, agent, user_id, title) "
                "VALUES (?, 'supervisor', 'default', 'New Conversation')",
                (session_id,),
                fetch="none",
            )
        except Exception as e:
            logger.warning(f"Could not create session: {e}")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "supervisor" not in st.session_state:
        from agents.supervisor import SupervisorAgent
        st.session_state["supervisor"] = SupervisorAgent()
    if "quick_prompt" not in st.session_state:
        st.session_state["quick_prompt"] = None


_init_session()

# ── Sidebar ───────────────────────────────────────────────────
render_sidebar()

# ── Main Content Tabs ─────────────────────────────────────────
tab_overview, tab_chat, tab_dashboard, tab_tasks = st.tabs([
    "🏠 OS Overview",
    "💬 Chat Terminal",
    "📊 Live Dashboard",
    "📋 Task Log",
])

# ── Tab 1: OS Overview ────────────────────────────────────────
with tab_overview:
    render_overview()

# ── Tab 2: Chat Terminal ──────────────────────────────────────
with tab_chat:
    # 1. Sync messages from DB on every render to catch background thread updates
    session_id = st.session_state["session_id"]
    db_msgs_res = get_session_messages(session_id, limit=50)
    if db_msgs_res.get("success"):
        st.session_state["messages"] = db_msgs_res["data"]

    # 2. Render existing messages
    render_chat_window(st.session_state["messages"])

    # 3. Render active workflow timeline (polls while running)
    is_workflow_running = render_workflow_timeline(session_id)

    # 4. Handle quick action prompt injected from sidebar
    if st.session_state.get("quick_prompt"):
        user_input = st.session_state.pop("quick_prompt")
    else:
        user_input = render_chat_input()

    if user_input:
        session_id = st.session_state["session_id"]
        supervisor = st.session_state["supervisor"]

        # Add user message to display
        st.session_state["messages"].append({"role": "user", "content": user_input})

        # Show user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Stream agent response
        with st.chat_message("assistant", avatar="🕊️"):
            with st.spinner("🧠 Supervisor routing workflow tasks..."):
                try:
                    response_text = supervisor.run(user_input, session_id)
                except Exception as e:
                    logger.error(f"Supervisor error: {e}")
                    response_text = (
                        "⚠️ I encountered an unexpected error. "
                        "Please check that your GROQ_API_KEY is configured in your .env, "
                        "then try again."
                    )

            st.markdown(response_text)

        st.rerun()

# ── Tab 3: Live Dashboard ─────────────────────────────────────
with tab_dashboard:
    render_dashboard()

# ── Tab 4: Task Log ───────────────────────────────────────────
with tab_tasks:
    render_task_tracker()
