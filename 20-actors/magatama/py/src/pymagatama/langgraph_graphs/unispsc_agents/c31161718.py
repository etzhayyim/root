from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ToggleNutState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_load_specs(state: ToggleNutState):
    errors = []
    if state['specifications'].get('load_capacity', 0) <= 0:
        errors.append('Invalid load capacity')
    return {'validation_errors': errors}

def check_compliance(state: ToggleNutState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(ToggleNutState)
graph.add_node('validate', validate_load_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()