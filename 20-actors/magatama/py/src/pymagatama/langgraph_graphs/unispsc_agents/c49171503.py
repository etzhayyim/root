from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VaultingState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_safety_specs(state: VaultingState):
    errors = []
    if not state['spec_data'].get('fig_certified', False):
        errors.append('Missing FIG certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_stability(state: VaultingState):
    if state['spec_data'].get('max_load', 0) < 150:
        return {'validation_errors': state['validation_errors'] + ['Load capacity insufficient']}
    return {}

graph = StateGraph(VaultingState)
graph.add_node('safety_check', validate_safety_specs)
graph.add_node('stability_check', check_stability)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'stability_check')
graph.add_edge('stability_check', END)
graph = graph.compile()
