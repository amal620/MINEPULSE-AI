
from pydantic import BaseModel
from typing import Literal


class DiagnosisInput(BaseModel):
    equipment_id: str
    temperature: float
    vibration: float
    speed: float
    sensor_status: Literal["NORMAL", "WARNING", "CRITICAL"]
    anomalies: list[str]


class DiagnosisResult(BaseModel):
    equipment_id: str
    possible_causes: list[str]
    explanation: str
    confidence_score: int
    recommended_inspection: list[str]


def predictive_diagnosis(data: DiagnosisInput) -> DiagnosisResult:
    causes = []
    inspections = []

    if "HIGH_TEMPERATURE" in data.anomalies:
        causes.append("Possible overheating or cooling system issue")
        inspections.append("Inspect the cooling and ventilation system")

    if "HIGH_VIBRATION" in data.anomalies:
        causes.append("Possible bearing wear or mechanical imbalance")
        inspections.append("Inspect bearings, alignment and mechanical components")

    if "EQUIPMENT_STOPPED" in data.anomalies:
        causes.append("Possible mechanical or electrical failure")
        inspections.append("Check the equipment power supply and drive system")

    if not causes:
        causes.append("No specific fault identified from the available sensor data")
        inspections.append("Continue routine monitoring")

    confidence = min(95, 60 + (len(data.anomalies) * 15))

    explanation = (
        "Potential causes identified from simulated sensor anomalies. "
        "These hypotheses require inspection and confirmation."
    )

    return DiagnosisResult(
        equipment_id=data.equipment_id,
        possible_causes=causes,
        explanation=explanation,
        confidence_score=confidence,
        recommended_inspection=inspections
    )
