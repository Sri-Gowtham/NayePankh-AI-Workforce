"""
config.py — NayePankh AI Workforce
====================================
Single source of truth for all application constants.
All values fall back to .env via python-dotenv.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ── Project ─────────────────────────────────────────────────
APP_TITLE       = os.getenv("APP_TITLE", "NayePankh AI Workforce")
APP_ENV         = os.getenv("APP_ENV", "development")
LOG_LEVEL       = os.getenv("LOG_LEVEL", "INFO")

# ── Groq / LLM ──────────────────────────────────────────────
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL      = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_MAX_TOKENS  = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ── Database ─────────────────────────────────────────────────
DB_PATH         = Path(os.getenv("DB_PATH", "./memory/nayepankh.db")).resolve()
SCHEMA_PATH     = Path(__file__).parent / "schemas" / "db_schema.sql"

# ── Knowledge Bases ──────────────────────────────────────────
KB_DIR          = Path(__file__).parent / "knowledge"
KB_PATHS = {
    "volunteer":   KB_DIR / "volunteer_kb.json",
    "internship":  KB_DIR / "internship_kb.json",
    "content":     KB_DIR / "content_kb.json",
    "analytics":   KB_DIR / "analytics_kb.json",
    "resource":    KB_DIR / "resource_kb.json",
}

# ── Email (SMTP) ─────────────────────────────────────────────
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER       = os.getenv("SMTP_USER", "")
SMTP_PASSWORD   = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM      = os.getenv("EMAIL_FROM", "NayePankh Foundation <noreply@nayepankh.org>")

# ── Agent Names ──────────────────────────────────────────────
AGENTS = {
    "supervisor":  "Supervisor Agent",
    "volunteer":   "Volunteer Agent",
    "internship":  "Internship Agent",
    "content":     "Content Agent",
    "analytics":   "Analytics Agent",
    "resource":    "Resource Agent",
}

# ── Streamlit ─────────────────────────────────────────────────
PAGE_ICON       = "🕊️"
SIDEBAR_WIDTH   = 300

# ── Finance ───────────────────────────────────────────────────
DEFAULT_CURRENCY       = "INR"
BUDGET_ALERT_THRESHOLD = 0.85   # Alert when 85% of category budget is consumed

# ── Analytics ─────────────────────────────────────────────────
SNAPSHOT_METRICS = [
    "active_volunteers",
    "total_interns",
    "active_interns",
    "completed_interns",
    "total_funds_raised",
    "total_expenditure",
    "content_published",
    "open_tasks",
]
