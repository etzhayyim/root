from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CraneState(TypedDict):
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_specs(state: CraneState):
    errors = []
    if state['specs'].get('max_capacity', 0) <= 0:
        errors.append('Invalid lifting capacity')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_by_validation(state: CraneState):
    return 'approve' if state['approved'] else 'reject'

graph = StateGraph(CraneState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'approve': END, 'reject': END})
