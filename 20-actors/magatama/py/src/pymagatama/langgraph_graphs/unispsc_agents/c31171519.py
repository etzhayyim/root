from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BearingProcurementState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_load_specs(state: BearingProcurementState):
    errors = []
    if 'load_capacity' not in state['specifications']:
        errors.append('Missing mandatory load capacity specification')
    return {'validation_errors': errors}

def check_compliance(state: BearingProcurementState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(BearingProcurementState)
graph.add_node('validate', validate_load_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
