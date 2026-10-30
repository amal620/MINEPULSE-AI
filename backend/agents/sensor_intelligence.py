
from pydantic import BaseModel
from typing import Literal


class SensorInput(BaseModel):
    equipment_id: str
    temperature: float
    vibration: float
    speed: float


class SensorAnalysis(BaseModel):
    equipment_id: str
    status: Literal["NORMAL", "WARNING", "CRITICAL"]
    anomalies: list[str]
    explanation: str


def analyze_sensors(data: SensorInput) -> SensorAnalysis:
    anomalies = []

    # Illustrative simulation rules, not real industrial safety thresholds
    if data.temperature > 80:
        anomalies.append("HIGH_TEMPERATURE")

    if data.vibration > 10:
        anomalies.append("HIGH_VIBRATION")

    if data.speed <= 0:
        anomalies.append("EQUIPMENT_STOPPED")

    if len(anomalies) >= 2:
        status = "CRITICAL"
    elif len(anomalies) == 1:
        status = "WARNING"
    else:
        status = "NORMAL"

    explanation = (
        "Anomalies detected: " + ", ".join(anomalies)
        if anomalies
        else "All simulated sensor values are within configured limits."
    )

    return SensorAnalysis(
        equipment_id=data.equipment_id,
        status=status,
        anomalies=anomalies,
        explanation=explanation
    )
