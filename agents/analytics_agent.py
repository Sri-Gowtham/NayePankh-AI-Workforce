"""
agents/analytics_agent.py — NayePankh AI Workforce
====================================================
Specialist agent for KPI computation, trend analysis, and report generation.
"""
import logging

from agno.agent import Agent
from agno.models.ollama import Ollama

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from tools.db_tools import (
    compute_kpis, get_snapshots, save_snapshot,
    get_budget_utilization, get_recent_tasks,
    create_task_record, update_task_record,
)
from tools.kb_tools import get_full_kb_as_context
from tools.file_tools import export_to_csv, export_to_pdf

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Analytics Agent for NayePankh Foundation.
Your role is to compute KPIs, analyze trends, identify anomalies, and 
generate comprehensive impact reports for donors, board members, and operations teams.

Capabilities:
- Compute real-time KPIs from the database
- Compare metrics month-over-month and quarter-over-quarter
- Identify anomalies (e.g., volunteer drop, budget overrun)
- Generate narrative summaries of data in plain language
- Export reports as CSV or PDF

When presenting analytics:
1. Always show numbers with context (e.g., "25 active volunteers, up 12% from last month")
2. Highlight both achievements and areas of concern
3. Provide actionable recommendations based on data
4. Use clear formatting with sections and bullet points
5. Include the time period being analyzed

When generating reports, first compute_kpis to get fresh data, then analyze.
"""


class AnalyticsAgent:
    """Handles all analytics and reporting queries."""

    def __init__(self):
        self.llm = Ollama(id=OLLAMA_MODEL, host=OLLAMA_BASE_URL)
        kb_context = get_full_kb_as_context("analytics")
        self.agent = Agent(
            model=self.llm,
            system_prompt=SYSTEM_PROMPT + f"\n\n--- ANALYTICS KNOWLEDGE BASE ---\n{kb_context}",
            tools=[
                compute_kpis, get_snapshots, save_snapshot,
                get_budget_utilization, get_recent_tasks,
                export_to_csv, export_to_pdf,
            ],
            markdown=True,
            show_tool_calls=True,
        )
        logger.info("[AnalyticsAgent] Initialized.")

    def run(self, user_message: str, history: list[dict], session_id: str) -> str:
        task_res = create_task_record("analytics_agent", "generate_analytics",
                                     {"message": user_message[:200]}, session_id)
        task_id = task_res.get("data", {}).get("task_id")
        try:
            context = _build_history_context(history)
            prompt = f"{context}\nUser: {user_message}" if context else user_message
            response = self.agent.run(prompt)
            result_text = response.content
            if task_id:
                update_task_record(task_id, "done", {"length": len(result_text)})
            return result_text
        except Exception as e:
            logger.error(f"[AnalyticsAgent] Error: {e}")
            if task_id:
                update_task_record(task_id, "failed", error_msg=str(e))
            return f"⚠️ Analytics Agent encountered an error: {str(e)}"


def _build_history_context(history: list[dict], max_turns: int = 4) -> str:
    lines = []
    for msg in history[-max_turns * 2:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
