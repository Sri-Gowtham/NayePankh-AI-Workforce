"""
ui/components/task_tracker.py — NayePankh AI Workforce
=======================================================
Task history viewer with status badges and expandable results.
"""
import json
import streamlit as st
from memory.db import execute_query


STATUS_COLORS = {
    "done":        ("✅", "#22c55e"),
    "in_progress": ("🔄", "#f59e0b"),
    "pending":     ("⏳", "#64748b"),
    "failed":      ("❌", "#ef4444"),
}

AGENT_EMOJIS = {
    "supervisor":      "🧠",
    "volunteer_agent": "🙋",
    "internship_agent":"🎓",
    "content_agent":   "✍️",
    "analytics_agent": "📊",
    "resource_agent":  "💰",
    "email_tool":      "📧",
}


def render_task_tracker() -> None:
    """Render the task history table with filters and expandable rows."""
    st.markdown("## 📋 Task History")

    # ── Filters ───────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_agent = st.selectbox(
            "Filter by Agent",
            ["All", "supervisor", "volunteer_agent", "internship_agent",
             "content_agent", "analytics_agent", "resource_agent"],
        )
    with col2:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "done", "in_progress", "pending", "failed"],
        )
    with col3:
        limit = st.selectbox("Show last", [20, 50, 100], index=0)

    # ── Query ──────────────────────────────────────────────────
    conditions, params = [], []
    if filter_agent != "All":
        conditions.append("agent=?")
        params.append(filter_agent)
    if filter_status != "All":
        conditions.append("status=?")
        params.append(filter_status)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    try:
        tasks = execute_query(
            f"SELECT * FROM tasks {where_clause} ORDER BY created_at DESC LIMIT ?",
            tuple(params),
        )
    except Exception as e:
        st.error(f"Could not load tasks: {e}")
        return

    if not tasks:
        st.info("No tasks match the selected filters.")
        return

    st.caption(f"Showing {len(tasks)} task(s)")

    # ── Task Cards ─────────────────────────────────────────────
    for task in tasks:
        status        = task.get("status", "pending")
        icon, color   = STATUS_COLORS.get(status, ("❓", "#64748b"))
        agent         = task.get("agent", "unknown")
        agent_emoji   = AGENT_EMOJIS.get(agent, "🤖")
        task_type     = task.get("task_type", "")
        created_at    = (task.get("created_at") or "")[:19]
        completed_at  = (task.get("completed_at") or "—")[:19]

        with st.expander(
            f"{icon} `{agent_emoji} {agent}` → **{task_type}** | {created_at}",
            expanded=False,
        ):
            col_a, col_b, col_c = st.columns(3)
            col_a.markdown(f"**Status:** <span style='color:{color}'>{status}</span>",
                           unsafe_allow_html=True)
            col_b.markdown(f"**Completed:** {completed_at}")
            col_c.markdown(f"**Task ID:** #{task.get('id')}")

            # Payload
            if task.get("payload"):
                try:
                    payload = json.loads(task["payload"])
                    st.markdown("**📥 Input:**")
                    st.json(payload)
                except Exception:
                    st.code(task["payload"])

            # Result
            if task.get("result"):
                try:
                    result = json.loads(task["result"])
                    st.markdown("**📤 Output:**")
                    st.json(result)
                except Exception:
                    st.code(task["result"])

            # Error
            if task.get("error_msg"):
                st.error(f"**Error:** {task['error_msg']}")
