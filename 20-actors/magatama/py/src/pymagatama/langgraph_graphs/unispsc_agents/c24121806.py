from typing import TypedDict
from langgraph.graph import StateGraph, END

class CanState(TypedDict):
    material_spec: str
    pressure_tolerance: float
    compliant: bool

def validate_materials(state: CanState):
    state['compliant'] = state['material_spec'] == '3104' and state['pressure_tolerance'] > 90.0
    return state

def check_quality(state: CanState):
    print(f"Quality assurance check: {state['compliant']}")
    return state

graph = StateGraph(CanState)
graph.add_node("validate", validate_materials)
graph.add_node("quality", check_quality)
graph.set_entry_point("validate")
graph.add_edge("validate", "quality")
graph.add_edge("quality", END)
graph = graph.compile()
