"""
tests/test_tools.py — NayePankh AI Workforce
=============================================
Tests for all db_tools functions using an in-memory SQLite database.
"""
import json
import pytest
import sys
import os

# Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Patch DB path to in-memory before importing tools
import memory.db as db_module
from pathlib import Path

# Use a temporary file-backed DB for tests
import tempfile

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Redirect DB to a temp file for each test."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "_DB_PATH", test_db)
    # Clear thread-local connection
    if hasattr(db_module._local, "conn"):
        db_module._local.conn = None
    db_module.init_db(test_db)
    yield test_db
    db_module.close_connection()


# ── Import tools after patching ──────────────────────────────
from tools.db_tools import (
    add_volunteer, get_volunteer, list_volunteers,
    update_volunteer_status, log_volunteer_hours,
    add_intern, get_intern, list_interns, update_intern_status,
    add_intern_milestone, get_intern_milestones,
    save_content, get_content_items,
    add_donor, add_fund, add_expenditure, get_budget_utilization,
    compute_kpis, create_task_record, update_task_record,
)


class TestVolunteerTools:
    def test_add_and_get_volunteer(self):
        res = add_volunteer("Priya Sharma", "priya@test.com", role="field")
        assert res["success"] is True

        res2 = get_volunteer("priya@test.com")
        assert res2["success"] is True
        assert res2["data"]["name"] == "Priya Sharma"
        assert res2["data"]["status"] == "active"

    def test_list_volunteers(self):
        add_volunteer("Alice", "alice@test.com")
        add_volunteer("Bob",   "bob@test.com")
        res = list_volunteers(status="active")
        assert res["success"] is True
        assert len(res["data"]) == 2

    def test_update_volunteer_status(self):
        add_volunteer("Charlie", "charlie@test.com")
        res = update_volunteer_status("charlie@test.com", "inactive")
        assert res["success"] is True
        vol = get_volunteer("charlie@test.com")
        assert vol["data"]["status"] == "inactive"

    def test_log_volunteer_hours(self):
        add_volunteer("Dave", "dave@test.com")
        log_volunteer_hours("dave@test.com", 5.5)
        log_volunteer_hours("dave@test.com", 2.0)
        vol = get_volunteer("dave@test.com")
        assert abs(vol["data"]["hours_logged"] - 7.5) < 0.01

    def test_duplicate_email_fails(self):
        add_volunteer("Eve", "eve@test.com")
        res = add_volunteer("Eve2", "eve@test.com")  # duplicate email
        assert res["success"] is False


class TestInternTools:
    def test_add_and_get_intern(self):
        res = add_intern("Rahul Kumar", "rahul@test.com",
                         college="IIT Delhi", program="Summer 2025")
        assert res["success"] is True

        res2 = get_intern("rahul@test.com")
        assert res2["success"] is True
        assert res2["data"]["status"] == "applied"

    def test_status_transition(self):
        add_intern("Sneha", "sneha@test.com")
        res = update_intern_status("sneha@test.com", "accepted", start_date="2025-06-01")
        assert res["success"] is True
        intern = get_intern("sneha@test.com")
        assert intern["data"]["status"] == "accepted"

    def test_milestone_logging(self):
        add_intern("Arjun", "arjun@test.com")
        intern = get_intern("arjun@test.com")
        intern_id = intern["data"]["id"]
        res = add_intern_milestone(intern_id, week=1, title="Week 1",
                                   description="Orientation completed", rating=4)
        assert res["success"] is True

        milestones = get_intern_milestones(intern_id)
        assert milestones["success"] is True
        assert len(milestones["data"]) == 1
        assert milestones["data"][0]["rating"] == 4

    def test_list_by_status(self):
        add_intern("I1", "i1@test.com")
        add_intern("I2", "i2@test.com")
        update_intern_status("i1@test.com", "active")
        res = list_interns(status="active")
        assert res["success"] is True
        assert len(res["data"]) == 1


class TestContentTools:
    def test_save_and_retrieve_content(self):
        res = save_content("post", "Test post body", platform="instagram",
                           title="Test", hashtags="#NayePankh")
        assert res["success"] is True
        assert res["data"]["status"] == "draft"

        items = get_content_items(type="post")
        assert items["success"] is True
        assert len(items["data"]) == 1


class TestResourceTools:
    def test_add_fund_and_expenditure(self):
        donor_res = add_donor("Ratan Tata", "ratan@tata.com")
        assert donor_res["success"] is True

        fund_res = add_fund("Tata Trust", "education", 50000.0,
                            donor_id=donor_res["data"]["donor_id"])
        assert fund_res["success"] is True

        exp_res = add_expenditure("education", "Textbooks Q1", 10000.0)
        assert exp_res["success"] is True

    def test_budget_utilization(self):
        add_fund("Donor A", "health", 20000.0)
        add_expenditure("health", "Medical camp", 5000.0)

        res = get_budget_utilization("health")
        assert res["success"] is True
        assert res["data"]["funds_raised"] == 20000.0
        assert res["data"]["expenditure"] == 5000.0
        assert abs(res["data"]["utilization_ratio"] - 0.25) < 0.01


class TestKPITools:
    def test_compute_kpis(self):
        add_volunteer("V1", "v1@test.com")
        add_volunteer("V2", "v2@test.com")
        add_intern("I1", "in1@test.com")
        update_intern_status("in1@test.com", "completed")
        add_fund("Donor", "education", 10000.0)

        res = compute_kpis()
        assert res["success"] is True
        kpis = res["data"]
        assert kpis["active_volunteers"] == 2
        assert kpis["completed_interns"] == 1
        assert kpis["total_funds_raised"] == 10000.0


class TestTaskTools:
    def test_create_and_update_task(self):
        res = create_task_record("volunteer_agent", "onboard", {"name": "Test"})
        assert res["success"] is True
        task_id = res["data"]["task_id"]

        update_res = update_task_record(task_id, "done", {"result": "ok"})
        assert update_res["success"] is True
