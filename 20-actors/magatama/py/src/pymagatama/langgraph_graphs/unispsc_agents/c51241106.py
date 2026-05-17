from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    material: str
    purity: float
    verified: bool
    safety_check: bool

def validate_material(state: ProcurementState):
    print(f'Checking {state["material"]} specs...')
    state['verified'] = state['purity'] >= 99.0
    return state

def safety_compliance(state: ProcurementState):
    print('Performing hazmat safety check...')
    state['safety_check'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_material)
graph.add_node("safety", safety_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph = graph.compile()