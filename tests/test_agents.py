from backend.agents.sensor_intelligence import SensorInput, analyze_sensors
from backend.agents.predictive_diagnosis import DiagnosisInput, predictive_diagnosis
from backend.agents.risk_assessment import RiskInput, assess_risk
from backend.agents.digital_twin_simulator import DigitalTwinInput, simulate_digital_twin
from backend.agents.decision_optimizer import DecisionInput, optimize_decision
from backend.agents.resource_coordinator import ResourceInput, coordinate_resources


def test_sensor_detects_two_simulated_anomalies():
    result = analyze_sensors(SensorInput(
        equipment_id="C-TEST", temperature=92, vibration=12, speed=1.8
    ))
    assert result.status == "CRITICAL"
    assert set(result.anomalies) == {"HIGH_TEMPERATURE", "HIGH_VIBRATION"}


def test_sensor_normal_case():
    result = analyze_sensors(SensorInput(
        equipment_id="C-TEST", temperature=55, vibration=3, speed=2.4
    ))
    assert result.status == "NORMAL"
    assert result.anomalies == []


def test_predictive_diagnosis_returns_hypotheses():
    result = predictive_diagnosis(DiagnosisInput(
        equipment_id="C-TEST", temperature=92, vibration=12, speed=1.8,
        sensor_status="CRITICAL",
        anomalies=["HIGH_TEMPERATURE", "HIGH_VIBRATION"],
    ))
    assert len(result.possible_causes) >= 2
    assert 0 <= result.confidence_score <= 100


def test_critical_risk_requires_human_review():
    result = assess_risk(RiskInput(
        equipment_id="C-TEST", sensor_status="CRITICAL",
        anomalies=["HIGH_TEMPERATURE"], possible_causes=["Overheating"],
        confidence_score=75,
    ))
    assert result.risk_level == "CRITICAL"
    assert result.human_approval_required is True


def test_digital_twin_maps_critical_state():
    result = simulate_digital_twin(DigitalTwinInput(
        equipment_id="C-TEST", sensor_status="CRITICAL",
        risk_level="CRITICAL", anomalies=["HIGH_VIBRATION"],
        operational_impact="Potential interruption",
    ))
    assert result.virtual_status == "CRITICAL"
    assert result.health_status == "CRITICAL"


def test_decision_optimizer_selects_immediate_for_critical():
    result = optimize_decision(DecisionInput(
        equipment_id="C-TEST", risk_level="CRITICAL",
        operational_impact="Potential damage", virtual_status="CRITICAL",
    ))
    assert result.recommended_option == "Immediate Maintenance"
    assert result.human_approval_required is True


def test_resource_coordinator_reports_missing_parts():
    result = coordinate_resources(ResourceInput(
        equipment_id="C-TEST", recommended_option="Immediate Maintenance",
        required_resources=["Maintenance team", "Specialist crane"],
        human_approval_required=True,
    ))
    assert result.assigned_resources == ["Maintenance team"]
    assert result.missing_resources == ["Specialist crane"]
    assert result.planning_status == "RESOURCES_INCOMPLETE"
