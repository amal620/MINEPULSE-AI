
from pydantic import BaseModel
from typing import Literal


class ResourceInput(BaseModel):
    equipment_id: str
    recommended_option: str
    required_resources: list[str]
    human_approval_required: bool


class ResourceResult(BaseModel):
    equipment_id: str
    assigned_resources: list[str]
    missing_resources: list[str]
    planning_status: Literal[
        "READY_FOR_REVIEW",
        "RESOURCES_INCOMPLETE",
        "AWAITING_APPROVAL"
    ]
    coordination_summary: str
    human_approval_required: bool


def coordinate_resources(data: ResourceInput) -> ResourceResult:

    # Simulation only: no real inventory or staff database connected.
    simulated_available_resources = [
        "Maintenance team",
        "Technical inspection",
        "Maintenance planning",
        "Monitoring system",
        "Technical supervision",
    ]

    assigned = [
        resource
        for resource in data.required_resources
        if resource in simulated_available_resources
    ]

    missing = [
        resource
        for resource in data.required_resources
        if resource not in simulated_available_resources
    ]

    if missing:
        status = "RESOURCES_INCOMPLETE"
    elif data.human_approval_required:
        status = "AWAITING_APPROVAL"
    else:
        status = "READY_FOR_REVIEW"

    summary = (
        f"Resource coordination for {data.equipment_id}: "
        f"{len(assigned)} resources identified and "
        f"{len(missing)} resources missing. "
        f"Recommended action: {data.recommended_option}."
    )

    return ResourceResult(
        equipment_id=data.equipment_id,
        assigned_resources=assigned,
        missing_resources=missing,
        planning_status=status,
        coordination_summary=summary,
        human_approval_required=data.human_approval_required
    )
