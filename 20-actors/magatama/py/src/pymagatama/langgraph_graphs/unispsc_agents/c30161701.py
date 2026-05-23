from typing import TypedDict
from langgraph.graph import StateGraph, END

class CarpetState(TypedDict):
    specs: dict
    validation_score: float
    approved: bool

def validate_specs(state: CarpetState) -> dict:
    required_fields = ['Flame Retardancy Rating', 'Material Composition']
    all_present = all(field in state['specs'] for field in required_fields)
    return {'validation_score': 1.0 if all_present else 0.0}

def check_compliance(state: CarpetState) -> dict:
    is_approved = state.get('validation_score', 0) >= 1.0
    return {'approved': is_approved}

graph = StateGraph(CarpetState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
