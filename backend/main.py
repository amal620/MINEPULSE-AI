from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from backend.database.database import Base, sync_engine, SyncSessionLocal
from backend.database import models  # noqa: F401 - register ORM tables
from backend.graph.sensor_graph import run_mining_graph
from backend.incidents.incident_manager import list_incidents, get_incident
from backend.incidents.approval_manager import ApprovalInput, review_incident, get_approval_history
from backend.incidents.maintenance_manager import (
    MaintenanceInput, start_maintenance, complete_maintenance,
    verify_maintenance, close_maintenance_incident,
)
from backend.monitoring.monitoring_agent import get_monitoring_report
from backend.database.models import (
    IncidentModel, ApprovalModel, MaintenanceModel, MonitoringEventModel
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=sync_engine)
    yield


app = FastAPI(
    title="MINEPULSE AI API",
    version="1.0.0",
    description="Mining operations decision-support prototype using LangGraph.",
    lifespan=lifespan,
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class AnalysisRequest(BaseModel):
    equipment_id: str = Field(default="C-02", min_length=2, max_length=100)
    temperature: float = Field(ge=-50, le=300)
    vibration: float = Field(ge=0, le=100)
    speed: float = Field(ge=0, le=100)
    simulation_mode: bool = True


class ApprovalRequest(BaseModel):
    reviewer: str = Field(min_length=2, max_length=150)
    decision: str
    comment: str = ""


class MaintenanceRequest(BaseModel):
    technician: str = Field(min_length=2, max_length=150)
    intervention_description: str = Field(min_length=3, max_length=2000)


class VerificationRequest(BaseModel):
    equipment_operational: bool


def as_error(exc: Exception):
    raise HTTPException(status_code=400, detail=str(exc))


@app.get("/", include_in_schema=False)
def home():
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not installed")
    return FileResponse(index)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MINEPULSE AI", "mode": "simulation"}


@app.post("/api/analyze")
def analyze(request: AnalysisRequest):
    try:
        payload = request.model_dump(exclude={"simulation_mode"})
        return run_mining_graph(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {exc}")


@app.get("/api/dashboard")
def dashboard():
    with SyncSessionLocal() as session:
        incident_count = session.scalar(select(func.count()).select_from(IncidentModel)) or 0
        open_count = session.scalar(
            select(func.count()).select_from(IncidentModel)
            .where(IncidentModel.status.notin_(["CLOSED", "REJECTED"]))
        ) or 0
        critical_count = session.scalar(
            select(func.count()).select_from(IncidentModel)
            .where(IncidentModel.severity == "CRITICAL")
        ) or 0
        approval_count = session.scalar(
            select(func.count()).select_from(ApprovalModel)
        ) or 0
        maintenance_count = session.scalar(
            select(func.count()).select_from(MaintenanceModel)
        ) or 0
        event_count = session.scalar(
            select(func.count()).select_from(MonitoringEventModel)
        ) or 0
    incidents = list_incidents()[:8]
    return {
        "kpis": {
            "total_incidents": incident_count,
            "active_incidents": open_count,
            "critical_incidents": critical_count,
            "approvals_recorded": approval_count,
            "maintenance_jobs": maintenance_count,
            "monitoring_events": event_count,
        },
        "incidents": [item.model_dump() for item in incidents],
    }


@app.get("/api/incidents")
def incidents():
    return [item.model_dump() for item in list_incidents()]


@app.get("/api/incidents/{incident_id}")
def incident_detail(incident_id: str):
    item = get_incident(incident_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {
        "incident": item.model_dump(),
        "approvals": [a.model_dump() for a in get_approval_history(incident_id)],
    }


@app.post("/api/incidents/{incident_id}/approval")
def approve_incident(incident_id: str, request: ApprovalRequest):
    try:
        result = review_incident(ApprovalInput(
            incident_id=incident_id,
            reviewer=request.reviewer,
            decision=request.decision,
            comment=request.comment,
        ))
        return result.model_dump()
    except ValueError as exc:
        as_error(exc)


@app.post("/api/incidents/{incident_id}/maintenance")
def begin_maintenance(incident_id: str, request: MaintenanceRequest):
    try:
        result = start_maintenance(MaintenanceInput(
            incident_id=incident_id,
            technician=request.technician,
            intervention_description=request.intervention_description,
        ))
        return result.model_dump()
    except ValueError as exc:
        as_error(exc)


@app.get("/api/incidents/{incident_id}/maintenance/latest")
def latest_maintenance(incident_id: str):
    with SyncSessionLocal() as session:
        row = session.scalars(
            select(MaintenanceModel)
            .where(MaintenanceModel.incident_id == incident_id)
            .order_by(MaintenanceModel.started_at.desc())
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Maintenance record not found")
        return {"maintenance_id": row.maintenance_id, "status": row.status}


@app.post("/api/maintenance/{maintenance_id}/complete")
def finish_maintenance(maintenance_id: str):
    try:
        return complete_maintenance(maintenance_id).model_dump()
    except ValueError as exc:
        as_error(exc)


@app.post("/api/maintenance/{maintenance_id}/verify")
def verify_job(maintenance_id: str, request: VerificationRequest):
    try:
        return verify_maintenance(maintenance_id, request.equipment_operational)
    except ValueError as exc:
        as_error(exc)


@app.post("/api/incidents/{incident_id}/close")
def close_incident(incident_id: str):
    try:
        return close_maintenance_incident(incident_id).model_dump()
    except ValueError as exc:
        as_error(exc)


@app.get("/api/monitoring/recent")
def recent_monitoring(limit: int = 8):
    limit = max(1, min(limit, 30))
    with SyncSessionLocal() as session:
        ids = session.execute(
            select(
                MonitoringEventModel.correlation_id,
                func.max(MonitoringEventModel.timestamp).label("last_seen")
            )
            .group_by(MonitoringEventModel.correlation_id)
            .order_by(func.max(MonitoringEventModel.timestamp).desc())
            .limit(limit)
        ).all()
    reports = []
    for correlation_id, _ in ids:
        try:
            reports.append(get_monitoring_report(correlation_id).model_dump())
        except ValueError:
            continue
    return reports


@app.get("/api/monitoring/{correlation_id}")
def monitoring_report(correlation_id: str):
    try:
        return get_monitoring_report(correlation_id).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/governance/agent-cards")
def agent_cards():
    cards_path = BASE_DIR / "agent_cards" / "agent_cards.json"
    if not cards_path.exists():
        return []
    import json
    return json.loads(cards_path.read_text(encoding="utf-8"))
