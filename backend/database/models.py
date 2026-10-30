
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class IncidentModel(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )
    equipment_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    possible_causes: Mapped[list] = mapped_column(
        JSON, nullable=False
    )
    recommended_action: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )
    human_approval_required: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class ApprovalModel(Base):
    __tablename__ = "approvals"

    approval_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.incident_id"),
        nullable=False,
        index=True,
    )
    reviewer: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    decision: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    previous_status: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    new_status: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    comment: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class MaintenanceModel(Base):
    __tablename__ = "maintenance_records"

    maintenance_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.incident_id"),
        nullable=False,
        index=True,
    )
    equipment_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    technician: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    intervention_description: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class MonitoringEventModel(Base):
    __tablename__ = "monitoring_events"

    event_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    correlation_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    details: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )


Index(
    "ix_monitoring_correlation_timestamp",
    MonitoringEventModel.correlation_id,
    MonitoringEventModel.timestamp,
)
