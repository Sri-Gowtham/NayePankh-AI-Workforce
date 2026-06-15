"""
agents/internship_agent.py — NayePankh AI Workforce
=====================================================
Specialist agent for the full intern lifecycle.
"""
import logging

from agno.agent import Agent
from agno.models.ollama import Ollama

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from tools.db_tools import (
    add_intern, get_intern, list_interns,
    update_intern_status, add_intern_milestone,
    get_intern_milestones, mark_certificate_issued,
    create_task_record, update_task_record,
)
from tools.kb_tools import get_full_kb_as_context
from tools.email_tools import send_intern_offer_letter, send_certificate_notification

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Internship Agent for NayePankh Foundation.
You manage the complete intern lifecycle: applications, review, acceptance, 
active tracking, milestone logging, and certificate issuance.

Pipeline stages: applied → reviewing → accepted → active → completed → rejected

Key rules:
- Always check if an intern already exists before adding a new one
- When moving an intern to 'accepted', send an offer letter
- When moving to 'completed', verify certificate conditions before issuing
- Weekly milestone submissions should include: tasks done, learnings, challenges, next plan
- Be precise with dates and program durations

Always confirm actions before executing irreversible operations.
"""


class InternshipAgent:
    """Handles all internship-domain queries."""

    def __init__(self):
        self.llm = Ollama(id=OLLAMA_MODEL, host=OLLAMA_BASE_URL)
        kb_context = get_full_kb_as_context("internship")
        self.agent = Agent(
            model=self.llm,
            system_message=SYSTEM_PROMPT + f"\n\n--- INTERNSHIP KNOWLEDGE BASE ---\n{kb_context}",
            tools=[
                add_intern, get_intern, list_interns,
                update_intern_status, add_intern_milestone,
                get_intern_milestones, mark_certificate_issued,
                send_intern_offer_letter, send_certificate_notification,
            ],
            markdown=True,
        )
        logger.info("[InternshipAgent] Initialized.")

    def run(self, user_message: str, history: list[dict], session_id: str) -> str:
        task_res = create_task_record("internship_agent", "handle_query",
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
            logger.error(f"[InternshipAgent] Error: {e}")
            if task_id:
                update_task_record(task_id, "failed", error_msg=str(e))
            return f"⚠️ Internship Agent encountered an error: {str(e)}"


def _build_history_context(history: list[dict], max_turns: int = 4) -> str:
    lines = []
    for msg in history[-max_turns * 2:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
