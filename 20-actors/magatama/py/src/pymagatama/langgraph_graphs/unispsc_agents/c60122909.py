from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BeadProcurementState(TypedDict):
    bead_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: BeadProcurementState):
    errors = []
    if state['bead_specs'].get('material') != 'plastic':
        errors.append('Invalid material type')
    return {'validation_errors': errors}

def approval_node(state: BeadProcurementState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(BeadProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
