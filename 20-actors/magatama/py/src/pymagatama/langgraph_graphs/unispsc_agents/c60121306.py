from typing import TypedDict
from langgraph.graph import StateGraph, END

class CutterState(TypedDict):
    model_id: str
    blade_spec: str
    safety_check: bool

def validate_blade(state: CutterState):
    return {'blade_spec': f'Validated:{state["blade_spec"]}'}

def safety_audit(state: CutterState):
    return {'safety_check': True}

graph = StateGraph(CutterState)
graph.add_node("validate", validate_blade)
graph.add_node("audit", safety_audit)
graph.add_edge("validate", "audit")
graph.add_edge("audit", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()