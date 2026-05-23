from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServoProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ServoProcurementState):
    errors = []
    if state['spec_data'].get('rated_power_kw', 0) <= 0:
        errors.append('Invalid power rating')
    return {'validation_errors': errors}

def check_compliance(state: ServoProcurementState):
    approved = len(state['validation_errors']) == 0
    return {'approved': approved}

graph = StateGraph(ServoProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
