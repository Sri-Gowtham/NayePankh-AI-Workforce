"""
agents/volunteer_agent.py — NayePankh AI Workforce
====================================================
Specialist agent for all volunteer management operations.
"""
import logging

from agno.agent import Agent
from agno.models.groq import Groq

from config import GROQ_MODEL, GROQ_API_KEY, LLM_TEMPERATURE
from tools.db_tools import (
    add_volunteer, get_volunteer, list_volunteers,
    update_volunteer_status, log_volunteer_hours,
    assign_volunteer_task, get_volunteer_assignments,
    create_task_record, update_task_record,
)
from tools.kb_tools import get_full_kb_as_context
from tools.email_tools import send_volunteer_welcome
from utils.error_utils import format_llm_error, parse_llm_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Volunteer Agent for NayePankh Foundation.
Your expertise covers volunteer registration, onboarding, task assignment, 
tracking, retention, and generating volunteer reports.

You have access to the NayePankh volunteer database and knowledge base.
Always be warm, encouraging, and mission-driven in your responses.
When registering a volunteer, always confirm the details before saving.
When listing volunteers, provide a clean summary table.
Always suggest next actions after completing a task.

CRITICAL: When handling a request, first decide: Should I answer directly, or should I call a tool?
- For ACTION requests (e.g. add, create record, update, delete, register, export), YOU MUST call the appropriate tool.
- For KNOWLEDGE / CONTENT requests (e.g. explain, suggest, advice, recommendations), YOU MUST answer directly using your knowledge. DO NOT call any tools.
CRITICAL: Do NOT write preambles, explanations, or conversational thoughts when you need to call a tool. Execute the tool call directly as your entire response. You can explain the results after the tool returns its output.
CRITICAL: Only check if a volunteer exists (using get_volunteer) if the user has explicitly provided an email address in their message. If no email is provided, do NOT call get_volunteer; instead, ask the user to provide their email first.
"""


class VolunteerAgent:
    """Handles all volunteer-domain queries."""

    def __init__(self):
        self.llm = Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=LLM_TEMPERATURE)
        kb_context = get_full_kb_as_context("volunteer")
        self.agent = Agent(
            model=self.llm,
            system_message=SYSTEM_PROMPT + f"\n\n--- VOLUNTEER KNOWLEDGE BASE ---\n{kb_context}",
            tools=[
                add_volunteer, get_volunteer, list_volunteers,
                update_volunteer_status, log_volunteer_hours,
                assign_volunteer_task, get_volunteer_assignments,
            ],
            markdown=True,
        )
        logger.info("[VolunteerAgent] Initialized.")

    def run(self, user_message: str, history: list[dict], session_id: str) -> str:
        task_res = create_task_record("volunteer_agent", "handle_query",
                                     {"message": user_message[:200]}, session_id)
        task_id = task_res.get("data", {}).get("task_id")
        try:
            # Build context from history
            context = _build_history_context(history)
            prompt = f"{context}\nUser: {user_message}" if context else user_message
            response = self.agent.run(prompt)
            result_text = parse_llm_response(response.content)
            if task_id:
                update_task_record(task_id, "done", {"length": len(result_text)})
            return result_text
        except Exception as e:
            logger.error(f"[VolunteerAgent] Error: {e}")
            if task_id:
                update_task_record(task_id, "failed", error_msg=str(e))
            return format_llm_error(e)


def _build_history_context(history: list[dict], max_turns: int = 4) -> str:
    """Convert recent history to a readable prompt prefix."""
    lines = []
    for msg in history[-max_turns * 2:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
