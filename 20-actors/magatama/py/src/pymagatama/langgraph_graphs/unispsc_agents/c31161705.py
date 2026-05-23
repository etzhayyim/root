from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_dimensions(state: ProcurementState):
    errors = []
    if 'thread' not in state['spec_data']: errors.append('Missing thread specs')
    return {'validation_errors': errors}

def check_compliance(state: ProcurementState):
    is_valid = len(state.get('validation_errors', [])) == 0
    return {'approved': is_valid}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
