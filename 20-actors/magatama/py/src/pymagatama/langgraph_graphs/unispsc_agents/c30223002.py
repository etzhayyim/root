from typing import TypedDict
from langgraph.graph import StateGraph, END

class TempleSpecState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_structural_specs(state: TempleSpecState):
    """Validates structural load and compliance with architectural style."""
    reqs = state['spec_data']
    state['is_compliant'] = 'material_grade' in reqs and 'load_rating' in reqs
    return state

builder = StateGraph(TempleSpecState)
builder.add_node('validation', validate_structural_specs)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()