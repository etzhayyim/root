from typing import TypedDict
from langgraph.graph import StateGraph, END

class DSPState(TypedDict):
    spec_sheet: dict
    eccn_check: bool
    validation_passed: bool

def validate_eccn(state: DSPState):
    eccn = state['spec_sheet'].get('export_control_classification_eccn')
    state['eccn_check'] = eccn is not None and len(eccn) > 0
    return state

def validate_specs(state: DSPState):
    state['validation_passed'] = 'clock_speed_mhz' in state['spec_sheet']
    return state

graph = StateGraph(DSPState)
graph.add_node('validate_eccn', validate_eccn)
graph.add_node('validate_specs', validate_specs)
graph.set_entry_point('validate_eccn')
graph.add_edge('validate_eccn', 'validate_specs')
graph.add_edge('validate_specs', END)
graph = graph.compile()
