
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from time import perf_counter

from backend.incidents.incident_manager import (
    IncidentInput,
    create_incident,
)

from backend.monitoring.monitoring_agent import (
    create_execution,
    record_agent_event,
    get_monitoring_report,
)
from backend.agents.sensor_intelligence import (
    SensorInput,
    analyze_sensors,
)
from backend.agents.predictive_diagnosis import (
    DiagnosisInput,
    predictive_diagnosis,
)
from backend.agents.risk_assessment import (
    RiskInput,
    assess_risk,
)
from backend.agents.digital_twin_simulator import (
    DigitalTwinInput,
    simulate_digital_twin,
)
from backend.agents.decision_optimizer import (
    DecisionInput,
    optimize_decision,
)
from backend.agents.resource_coordinator import (
    ResourceInput,
    coordinate_resources,
)


class MiningState(TypedDict):
    correlation_id: str
    equipment_id: str
    temperature: float
    vibration: float
    speed: float

    incident_result: dict | None
    sensor_result: dict
    diagnosis_result: dict
    risk_result: dict
    digital_twin_result: dict
    decision_result: dict
    resource_result: dict


# AGENT 01
def sensor_intelligence_node(state: MiningState):
    data = SensorInput(
        equipment_id=state["equipment_id"],
        temperature=state["temperature"],
        vibration=state["vibration"],
        speed=state["speed"],
    )

    result = analyze_sensors(data)
    return {"sensor_result": result.model_dump()}


# AGENT 02
def predictive_diagnosis_node(state: MiningState):
    sensor = state["sensor_result"]

    data = DiagnosisInput(
        equipment_id=state["equipment_id"],
        temperature=state["temperature"],
        vibration=state["vibration"],
        speed=state["speed"],
        sensor_status=sensor["status"],
        anomalies=sensor["anomalies"],
    )

    result = predictive_diagnosis(data)
    return {"diagnosis_result": result.model_dump()}


# AGENT 03
def risk_assessment_node(state: MiningState):
    sensor = state["sensor_result"]
    diagnosis = state["diagnosis_result"]

    data = RiskInput(
        equipment_id=state["equipment_id"],
        sensor_status=sensor["status"],
        anomalies=sensor["anomalies"],
        possible_causes=diagnosis["possible_causes"],
        confidence_score=diagnosis["confidence_score"],
    )

    result = assess_risk(data)
    return {"risk_result": result.model_dump()}


# AGENT 04
def digital_twin_node(state: MiningState):
    sensor = state["sensor_result"]
    risk = state["risk_result"]

    data = DigitalTwinInput(
        equipment_id=state["equipment_id"],
        sensor_status=sensor["status"],
        risk_level=risk["risk_level"],
        anomalies=sensor["anomalies"],
        operational_impact=risk["operational_impact"],
    )

    result = simulate_digital_twin(data)
    return {"digital_twin_result": result.model_dump()}


# AGENT 05
def decision_optimizer_node(state: MiningState):
    risk = state["risk_result"]
    twin = state["digital_twin_result"]

    data = DecisionInput(
        equipment_id=state["equipment_id"],
        risk_level=risk["risk_level"],
        operational_impact=risk["operational_impact"],
        virtual_status=twin["virtual_status"],
    )

    result = optimize_decision(data)
    return {"decision_result": result.model_dump()}


# AGENT 06
def resource_coordinator_node(state: MiningState):
    decision = state["decision_result"]

    selected_option = decision["recommended_option"]

    selected = next(
        option for option in decision["options"]
        if option["option_name"] == selected_option
    )

    data = ResourceInput(
        equipment_id=state["equipment_id"],
        recommended_option=selected_option,
        required_resources=selected["required_resources"],
        human_approval_required=decision["human_approval_required"],
    )

    result = coordinate_resources(data)
    return {"resource_result": result.model_dump()}

def monitored_node(agent_name, operation):

    def execute(state: MiningState):
        correlation_id = state["correlation_id"]
        start_time = perf_counter()

        record_agent_event(
            correlation_id,
            agent_name,
            "STARTED",
            "Agent execution started"
        )

        try:
            result = operation(state)

            duration = round(perf_counter() - start_time, 4)

            record_agent_event(
                correlation_id,
                agent_name,
                "SUCCESS",
                "Agent execution completed",
                duration_seconds=duration
            )

            return result

        except Exception as error:
            duration = round(perf_counter() - start_time, 4)

            record_agent_event(
                correlation_id,
                agent_name,
                "FAILED",
                str(error),
                duration_seconds=duration
            )

            raise

    return execute

# AGENT 08 — INCIDENT MANAGEMENT
def incident_management_node(state: MiningState):

    sensor = state["sensor_result"]
    diagnosis = state["diagnosis_result"]
    risk = state["risk_result"]
    decision = state["decision_result"]

    data = IncidentInput(
        equipment_id=state["equipment_id"],
        risk_level=risk["risk_level"],
        anomalies=sensor["anomalies"],
        possible_causes=diagnosis["possible_causes"],
        operational_impact=risk["operational_impact"],
        recommended_action=decision["recommendation_reason"],
    )

    incident = create_incident(data)

    return {
        "incident_result": (
            incident.model_dump() if incident else None
        )
    }

# BUILD LANGGRAPH
def build_mining_graph():
    workflow = StateGraph(MiningState)

    workflow.add_node(
        "sensor_intelligence",
        monitored_node("Sensor Intelligence", sensor_intelligence_node)
    )

    workflow.add_node(
        "predictive_diagnosis",
        monitored_node("Predictive Diagnosis", predictive_diagnosis_node)
    )

    workflow.add_node(
        "risk_assessment",
        monitored_node("Risk Assessment", risk_assessment_node)
    )

    workflow.add_node(
        "digital_twin",
        monitored_node("Digital Twin Simulator", digital_twin_node)
    )

    workflow.add_node(
        "decision_optimizer",
        monitored_node("Decision Optimizer", decision_optimizer_node)
    )

    workflow.add_node(
        "resource_coordinator",
        monitored_node("Resource Coordinator", resource_coordinator_node)
    )

    workflow.add_node(
       "incident_management",
        monitored_node(
            "Incident Management",
            incident_management_node
        )
    )
    
    workflow.add_edge("resource_coordinator", "incident_management")
    workflow.add_edge("incident_management", END)
    workflow.add_edge(START, "sensor_intelligence")
    workflow.add_edge("sensor_intelligence", "predictive_diagnosis")
    workflow.add_edge("predictive_diagnosis", "risk_assessment")
    workflow.add_edge("risk_assessment", "digital_twin")
    workflow.add_edge("digital_twin", "decision_optimizer")
    workflow.add_edge("decision_optimizer", "resource_coordinator")
    
    return workflow.compile()


mining_graph = build_mining_graph()
def run_mining_graph(input_data: dict):
    correlation_id = create_execution()
    initial_state = {**input_data, "correlation_id": correlation_id}

    try:
        result = mining_graph.invoke(initial_state)
    except Exception:
        # Agent-level failure is already persisted by monitored_node.
        # Preserve the correlation id so the failed execution remains traceable.
        raise

    report = get_monitoring_report(correlation_id)
    return {
        "correlation_id": correlation_id,
        "result": result,
        "monitoring_report": report.model_dump(),
    }
