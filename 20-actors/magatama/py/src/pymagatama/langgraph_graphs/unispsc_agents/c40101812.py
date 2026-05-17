from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExchangeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_pressure_specs(state: ExchangeState):
    errors = []
    if state['spec_data'].get('pressure', 0) > 1000:
        errors.append('High pressure rating requires extra safety verification')
    return {'validation_errors': errors}

def check_compliance(state: ExchangeState):
    approved = len(state['validation_errors']) == 0
    return {'approved': approved}

graph = StateGraph(ExchangeState)
graph.add_node('validate', validate_pressure_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()