
from pydantic import BaseModel
from typing import Literal


class DigitalTwinInput(BaseModel):
    equipment_id: str
    sensor_status: Literal["NORMAL", "WARNING", "CRITICAL"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    anomalies: list[str]
    operational_impact: str


class DigitalTwinResult(BaseModel):
    equipment_id: str
    virtual_status: Literal["OPERATIONAL", "WARNING", "CRITICAL"]
    health_status: Literal["HEALTHY", "DEGRADED", "CRITICAL"]
    location: str
    anomalies: list[str]
    simulated_impact: str
    human_approval_required: bool


def simulate_digital_twin(data: DigitalTwinInput) -> DigitalTwinResult:

    if data.risk_level == "CRITICAL":
        virtual_status = "CRITICAL"
        health_status = "CRITICAL"

    elif data.risk_level in ["HIGH", "MEDIUM"]:
        virtual_status = "WARNING"
        health_status = "DEGRADED"

    else:
        virtual_status = "OPERATIONAL"
        health_status = "HEALTHY"

    simulated_impact = (
        f"Virtual equipment {data.equipment_id} is represented as "
        f"{virtual_status}. Operational impact: {data.operational_impact}"
    )

    return DigitalTwinResult(
        equipment_id=data.equipment_id,
        virtual_status=virtual_status,
        health_status=health_status,
        location="Mining Zone A - Conveyor Area",
        anomalies=data.anomalies,
        simulated_impact=simulated_impact,
        human_approval_required=data.risk_level in ["HIGH", "CRITICAL"]
    )
