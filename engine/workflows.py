"""
engine/workflows.py — NayePankh AI Workforce
============================================
Pre-defined multi-agent workflow templates.
"""

WORKFLOW_TEMPLATES = {
    "campaign_builder": {
        "title": "Campaign Builder",
        "description": "Create a comprehensive awareness or donation campaign.",
        "trigger_keywords": ["campaign", "awareness", "blood donation", "fundraiser promotion"],
        "steps": [
            {
                "agent": "content",
                "task_prompt": "Develop a core campaign idea, 3 social media posts (with hashtags), and an outreach email template based on the user's request."
            },
            {
                "agent": "analytics",
                "task_prompt": "Analyze the target audience for this campaign. Suggest engagement recommendations and 3 key metrics we should track."
            },
            {
                "agent": "volunteer",
                "task_prompt": "Estimate volunteer requirements to execute this campaign and draft a brief recruitment strategy."
            }
        ]
    },
    "internship_guidance": {
        "title": "Internship Career Path",
        "description": "Provide career guidance and resources based on intern skills.",
        "trigger_keywords": ["career path", "career guidance", "suggest a career", "internship recommendation"],
        "steps": [
            {
                "agent": "internship",
                "task_prompt": "Assess the user's current skills and recommend 2-3 relevant internship roles within the NGO."
            },
            {
                "agent": "resource",
                "task_prompt": "Based on the user's skills and potential roles, suggest 3 free learning resources or certifications they should pursue."
            }
        ]
    },
    "event_planning": {
        "title": "Event Planning",
        "description": "Plan a large-scale community event.",
        "trigger_keywords": ["organizing an event", "community event", "event planning"],
        "steps": [
            {
                "agent": "volunteer",
                "task_prompt": "Create a detailed volunteer shift plan and crowd management strategy for this event."
            },
            {
                "agent": "analytics",
                "task_prompt": "Estimate resources needed (budget, materials, space) based on the expected audience size."
            },
            {
                "agent": "content",
                "task_prompt": "Draft a promotion strategy for the event, including a press release draft and local outreach plan."
            }
        ]
    }
}
