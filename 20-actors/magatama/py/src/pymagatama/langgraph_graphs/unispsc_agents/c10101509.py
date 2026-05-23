from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AnimalProcurementState(TypedDict):
    animal_id: str
    health_status: str
    quarantine_clearance: bool
    log: Annotated[Sequence[str], operator.add]

def validate_health_node(state: AnimalProcurementState):
    # Simulate health check logic
    return {"health_status": "cleared", "log": [f"Health check verified for {state['animal_id']}"]}

def quarantine_node(state: AnimalProcurementState):
    # Simulate quarantine process
    return {"quarantine_clearance": True, "log": ["Quarantine protocol complete"]}

workflow = StateGraph(AnimalProcurementState)
workflow.add_node("health_check", validate_health_node)
workflow.add_node("quarantine", quarantine_node)
workflow.set_entry_point("health_check")
workflow.add_edge("health_check", "quarantine")
workflow.add_edge("quarantine", END)

graph = workflow.compile()
