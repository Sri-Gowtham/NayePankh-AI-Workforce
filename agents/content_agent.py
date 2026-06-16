"""
agents/content_agent.py — NayePankh AI Workforce
=================================================
Specialist agent for content generation.
Generates brand-aligned social media posts, newsletters, campaigns, etc.
"""
import logging

from agno.agent import Agent
from agno.models.groq import Groq

from config import GROQ_MODEL, GROQ_API_KEY, LLM_TEMPERATURE
from tools.db_tools import (
    save_content, get_content_items, update_content_status,
    create_task_record, update_task_record,
)
from tools.kb_tools import get_full_kb_as_context
from utils.error_utils import format_llm_error, parse_llm_response

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

CRITICAL: When handling a request, first decide: Should I answer directly, or should I call a tool?
- For ACTION requests (e.g. save, add, create record, update, delete, register, export), YOU MUST call the appropriate tool.
- For KNOWLEDGE / CONTENT requests (e.g. explain, suggest, generate content, campaign ideas, advice, recommendations, write a post), YOU MUST answer directly using your knowledge and return the generated content. DO NOT call any tools. Do not save drafts unless explicitly asked to do so.
CRITICAL: Do NOT write preambles, explanations, or conversational thoughts when you need to call a tool. Execute the tool call directly as your entire response.
"""


class ContentAgent:
    """Handles all content generation queries."""

    def __init__(self):
        self.llm = Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=LLM_TEMPERATURE)
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
            result_text = parse_llm_response(response.content)
            if task_id:
                update_task_record(task_id, "done", {"length": len(result_text)})
            return result_text
        except Exception as e:
            logger.error(f"[ContentAgent] Error: {e}")
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
