from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlasticState(TypedDict):
    material: str
    dimensions: dict
    approved: bool

def validate_specs(state: PlasticState):
    state['approved'] = all(k in state['dimensions'] for k in ['length', 'diameter'])
    print(f"Validation status: {state['approved']}")
    return state

graph = StateGraph(PlasticState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
