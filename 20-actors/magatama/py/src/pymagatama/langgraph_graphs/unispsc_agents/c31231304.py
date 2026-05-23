from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnesiumSpecState(TypedDict):
    alloy_grade: str
    thickness_mm: float
    has_coating: bool
    is_compliant: bool

def validate_magnesium_specs(state: MagnesiumSpecState):
    # Magnesium is highly flammable; check coating compliance
    if state['thickness_mm'] < 0.5 and not state['has_coating']:
        return {'is_compliant': False}
    return {'is_compliant': True}

graph = StateGraph(MagnesiumSpecState)
graph.add_node('validate', validate_magnesium_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
