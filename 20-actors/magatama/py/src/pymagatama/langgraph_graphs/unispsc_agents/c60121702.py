from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StampPadState(TypedDict):
    brand: str
    ink_type: str
    size_dimensions: str
    is_validated: bool

def validate_ink_spec(state: StampPadState):
    # Business logic for ink type validation
    valid_types = ['oil-based', 'water-based']
    state['is_validated'] = state['ink_type'] in valid_types
    return state

def route_by_validation(state: StampPadState):
    return 'success' if state['is_validated'] else 'error'

graph = StateGraph(StampPadState)
graph.add_node('validate', validate_ink_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
