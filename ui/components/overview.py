"""
ui/components/overview.py — NayePankh AI Workforce
=====================================================
Landing dashboard, agent cards, and workflow visualization.
"""
import streamlit as st
from memory.db import execute_query
from tools.db_tools import compute_kpis

def render_overview() -> None:
    """Render the main landing page overview of the AI Operating System."""
    st.markdown('<h1 class="gradient-text" style="font-size: 2.8rem; margin-bottom: 5px;">🕊️ NayePankh AI OS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-muted); font-size: 1.1rem; margin-bottom: 25px;">Autonomous multi-agent orchestration platform for charity operations</p>', unsafe_allow_html=True)

    # ── 1. KPI Stats Cards ─────────────────────────────────────
    stats = _get_overview_stats()
    
    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div style="font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Total Workflows</div>
                <div class="kpi-value">{stats["total_workflows"]}</div>
                <div style="font-size: 11px; color: #10b981;">● Active Collaborate sessions</div>
            </div>
            <div class="kpi-card">
                <div style="font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Active Agents</div>
                <div class="kpi-value">{stats["active_agents"]}</div>
                <div style="font-size: 11px; color: #10b981;">● Online & ready</div>
            </div>
            <div class="kpi-card">
                <div style="font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Tasks Completed</div>
                <div class="kpi-value">{stats["completed_tasks"]}</div>
                <div style="font-size: 11px; color: #10b981;">● Successful dispatches</div>
            </div>
            <div class="kpi-card">
                <div style="font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Success Rate</div>
                <div class="kpi-value">{stats["success_rate"]}</div>
                <div style="font-size: 11px; color: #10b981;">● Operational accuracy</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── 2. Columns: Agent Grid & Architecture Flow ─────────────
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.markdown('### 🤖 Active Agent Directory')
        _render_agent_grid()

    with right_col:
        st.markdown('### 📐 OS Architecture')
        _render_architecture_flow()

def _get_overview_stats() -> dict:
    try:
        w_row = execute_query("SELECT COUNT(*) AS c FROM workflows", fetch="one")
        t_row = execute_query("SELECT COUNT(*) AS c FROM tasks", fetch="one")
        tc_row = execute_query("SELECT COUNT(*) AS c FROM tasks WHERE status='done'", fetch="one")
        
        total_workflows = w_row["c"] if w_row else 0
        total_tasks = t_row["c"] if t_row else 0
        completed_tasks = tc_row["c"] if tc_row else 0
        
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100.0
        return {
            "total_workflows": total_workflows,
            "active_agents": 6,
            "completed_tasks": completed_tasks,
            "success_rate": f"{success_rate:.1f}%"
        }
    except Exception:
        return {
            "total_workflows": 0,
            "active_agents": 6,
            "completed_tasks": 0,
            "success_rate": "100.0%"
        }

def _render_agent_grid() -> None:
    # Specialist agent configs
    agents_info = [
        {
            "name": "Supervisor Agent",
            "icon": "🧠",
            "badge": "coordinator",
            "desc": "Orchestrates multi-agent collaboration, dynamically dispatches steps, and synthesizes reports.",
            "activity": "Monitoring chat channel & task registry"
        },
        {
            "name": "Volunteer Agent",
            "icon": "🙋",
            "badge": "operations",
            "desc": "Manages volunteer profiles, onboardings, logging hours, and coordinating activity runs.",
            "activity": "Idle — Ready to process logs"
        },
        {
            "name": "Internship Agent",
            "icon": "🎓",
            "badge": "operations",
            "desc": "Reviews applicant pipeline, transitions internship statuses, logs milestones, and prints certificates.",
            "activity": "Idle — Watching milestones"
        },
        {
            "name": "Content Agent",
            "icon": "✍️",
            "badge": "marketing",
            "desc": "Generates promotional announcements, social media outlines, newsletters, and email copies.",
            "activity": "Idle — Copywriter ready"
        },
        {
            "name": "Analytics Agent",
            "icon": "📊",
            "badge": "analytics",
            "desc": "Aggregates performance snapshots, logs metrics, and produces real-time KPI evaluations.",
            "activity": "Idle — SQL analyzer online"
        },
        {
            "name": "Resource Agent",
            "icon": "💰",
            "badge": "finance",
            "desc": "Validates project categories, tracks donor collections, logs expenditures, and issues budget warning flags.",
            "activity": "Idle — Budget validator online"
        }
    ]

    for agent in agents_info:
        st.markdown(
            f"""
            <div class="cyber-card" style="padding: 16px; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 18px; font-weight: 700; color: var(--text-main);">
                        {agent["icon"]} {agent["name"]}
                    </span>
                    <span style="font-size: 10px; padding: 2px 8px; border-radius: 12px; background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0,240,255,0.3); color: var(--primary); font-weight: 700; text-transform: uppercase;">
                        {agent["badge"]}
                    </span>
                </div>
                <div style="color: var(--text-muted); font-size: 13px; line-height: 1.5; margin-bottom: 10px;">
                    {agent["desc"]}
                </div>
                <div style="font-size: 11px; color: #10b981; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 6px;">
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: #10b981; animation: pulse 1.5s infinite;"></span>
                    <span>{agent["activity"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def _render_architecture_flow() -> None:
    st.markdown(
        '<div class="cyber-card" style="padding: 20px; text-align: center;">'
        '<div class="flow-container">'
        '<div class="flow-node supervisor">🧠 Supervisor Agent<div style="font-size: 9px; font-weight: normal; color: #aaa; margin-top: 2px;">Router & Aggregator</div></div>'
        '<div class="flow-arrow">↓</div>'
        '<div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Orchestrates</div>'
        '<div class="flow-arrow">↓</div>'
        '<div class="flow-node specialist">🙋 Volunteer Agent</div>'
        '<div class="flow-node specialist">🎓 Internship Agent</div>'
        '<div class="flow-node specialist">✍️ Content Agent</div>'
        '<div class="flow-node specialist">📊 Analytics Agent</div>'
        '<div class="flow-node specialist">💰 Resource Agent</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
