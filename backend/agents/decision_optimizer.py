
from typing import Literal
from pydantic import BaseModel


class DecisionInput(BaseModel):
    equipment_id: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    operational_impact: str
    virtual_status: Literal["OPERATIONAL", "WARNING", "CRITICAL"]


class DecisionOption(BaseModel):
    option_name: str
    operational_risk: str
    production_impact: str
    estimated_downtime: str
    required_resources: list[str]


class DecisionResult(BaseModel):
    equipment_id: str
    options: list[DecisionOption]
    recommended_option: str
    recommendation_reason: str
    human_approval_required: bool


def optimize_decision(data: DecisionInput) -> DecisionResult:

    options = [
        DecisionOption(
            option_name="Immediate Maintenance",
            operational_risk="LOW after successful intervention",
            production_impact="Temporary production interruption",
            estimated_downtime="High",
            required_resources=[
                "Maintenance team",
                "Technical inspection",
                "Replacement parts if needed"
            ]
        ),
        DecisionOption(
            option_name="Scheduled Maintenance",
            operational_risk="Potential risk until intervention",
            production_impact="Planned production interruption",
            estimated_downtime="Medium",
            required_resources=[
                "Maintenance team",
                "Maintenance planning"
            ]
        ),
        DecisionOption(
            option_name="Continued Monitoring",
            operational_risk="Risk may increase if anomaly persists",
            production_impact="Possible unexpected interruption",
            estimated_downtime="Uncertain",
            required_resources=[
                "Monitoring system",
                "Technical supervision"
            ]
        )
    ]

    if data.risk_level == "CRITICAL":
        recommended = "Immediate Maintenance"
        reason = (
            "Critical risk detected. Immediate human assessment "
            "and maintenance planning are recommended."
        )

    elif data.risk_level in ["HIGH", "MEDIUM"]:
        recommended = "Scheduled Maintenance"
        reason = (
            "The detected risk requires a planned technical "
            "intervention and continued monitoring."
        )

    else:
        recommended = "Continued Monitoring"
        reason = (
            "No critical risk detected. Continue monitoring "
            "and review equipment condition."
        )

    return DecisionResult(
        equipment_id=data.equipment_id,
        options=options,
        recommended_option=recommended,
        recommendation_reason=reason,
        human_approval_required=recommended != "Continued Monitoring"
    )
