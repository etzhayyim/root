from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CrimpingToolState(TypedDict):
    part_number: str
    crimp_force_kn: float
    compatibility_checked: bool
    approved: bool

def validate_specs(state: CrimpingToolState):
    # Simulate validation logic for die tolerances
    state['compatibility_checked'] = state['crimp_force_kn'] > 0
    return state

def approve_die(state: CrimpingToolState):
    state['approved'] = state['compatibility_checked']
    return state

graph = StateGraph(CrimpingToolState)
graph.add_node("validate", validate_specs)
graph.add_node("approve", approve_die)
graph.set_entry_point("validate")
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
app = graph.compile()