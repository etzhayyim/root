from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_dimensions(state: KitchenProcurementState):
    errors = []
    if 'dimensions' not in state['spec_data']: errors.append('Missing dimensions')
    return {'validation_errors': errors}

def check_compliance(state: KitchenProcurementState):
    is_valid = len(state['validation_errors']) == 0
    return {'approved': is_valid}

graph = StateGraph(KitchenProcurementState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
