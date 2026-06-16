"""
agents/resource_agent.py — NayePankh AI Workforce
==================================================
Specialist agent for fund tracking, budget management, and donor relations.
"""
import logging

from agno.agent import Agent
from agno.models.groq import Groq

from config import GROQ_MODEL, GROQ_API_KEY, BUDGET_ALERT_THRESHOLD, LLM_TEMPERATURE
from tools.db_tools import (
    add_fund, add_expenditure, add_donor,
    get_budget_utilization, create_task_record, update_task_record,
)
from tools.kb_tools import get_full_kb_as_context
from tools.file_tools import export_to_csv, export_to_pdf
from utils.error_utils import format_llm_error, parse_llm_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are the Resource Agent for NayePankh Foundation.
You manage all financial operations: incoming funds, expenditures, donor records,
budget tracking, and compliance reporting.

Budget alert threshold: {BUDGET_ALERT_THRESHOLD * 100:.0f}% utilization triggers a warning.

Core rules:
1. Always verify procurement approval thresholds before logging expenditures:
   - Under ₹1,000: No approval needed
   - ₹1,000–₹10,000: Program Coordinator approval
   - ₹10,000–₹50,000: Finance Manager approval
   - Above ₹50,000: Executive Director + Board approval
2. Check budget utilization before logging large expenditures
3. Always create/update donor records when logging donations
4. Generate 80G receipts for eligible donors
5. Alert immediately if any category exceeds the warning threshold
6. All amounts default to INR unless specified

When asked for budget status, show category-wise breakdown with utilization ratios.
When funds are low in a category, suggest alternatives or escalation paths.

CRITICAL: When handling a request, first decide: Should I answer directly, or should I call a tool?
- For ACTION requests (e.g. add fund, create record, update, delete, register, export), YOU MUST call the appropriate tool.
- For KNOWLEDGE / CONTENT requests (e.g. explain, suggest, advice, recommendations, fundraising ideas), YOU MUST answer directly using your knowledge. DO NOT call any tools.
CRITICAL: Do NOT write preambles, explanations, or conversational thoughts when you need to call a tool. Execute the tool call directly as your entire response.
"""


class ResourceAgent:
    """Handles all resource and finance queries."""

    def __init__(self):
        self.llm = Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=LLM_TEMPERATURE)
        kb_context = get_full_kb_as_context("resource")
        self.agent = Agent(
            model=self.llm,
            system_message=SYSTEM_PROMPT + f"\n\n--- RESOURCE KNOWLEDGE BASE ---\n{kb_context}",
            tools=[
                add_fund, add_expenditure, add_donor,
                get_budget_utilization, export_to_csv, export_to_pdf,
            ],
            markdown=True,
        )
        logger.info("[ResourceAgent] Initialized.")

    def run(self, user_message: str, history: list[dict], session_id: str) -> str:
        task_res = create_task_record("resource_agent", "handle_finance",
                                     {"message": user_message[:200]}, session_id)
        task_id = task_res.get("data", {}).get("task_id")
        try:
            context = _build_history_context(history)
            prompt = f"{context}\nUser: {user_message}" if context else user_message
            response = self.agent.run(prompt)
            result_text = parse_llm_response(response.content)
            if task_id:
                update_task_record(task_id, "done", {"length": len(result_text)})
            return result_text
        except Exception as e:
            logger.error(f"[ResourceAgent] Error: {e}")
            if task_id:
                update_task_record(task_id, "failed", error_msg=str(e))
            return format_llm_error(e)


def _build_history_context(history: list[dict], max_turns: int = 4) -> str:
    lines = []
    for msg in history[-max_turns * 2:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
