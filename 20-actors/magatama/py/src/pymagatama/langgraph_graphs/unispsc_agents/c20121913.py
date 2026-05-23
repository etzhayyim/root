from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MetalProcureState(TypedDict):
    part_id: str
    specs: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    status: str

def validate_material(state: MetalProcureState):
    # Simulate CAD/Spec validation for 20121913
    logs = [f"Validating composition for {state['part_id']}"]
    return {"validation_logs": logs, "status": "validated"}

def check_compliance(state: MetalProcureState):
    # Simulate export control/dual-use check
    logs = ["Compliance check completed"]
    return {"validation_logs": logs, "status": "approved"}

graph = StateGraph(MetalProcureState)
graph.add_node("validate", validate_material)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
