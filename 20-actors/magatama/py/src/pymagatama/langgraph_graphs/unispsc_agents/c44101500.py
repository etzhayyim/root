from typing import TypedDict
from langgraph.graph import StateGraph, END

class OfficeEquipmentState(TypedDict):
    model: str
    spec_check: bool
    sla_approved: bool

def validate_specs(state: OfficeEquipmentState):
    print(f"Validating specs for {state['model']}")
    return {"spec_check": True}

def check_sla(state: OfficeEquipmentState):
    print("Verifying maintenance service agreement levels")
    return {"sla_approved": True}

graph = StateGraph(OfficeEquipmentState)
graph.add_node("validate", validate_specs)
graph.add_node("sla", check_sla)
graph.set_entry_point("validate")
graph.add_edge("validate", "sla")
graph.add_edge("sla", END)
compiled_graph = graph.compile()