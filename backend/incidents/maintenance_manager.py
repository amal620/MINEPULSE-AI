
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select

from backend.database.database import SyncSessionLocal
from backend.database.models import IncidentModel, MaintenanceModel
from backend.incidents.incident_manager import (
    get_incident,
    update_incident_status,
)


class MaintenanceInput(BaseModel):
    incident_id: str
    technician: str
    intervention_description: str


class MaintenanceRecord(BaseModel):
    maintenance_id: str
    incident_id: str
    equipment_id: str
    technician: str
    intervention_description: str
    status: Literal["IN_PROGRESS", "COMPLETED"]
    started_at: str
    completed_at: str | None = None


def _to_maintenance(row: MaintenanceModel) -> MaintenanceRecord:
    return MaintenanceRecord(
        maintenance_id=row.maintenance_id,
        incident_id=row.incident_id,
        equipment_id=row.equipment_id,
        technician=row.technician,
        intervention_description=row.intervention_description,
        status=row.status,
        started_at=row.started_at.isoformat(),
        completed_at=(
            row.completed_at.isoformat()
            if row.completed_at else None
        )
    )


def start_maintenance(data: MaintenanceInput) -> MaintenanceRecord:

    if not data.technician.strip():
        raise ValueError("Technician name is required")

    if not data.intervention_description.strip():
        raise ValueError("Intervention description is required")

    with SyncSessionLocal() as session:
        incident = session.get(IncidentModel, data.incident_id)

        if incident is None:
            raise ValueError("Incident not found")

        if incident.status != "APPROVED":
            raise ValueError("Maintenance requires an approved incident")

        record = MaintenanceModel(
            maintenance_id=f"MAINT-{uuid4().hex[:8].upper()}",
            incident_id=data.incident_id,
            equipment_id=incident.equipment_id,
            technician=data.technician,
            intervention_description=data.intervention_description,
            status="IN_PROGRESS",
            started_at=datetime.now(timezone.utc)
        )

        incident.status = "IN_PROGRESS"

        session.add(record)
        session.commit()
        session.refresh(record)

        return _to_maintenance(record)


def complete_maintenance(maintenance_id: str) -> MaintenanceRecord:

    with SyncSessionLocal() as session:
        record = session.get(MaintenanceModel, maintenance_id)

        if record is None:
            raise ValueError("Maintenance record not found")

        if record.status != "IN_PROGRESS":
            raise ValueError("Maintenance is not in progress")

        record.status = "COMPLETED"
        record.completed_at = datetime.now(timezone.utc)

        session.commit()
        session.refresh(record)

        return _to_maintenance(record)


def verify_maintenance(
    maintenance_id: str,
    equipment_operational: bool
):

    with SyncSessionLocal() as session:
        record = session.get(MaintenanceModel, maintenance_id)

        if record is None:
            raise ValueError("Maintenance record not found")

        if record.status != "COMPLETED":
            raise ValueError(
                "Maintenance must be completed before verification"
            )

        incident = session.get(IncidentModel, record.incident_id)

        if incident is None:
            raise ValueError("Incident not found")

        if incident.status != "IN_PROGRESS":
            raise ValueError(
                f"Incident cannot be verified from status: {incident.status}"
            )

        if equipment_operational:
            incident.status = "RESOLVED"
            session.commit()

            return {
                "maintenance_id": maintenance_id,
                "incident_id": record.incident_id,
                "verification_status": "PASSED",
                "incident_status": "RESOLVED",
                "message": (
                    "Equipment operational status confirmed in simulation."
                )
            }

        return {
            "maintenance_id": maintenance_id,
            "incident_id": record.incident_id,
            "verification_status": "FAILED",
            "incident_status": "IN_PROGRESS",
            "message": (
                "The simulated equipment condition still requires attention."
            )
        }


def close_maintenance_incident(incident_id: str):

    incident = get_incident(incident_id)

    if incident is None:
        raise ValueError("Incident not found")

    if incident.status != "RESOLVED":
        raise ValueError("Only resolved incidents can be closed")

    return update_incident_status(incident_id, "CLOSED")
