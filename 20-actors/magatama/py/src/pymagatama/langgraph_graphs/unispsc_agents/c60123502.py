from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LeatherSpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material(state: LeatherSpecState):
    errors = []
    if state['spec_data'].get('leather_grade') not in ['Full-grain', 'Top-grain']:
        errors.append('Invalid leather grade for high-quality accessories.')
    return {'validation_errors': errors}

def compliance_check(state: LeatherSpecState):
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(LeatherSpecState)
graph.add_node('validate', validate_material)
graph.add_node('check', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()