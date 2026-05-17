from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StretcherState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_load_capacity(state: StretcherState):
    errors = []
    if state['spec_data'].get('load_capacity_kg', 0) < 150:
        errors.append('Load capacity below minimum safety threshold')
    return {'validation_errors': errors}

def check_compliance(state: StretcherState):
    if 'ISO_13485' not in state['spec_data'].get('certifications', []):
        return {'validation_errors': state['validation_errors'] + ['Missing medical device certification']}
    return {}

graph = StateGraph(StretcherState)
graph.add_node('validate_capacity', validate_load_capacity)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_capacity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_capacity')
graph = graph.compile()