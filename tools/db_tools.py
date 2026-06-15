"""
tools/db_tools.py — NayePankh AI Workforce
==========================================
All SQLite CRUD operations exposed as plain Python functions.
These are registered as Agno tools in agent definitions.
Every function returns a dict with keys: success, data, error.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from memory.db import execute_query, execute_many

logger = logging.getLogger(__name__)


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg: str):
    logger.error(f"[DBTool] {msg}")
    return {"success": False, "data": None, "error": msg}


# ════════════════════════════════════════════════════════════
# SESSION & MESSAGE TOOLS
# ════════════════════════════════════════════════════════════

def create_session(user_id: str = "default", agent: str = "supervisor") -> dict:
    """Create a new conversation session. Returns session_id."""
    session_id = str(uuid.uuid4())
    try:
        execute_query(
            "INSERT INTO sessions (id, agent, user_id) VALUES (?, ?, ?)",
            (session_id, agent, user_id),
            fetch="none",
        )
        return _ok({"session_id": session_id})
    except Exception as e:
        return _err(str(e))


def save_message(session_id: str, role: str, content: str, agent: str = None) -> dict:
    """Persist a chat message to the messages table."""
    try:
        execute_query(
            "INSERT INTO messages (session_id, role, content, agent) VALUES (?, ?, ?, ?)",
            (session_id, role, content, agent),
            fetch="none",
        )
        return _ok({"saved": True})
    except Exception as e:
        return _err(str(e))


def get_session_messages(session_id: str, limit: int = 20) -> dict:
    """Retrieve recent messages for a session (for context window)."""
    try:
        rows = execute_query(
            "SELECT role, content, agent, timestamp FROM messages "
            "WHERE session_id=? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit),
        )
        return _ok(list(reversed(rows)))  # chronological order
    except Exception as e:
        return _err(str(e))


# ════════════════════════════════════════════════════════════
# TASK TRACKING TOOLS
# ════════════════════════════════════════════════════════════

def create_task_record(agent: str, task_type: str, payload: dict,
                       session_id: str = None) -> dict:
    """Log a new task execution in the tasks table."""
    try:
        cur = execute_query(
            "INSERT INTO tasks (session_id, agent, task_type, status, payload) "
            "VALUES (?, ?, ?, 'in_progress', ?)",
            (session_id, agent, task_type, json.dumps(payload)),
            fetch="none",
        )
        # Get last inserted id
        row = execute_query("SELECT last_insert_rowid() AS id", fetch="one")
        return _ok({"task_id": row["id"]})
    except Exception as e:
        return _err(str(e))


def update_task_record(task_id: int, status: str, result: dict = None,
                       error_msg: str = None) -> dict:
    """Update a task's status and result."""
    try:
        execute_query(
            "UPDATE tasks SET status=?, result=?, error_msg=?, completed_at=? WHERE id=?",
            (status, json.dumps(result) if result else None,
             error_msg, datetime.utcnow().isoformat(), task_id),
            fetch="none",
        )
        return _ok({"updated": True})
    except Exception as e:
        return _err(str(e))


def get_recent_tasks(agent: str = None, limit: int = 20) -> dict:
    """Fetch recent task records, optionally filtered by agent."""
    try:
        if agent:
            rows = execute_query(
                "SELECT * FROM tasks WHERE agent=? ORDER BY created_at DESC LIMIT ?",
                (agent, limit),
            )
        else:
            rows = execute_query(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        return _ok(rows)
    except Exception as e:
        return _err(str(e))


# ════════════════════════════════════════════════════════════
# VOLUNTEER TOOLS
# ════════════════════════════════════════════════════════════

def add_volunteer(name: str, email: str, phone: str = None, city: str = None,
                  skills: list = None, role: str = "field") -> dict:
    """Register a new volunteer."""
    try:
        execute_query(
            "INSERT INTO volunteers (name, email, phone, city, skills, role) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, phone, city, json.dumps(skills or []), role),
            fetch="none",
        )
        return _ok({"registered": name})
    except Exception as e:
        return _err(str(e))


def get_volunteer(email: str) -> dict:
    """Fetch a volunteer record by email."""
    try:
        row = execute_query(
            "SELECT * FROM volunteers WHERE email=?", (email,), fetch="one"
        )
        return _ok(row)
    except Exception as e:
        return _err(str(e))


def list_volunteers(status: str = "active", limit: int = 50) -> dict:
    """List volunteers filtered by status."""
    try:
        rows = execute_query(
            "SELECT id, name, email, role, status, hours_logged FROM volunteers "
            "WHERE status=? ORDER BY name LIMIT ?",
            (status, limit),
        )
        return _ok(rows)
    except Exception as e:
        return _err(str(e))


def update_volunteer_status(email: str, status: str) -> dict:
    """Update a volunteer's status (active / inactive / alumni)."""
    try:
        execute_query(
            "UPDATE volunteers SET status=? WHERE email=?", (status, email), fetch="none"
        )
        return _ok({"updated": email, "new_status": status})
    except Exception as e:
        return _err(str(e))


def log_volunteer_hours(email: str, hours: float) -> dict:
    """Increment volunteer's total logged hours."""
    try:
        execute_query(
            "UPDATE volunteers SET hours_logged = hours_logged + ? WHERE email=?",
            (hours, email), fetch="none",
        )
        return _ok({"hours_added": hours, "volunteer": email})
    except Exception as e:
        return _err(str(e))


def assign_volunteer_task(volunteer_id: int, task_name: str,
                          description: str = None, due_date: str = None) -> dict:
    """Assign a task to a volunteer."""
    try:
        execute_query(
            "INSERT INTO volunteer_assignments (volunteer_id, task_name, description, due_date) "
            "VALUES (?, ?, ?, ?)",
            (volunteer_id, task_name, description, due_date), fetch="none",
        )
        return _ok({"assigned": task_name, "volunteer_id": volunteer_id})
    except Exception as e:
        return _err(str(e))


def get_volunteer_assignments(volunteer_id: int) -> dict:
    """Get all assignments for a volunteer."""
    try:
        rows = execute_query(
            "SELECT * FROM volunteer_assignments WHERE volunteer_id=? ORDER BY assigned_at DESC",
            (volunteer_id,),
        )
        return _ok(rows)
    except Exception as e:
        return _err(str(e))


# ════════════════════════════════════════════════════════════
# INTERN TOOLS
# ════════════════════════════════════════════════════════════

def add_intern(name: str, email: str, college: str = None, department: str = None,
               program: str = None, duration_months: int = 1) -> dict:
    """Register a new intern application."""
    try:
        execute_query(
            "INSERT INTO interns (name, email, college, department, program, duration_months) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, college, department, program, duration_months),
            fetch="none",
        )
        return _ok({"registered": name})
    except Exception as e:
        return _err(str(e))


def get_intern(email: str) -> dict:
    """Fetch an intern record by email."""
    try:
        row = execute_query("SELECT * FROM interns WHERE email=?", (email,), fetch="one")
        return _ok(row)
    except Exception as e:
        return _err(str(e))


def list_interns(status: str = None, program: str = None, limit: int = 50) -> dict:
    """List interns with optional filters."""
    try:
        if status and program:
            rows = execute_query(
                "SELECT * FROM interns WHERE status=? AND program=? LIMIT ?",
                (status, program, limit),
            )
        elif status:
            rows = execute_query(
                "SELECT * FROM interns WHERE status=? LIMIT ?", (status, limit)
            )
        else:
            rows = execute_query("SELECT * FROM interns ORDER BY applied_at DESC LIMIT ?", (limit,))
        return _ok(rows)
    except Exception as e:
        return _err(str(e))


def update_intern_status(email: str, status: str, start_date: str = None,
                         end_date: str = None, mentor_id: int = None) -> dict:
    """Update intern status through the pipeline."""
    try:
        if start_date or end_date or mentor_id:
            execute_query(
                "UPDATE interns SET status=?, start_date=COALESCE(?,start_date), "
                "end_date=COALESCE(?,end_date), mentor_id=COALESCE(?,mentor_id) WHERE email=?",
                (status, start_date, end_date, mentor_id, email), fetch="none",
            )
        else:
            execute_query(
                "UPDATE interns SET status=? WHERE email=?", (status, email), fetch="none"
            )
        return _ok({"updated": email, "new_status": status})
    except Exception as e:
        return _err(str(e))


def add_intern_milestone(intern_id: int, week: int, title: str,
                         description: str, feedback: str = None, rating: int = None) -> dict:
    """Log a weekly milestone for an intern."""
    try:
        execute_query(
            "INSERT INTO intern_milestones (intern_id, week, title, description, feedback, rating) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (intern_id, week, title, description, feedback, rating), fetch="none",
        )
        return _ok({"milestone_added": f"Week {week} for intern {intern_id}"})
    except Exception as e:
        return _err(str(e))


def get_intern_milestones(intern_id: int) -> dict:
    """Retrieve all milestones for an intern."""
    try:
        rows = execute_query(
            "SELECT * FROM intern_milestones WHERE intern_id=? ORDER BY week",
            (intern_id,),
        )
        return _ok(rows)
    except Exception as e:
        return _err(str(e))


def mark_certificate_issued(intern_id: int, certificate_url: str = None) -> dict:
    """Mark certificate as issued for an intern."""
    try:
        execute_query(
            "UPDATE interns SET certificate_issued=1, certificate_url=? WHERE id=?",
            (certificate_url, intern_id), fetch="none",
        )
        return _ok({"certificate_issued": True, "intern_id": intern_id})
    except Exception as e:
        return _err(str(e))


# ════════════════════════════════════════════════════════════
# CONTENT TOOLS
# ════════════════════════════════════════════════════════════

def save_content(type: str, body: str, platform: str = None, title: str = None,
                 hashtags: str = None, created_by: str = "content_agent") -> dict:
    """Save a generated content item as draft."""
    try:
        execute_query(
            "INSERT INTO content_items (type, platform, title, body, hashtags, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (type, platform, title, body, hashtags, created_by), fetch="none",
        )
        row = execute_query("SELECT last_insert_rowid() AS id", fetch="one")
        return _ok({"content_id": row["id"], "status": "draft"})
    except Exception as e:
        return _err(str(e))


def get_content_items(type: str = None, status: str = None, limit: int = 20) -> dict:
    """Retrieve content items with optional filters."""
    try:
        if type and status:
            rows = execute_query(
                "SELECT * FROM content_items WHERE type=? AND status=? ORDER BY created_at DESC LIMIT ?",
                (type, status, limit),
            )
        elif status:
            rows = execute_query(
                "SELECT * FROM content_items WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            rows = execute_query(
                "SELECT * FROM content_items ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        return _ok(rows)
    except Exception as e:
        return _err(str(e))


def update_content_status(content_id: int, status: str) -> dict:
    """Update content item status (draft→review→approved→published)."""
    try:
        pub_at = datetime.utcnow().isoformat() if status == "published" else None
        execute_query(
            "UPDATE content_items SET status=?, published_at=COALESCE(?,published_at) WHERE id=?",
            (status, pub_at, content_id), fetch="none",
        )
        return _ok({"updated": content_id, "status": status})
    except Exception as e:
        return _err(str(e))


# ════════════════════════════════════════════════════════════
# RESOURCE / FINANCE TOOLS
# ════════════════════════════════════════════════════════════

def add_donor(name: str, email: str = None, phone: str = None, city: str = None,
              donor_type: str = "individual") -> dict:
    """Register or update a donor record."""
    try:
        existing = execute_query(
            "SELECT id FROM donors WHERE email=?", (email,), fetch="one"
        ) if email else None

        if existing:
            return _ok({"donor_id": existing["id"], "exists": True})

        execute_query(
            "INSERT INTO donors (name, email, phone, city, donor_type) VALUES (?, ?, ?, ?, ?)",
            (name, email, phone, city, donor_type), fetch="none",
        )
        row = execute_query("SELECT last_insert_rowid() AS id", fetch="one")
        return _ok({"donor_id": row["id"], "created": True})
    except Exception as e:
        return _err(str(e))


def add_fund(source: str, category: str, amount: float, currency: str = "INR",
             received_at: str = None, donor_id: int = None,
             reference_no: str = None, notes: str = None) -> dict:
    """Log an incoming fund entry."""
    try:
        execute_query(
            "INSERT INTO funds (donor_id, source, category, amount, currency, "
            "received_at, reference_no, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (donor_id, source, category, amount, currency,
             received_at or datetime.utcnow().date().isoformat(),
             reference_no, notes),
            fetch="none",
        )
        # Update donor total
        if donor_id:
            execute_query(
                "UPDATE donors SET total_donated=total_donated+?, last_donation_date=date('now') "
                "WHERE id=?",
                (amount, donor_id), fetch="none",
            )
        return _ok({"fund_logged": amount, "category": category})
    except Exception as e:
        return _err(str(e))


def add_expenditure(category: str, description: str, amount: float,
                    currency: str = "INR", approved_by: str = None,
                    vendor: str = None, receipt_url: str = None) -> dict:
    """Log an expenditure."""
    try:
        execute_query(
            "INSERT INTO expenditures (category, description, amount, currency, "
            "approved_by, vendor, receipt_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (category, description, amount, currency, approved_by, vendor, receipt_url),
            fetch="none",
        )
        return _ok({"expenditure_logged": amount, "category": category})
    except Exception as e:
        return _err(str(e))


def get_budget_utilization(category: str = None) -> dict:
    """
    Return fund inflow vs expenditure for each category (or a specific one).
    """
    try:
        if category:
            funds_row = execute_query(
                "SELECT SUM(amount) AS total FROM funds WHERE category=?", (category,), fetch="one"
            )
            exp_row = execute_query(
                "SELECT SUM(amount) AS total FROM expenditures WHERE category=?", (category,), fetch="one"
            )
            return _ok({
                "category": category,
                "funds_raised": funds_row["total"] or 0,
                "expenditure": exp_row["total"] or 0,
                "utilization_ratio": round(
                    (exp_row["total"] or 0) / max(funds_row["total"] or 1, 1), 3
                ),
            })
        else:
            rows = execute_query(
                "SELECT category, SUM(amount) AS total FROM funds GROUP BY category"
            )
            exp_rows = execute_query(
                "SELECT category, SUM(amount) AS total FROM expenditures GROUP BY category"
            )
            exp_map = {r["category"]: r["total"] for r in exp_rows}
            result = []
            for r in rows:
                cat = r["category"]
                income = r["total"] or 0
                spent = exp_map.get(cat, 0) or 0
                result.append({
                    "category": cat,
                    "funds_raised": income,
                    "expenditure": spent,
                    "utilization_ratio": round(spent / max(income, 1), 3),
                })
            return _ok(result)
    except Exception as e:
        return _err(str(e))


# ════════════════════════════════════════════════════════════
# ANALYTICS SNAPSHOT TOOLS
# ════════════════════════════════════════════════════════════

def save_snapshot(metric_key: str, metric_value: float,
                  dimensions: dict = None) -> dict:
    """Persist a computed KPI snapshot."""
    try:
        execute_query(
            "INSERT INTO analytics_snapshots (metric_key, metric_value, dimensions) "
            "VALUES (?, ?, ?)",
            (metric_key, metric_value, json.dumps(dimensions or {})), fetch="none",
        )
        return _ok({"snapshot_saved": metric_key})
    except Exception as e:
        return _err(str(e))


def get_snapshots(metric_key: str = None, limit: int = 30) -> dict:
    """Retrieve recent analytics snapshots."""
    try:
        if metric_key:
            rows = execute_query(
                "SELECT * FROM analytics_snapshots WHERE metric_key=? "
                "ORDER BY snapshot_date DESC LIMIT ?",
                (metric_key, limit),
            )
        else:
            rows = execute_query(
                "SELECT * FROM analytics_snapshots ORDER BY computed_at DESC LIMIT ?",
                (limit,),
            )
        return _ok(rows)
    except Exception as e:
        return _err(str(e))


def compute_kpis() -> dict:
    """
    Compute all standard KPIs and return as a dict.
    Also persists each metric as a snapshot.
    """
    try:
        kpis = {}

        # Active volunteers
        row = execute_query(
            "SELECT COUNT(*) AS c FROM volunteers WHERE status='active'", fetch="one"
        )
        kpis["active_volunteers"] = row["c"]

        # Total interns
        row = execute_query("SELECT COUNT(*) AS c FROM interns", fetch="one")
        kpis["total_interns"] = row["c"]

        # Active interns
        row = execute_query("SELECT COUNT(*) AS c FROM interns WHERE status='active'", fetch="one")
        kpis["active_interns"] = row["c"]

        # Completed interns
        row = execute_query("SELECT COUNT(*) AS c FROM interns WHERE status='completed'", fetch="one")
        kpis["completed_interns"] = row["c"]

        # Total funds raised (INR)
        row = execute_query(
            "SELECT COALESCE(SUM(amount),0) AS t FROM funds WHERE currency='INR'", fetch="one"
        )
        kpis["total_funds_raised"] = row["t"]

        # Total expenditure (INR)
        row = execute_query(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenditures WHERE currency='INR'", fetch="one"
        )
        kpis["total_expenditure"] = row["t"]

        # Content published this month
        row = execute_query(
            "SELECT COUNT(*) AS c FROM content_items WHERE status='published' "
            "AND strftime('%Y-%m', published_at)=strftime('%Y-%m','now')",
            fetch="one",
        )
        kpis["content_published"] = row["c"]

        # Open tasks
        row = execute_query(
            "SELECT COUNT(*) AS c FROM tasks WHERE status IN ('pending','in_progress')", fetch="one"
        )
        kpis["open_tasks"] = row["c"]

        # Total volunteer hours
        row = execute_query(
            "SELECT COALESCE(SUM(hours_logged),0) AS t FROM volunteers WHERE status='active'",
            fetch="one",
        )
        kpis["volunteer_hours_total"] = row["t"]

        # Persist snapshots
        for key, value in kpis.items():
            save_snapshot(key, float(value))

        return _ok(kpis)
    except Exception as e:
        return _err(str(e))
