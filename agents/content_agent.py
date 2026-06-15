"""
agents/content_agent.py — NayePankh AI Workforce
=================================================
Specialist agent for content generation.
Generates brand-aligned social media posts, newsletters, campaigns, etc.
"""
import logging

from agno.agent import Agent
from agno.models.ollama import Ollama

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from tools.db_tools import (
    save_content, get_content_items, update_content_status,
    create_task_record, update_task_record,
)
from tools.kb_tools import get_full_kb_as_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Content Agent for NayePankh Foundation.
Your role is to generate compelling, brand-aligned content including:
- Social media posts (Instagram, LinkedIn, Twitter)
- Monthly newsletters
- Fundraising campaign copy
- Press releases and announcements
- Blog posts and impact stories

Brand voice: Warm, inspiring, impactful, authentic.
Organization tagline: "Spreading Wings, Changing Lives"
Primary mission: Empowering underprivileged youth through education and mentorship.

Content generation rules:
1. ALWAYS follow the tone guidelines for each platform from the knowledge base
2. ALWAYS include appropriate hashtags from the approved hashtag list
3. NEVER use restricted words
4. Keep content factual — do not fabricate statistics
5. Save every generated piece to the database as a draft
6. Use the provided templates as a starting point, then customize

After generating content, ask if the user wants to:
- Edit/refine it
- Save it as draft (default)
- Mark it as ready for review
"""


class ContentAgent:
    """Handles all content generation queries."""

    def __init__(self):
        self.llm = Ollama(id=OLLAMA_MODEL, host=OLLAMA_BASE_URL)
        kb_context = get_full_kb_as_context("content")
        self.agent = Agent(
            model=self.llm,
            system_message=SYSTEM_PROMPT + f"\n\n--- CONTENT KNOWLEDGE BASE ---\n{kb_context}",
            tools=[
                save_content, get_content_items, update_content_status,
            ],
            markdown=True,
        )
        logger.info("[ContentAgent] Initialized.")

    def run(self, user_message: str, history: list[dict], session_id: str) -> str:
        task_res = create_task_record("content_agent", "generate_content",
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
            logger.error(f"[ContentAgent] Error: {e}")
            if task_id:
                update_task_record(task_id, "failed", error_msg=str(e))
            return f"⚠️ Content Agent encountered an error: {str(e)}"


def _build_history_context(history: list[dict], max_turns: int = 4) -> str:
    lines = []
    for msg in history[-max_turns * 2:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")[:300]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
