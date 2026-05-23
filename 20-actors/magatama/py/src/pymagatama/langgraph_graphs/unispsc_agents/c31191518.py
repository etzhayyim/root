from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CarbideState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_composition(state: CarbideState):
    errors = []
    if state['spec_data'].get('hardness', 0) < 85:
        errors.append('Hardness value below industrial standards.')
    return {'validation_errors': errors}

def check_compliance(state: CarbideState):
    compliance = len(state['validation_errors']) == 0
    return {'approved': compliance}

graph = StateGraph(CarbideState)
graph.add_node('validate', validate_composition)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
