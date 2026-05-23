from typing import TypedDict
from langgraph.graph import StateGraph, END

class CushionState(TypedDict):
    spec_data: dict
    approved: bool

def validate_materials(state: CushionState) -> CushionState:
    # Logic to verify flame retardancy and durability spec
    state['approved'] = state['spec_data'].get('fire_rating') == 'FMVSS302'
    return state

def check_dimensions(state: CushionState) -> CushionState:
    # Logic to verify dimensional tolerances
    return state

graph = StateGraph(CushionState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph.set_entry_point('validate_materials')
graph = graph.compile()
