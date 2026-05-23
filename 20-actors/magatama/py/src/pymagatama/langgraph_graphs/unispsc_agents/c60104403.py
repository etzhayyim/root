from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FossilProcurementState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_provenance(state: FossilProcurementState):
    errors = []
    if not state['specifications'].get('provenance_certification'):
        errors.append('Missing provenance certification')
    return {'validation_errors': errors}

def update_approval_status(state: FossilProcurementState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(FossilProcurementState)
graph.add_node('validate', validate_provenance)
graph.add_node('approve', update_approval_status)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
