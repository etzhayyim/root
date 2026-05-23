from typing import TypedDict
from langgraph.graph import StateGraph, END

class SiloState(TypedDict):
    capacity: float
    material: str
    is_compliant: bool

def validate_structural_specs(state: SiloState):
    state['is_compliant'] = state['capacity'] > 0 and bool(state['material'])
    print(f"Validating silo with capacity: {state['capacity']}")
    return state

graph = StateGraph(SiloState)
graph.add_node("validate", validate_structural_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
