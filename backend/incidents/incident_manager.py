
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select

from backend.database.database import SyncSessionLocal
from backend.database.models import IncidentModel


class IncidentInput(BaseModel):
    equipment_id: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    anomalies: list[str]
    possible_causes: list[str]
    operational_impact: str
    recommended_action: str


class Incident(BaseModel):
    incident_id: str
    equipment_id: str
    severity: Literal["HIGH", "CRITICAL"]
    title: str
    description: str
    possible_causes: list[str]
    recommended_action: str
    status: Literal[
        "OPEN",
        "AWAITING_APPROVAL",
        "APPROVED",
        "REJECTED",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    ]
    human_approval_required: bool
    created_at: str


def _to_incident(row: IncidentModel) -> Incident:
    return Incident(
        incident_id=row.incident_id,
        equipment_id=row.equipment_id,
        severity=row.severity,
        title=row.title,
        description=row.description,
        possible_causes=row.possible_causes,
        recommended_action=row.recommended_action,
        status=row.status,
        human_approval_required=row.human_approval_required,
        created_at=row.created_at.isoformat()
    )


def create_incident(data: IncidentInput) -> Incident | None:

    if data.risk_level not in ["HIGH", "CRITICAL"]:
        return None

    incident_id = f"INC-{uuid4().hex[:8].upper()}"

    description = (
        f"Anomalies detected: {', '.join(data.anomalies)}. "
        f"Operational impact: {data.operational_impact}"
    )

    with SyncSessionLocal() as session:
        row = IncidentModel(
            incident_id=incident_id,
            equipment_id=data.equipment_id,
            severity=data.risk_level,
            title=f"{data.risk_level} RISK - Equipment {data.equipment_id}",
            description=description,
            possible_causes=data.possible_causes,
            recommended_action=data.recommended_action,
            status="AWAITING_APPROVAL",
            human_approval_required=True,
            created_at=datetime.now(timezone.utc)
        )

        session.add(row)
        session.commit()
        session.refresh(row)

        return _to_incident(row)


def get_incident(incident_id: str) -> Incident | None:

    with SyncSessionLocal() as session:
        row = session.get(IncidentModel, incident_id)

        if row is None:
            return None

        return _to_incident(row)


def list_incidents() -> list[Incident]:

    with SyncSessionLocal() as session:
        rows = session.scalars(
            select(IncidentModel).order_by(
                IncidentModel.created_at.desc()
            )
        ).all()

        return [_to_incident(row) for row in rows]


def update_incident_status(
    incident_id: str,
    new_status: Literal[
        "APPROVED",
        "REJECTED",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    ]
) -> Incident:

    allowed_transitions = {
        "AWAITING_APPROVAL": ["APPROVED", "REJECTED"],
        "APPROVED": ["IN_PROGRESS"],
        "IN_PROGRESS": ["RESOLVED"],
        "RESOLVED": ["CLOSED"],
        "REJECTED": [],
        "CLOSED": []
    }

    with SyncSessionLocal() as session:
        row = session.get(IncidentModel, incident_id)

        if row is None:
            raise ValueError("Incident not found")

        if new_status not in allowed_transitions.get(row.status, []):
            raise ValueError(
                f"Invalid transition: {row.status} -> {new_status}"
            )

        row.status = new_status

        session.commit()
        session.refresh(row)

        return _to_incident(row)
