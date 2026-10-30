
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select

from backend.database.database import SyncSessionLocal
from backend.database.models import IncidentModel, ApprovalModel


class ApprovalInput(BaseModel):
    incident_id: str
    reviewer: str
    decision: Literal["APPROVE", "REJECT"]
    comment: str = ""


class ApprovalRecord(BaseModel):
    approval_id: str
    incident_id: str
    reviewer: str
    decision: Literal["APPROVE", "REJECT"]
    previous_status: str
    new_status: str
    comment: str
    timestamp: str


def review_incident(data: ApprovalInput) -> ApprovalRecord:

    if not data.reviewer.strip():
        raise ValueError("Reviewer name is required")

    new_status = (
        "APPROVED"
        if data.decision == "APPROVE"
        else "REJECTED"
    )

    with SyncSessionLocal() as session:

        incident = session.get(
            IncidentModel,
            data.incident_id
        )

        if incident is None:
            raise ValueError("Incident not found")

        if incident.status != "AWAITING_APPROVAL":
            raise ValueError(
                f"Incident cannot be reviewed from status: {incident.status}"
            )

        previous_status = incident.status

        approval = ApprovalModel(
            approval_id=f"APR-{uuid4().hex[:8].upper()}",
            incident_id=data.incident_id,
            reviewer=data.reviewer,
            decision=data.decision,
            previous_status=previous_status,
            new_status=new_status,
            comment=data.comment,
            timestamp=datetime.now(timezone.utc)
        )

        # Update incident and save approval in one transaction
        incident.status = new_status
        session.add(approval)
        session.commit()
        session.refresh(approval)

        return ApprovalRecord(
            approval_id=approval.approval_id,
            incident_id=approval.incident_id,
            reviewer=approval.reviewer,
            decision=approval.decision,
            previous_status=approval.previous_status,
            new_status=approval.new_status,
            comment=approval.comment,
            timestamp=approval.timestamp.isoformat()
        )


def get_approval_history(
    incident_id: str
) -> list[ApprovalRecord]:

    with SyncSessionLocal() as session:

        rows = session.scalars(
            select(ApprovalModel)
            .where(ApprovalModel.incident_id == incident_id)
            .order_by(ApprovalModel.timestamp.desc())
        ).all()

        return [
            ApprovalRecord(
                approval_id=row.approval_id,
                incident_id=row.incident_id,
                reviewer=row.reviewer,
                decision=row.decision,
                previous_status=row.previous_status,
                new_status=row.new_status,
                comment=row.comment,
                timestamp=row.timestamp.isoformat()
            )
            for row in rows
        ]
