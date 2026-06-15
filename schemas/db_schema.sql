-- ============================================================
-- NayePankh AI Workforce — SQLite Database Schema
-- ============================================================
-- Run automatically by memory/db.py on first boot.
-- Tables: sessions, messages, tasks, volunteers,
--         volunteer_assignments, interns, intern_milestones,
--         content_items, funds, expenditures, donors,
--         analytics_snapshots
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ────────────────────────────────────────────────
-- 1. Sessions — Conversation context per user
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,           -- UUID v4
    agent       TEXT NOT NULL DEFAULT 'supervisor',
    user_id     TEXT NOT NULL DEFAULT 'default',
    title       TEXT,                       -- auto-generated short title
    created_at  DATETIME DEFAULT (datetime('now')),
    updated_at  DATETIME DEFAULT (datetime('now'))
);

-- ────────────────────────────────────────────────
-- 2. Messages — Full conversation history
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
    content     TEXT NOT NULL,
    agent       TEXT,                       -- which agent produced this message
    timestamp   DATETIME DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);

-- ────────────────────────────────────────────────
-- 3. Tasks — All agent task executions
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT REFERENCES sessions(id) ON DELETE SET NULL,
    agent        TEXT NOT NULL,
    task_type    TEXT NOT NULL,             -- e.g. "onboard_volunteer", "generate_post"
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK(status IN ('pending', 'in_progress', 'done', 'failed')),
    payload      TEXT,                      -- JSON input params
    result       TEXT,                      -- JSON output
    error_msg    TEXT,
    created_at   DATETIME DEFAULT (datetime('now')),
    completed_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_tasks_agent   ON tasks(agent);
CREATE INDEX IF NOT EXISTS idx_tasks_status  ON tasks(status);

-- ────────────────────────────────────────────────
-- 4. Volunteers
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS volunteers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    email        TEXT UNIQUE NOT NULL,
    phone        TEXT,
    city         TEXT,
    skills       TEXT,                      -- JSON array e.g. ["design","outreach"]
    role         TEXT,                      -- coordinator | field | mentor | admin
    status       TEXT NOT NULL DEFAULT 'active'
                 CHECK(status IN ('active', 'inactive', 'alumni')),
    joined_at    DATE DEFAULT (date('now')),
    hours_logged REAL NOT NULL DEFAULT 0.0,
    notes        TEXT
);
CREATE INDEX IF NOT EXISTS idx_volunteers_status ON volunteers(status);
CREATE INDEX IF NOT EXISTS idx_volunteers_email  ON volunteers(email);

-- ────────────────────────────────────────────────
-- 5. Volunteer Assignments
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS volunteer_assignments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    volunteer_id  INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
    task_name     TEXT NOT NULL,
    description   TEXT,
    assigned_at   DATETIME DEFAULT (datetime('now')),
    due_date      DATE,
    completed_at  DATETIME,
    hours_spent   REAL DEFAULT 0.0,
    feedback      TEXT,
    status        TEXT NOT NULL DEFAULT 'assigned'
                  CHECK(status IN ('assigned', 'in_progress', 'completed', 'cancelled'))
);
CREATE INDEX IF NOT EXISTS idx_va_volunteer ON volunteer_assignments(volunteer_id);

-- ────────────────────────────────────────────────
-- 6. Interns
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS interns (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL,
    email                TEXT UNIQUE NOT NULL,
    phone                TEXT,
    college              TEXT,
    department           TEXT,
    program              TEXT,              -- e.g. "Summer 2025", "6-Month 2026"
    duration_months      INTEGER DEFAULT 1,
    status               TEXT NOT NULL DEFAULT 'applied'
                         CHECK(status IN ('applied','reviewing','accepted',
                                          'active','completed','rejected')),
    start_date           DATE,
    end_date             DATE,
    mentor_id            INTEGER REFERENCES volunteers(id) ON DELETE SET NULL,
    project_assigned     TEXT,
    certificate_issued   INTEGER NOT NULL DEFAULT 0,  -- 0=No, 1=Yes
    certificate_url      TEXT,
    applied_at           DATETIME DEFAULT (datetime('now')),
    notes                TEXT
);
CREATE INDEX IF NOT EXISTS idx_interns_status  ON interns(status);
CREATE INDEX IF NOT EXISTS idx_interns_program ON interns(program);

-- ────────────────────────────────────────────────
-- 7. Intern Milestones
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS intern_milestones (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    intern_id    INTEGER NOT NULL REFERENCES interns(id) ON DELETE CASCADE,
    week         INTEGER NOT NULL,
    title        TEXT,
    description  TEXT,
    feedback     TEXT,
    rating       INTEGER CHECK(rating BETWEEN 1 AND 5),
    logged_at    DATETIME DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_milestones_intern ON intern_milestones(intern_id);

-- ────────────────────────────────────────────────
-- 8. Content Items
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS content_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type         TEXT NOT NULL             -- post | newsletter | press_release | campaign | blog
                 CHECK(type IN ('post','newsletter','press_release','campaign','blog','other')),
    platform     TEXT,                     -- instagram | linkedin | twitter | email | web
    title        TEXT,
    body         TEXT NOT NULL,
    hashtags     TEXT,                     -- comma-separated
    status       TEXT NOT NULL DEFAULT 'draft'
                 CHECK(status IN ('draft','review','approved','published','archived')),
    created_by   TEXT DEFAULT 'content_agent',
    created_at   DATETIME DEFAULT (datetime('now')),
    published_at DATETIME,
    notes        TEXT
);
CREATE INDEX IF NOT EXISTS idx_content_type   ON content_items(type);
CREATE INDEX IF NOT EXISTS idx_content_status ON content_items(status);

-- ────────────────────────────────────────────────
-- 9. Donors
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS donors (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL,
    email                TEXT,
    phone                TEXT,
    city                 TEXT,
    donor_type           TEXT DEFAULT 'individual'
                         CHECK(donor_type IN ('individual','corporate','grant','govt')),
    total_donated        REAL NOT NULL DEFAULT 0.0,
    currency             TEXT NOT NULL DEFAULT 'INR',
    first_donation_date  DATE,
    last_donation_date   DATE,
    is_recurring         INTEGER NOT NULL DEFAULT 0,  -- 0=No, 1=Yes
    notes                TEXT
);
CREATE INDEX IF NOT EXISTS idx_donors_email ON donors(email);

-- ────────────────────────────────────────────────
-- 10. Funds (Income / Donations received)
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS funds (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id     INTEGER REFERENCES donors(id) ON DELETE SET NULL,
    source       TEXT NOT NULL,            -- donor name or grant name
    category     TEXT NOT NULL             -- education|health|operations|events|other
                 CHECK(category IN ('education','health','operations','events','emergency','other')),
    amount       REAL NOT NULL CHECK(amount > 0),
    currency     TEXT NOT NULL DEFAULT 'INR',
    received_at  DATE DEFAULT (date('now')),
    reference_no TEXT,                     -- bank transaction / cheque number
    notes        TEXT
);
CREATE INDEX IF NOT EXISTS idx_funds_category ON funds(category);
CREATE INDEX IF NOT EXISTS idx_funds_date     ON funds(received_at);

-- ────────────────────────────────────────────────
-- 11. Expenditures
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenditures (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     TEXT NOT NULL
                 CHECK(category IN ('education','health','operations','events','emergency','other')),
    description  TEXT NOT NULL,
    amount       REAL NOT NULL CHECK(amount > 0),
    currency     TEXT NOT NULL DEFAULT 'INR',
    approved_by  TEXT,
    vendor       TEXT,
    spent_at     DATE DEFAULT (date('now')),
    receipt_url  TEXT,
    notes        TEXT
);
CREATE INDEX IF NOT EXISTS idx_expenditures_category ON expenditures(category);
CREATE INDEX IF NOT EXISTS idx_expenditures_date     ON expenditures(spent_at);

-- ────────────────────────────────────────────────
-- 12. Analytics Snapshots (pre-computed KPIs)
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date  DATE NOT NULL DEFAULT (date('now')),
    metric_key     TEXT NOT NULL,          -- e.g. "active_volunteers", "funds_raised_INR"
    metric_value   REAL NOT NULL,
    dimensions     TEXT,                   -- JSON e.g. {"month":"June","program":"Summer 2025"}
    computed_at    DATETIME DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_snapshots_metric ON analytics_snapshots(metric_key, snapshot_date);

-- ────────────────────────────────────────────────
-- 13. Workflows (Parent record for an orchestration run)
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workflows (
    id            TEXT PRIMARY KEY,           -- UUID
    session_id    TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,              -- e.g., "Campaign Builder"
    original_prompt TEXT NOT NULL,
    status        TEXT DEFAULT 'planning'     -- planning | running | completed | failed
                  CHECK(status IN ('planning', 'running', 'completed', 'failed')),
    final_result  TEXT,                       -- Aggregated response from Supervisor
    created_at    DATETIME DEFAULT (datetime('now')),
    completed_at  DATETIME
);
CREATE INDEX IF NOT EXISTS idx_workflows_session ON workflows(session_id);

-- ────────────────────────────────────────────────
-- 14. Workflow Steps (Individual agent execution records)
-- ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workflow_steps (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id   TEXT REFERENCES workflows(id) ON DELETE CASCADE,
    agent         TEXT NOT NULL,              -- e.g., "content_agent"
    task_prompt   TEXT NOT NULL,              -- Specific instruction given to this agent
    status        TEXT DEFAULT 'pending'      -- pending | running | completed | failed
                  CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    result        TEXT,                       -- Output from the agent
    started_at    DATETIME,
    completed_at  DATETIME
);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow ON workflow_steps(workflow_id);

-- ============================================================
-- End of Schema
-- ============================================================

