from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    dimensions: dict
    material_spec: str
    ndt_results: str
    approved: bool

def validate_dimensions(state: ForgingState):
    # Simulate CAD/Engineering check
    state['approved'] = all(val > 0 for val in state['dimensions'].values())
    return state

def verify_metallurgy(state: ForgingState):
    # Simulate chemical composition validation
    if 'Nickel' in state['material_spec']:
        state['approved'] = state['approved'] and True
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_dimensions)
graph.add_node('metallurgy', verify_metallurgy)
graph.set_entry_point('validate')
graph.add_edge('validate', 'metallurgy')
graph.add_edge('metallurgy', END)
graph = graph.compile()