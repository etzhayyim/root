from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LabBottleState(TypedDict):
    material: str
    capacity_ml: int
    is_compliant: bool
    validation_log: List[str]

def validate_material(state: LabBottleState):
    allowed = ['LDPE', 'HDPE', 'PP']
    state['is_compliant'] = state['material'] in allowed
    state['validation_log'].append(f"Material check: {state['material']} - {'OK' if state['is_compliant'] else 'FAIL'}")
    return state

def check_capacity(state: LabBottleState):
    if state['capacity_ml'] <= 0:
        state['is_compliant'] = False
        state['validation_log'].append("Invalid capacity")
    return state

graph = StateGraph(LabBottleState)
graph.add_node("validate", validate_material)
graph.add_node("capacity", check_capacity)
graph.add_edge("validate", "capacity")
graph.add_edge("capacity", END)
graph.set_entry_point("validate")
graph = graph.compile()