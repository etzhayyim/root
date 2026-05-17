from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ScreenState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_sensitivity(state: ScreenState):
    errors = []
    if state['spec_data'].get('sensitivity_class', 0) < 100:
        errors.append('Sensitivity below standard threshold')
    return {'validation_errors': errors}

def compliance_check(state: ScreenState):
    is_safe = state['spec_data'].get('radiation_safety_cert') is not None
    return {'approved': is_safe and not state['validation_errors']}

graph = StateGraph(ScreenState)
graph.add_node('validate', validate_sensitivity)
graph.add_node('compliance', compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()