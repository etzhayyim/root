from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LinearBearingState(TypedDict):
    part_number: str
    specifications: dict
    compliance_check: bool
    export_control_flag: bool

def validate_load_specs(state: LinearBearingState):
    # Simulate CAD/Spec validation for linear bearings
    print(f"Validating specs for {state['part_number']}")
    state['compliance_check'] = True
    return state

def export_review(state: LinearBearingState):
    # Dual-use review logic
    state['export_control_flag'] = False
    return state

graph = StateGraph(LinearBearingState)
graph.add_node("validate", validate_load_specs)
graph.add_node("export", export_review)
graph.set_entry_point("validate")
graph.add_edge("validate", "export")
graph.add_edge("export", END)
graph = graph.compile()
