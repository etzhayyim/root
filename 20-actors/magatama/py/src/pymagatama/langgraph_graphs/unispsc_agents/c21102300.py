from typing import TypedDict
from langgraph.graph import StateGraph, END

class SprayEquipmentState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: SprayEquipmentState):
    pressure = state['specs'].get('pressure', 0)
    state['is_compliant'] = 1.0 <= pressure <= 20.0
    return state

def check_certification(state: SprayEquipmentState):
    return "compliant" if state['is_compliant'] else "non_compliant"

graph = StateGraph(SprayEquipmentState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()