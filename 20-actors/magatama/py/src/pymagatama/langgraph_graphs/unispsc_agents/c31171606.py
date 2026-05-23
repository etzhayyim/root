from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlangeBushingState(TypedDict):
    material: str
    tolerance_check: bool
    dimensions: dict
    approved: bool

def validate_specs(state: FlangeBushingState):
    # Simulate CAD/Spec validation logic
    tolerance = state['dimensions'].get('tolerance', 0.05)
    return {'tolerance_check': tolerance <= 0.02}

def approval_check(state: FlangeBushingState):
    return {'approved': state['tolerance_check']}

graph = StateGraph(FlangeBushingState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
