from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select

from backend.database.database import SyncSessionLocal, init_sync_db
from backend.database.models import MonitoringEventModel


class MonitoringEvent(BaseModel):
    correlation_id: str
    agent_name: str
    status: Literal["STARTED", "SUCCESS", "FAILED"]
    timestamp: str
    details: str = ""
    duration_seconds: float | None = None


class MonitoringReport(BaseModel):
    correlation_id: str
    total_events: int
    successful_agents: int
    failed_agents: int
    execution_status: Literal["SUCCESS", "FAILED"]
    events: list[MonitoringEvent]


def create_execution() -> str:
    return str(uuid4())


def record_agent_event(
    correlation_id: str,
    agent_name: str,
    status: Literal["STARTED", "SUCCESS", "FAILED"],
    details: str = "",
    duration_seconds: float | None = None
) -> MonitoringEvent:
    timestamp = datetime.now(timezone.utc)
    init_sync_db()
    with SyncSessionLocal() as session:
        event = MonitoringEventModel(
            correlation_id=correlation_id,
            agent_name=agent_name,
            status=status,
            timestamp=timestamp,
            details=details,
            duration_seconds=duration_seconds,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return MonitoringEvent(
            correlation_id=event.correlation_id,
            agent_name=event.agent_name,
            status=event.status,
            timestamp=event.timestamp.isoformat(),
            details=event.details,
            duration_seconds=event.duration_seconds,
        )


def get_monitoring_report(correlation_id: str) -> MonitoringReport:
    with SyncSessionLocal() as session:
        rows = session.scalars(
            select(MonitoringEventModel)
            .where(MonitoringEventModel.correlation_id == correlation_id)
            .order_by(MonitoringEventModel.timestamp.asc(), MonitoringEventModel.event_id.asc())
        ).all()
        if not rows:
            raise ValueError("Unknown Correlation ID")

        events = [
            MonitoringEvent(
                correlation_id=row.correlation_id,
                agent_name=row.agent_name,
                status=row.status,
                timestamp=row.timestamp.isoformat(),
                details=row.details,
                duration_seconds=row.duration_seconds,
            )
            for row in rows
        ]

    successful = sum(event.status == "SUCCESS" for event in events)
    failed = sum(event.status == "FAILED" for event in events)
    return MonitoringReport(
        correlation_id=correlation_id,
        total_events=len(events),
        successful_agents=successful,
        failed_agents=failed,
        execution_status="FAILED" if failed else "SUCCESS",
        events=events,
    )
