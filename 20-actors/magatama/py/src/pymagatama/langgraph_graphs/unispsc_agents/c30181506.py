from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class UrinalState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: UrinalState):
    errors = []
    if state['spec_data'].get('flush_rate', 0) > 2.0:
        errors.append('Flush rate exceeds efficiency limits')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_approval(state: UrinalState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(UrinalState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()