"""
tools/kb_tools.py — NayePankh AI Workforce
==========================================
Knowledge base retrieval functions.
Loads domain-specific JSON knowledge bases and performs
keyword-based context search to inject into agent prompts.
"""
import json
import logging
from pathlib import Path
from typing import Any

from config import KB_PATHS

logger = logging.getLogger(__name__)


def load_knowledge_base(domain: str) -> dict:
    """
    Load the entire JSON knowledge base for a given domain.

    Args:
        domain: One of 'volunteer', 'internship', 'content', 'analytics', 'resource'

    Returns:
        Parsed JSON dict or empty dict on error.
    """
    path: Path = KB_PATHS.get(domain)
    if not path:
        logger.warning(f"[KB] Unknown domain: {domain}")
        return {}
    if not path.exists():
        logger.warning(f"[KB] File not found: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"[KB] JSON parse error in {path}: {e}")
        return {}


def search_knowledge(domain: str, query: str, max_results: int = 5) -> list[dict]:
    """
    Keyword-based search over a domain knowledge base.

    Flattens the JSON structure into searchable text chunks,
    scores each by keyword overlap with the query, and returns
    the top `max_results` matching chunks.

    Args:
        domain:      Knowledge base domain key
        query:       Natural language query string
        max_results: Maximum number of chunks to return

    Returns:
        List of {"key": str, "content": str, "score": int} dicts
    """
    kb = load_knowledge_base(domain)
    if not kb:
        return []

    query_words = set(query.lower().split())
    chunks = _flatten_kb(kb)

    scored = []
    for key, content in chunks.items():
        content_lower = content.lower()
        score = sum(1 for w in query_words if w in content_lower)
        if score > 0:
            scored.append({"key": key, "content": content, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max_results]


def get_full_kb_as_context(domain: str) -> str:
    """
    Return a concise text representation of the full KB for prompt injection.

    Args:
        domain: Knowledge base domain key

    Returns:
        Formatted string ready for LLM context window injection.
    """
    kb = load_knowledge_base(domain)
    if not kb:
        return f"No knowledge base found for domain: {domain}"
    return _kb_to_text(kb)


# ── Private helpers ─────────────────────────────────────────

def _flatten_kb(obj: Any, prefix: str = "", result: dict = None) -> dict:
    """Recursively flatten nested JSON into key: text_value pairs."""
    if result is None:
        result = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            _flatten_kb(v, new_key, result)
    elif isinstance(obj, list):
        result[prefix] = " | ".join(str(i) for i in obj)
    else:
        result[prefix] = str(obj)
    return result


def _kb_to_text(kb: dict, indent: int = 0) -> str:
    """Convert nested dict KB into human-readable indented text."""
    lines = []
    for key, value in kb.items():
        pad = "  " * indent
        if isinstance(value, dict):
            lines.append(f"{pad}[{key}]")
            lines.append(_kb_to_text(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{pad}{key}: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"{pad}{key}: {value}")
    return "\n".join(lines)
