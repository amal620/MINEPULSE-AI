import pytest
from backend.graph.sensor_graph import run_mining_graph
from backend.monitoring.monitoring_agent import get_monitoring_report


def test_end_to_end_critical_workflow_persists_monitoring():
    output = run_mining_graph({
        "equipment_id": "C-PYTEST",
        "temperature": 92,
        "vibration": 12,
        "speed": 1.8,
    })
    result = output["result"]
    report = output["monitoring_report"]
    assert result["sensor_result"]["status"] == "CRITICAL"
    assert result["incident_result"]["status"] == "AWAITING_APPROVAL"
    assert report["execution_status"] == "SUCCESS"
    assert report["successful_agents"] == 7
    assert report["failed_agents"] == 0
    persisted = get_monitoring_report(output["correlation_id"])
    assert persisted.total_events == 14


def test_normal_workflow_does_not_create_incident():
    output = run_mining_graph({
        "equipment_id": "C-NORMAL",
        "temperature": 55,
        "vibration": 3,
        "speed": 2.4,
    })
    assert output["result"]["sensor_result"]["status"] == "NORMAL"
    assert output["result"]["incident_result"] is None
