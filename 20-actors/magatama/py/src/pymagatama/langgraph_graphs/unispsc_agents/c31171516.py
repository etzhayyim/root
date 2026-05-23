from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_load_capacity(state: BearingState):
    errors = []
    if state['spec_data'].get('load_rating_kn', 0) <= 0:
        errors.append('Invalid load rating')
    return {'validation_errors': errors}

def check_compliance(state: BearingState):
    compliant = len(state['validation_errors']) == 0
    return {'is_compliant': compliant}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
