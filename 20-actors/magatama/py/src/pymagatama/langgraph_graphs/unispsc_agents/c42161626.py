from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DialysisStandState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_load_capacity(state: DialysisStandState):
    capacity = state['spec_data'].get('load_capacity', 0)
    if capacity < 50:
        state['validation_errors'].append('Load capacity below minimum safety threshold')
    return state

def check_medical_compliance(state: DialysisStandState):
    if not state['spec_data'].get('iso_13485'):
        state['validation_errors'].append('ISO 13485 certification required')
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(DialysisStandState)
graph.add_node('validate_capacity', validate_load_capacity)
graph.add_node('check_compliance', check_medical_compliance)
graph.set_entry_point('validate_capacity')
graph.add_edge('validate_capacity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()