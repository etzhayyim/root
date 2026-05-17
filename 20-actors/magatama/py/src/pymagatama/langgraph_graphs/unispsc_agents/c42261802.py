from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    spec_requirements: List[str]
    approved: bool
    validation_notes: str

def validate_specs(state: ProcurementState):
    required = ['Material composition', 'Load capacity']
    missing = [s for s in required if s not in state['spec_requirements']]
    if missing:
        return {'approved': False, 'validation_notes': f'Missing: {missing}'}
    return {'approved': True, 'validation_notes': 'Verified clinical grade'}

def route_by_validation(state: ProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()