from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OpticalState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_surface_accuracy(state: OpticalState):
    accuracy = state['spec_data'].get('surface_accuracy', 0)
    if accuracy < 0.1: state['validation_errors'].append('Surface accuracy too low')
    return state

def check_compliance(state: OpticalState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(OpticalState)
graph.add_node('validate', validate_surface_accuracy)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()