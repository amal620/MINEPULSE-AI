
from pydantic import BaseModel
from typing import Literal


class RiskInput(BaseModel):
    equipment_id: str
    sensor_status: Literal["NORMAL", "WARNING", "CRITICAL"]
    anomalies: list[str]
    possible_causes: list[str]
    confidence_score: int


class RiskResult(BaseModel):
    equipment_id: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    operational_impact: str
    recommended_response: str
    human_approval_required: bool
    explanation: str


def assess_risk(data: RiskInput) -> RiskResult:

    if data.sensor_status == "CRITICAL":
        risk_level = "CRITICAL"
        impact = "Potential equipment damage and production interruption."
        response = "Escalate the incident and request an immediate human assessment."
        approval = True

    elif data.sensor_status == "WARNING":
        risk_level = "MEDIUM"
        impact = "Potential reduction in equipment performance."
        response = "Schedule a technical inspection and increase monitoring."
        approval = True

    elif data.anomalies:
        risk_level = "LOW"
        impact = "Minor anomaly requiring observation."
        response = "Continue monitoring and review sensor measurements."
        approval = False

    else:
        risk_level = "LOW"
        impact = "No operational impact identified from available data."
        response = "Continue normal monitoring."
        approval = False

    explanation = (
        f"Risk assessment for {data.equipment_id} "
        f"based on sensor status {data.sensor_status} "
        f"and {len(data.anomalies)} detected anomalies."
    )

    return RiskResult(
        equipment_id=data.equipment_id,
        risk_level=risk_level,
        operational_impact=impact,
        recommended_response=response,
        human_approval_required=approval,
        explanation=explanation
    )
