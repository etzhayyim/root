from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class JoistState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_structural_specs(state: JoistState):
    errors = []
    if state['spec_data'].get('moisture_content', 0) > 20:
        errors.append('High moisture content: Risk of warping')
    return {'validation_errors': errors}

def check_compliance(state: JoistState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(JoistState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
