# 🗺️ Hybrid Cloud Migration Planner

**A practical little atlas for moving workloads in sensible waves.** This portfolio prototype turns a workload inventory into a dependency-aware migration plan, maps common workload types to Azure landing targets, and stores planning runs in SQLite.

It focuses on sequencing and visibility. It does not provision resources or claim to estimate migration cost.

## ✨ What it demonstrates

- Input validation for workload inventories
- Dependency graph construction and cycle detection
- Topological wave planning with configurable wave size
- Azure target suggestions by workload type
- Risk flags for data sensitivity, unsupported targets, and missing recovery objectives
- Durable run history through SQLAlchemy and SQLite
- Exportable JSON plans and a simple rose-and-sky dashboard

## 🌷 Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> for the dashboard or <http://127.0.0.1:8000/docs> for the API. Submit `sample/inventory.json` as the body of `POST /plans`.

## 🧁 API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service status |
| `POST` | `/plans` | Build and persist a migration plan |
| `GET` | `/plans` | List recent planning runs |
| `GET` | `/plans/{plan_id}` | Retrieve a saved plan |

Example workload:

```json
{
  "id": "orders-api",
  "name": "Orders API",
  "type": "api",
  "environment": "production",
  "data_classification": "confidential",
  "rto_hours": 4,
  "rpo_hours": 1,
  "depends_on": ["orders-db"]
}
```

## 🪄 Planning model

```text
Inventory → validation → dependency graph → migration waves → Azure target hints → saved plan
```

Dependencies are interpreted as “this workload depends on these workloads,” so prerequisites are scheduled in earlier waves. Cycles are returned as actionable validation errors rather than silently producing an invalid sequence. High-sensitivity workloads and missing RTO/RPO values become explicit review flags.

## 🧭 Azure mapping

The mapping catalog in `app/planner.py` is intentionally small and editable. For example, a relational database maps to Azure SQL Database as a starting point. Final selection depends on compatibility, availability, identity, networking, and recovery requirements; the suggestion is not an architecture decision.

Set `DATABASE_URL` to a SQLAlchemy-compatible URL to use a different relational store. SQLite is the no-setup local default.

## 🎨 Visual notes

Warm cream, rose, and sky-blue accents make the migration map feel less like a spreadsheet marathon. The planner itself remains explicit about dependencies, assumptions, and open decisions.
