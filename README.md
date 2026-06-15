# NayePankh AI Workforce 🕊️

> **Multi-Agent NGO Operating System** — Powered by Agno + Ollama (qwen3:8b) + Streamlit

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/Ollama-qwen3:8b-green)](https://ollama.ai)

## 🌟 Overview

NayePankh AI Workforce is a production-ready multi-agent operating system for the NayePankh Foundation NGO. A **Supervisor Agent** intelligently routes natural language queries to 5 specialist agents:

| Agent | Domain |
|---|---|
| 🙋 Volunteer Agent | Registration, assignments, retention, hours tracking |
| 🎓 Internship Agent | Applications → milestones → certificate issuance |
| ✍️ Content Agent | Social posts, newsletters, campaigns, press releases |
| 📊 Analytics Agent | KPIs, trends, impact reports, budget alerts |
| 💰 Resource Agent | Funds, donations, expenditures, donor management |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- qwen3:8b model pulled

### 1. Pull the LLM
```bash
ollama pull qwen3:8b
```

### 2. Clone & Setup
```bash
git clone <repo-url>
cd NayePankh-AI-Workforce

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
copy .env .env.local   # Edit .env with your SMTP credentials if needed
```

### 4. Run the App
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 📁 Project Structure

```
NayePankh-AI-Workforce/
├── app.py                  # Streamlit entry point
├── config.py               # Global configuration
├── requirements.txt
├── .env                    # Environment variables (never commit!)
├── agents/                 # 6 Agno agents
│   ├── supervisor.py       # Router + Orchestrator
│   ├── volunteer_agent.py
│   ├── internship_agent.py
│   ├── content_agent.py
│   ├── analytics_agent.py
│   └── resource_agent.py
├── tools/                  # Agno tool functions
│   ├── db_tools.py         # All SQLite CRUD operations
│   ├── kb_tools.py         # JSON knowledge base search
│   ├── email_tools.py      # SMTP + email templates
│   └── file_tools.py       # CSV + PDF export
├── knowledge/              # Domain JSON knowledge bases
│   ├── volunteer_kb.json
│   ├── internship_kb.json
│   ├── content_kb.json
│   ├── analytics_kb.json
│   └── resource_kb.json
├── memory/
│   ├── db.py               # SQLite connection manager
│   └── nayepankh.db        # Auto-generated database
├── ui/
│   ├── components/         # Streamlit UI components
│   └── styles/custom.css   # Dark theme + animations
├── schemas/db_schema.sql   # 12-table SQLite DDL
└── tests/                  # Pytest test suite
```

## 💬 Example Queries

```
"Register a new volunteer: Priya Sharma, priya@example.com, skills: outreach"
"Show all active interns in the Summer 2025 program"
"Write an Instagram post about our 100th volunteer milestone"
"Generate the monthly impact report"
"Log a donation of ₹50,000 from Ratan Tata Foundation for education"
"What's our current budget utilization for operations?"
```

## 🗄️ Database

SQLite database with 12 tables auto-created on first boot:
`sessions · messages · tasks · volunteers · volunteer_assignments · interns · intern_milestones · content_items · donors · funds · expenditures · analytics_snapshots`

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen3:8b` | LLM model name |
| `DB_PATH` | `./memory/nayepankh.db` | SQLite file path |
| `APP_ENV` | `development` | `development` skips email sending |

## 🧪 Tests

```bash
pytest tests/ -v
```

## 📄 License

MIT © NayePankh Foundation 2025
