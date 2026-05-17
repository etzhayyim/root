from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AluminumState(TypedDict):
    spec: dict
    validation_errors: List[str]
    is_approved: bool

def validate_alloy_compliance(state: AluminumState):
    alloy = state['spec'].get('Alloy', '1100')
    errors = []
    if alloy not in ['1100', '3003', '5052', '6061']:
        errors.append(f'Invalid alloy grade: {alloy}')
    return {'validation_errors': errors}

def approval_check(state: AluminumState):
    return 'approved' if not state['validation_errors'] else 'rejected'

graph = StateGraph(AluminumState)
graph.add_node('validate', validate_alloy_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()