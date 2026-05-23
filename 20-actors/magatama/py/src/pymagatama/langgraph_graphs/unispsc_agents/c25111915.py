from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DockStepState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    approved: bool

def validate_load_capacity(state: DockStepState):
    capacity = state['spec_sheet'].get('load_capacity', 0)
    if capacity < 500:
        state['validation_errors'].append('Load capacity too low for industrial use.')
    return state

def check_compliance(state: DockStepState):
    compliance = state['spec_sheet'].get('safety_standard', False)
    state['approved'] = compliance
    return state

graph = StateGraph(DockStepState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_safety', check_compliance)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()
