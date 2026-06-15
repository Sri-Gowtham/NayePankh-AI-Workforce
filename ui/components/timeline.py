import streamlit as st
import time
from tools.db_tools import get_active_workflow, get_workflow_steps

# Emojis for agent domains
AGENT_ICONS = {
    "supervisor": "🧠",
    "volunteer": "🙋",
    "internship": "🎓",
    "content": "✍️",
    "analytics": "📈",
    "resource": "💰"
}

def render_workflow_timeline(session_id: str):
    """
    Renders an active workflow's timeline in the Streamlit UI.
    Auto-updates using st.rerun() if a workflow is currently running.
    """
    wf_res = get_active_workflow(session_id)
    
    if not wf_res.get("success") or not wf_res.get("data"):
        return False  # No active workflow

    workflow = wf_res["data"]
    workflow_id = workflow["id"]
    status = workflow["status"]
    
    st.markdown("---")
    st.markdown(f"### ⚡ Active Workflow: {workflow['title']}")
    
    steps_res = get_workflow_steps(workflow_id)
    steps = steps_res.get("data", [])

    # Display steps visually
    for step in steps:
        agent = step["agent"]
        icon = AGENT_ICONS.get(agent, "🤖")
        step_status = step["status"]
        
        if step_status == "completed":
            status_icon = "✅"
            color = "green"
        elif step_status == "running":
            status_icon = "🔄"
            color = "orange"
        elif step_status == "failed":
            status_icon = "❌"
            color = "red"
        else:
            status_icon = "⏳"
            color = "gray"

        st.markdown(
            f"""
            <div style="padding: 10px; border-left: 3px solid {color}; margin-bottom: 5px; background-color: rgba(255,255,255,0.05); border-radius: 4px;">
                <strong>{status_icon} [{icon} {agent.capitalize()}]</strong> 
                <br/><span style="color: #aaa; font-size: 0.9em;">{step['task_prompt']}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # If it's still running, wait a bit and refresh the UI so the user sees progress
    if status in ("planning", "running"):
        with st.spinner("Agents are collaborating..."):
            time.sleep(2)
            st.rerun()

    return True
