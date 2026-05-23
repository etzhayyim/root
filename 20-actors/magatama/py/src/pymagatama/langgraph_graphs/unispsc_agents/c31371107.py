from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrickSpecState(TypedDict):
    dimensions: dict
    material_grade: str
    quality_passed: bool

def validate_dimensions(state: BrickSpecState):
    # Simulate CAD/Spec validation
    if state['dimensions'].get('tolerance') < 0.05:
        state['quality_passed'] = True
    return state

def approve_procurement(state: BrickSpecState):
    return 'APPROVED' if state['quality_passed'] else 'REJECTED'

graph = StateGraph(BrickSpecState)
graph.add_node('validate', validate_dimensions)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.set_entry_point('validate')
graph.add_edge('approve', END)
graph = graph.compile()
