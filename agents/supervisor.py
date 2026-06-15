"""
agents/supervisor.py — NayePankh AI Workforce
===============================================
Supervisor Agent: the orchestrator that routes user queries
to the appropriate specialist agent(s).

Routing Logic:
  1. Receives user message + session history
  2. Calls qwen3:8b to classify intent → one of 5 domains
  3. Instantiates and calls the matching specialist agent
  4. Returns the specialist's response (or aggregates multiple)
"""
import json
import logging
from typing import Optional

from agno.agent import Agent
from agno.models.ollama import Ollama

from config import OLLAMA_MODEL, OLLAMA_BASE_URL, LLM_TEMPERATURE
from tools.db_tools import (
    create_task_record, update_task_record,
    save_message, get_session_messages
)

logger = logging.getLogger(__name__)

# ── Intent classification prompt ─────────────────────────────
ROUTER_SYSTEM_PROMPT = """You are the Supervisor Agent for NayePankh Foundation's AI Workforce system.
Your ONLY job is to classify the user's request into one of the following routing categories:

Categories:
- volunteer   → queries about volunteer management, onboarding, assignments, retention
- internship  → queries about intern applications, pipeline, milestones, certificates
- content     → requests to generate social media posts, newsletters, campaigns, press releases
- analytics   → requests for reports, KPIs, statistics, dashboards, trend analysis
- resource    → queries about funds, donations, expenditures, budget, donors
- workflow    → complex requests that require multiple agents collaborating (e.g. event planning, campaigns, career path guidance)
- general     → greetings, meta questions about the system, or unclear requests

Respond with a JSON object ONLY, no explanation:
{"domain": "<one of the above>", "confidence": <0.0-1.0>, "summary": "<one-line task summary>"}
"""

# ── Specialist agent system prompts ──────────────────────────
AGENT_DESCRIPTIONS = {
    "volunteer":  "volunteer management (registration, assignments, retention)",
    "internship": "internship pipeline (applications, milestones, certificates)",
    "content":    "content generation (social posts, newsletters, campaigns)",
    "analytics":  "analytics and reporting (KPIs, trends, impact reports)",
    "resource":   "resource and finance management (funds, donations, budgets)",
}


class SupervisorAgent:
    """
    Supervisor Agent — classifies intent and delegates to specialist agents.

    Usage:
        supervisor = SupervisorAgent()
        response = supervisor.run(user_message, session_id)
    """

    def __init__(self):
        self.router_llm = Ollama(
            id=OLLAMA_MODEL,
            host=OLLAMA_BASE_URL,
        )
        self._router_agent = Agent(
            model=self.router_llm,
            system_message=ROUTER_SYSTEM_PROMPT,
            markdown=False,
        )
        logger.info("[Supervisor] Initialized with router agent.")

    def classify_intent(self, user_message: str, history: list[dict]) -> dict:
        """
        Call the router LLM to classify the user's intent.

        Returns:
            {"domain": str, "confidence": float, "summary": str}
        """
        # Build a condensed history context (last 6 turns)
        context_lines = []
        for msg in history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]  # truncate long messages
            context_lines.append(f"{role.upper()}: {content}")

        context_str = "\n".join(context_lines)
        classification_prompt = (
            f"Recent conversation:\n{context_str}\n\n"
            f"New user message: {user_message}\n\n"
            f"Classify the intent. Reply with JSON only."
        )

        try:
            response = self._router_agent.run(classification_prompt)
            raw = response.content.strip()

            # Extract JSON even if surrounded by markdown fences
            if "```" in raw:
                raw = raw.split("```")[1].replace("json", "").strip()

            classification = json.loads(raw)
            return classification
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[Supervisor] Classification failed: {e}. Defaulting to 'general'.")
            return {"domain": "general", "confidence": 0.5, "summary": user_message[:80]}

    def run(self, user_message: str, session_id: str) -> str:
        """
        Main entry point. Routes user message to the correct specialist agent.

        Args:
            user_message: Raw user input string
            session_id:   Active session UUID

        Returns:
            Agent response string
        """
        # 1. Load session history
        history_result = get_session_messages(session_id, limit=10)
        history = history_result.get("data", []) if history_result.get("success") else []

        # 2. Save user message
        save_message(session_id, "user", user_message, agent="supervisor")

        # 3. Classify intent
        classification = self.classify_intent(user_message, history)
        domain  = classification.get("domain", "general")
        summary = classification.get("summary", user_message[:80])
        logger.info(f"[Supervisor] Routed to '{domain}' | confidence={classification.get('confidence'):.2f} | {summary}")

        # 4. Create task record
        task_res = create_task_record(
            agent="supervisor",
            task_type="route_query",
            payload={"domain": domain, "summary": summary},
            session_id=session_id,
        )
        task_id = task_res.get("data", {}).get("task_id")

        # 5. Dispatch to specialist agent
        try:
            response_text = self._dispatch(domain, user_message, history, session_id)
        except Exception as e:
            logger.error(f"[Supervisor] Dispatch error: {e}")
            response_text = (
                "I encountered an issue processing your request. "
                "Please try rephrasing or contact the NayePankh admin team."
            )
            if task_id:
                update_task_record(task_id, "failed", error_msg=str(e))
            return response_text

        # 6. Save assistant response & update task
        save_message(session_id, "assistant", response_text, agent=domain)
        if task_id:
            update_task_record(task_id, "done", result={"domain": domain, "response_length": len(response_text)})

        return response_text

    def _dispatch(self, domain: str, user_message: str,
                  history: list[dict], session_id: str) -> str:
        """Lazy-import and invoke the appropriate specialist agent."""
        if domain == "volunteer":
            from agents.volunteer_agent import VolunteerAgent
            return VolunteerAgent().run(user_message, history, session_id)

        elif domain == "internship":
            from agents.internship_agent import InternshipAgent
            return InternshipAgent().run(user_message, history, session_id)

        elif domain == "content":
            from agents.content_agent import ContentAgent
            return ContentAgent().run(user_message, history, session_id)

        elif domain == "analytics":
            from agents.analytics_agent import AnalyticsAgent
            return AnalyticsAgent().run(user_message, history, session_id)

        elif domain == "resource":
            from agents.resource_agent import ResourceAgent
            return ResourceAgent().run(user_message, history, session_id)

        elif domain == "workflow":
            from engine.orchestrator import Orchestrator
            import threading
            orch = Orchestrator()
            
            def run_workflow_in_background():
                result = orch.execute_workflow(session_id, user_message)
                # When done, save the final report to chat messages
                if result.get("success"):
                    save_message(session_id, "assistant", result.get("final_report"), agent="supervisor")
                else:
                    save_message(session_id, "assistant", f"Workflow failed: {result.get('error')}", agent="supervisor")

            thread = threading.Thread(target=run_workflow_in_background)
            thread.start()
            
            return "⚡ **Workflow Started**... Check the timeline below for live progress."

        else:
            return self._handle_general(user_message)

    def _handle_general(self, user_message: str) -> str:
        """Handle greetings and meta queries directly in the supervisor."""
        general_prompt = (
            "You are the NayePankh AI Workforce assistant — an intelligent operating system "
            "for NayePankh Foundation NGO. You have 5 specialist agents:\n"
            "• Volunteer Agent — volunteer onboarding, assignments, retention\n"
            "• Internship Agent — intern applications, milestones, certificates\n"
            "• Content Agent — social posts, newsletters, campaigns\n"
            "• Analytics Agent — KPIs, reports, trends\n"
            "• Resource Agent — funds, donations, budget tracking\n\n"
            f"User asked: {user_message}\n\n"
            "Respond warmly and helpfully. Guide them on what you can help with."
        )
        try:
            response = self._router_agent.run(general_prompt)
            return response.content
        except Exception as e:
            return (
                "👋 Welcome to NayePankh AI Workforce! I can help with:\n"
                "• Volunteer management\n• Internship pipeline\n"
                "• Content generation\n• Analytics & reports\n"
                "• Fund & resource tracking\n\nWhat would you like to do today?"
            )
