from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SnapRingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: List[str]

def validate_specs(state: SnapRingState):
    errors = []
    if 'material' not in state['spec_data']:
        errors.append('Missing material specification')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def approval_node(state: SnapRingState):
    return {'validation_passed': True}

graph = StateGraph(SnapRingState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()