from typing import TypedDict
from langgraph.graph import StateGraph, END

class DockState(TypedDict):
    spec_data: dict
    validation_scores: dict

def validate_specs(state: DockState):
    # Simulate CAD/Spec validation for heavy machinery
    score = 1.0 if state['spec_data'].get('load_capacity', 0) > 0 else 0.0
    return {'validation_scores': {'technical_compliance': score}}

def approve_procurement(state: DockState):
    return {'validation_scores': {'status': 'APPROVED'}}

graph = StateGraph(DockState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()