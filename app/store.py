from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class PlanRun(Base):
    __tablename__ = "plan_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    workload_count: Mapped[int] = mapped_column(Integer)
    wave_count: Mapped[int] = mapped_column(Integer)
    plan_json: Mapped[str] = mapped_column(Text)


database_url = os.getenv("DATABASE_URL", "sqlite:///./migration_plans.db")
engine = create_engine(database_url, connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {})
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)


def save_plan(plan: dict) -> dict:
    with Session.begin() as db:
        row = PlanRun(
            created_at=datetime.now(timezone.utc),
            workload_count=plan["summary"]["workload_count"],
            wave_count=plan["summary"]["wave_count"],
            plan_json=json.dumps(plan, sort_keys=True),
        )
        db.add(row)
        db.flush()
        return {"id": row.id, "created_at": row.created_at.isoformat(), "plan": plan}


def get_plan(plan_id: int) -> dict | None:
    with Session() as db:
        row = db.get(PlanRun, plan_id)
        if row is None:
            return None
        return {"id": row.id, "created_at": row.created_at.isoformat(), "plan": json.loads(row.plan_json)}


def list_plans(limit: int = 20) -> list[dict]:
    with Session() as db:
        rows = db.scalars(select(PlanRun).order_by(PlanRun.created_at.desc(), PlanRun.id.desc()).limit(limit)).all()
        return [{"id": row.id, "created_at": row.created_at.isoformat(), "workload_count": row.workload_count, "wave_count": row.wave_count} for row in rows]
