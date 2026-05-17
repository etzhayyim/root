import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class CableTrayState(TypedDict):
    spec_requirements: dict
    validation_errors: Annotated[list, operator.add]
    is_compliant: bool

def validate_load_capacity(state: CableTrayState):
    errors = []
    if state['spec_requirements'].get('load', 0) < 500:
        errors.append('Load capacity below industrial safety threshold.')
    return {'validation_errors': errors}

def check_compliance(state: CableTrayState):
    is_valid = len(state['validation_errors']) == 0
    return {'is_compliant': is_valid}

graph = StateGraph(CableTrayState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()