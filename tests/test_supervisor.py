"""
tests/test_supervisor.py — NayePankh AI Workforce
==================================================
Tests for supervisor intent classification and routing.
Uses mocked Agno Agent to avoid LLM calls in CI.
"""
import json
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class MockAgentResponse:
    def __init__(self, content: str):
        self.content = content


@pytest.fixture
def mock_supervisor():
    """Create a SupervisorAgent with mocked LLM calls."""
    with patch("agents.supervisor.Ollama"), \
         patch("agents.supervisor.Agent") as mock_agent_cls:
        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent

        from agents.supervisor import SupervisorAgent
        sup = SupervisorAgent()
        sup._router_agent = mock_agent
        yield sup, mock_agent


class TestIntentClassification:
    """Test the JSON-based intent classification."""

    @pytest.mark.parametrize("query,expected_domain", [
        ("Register a new volunteer named Priya", "volunteer"),
        ("Show me all active interns", "internship"),
        ("Write an Instagram post", "content"),
        ("Generate the monthly KPI report", "analytics"),
        ("Log a donation of ₹50000", "resource"),
        ("Hello, what can you do?", "general"),
    ])
    def test_classification_domains(self, mock_supervisor, query, expected_domain):
        sup, mock_agent = mock_supervisor
        mock_agent.run.return_value = MockAgentResponse(
            json.dumps({"domain": expected_domain, "confidence": 0.95, "summary": query[:50]})
        )
        result = sup.classify_intent(query, [])
        assert result["domain"] == expected_domain

    def test_malformed_json_defaults_to_general(self, mock_supervisor):
        sup, mock_agent = mock_supervisor
        mock_agent.run.return_value = MockAgentResponse("not valid json at all")
        result = sup.classify_intent("some query", [])
        assert result["domain"] == "general"

    def test_json_in_markdown_fence(self, mock_supervisor):
        sup, mock_agent = mock_supervisor
        response = '```json\n{"domain": "volunteer", "confidence": 0.9, "summary": "test"}\n```'
        mock_agent.run.return_value = MockAgentResponse(response)
        result = sup.classify_intent("volunteer query", [])
        assert result["domain"] == "volunteer"
