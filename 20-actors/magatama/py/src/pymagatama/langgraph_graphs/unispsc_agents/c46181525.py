from langgraph.graph import StateGraph, END
from typing import TypedDict

class WorkflowState(TypedDict):
    material_spec: str
    waterproof_rating: int
    is_compliant: bool

def validate_specs(state: WorkflowState):
    """Validates if the rainwear meets waterproof standards."""
    min_rating = 10000
    state['is_compliant'] = state['waterproof_rating'] >= min_rating
    return state

def route_approval(state: WorkflowState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(WorkflowState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
