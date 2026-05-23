from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DentureCupState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material_safety(state: DentureCupState):
    errors = []
    if 'BPA-Free' not in state['spec_data'].get('certifications', []):
        errors.append('Missing BPA-Free certification')
    return {'validation_errors': errors}

def final_approval(state: DentureCupState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(DentureCupState)
graph.add_node('validate', validate_material_safety)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
