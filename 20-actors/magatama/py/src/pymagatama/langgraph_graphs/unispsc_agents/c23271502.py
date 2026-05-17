from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrazingState(TypedDict):
    power_required: float
    safety_check_passed: bool
    is_compliant: bool

def validate_specs(state: BrazingState):
    state['is_compliant'] = state['power_required'] > 0
    return {'is_compliant': state['is_compliant']}

def perform_safety_check(state: BrazingState):
    state['safety_check_passed'] = True
    return {'safety_check_passed': True}

graph = StateGraph(BrazingState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', perform_safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()