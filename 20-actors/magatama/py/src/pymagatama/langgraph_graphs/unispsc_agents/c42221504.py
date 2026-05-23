from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_biocompatibility(state: CatheterState):
    errors = []
    if 'iso_10993_cert' not in state['spec_data']:
        errors.append('Missing ISO 10993 certification')
    return {'validation_errors': errors}

def decision_node(state: CatheterState):
    return 'approved' if not state['validation_errors'] else 'rejected'

workflow = StateGraph(CatheterState)
workflow.add_node('validate', validate_biocompatibility)
workflow.add_edge('validate', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
