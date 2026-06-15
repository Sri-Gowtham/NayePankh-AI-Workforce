"""
ui/components/dashboard.py — NayePankh AI Workforce
=====================================================
KPI dashboard panel with metric cards and Plotly charts.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from tools.db_tools import compute_kpis, get_budget_utilization


def render_dashboard() -> None:
    """Render the full KPI dashboard tab."""
    st.markdown("## 📊 Live Impact Dashboard")
    st.caption("Real-time data from NayePankh operations database")

    # Compute fresh KPIs
    with st.spinner("Fetching latest metrics..."):
        kpi_res = compute_kpis()
        budget_res = get_budget_utilization()

    kpis   = kpi_res.get("data", {}) if kpi_res.get("success") else {}
    budget = budget_res.get("data", []) if budget_res.get("success") else []

    # ── Row 1: Key Metrics ────────────────────────────────────
    st.markdown("### 🌟 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    _metric_card(col1, "🙋 Active Volunteers",  kpis.get("active_volunteers", 0),    "")
    _metric_card(col2, "🎓 Active Interns",      kpis.get("active_interns", 0),       "")
    _metric_card(col3, "✅ Interns Completed",   kpis.get("completed_interns", 0),    "")
    _metric_card(col4, "💰 Funds Raised",
                 f"₹{kpis.get('total_funds_raised', 0):,.0f}", "")
    _metric_card(col5, "📝 Content Published",   kpis.get("content_published", 0),    "this month")

    st.divider()

    # ── Row 2: Charts ─────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 💸 Budget Utilization by Category")
        if budget:
            fig = _budget_utilization_chart(budget)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No financial data yet. Log some funds and expenditures to see this chart.")

    with col_right:
        st.markdown("#### 🕐 Volunteer Hours Total")
        hours = kpis.get("volunteer_hours_total", 0)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=hours,
            title={"text": "Total Hours Logged"},
            gauge={
                "axis": {"range": [0, max(hours * 2, 100)]},
                "bar":  {"color": "#22c55e"},
                "steps": [
                    {"range": [0, hours * 0.5], "color": "#1e293b"},
                    {"range": [hours * 0.5, hours], "color": "#166534"},
                ],
            },
        ))
        fig.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#f8fafc"},
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Row 3: Intern Pipeline ────────────────────────────────
    st.markdown("#### 🎓 Intern Pipeline Overview")
    _render_intern_pipeline()

    st.divider()

    # ── Row 4: Open Tasks ─────────────────────────────────────
    st.markdown(f"#### 🔄 Open Tasks: `{kpis.get('open_tasks', 0)}`")
    _render_open_tasks()


def _metric_card(col, label: str, value, subtitle: str = "") -> None:
    with col:
        st.metric(label=label, value=value, delta=subtitle if subtitle else None)


def _budget_utilization_chart(budget: list[dict]):
    categories = [b["category"] for b in budget]
    raised     = [b["funds_raised"] for b in budget]
    spent      = [b["expenditure"] for b in budget]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Funds Raised", x=categories, y=raised,
                         marker_color="#22c55e"))
    fig.add_trace(go.Bar(name="Expenditure", x=categories, y=spent,
                         marker_color="#ef4444"))
    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.8)",
        font={"color": "#f8fafc"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        height=300,
        margin={"t": 20, "b": 10},
    )
    return fig


def _render_intern_pipeline() -> None:
    from memory.db import execute_query
    try:
        rows = execute_query(
            "SELECT status, COUNT(*) AS count FROM interns GROUP BY status"
        )
        if not rows:
            st.info("No intern records yet.")
            return

        status_order = ["applied", "reviewing", "accepted", "active", "completed", "rejected"]
        status_map   = {r["status"]: r["count"] for r in rows}

        cols = st.columns(len(status_order))
        status_colors = {
            "applied":   "#64748b", "reviewing": "#f59e0b", "accepted": "#3b82f6",
            "active":    "#22c55e", "completed": "#8b5cf6", "rejected": "#ef4444",
        }
        for i, status in enumerate(status_order):
            count = status_map.get(status, 0)
            color = status_colors.get(status, "#64748b")
            cols[i].markdown(
                f'<div style="text-align:center;padding:12px;border-radius:8px;'
                f'background:{color}22;border:1px solid {color}55;">'
                f'<div style="font-size:24px;font-weight:700;color:{color};">{count}</div>'
                f'<div style="font-size:11px;color:#94a3b8;">{status.title()}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.error(f"Could not load intern pipeline: {e}")


def _render_open_tasks() -> None:
    from memory.db import execute_query
    try:
        rows = execute_query(
            "SELECT agent, task_type, status, created_at FROM tasks "
            "WHERE status IN ('pending','in_progress') ORDER BY created_at DESC LIMIT 10"
        )
        if not rows:
            st.success("✅ No open tasks — all caught up!")
            return
        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Could not load tasks: {e}")
