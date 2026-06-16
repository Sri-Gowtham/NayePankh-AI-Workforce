import json
import logging
import threading
from typing import Dict, List, Any
from datetime import datetime

from agno.agent import Agent
from agno.models.groq import Groq

from config import GROQ_MODEL, GROQ_API_KEY, LLM_TEMPERATURE
from engine.workflows import WORKFLOW_TEMPLATES
from tools.db_tools import (
    create_workflow,
    update_workflow_status,
    get_workflow,
    add_workflow_step,
    update_workflow_step,
)

# Import specialist agents
from agents.volunteer_agent import VolunteerAgent
from agents.internship_agent import InternshipAgent
from agents.content_agent import ContentAgent
from agents.analytics_agent import AnalyticsAgent
from agents.resource_agent import ResourceAgent
from utils.error_utils import format_llm_error

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.llm = Groq(
            id=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=LLM_TEMPERATURE
        )
        self.planner_agent = Agent(
            model=self.llm,
            system_message="You are the Workflow Planner. Match the user's complex request to the closest predefined workflow.",
            markdown=False
        )
        self.aggregator_agent = Agent(
            model=self.llm,
            system_message="You are the Workflow Aggregator. Synthesize the outputs from multiple agents into a single, cohesive, well-formatted final report for the user.",
            markdown=True
        )

        # Lazy load agents to avoid circular dependencies and save memory
        self.specialists = {}

    def _get_specialist(self, agent_name: str) -> Agent:
        if agent_name not in self.specialists:
            if agent_name == "volunteer":
                self.specialists[agent_name] = VolunteerAgent().agent
            elif agent_name == "internship":
                self.specialists[agent_name] = InternshipAgent().agent
            elif agent_name == "content":
                self.specialists[agent_name] = ContentAgent().agent
            elif agent_name == "analytics":
                self.specialists[agent_name] = AnalyticsAgent().agent
            elif agent_name == "resource":
                self.specialists[agent_name] = ResourceAgent().agent
        return self.specialists[agent_name]

    def select_template(self, prompt: str) -> str:
        """Use LLM to select the best workflow template."""
        system_prompt = (
            "Analyze the user's request and map it to one of the following workflow templates:\n"
            "1. 'campaign_builder' - For creating awareness, donation, or social media campaigns.\n"
            "2. 'internship_guidance' - For career paths, skills assessment, or internship suggestions.\n"
            "3. 'event_planning' - For organizing community events, volunteer gathering, and budgeting.\n"
            "Return ONLY the template ID as a plain string, or 'custom' if none match."
        )
        try:
            response = self.planner_agent.run(f"{system_prompt}\n\nUser Request: {prompt}")
            res = response.content.strip().lower()
            if res in WORKFLOW_TEMPLATES:
                return res
            # Fallback to keyword matching
            prompt_lower = prompt.lower()
            for key, tmpl in WORKFLOW_TEMPLATES.items():
                if any(kw in prompt_lower for kw in tmpl["trigger_keywords"]):
                    return key
        except Exception as e:
            logger.error(f"[Orchestrator] Template selection failed: {e}")
        
        # Default fallback
        return "campaign_builder"

    def execute_workflow(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """
        Plans, executes, and aggregates a multi-agent workflow sequentially.
        """
        template_id = self.select_template(prompt)
        template = WORKFLOW_TEMPLATES.get(template_id)
        
        if not template:
            return {"error": "Could not determine workflow template."}

        # 1. Create Workflow Record
        wf_res = create_workflow(session_id, template["title"], prompt)
        if not wf_res["success"]:
            return {"error": "Failed to create workflow DB record."}
        workflow_id = wf_res["data"]["workflow_id"]
        update_workflow_status(workflow_id, "running")

        # 2. Create Step Records
        steps = []
        for step_def in template["steps"]:
            agent_name = step_def["agent"]
            task_prompt = f"Workflow Request: {prompt}\n\nYour Task: {step_def['task_prompt']}"
            step_res = add_workflow_step(workflow_id, agent_name, task_prompt)
            if step_res["success"]:
                steps.append({
                    "id": step_res["data"]["step_id"],
                    "agent": agent_name,
                    "task_prompt": task_prompt
                })

        # 3. Execute Steps (Sequentially for safety & context, updates UI)
        # Note: UI will read DB status to render timeline.
        outputs = []
        for step in steps:
            step_id = step["id"]
            agent_name = step["agent"]
            task_prompt = step["task_prompt"]
            
            update_workflow_step(step_id, "running")
            
            try:
                specialist = self._get_specialist(agent_name)
                # Ensure context is carried by passing prompt
                response = specialist.run(task_prompt)
                result_text = response.content
                
                update_workflow_step(step_id, "completed", result_text)
                outputs.append(f"--- Output from {agent_name.capitalize()} Agent ---\n{result_text}")
            except Exception as e:
                logger.error(f"[Orchestrator] Step failed: {e}")
                update_workflow_step(step_id, "failed", str(e))
                outputs.append(f"--- Output from {agent_name.capitalize()} Agent ---\nFailed: {format_llm_error(e)}")

        # 4. Aggregation
        aggregation_prompt = (
            "You are the NayePankh Supervisor Agent. The user requested: "
            f"'{prompt}'\n\n"
            "Below are the outputs from our specialist agents who collaborated on this task. "
            "Synthesize this into a cohesive, highly professional, and perfectly formatted final report "
            "using Markdown. Remove redundant information, organize with headers, and present it as a unified plan.\n\n"
            + "\n\n".join(outputs)
        )
        
        try:
            agg_response = self.aggregator_agent.run(aggregation_prompt)
            final_report = agg_response.content
            update_workflow_status(workflow_id, "completed", final_report)
            return {"success": True, "workflow_id": workflow_id, "final_report": final_report}
        except Exception as e:
            logger.error(f"[Orchestrator] Aggregation failed: {e}")
            update_workflow_status(workflow_id, "failed", str(e))
            return {"error": format_llm_error(e)}
